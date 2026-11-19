"""Volatility timing on the asset-class groups of the risk-budget book (2026-11-14). User: "大类资产加入vol timing呢？".

Base: risk budget 1:1:1:1 (股票 / 债券 / 黄金 / 商品 incl. 原油), weights ∝ 1 / 60-day vol, monthly, sums to 100% (no timing of
the total). Vol timing changes the total, freed weight to cash 511880 (long only, no leverage), weekly, 15 bp:
  V1 portfolio target: book x min(1, target / 60-day book vol), targets 3% / 4% / 5%
  V2 per group short / long vol: weight x min(1, 252-day vol / 20-day vol) (cut when vol jumps above normal)
  V3 per group Moreira-Muir: weight x min(1, k / 20-day variance), k = the group's median 20-day variance (expanding)
  V4 V2 on 股票 only
Plus the plan-24 A股 overlay on the best one. Reports full period, halves, max dd, worst month, worst 12 m.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("om", HERE / "oil_metals.py")
om = importlib.util.module_from_spec(spec); spec.loader.exec_module(om)
sy = om.sy
pd.set_option("display.width", 240)


def main() -> None:
    base = sy.GROUPS
    sy.GROUPS = {**base, "原油": {om.OIL: 1}}; R, cash = sy.load(); idx = R.index
    G = om.LAYOUTS["L4o 商品=有色+能化+原油"]; sy.GROUPS = G
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
    iv = 1 / (gr.rolling(60).std() * 252 ** 0.5); rb = iv.div(iv.sum(axis=1), axis=0)
    rb_m = rb.where(month).ffill()                                   # monthly risk weights held between rebalances
    v20, v252 = gr.rolling(20).std() * 252 ** 0.5, gr.rolling(252, min_periods=120).std() * 252 ** 0.5
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0); A = om.A
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()
    books = {}

    def add(name: str, m: pd.DataFrame, decide: pd.Series, a24: bool = False) -> None:
        w = sy.group_weights(R, m.fillna(0))
        if a24:
            w[A] = w[A] * a_pos.fillna(0)
        books[name] = sy.run(R, cash, w, decide)

    add("不择时", rb, month)
    book = (rb_m.shift(1) * gr).sum(axis=1); bvol = book.rolling(60).std() * 252 ** 0.5
    for t in (0.03, 0.04, 0.05):
        add(f"V1 组合目标波动 {t:.0%}", rb_m.mul((t / bvol).clip(upper=1.0), axis=0).where(fri).ffill(), fri)
    s2 = (v252 / v20).clip(upper=1.0)
    add("V2 各组 短期波动高于常态就减", (rb_m * s2).where(fri).ffill(), fri)
    var20 = v20 ** 2; k = var20.expanding(min_periods=120).median()
    add("V3 各组 Moreira-Muir 1/方差", (rb_m * (k / var20).clip(upper=1.0)).where(fri).ffill(), fri)
    m4 = rb_m.copy(); m4["股票"] = m4["股票"] * s2["股票"]
    add("V4 只对股票做 V2", m4.where(fri).ffill(), fri)
    add("不择时 + A股计划24", rb, fri, True)
    add("V2 + A股计划24", (rb_m * s2).where(fri).ffill(), fri, True)
    T = pd.DataFrame({k_: sy.stats(v, cash, np.nan) for k_, v in books.items()}).T.drop(columns="turnover_y")
    T["worst_month"] = [((1 + v).resample("ME").prod() - 1).min() for v in books.values()]
    T.to_csv(sy.OUT / "vol_timing.csv")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_12m", "worst_month"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    print("2020-02..2026-11, 15 bp:"); print(f.round(2).to_string())
    print("\naverage invested:", {k_: round(float(((rb_m * s2).sum(axis=1)).loc[sy.START:].mean()), 2) for k_ in ["V2"]})


if __name__ == "__main__":
    main()
