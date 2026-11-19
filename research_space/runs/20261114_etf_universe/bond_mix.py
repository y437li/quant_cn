"""Which bonds: 5-year only, or short + long (5y + 30y)? (2026-11-14). User: "5年国债？不用30年国债，可以短长都配吗？".
Book as split_sweep.py: 股/金/商 risk budget scaled to (1 - b) of capital, b in a bond sleeve with the trend switch, A股 plan-24
timing, 15 bp, 2014-01..2026-11. Bond ETFs before listing are proxied from the 中债国债 curve, daily y/252 − D·Δy + ½·C·Δy²
(511010 5y D 4.5; 511020 7y D 6.5; 511260 10y D 8.5; 511090 30y D 19), as bond_stress.py; proxy vs ETF correlation printed.
Sleeves (equal capital inside): 5y; 5y+10y; 5y+30y (barbell); 5y+10y+30y; 30y; 5/5-10/10 (the ⑤ set). Splits b = 0.2 and 0.4.
"""
from __future__ import annotations
import importlib.util, os
from pathlib import Path
import duckdb, numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fl", HERE / "full_scheme_long.py")
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
fs, sy, om = fl.fs, fl.sy, fl.om
LAKE = Path("/Volumes/Treasury/quant_cn_lake")
pd.set_option("display.width", 260)
LEGS = {"511010.SH": ("y5", 4.5, 25), "511020.SH": ("y7", 6.5, 50), "511260.SH": ("y10", 8.5, 90), "511090.SH": ("y30", 19.0, 450)}
SLEEVES = {"5年": ["511010.SH"], "5年+10年": ["511010.SH", "511260.SH"], "5年+30年(哑铃)": ["511010.SH", "511090.SH"],
           "5年+10年+30年": ["511010.SH", "511260.SH", "511090.SH"], "只30年": ["511090.SH"], "5/5-10/10年(⑤)": ["511010.SH", "511020.SH", "511260.SH"]}


def curve_proxy(index: pd.DatetimeIndex) -> pd.DataFrame:
    Y = duckdb.connect().execute(f"select trade_date, avg(y_5y) y5, avg(y_7y) y7, avg(y_10y) y10, avg(y_30y) y30 from read_parquet('{LAKE}/curated/macro/cn_bond_yield.parquet') "
                                 "where curve_name = '中债国债收益率曲线' group by 1 order by 1").df()
    Y["trade_date"] = pd.to_datetime(Y.trade_date); Y = Y.set_index("trade_date") / 100
    out = {k: Y[c].shift(1) / 252 - D * Y[c].diff() + 0.5 * C * Y[c].diff() ** 2 for k, (c, D, C) in LEGS.items()}
    return pd.DataFrame(out).reindex(index)


def main() -> None:
    base = sy.GROUPS
    sy.GROUPS = {**base, "原油": {om.OIL: 1}, "债券": {k: 1 for k in LEGS}}; R, cash = sy.load()
    R = R.loc["2012-01-01":]; cash = cash.reindex(R.index).fillna(0)
    px = fl.futures_proxy(R.index)
    for etf in fl.PROXY:
        R[etf] = R[etf].where(R[etf].notna().cumsum() > 0, px[etf])
    bp = curve_proxy(R.index)
    for etf in LEGS:
        j = pd.concat([R[etf], bp[etf]], axis=1).dropna()
        print(f"curve proxy {etf}: corr {j.iloc[:, 0].corr(j.iloc[:, 1]):.2f}, vol {j.iloc[:, 0].std()*252**.5:.1%} vs {j.iloc[:, 1].std()*252**.5:.1%}, listed {R[etf].first_valid_index().date()}")
        if not os.environ.get("NOPROXY"):  # NOPROXY=1: bond ETFs join when listed (plan 27 reproduction check)
            R[etf] = R[etf].where(R[etf].notna().cumsum() > 0, bp[etf])
    sy.START = fl.START; idx = R.index; A = fs.A
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()
    G3 = {k: v for k, v in fs.layout({"511010.SH": 1}).items() if k != "债券"}
    sy.GROUPS = G3
    gr3 = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G3}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G3})
    gr3 = gr3.where(pd.DataFrame({g: R[list(G3[g])].notna().any(axis=1) for g in G3}))
    iv = 1 / (gr3.rolling(60, min_periods=40).std() * 252 ** 0.5); m3 = iv.div(iv.sum(axis=1), axis=0).where(month).ffill()
    rows, out = {}, {}
    for sname, codes in SLEEVES.items():
        bret = R[codes].mean(axis=1); nav = (1 + bret.fillna(0)).cumprod()
        sw = (sum((nav > nav.shift(n)).astype(float).where(nav.shift(n).notna()) for n in (21, 63, 252)) / 3).where(fri).ffill().fillna(1.0)
        dur = np.mean([LEGS[c][1] for c in codes])
        for b in (0.2, 0.4):
            G = {**G3, "债券": {c: 1 for c in codes}}; sy.GROUPS = G
            m = m3 * (1 - b); m["债券"] = b * sw
            w = sy.group_weights(R, m.reindex(columns=list(G)).fillna(0)); w[A] = w[A] * a_pos.fillna(0)
            x = sy.run(R, cash, w, fri); k = f"{round((1-b)*100)}/{round(b*100)} {sname}"; out[k] = x
            ex = x - cash.loc[x.index]; cum = (1 + x).cumprod(); Y = (1 + x).groupby(x.index.year).prod() - 1
            ep = lambda a, z: (1 + x.loc[a:z]).prod() - 1
            rows[k] = {"年化": cum.iloc[-1] ** (252 / len(x)) - 1, "波动": x.std() * 252 ** 0.5, "夏普": ex.mean() / ex.std() * 252 ** 0.5,
                       "最大回撤": (cum / cum.cummax() - 1).min(), "最差年": Y.min(), "亏损年": int((Y < 0).sum()),
                       "股灾15-16": ep("2015-06", "2016-02"), "债熊16-17": ep("2016-10", "2017-12"), "2018": ep("2018", "2018"), "2020": ep("2020", "2020"),
                       "2026": ep("2026", "2026"), "久期(满仓)": b * dur, "今天开关": sw.iloc[-1],
                       "夏普20-26": ex.loc["2020-02":].mean() / ex.loc["2020-02":].std() * 252 ** 0.5}
    sy.GROUPS = base
    T = pd.DataFrame(rows).T; T.to_csv(sy.OUT / "bond_mix.csv"); pd.DataFrame(out).to_csv(sy.OUT / "bond_mix_daily.csv")
    f = T.copy()
    for c in ("年化", "波动", "最大回撤", "最差年", "股灾15-16", "债熊16-17", "2018", "2020", "2026"):
        f[c] = f[c].map(lambda v: f"{v*100:+.1f}%")
    print(f.round(2).to_string())


if __name__ == "__main__":
    main()
