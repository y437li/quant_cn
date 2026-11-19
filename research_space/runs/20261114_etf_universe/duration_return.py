"""Higher return with less duration risk (2026-11-14). User: "收益率这么低。。利率反弹久期会很惨。。。".

Long history as full_scheme_long.py (2014-, ETFs join when listed, commodity ETFs proxied by main futures before listing).
Variants (long only, no leverage, 15 bp, A股 plan-24 timing everywhere, freed weight to cash 511880):
  ⑤  reference: risk budget 1:1:1:1, bonds 5y/10y/5-10y, bond switch, cap 65%
  S1 short bonds: bond group = 5-year 511010 only (duration ~4.5), bond switch
  S2 no bonds: risk budget over 股票 / 黄金 / 商品 only, the rest of the weight stays invested (weights sum to 100%)
  S3 bonds as ballast: 股票 / 黄金 / 商品 at 1:1:1 risk weights scaled to 60% of capital, 40% 5-year bonds with switch
  S4 bond budget 0.5 + bond switch (bonds 5y/10y/5-10y)
  S5 bond budget 0.25 + bond switch
Plus the rate-shock arithmetic: bond weight x duration for a +1 pt rise in yields, today's weights.
Run with RAW=1 to read raw fund_daily while the backfill is not compacted.
"""
from __future__ import annotations
import importlib.util, os
from pathlib import Path
import duckdb, numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fl", HERE / "full_scheme_long.py")
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
fs, sy, om = fl.fs, fl.sy, fl.om
pd.set_option("display.width", 260)
DUR = {"511010.SH": 4.5, "511260.SH": 8.5, "511020.SH": 6.5, "511090.SH": 19.0}
LAKE = Path("/Volumes/Treasury/quant_cn_lake")


def load_raw() -> tuple[pd.DataFrame, pd.Series]:
    codes = [x for g in sy.GROUPS.values() for x in g] + [sy.CASH]
    D = duckdb.connect().execute(f"""select distinct ts_code, trade_date, close/pre_close-1 ret from (
        select ts_code, trade_date, close, pre_close from read_parquet('{LAKE}/raw/fund_daily/*.parquet', union_by_name=true)
        union all select ts_code, trade_date, close, pre_close from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet', union_by_name=true))
        where ts_code in ({','.join(repr(x) for x in codes)}) and pre_close > 0""").df()
    D["trade_date"] = pd.to_datetime(D.trade_date)
    R = D.pivot_table(index="trade_date", columns="ts_code", values="ret", aggfunc="first").sort_index().clip(-0.2, 0.2)
    return R.drop(columns=sy.CASH), R[sy.CASH].fillna(0)


def main() -> None:
    if os.environ.get("RAW"):
        sy.load = load_raw
    base = sy.GROUPS
    sy.GROUPS = {**base, "原油": {om.OIL: 1}}; R, cash = sy.load()
    R = R.loc["2012-01-01":]; cash = cash.reindex(R.index).fillna(0)
    px = fl.futures_proxy(R.index)
    for etf in fl.PROXY:
        R[etf] = R[etf].where(R[etf].notna().cumsum() > 0, px[etf])
    sy.START = fl.START; idx = R.index
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0); A = fs.A
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()

    def group_ret(G: dict) -> pd.DataFrame:
        sy.GROUPS = G
        gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
        return gr.where(pd.DataFrame({g: R[list(G[g])].notna().any(axis=1) for g in G}))

    def bond_switch(gr: pd.Series) -> pd.Series:
        nav = (1 + gr.fillna(0)).cumprod()
        return (sum((nav > nav.shift(n)).astype(float).where(nav.shift(n).notna()) for n in (21, 63, 252)) / 3).where(fri).ffill().fillna(1.0)

    def risk_weights(gr: pd.DataFrame, budget: dict) -> pd.DataFrame:
        iv = (1 / (gr.rolling(60, min_periods=40).std() * 252 ** 0.5)) * pd.Series(budget)
        return iv.div(iv.sum(axis=1), axis=0).where(month).ffill()

    def finish(G: dict, m: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        sy.GROUPS = G
        w = sy.group_weights(R, m.reindex(columns=list(G)).fillna(0)); w[A] = w[A] * a_pos.fillna(0)
        return sy.run(R, cash, w, fri), w.iloc[-1]

    bonds3 = fs.BOND_NO30; bond5 = {"511010.SH": 1}
    out, last = {}, {}
    G = fs.layout(bonds3); gr = group_ret(G); m = risk_weights(gr, {k: 1 for k in G})
    over = (m["债券"] - fs.CAP).clip(lower=0); rest = m.drop(columns="债券"); m["债券"] -= over
    m[rest.columns] = rest.add(rest.div(rest.sum(axis=1), axis=0).mul(over, axis=0)); m["债券"] *= bond_switch(gr["债券"])
    out["⑤ 完整方案"], last["⑤ 完整方案"] = finish(G, m)
    G = fs.layout(bond5); gr = group_ret(G); m = risk_weights(gr, {k: 1 for k in G}); m["债券"] *= bond_switch(gr["债券"])
    out["S1 只用5年国债+开关"], last["S1 只用5年国债+开关"] = finish(G, m)
    G3 = {k: v for k, v in fs.layout(bonds3).items() if k != "债券"}; gr3 = group_ret(G3)
    out["S2 不要债券(股/金/商 风险预算)"], last["S2 不要债券(股/金/商 风险预算)"] = finish(G3, risk_weights(gr3, {k: 1 for k in G3}))
    G = fs.layout(bond5); gr = group_ret(G); m3 = risk_weights(gr3, {k: 1 for k in G3}) * 0.6
    m3["债券"] = 0.4 * bond_switch(gr["债券"])
    out["S3 股金商60% + 5年国债40%(开关)"], last["S3 股金商60% + 5年国债40%(开关)"] = finish(G, m3)
    for b in (0.5, 0.25):
        G = fs.layout(bonds3); gr = group_ret(G); m = risk_weights(gr, {"股票": 1, "债券": b, "黄金": 1, "商品": 1}); m["债券"] *= bond_switch(gr["债券"])
        out[f"S{4 if b == 0.5 else 5} 债券预算{b} + 开关"], last[f"S{4 if b == 0.5 else 5} 债券预算{b} + 开关"] = finish(G, m)
    sy.GROUPS = base
    rows = {}
    for k, x in out.items():
        ex = x - cash.loc[x.index]; cum = (1 + x).cumprod(); w = last[k]
        bw = sum(w.get(c_, 0) for c_ in DUR); dur = sum(w.get(c_, 0) * d for c_, d in DUR.items())
        z = x.loc["2016-10":"2017-12"]; zc = (1 + z).cumprod()
        rows[k] = {"ann": cum.iloc[-1] ** (252 / len(x)) - 1, "vol": x.std() * 252 ** 0.5, "sharpe": ex.mean() / ex.std() * 252 ** 0.5,
                   "max_dd": (cum / cum.cummax() - 1).min(), "worst_12m": ((1 + x).rolling(252).apply(np.prod, raw=True) - 1).min(),
                   "债熊16-17": zc.iloc[-1] - 1, "股灾15-16": (1 + x.loc["2015-06":"2016-02"]).prod() - 1,
                   "今天债券%": bw, "今天组合久期": dur, "利率+1%冲击": -dur / 100}
    T = pd.DataFrame(rows).T; T.to_csv(sy.OUT / "duration_return.csv")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_12m", "债熊16-17", "股灾15-16", "今天债券%", "利率+1%冲击"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    f["今天组合久期"] = f["今天组合久期"].map(lambda v: f"{v:.2f}")
    print(f"{fl.START}..{idx[-1].date()}, 15 bp:"); print(f.round(2).to_string())
    Y = pd.DataFrame(out).groupby(lambda d: d.year).apply(lambda g_: (1 + g_).prod() - 1)
    print("\nBy year:"); print((Y * 100).round(1).T.to_string())


if __name__ == "__main__":
    main()
