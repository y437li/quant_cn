"""Gold timing inside the chosen ETF book (2026-11-14). User: "可以测一下黄金择时".

Book = plan 27 choice (bond_mix.py "60/40 5年+30年"): 股/金/商 at equal risk (1 / 60-day vol, monthly) on 60% of capital,
A股 plan-24 position, 40% in 5y + 30y bonds with the switch (bond ETFs before listing from the curve, commodity ETFs from
futures), 15 bp, 2014-01..2026-11. Only the gold weight changes; freed weight goes to cash. Weekly decisions (Friday close,
next session); US yields are taken from the day before (US closes after China).
Rules (gold multiplier):
  G0 none
  G1 gold own trend 21/63/252 (share up)            G2 gold own trend 10/21/42/252 (plan-24 windows, no sizing)
  G3 real 10y up over 13 weeks -> x0.5              G4 real 10y up over 13 weeks -> x0
  G5 2y nominal up over 13 weeks -> x0.5            G6 1 - 0.5 x share of real-10y windows (4/13/26 weeks) rising
  G7 0.5 x G1 + 0.5 x (real 10y falling over 13 weeks)
Reports book and gold-sleeve stats over the full period, 2014-19, 2020-23, 2024-25, 2026, and average gold weight.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("bm", HERE.parent / "20261114_etf_universe" / "bond_mix.py")
bm = importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)
fl, fs, sy, om = bm.fl, bm.fs, bm.sy, bm.om
OUT = Path("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261114_gold_us_rates")
GOLD = "518880.SH"
pd.set_option("display.width", 240)


def yields(idx: pd.DatetimeIndex) -> pd.DataFrame:
    n = pd.read_csv(OUT / "us_tycr_curve.csv", dtype={"date": str}).set_index("date")[["y2"]]
    r = pd.read_csv(OUT / "us_trycr_curve.csv", dtype={"date": str}).set_index("date")[["y10"]].rename(columns={"y10": "r10"})
    Y = n.join(r, how="outer"); Y.index = pd.to_datetime(Y.index); Y = Y.sort_index().astype(float)
    return Y.reindex(Y.index.union(idx)).ffill().shift(1).reindex(idx)  # the previous US session


def main() -> None:
    base = sy.GROUPS
    sy.GROUPS = {**base, "原油": {om.OIL: 1}, "债券": {k: 1 for k in bm.LEGS}}; R, cash = sy.load()
    R = R.loc["2012-01-01":]; cash = cash.reindex(R.index).fillna(0)
    px = fl.futures_proxy(R.index)
    for etf in fl.PROXY:
        R[etf] = R[etf].where(R[etf].notna().cumsum() > 0, px[etf])
    bp = bm.curve_proxy(R.index)
    for etf in bm.LEGS:
        R[etf] = R[etf].where(R[etf].notna().cumsum() > 0, bp[etf])
    sy.START = fl.START; idx = R.index; A = fs.A
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()
    G3 = {k: v for k, v in fs.layout({"511010.SH": 1}).items() if k != "债券"}; sy.GROUPS = G3
    gr3 = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G3}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G3})
    gr3 = gr3.where(pd.DataFrame({g: R[list(G3[g])].notna().any(axis=1) for g in G3}))
    iv = 1 / (gr3.rolling(60, min_periods=40).std() * 252 ** 0.5); m3 = iv.div(iv.sum(axis=1), axis=0).where(month).ffill()
    codes = ["511010.SH", "511090.SH"]; bret = R[codes].mean(axis=1); bnav = (1 + bret.fillna(0)).cumprod()
    sw = (sum((bnav > bnav.shift(n)).astype(float).where(bnav.shift(n).notna()) for n in (21, 63, 252)) / 3).where(fri).ffill().fillna(1.0)
    g = P[GOLD]; Y = yields(idx); wk = 5
    trend = lambda ns: (sum((g > g.shift(n)).astype(float).where(g.shift(n).notna()) for n in ns) / len(ns))
    up13 = (Y.r10 > Y.r10.shift(13 * wk)).astype(float); up2y = (Y.y2 > Y.y2.shift(13 * wk)).astype(float)
    share = sum((Y.r10 > Y.r10.shift(n * wk)).astype(float) for n in (4, 13, 26)) / 3
    rules = {"G0 不择时": pd.Series(1.0, index=idx), "G1 黄金自身趋势21/63/252": trend((21, 63, 252)), "G2 黄金自身趋势10/21/42/252": trend((10, 21, 42, 252)),
             "G3 实际利率13周上升→减半": 1 - 0.5 * up13, "G4 实际利率13周上升→清仓": 1 - up13, "G5 2年利率13周上升→减半": 1 - 0.5 * up2y,
             "G6 实际利率多窗口(4/13/26周)": 1 - 0.5 * share, "G7 G1与实际利率各半": 0.5 * trend((21, 63, 252)) + 0.5 * (1 - up13)}
    rows, years = {}, {}
    for name, mult in rules.items():
        mult = mult.where(fri).ffill().fillna(1.0)
        G = {**G3, "债券": {c: 1 for c in codes}}; sy.GROUPS = G
        m = m3 * 0.6; m["黄金"] = m["黄金"] * mult; m["债券"] = 0.4 * sw
        w = sy.group_weights(R, m.reindex(columns=list(G)).fillna(0)); w[A] = w[A] * a_pos.fillna(0)
        x = sy.run(R, cash, w, fri)
        sleeve = (mult.shift(1) * R[GOLD].fillna(0) + (1 - mult.shift(1)) * cash - 0.0015 * mult.diff().abs()).loc[fl.START:]
        r = {}
        for lab, (a, b) in {"全期": (None, None), "2014-19": ("2014", "2019"), "2020-23": ("2020", "2023"), "2024-25": ("2024", "2025"), "2026": ("2026", "2026")}.items():
            z = x.loc[a:b]; ze = z - cash.loc[z.index]; cz = (1 + z).cumprod()
            r[f"{lab} 夏普"] = ze.mean() / ze.std() * 252 ** 0.5
            if lab == "全期":
                r["年化"] = cz.iloc[-1] ** (252 / len(z)) - 1; r["最大回撤"] = (cz / cz.cummax() - 1).min()
            else:
                r[f"{lab} 收益"] = cz.iloc[-1] - 1
        sc = (1 + sleeve).cumprod(); se = sleeve - cash.loc[sleeve.index]
        r["黄金单独 夏普"] = se.mean() / se.std() * 252 ** 0.5; r["黄金单独 回撤"] = (sc / sc.cummax() - 1).min()
        r["平均黄金权重"] = w[GOLD].loc[fl.START:].mean(); r["今天黄金倍数"] = mult.iloc[-1]
        rows[name] = r; years[name] = (1 + x).groupby(x.index.year).prod() - 1
    sy.GROUPS = base
    T = pd.DataFrame(rows).T; T.to_csv(OUT / "gold_timing.csv")
    f = T.copy()
    for c in f.columns:
        if "夏普" not in c and "倍数" not in c:
            f[c] = f[c].map(lambda v: f"{v*100:+.1f}%")
    print(f"{fl.START}..{idx[-1].date()}, book 60/40 5y+30y, 15 bp:"); print(f.round(2).to_string())
    print("\nby year:"); print((pd.DataFrame(years) * 100).round(1).T.to_string())


if __name__ == "__main__":
    main()
