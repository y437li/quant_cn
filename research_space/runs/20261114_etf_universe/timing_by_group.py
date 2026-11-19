"""Which group of the risk-budget book benefits from trend timing? (2026-11-14). User: "只在A股加择时是吗".

Base: risk budget 1:1:1:1 on 股票 / 债券 / 黄金 / 商品(有色+能化+原油), monthly, long only, 15 bp, cash 511880.
Timing applied to one group at a time (weekly, freed weight to cash):
  trend switch = share of 21/63/252-session signals up on the group NAV; for 股票 also the plan-24 position on the A股 part only.
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
    nav = (1 + gr).cumprod()
    gsig = (sum((nav > nav.shift(n)).astype(float).where(nav.shift(n).notna()) for n in (21, 63, 252)) / 3).where(fri).ffill()
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0); A = om.A
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()
    books = {"不择时": sy.run(R, cash, sy.group_weights(R, rb.fillna(0)), month)}
    for g in G:
        m = rb.copy(); m[g] = m[g] * gsig[g]
        books[f"只给 {g} 加趋势开关"] = sy.run(R, cash, sy.group_weights(R, m.fillna(0)), fri)
    w = sy.group_weights(R, rb.fillna(0)); w[A] = w[A] * a_pos.fillna(0)
    books["只给 A股 加计划24仓位"] = sy.run(R, cash, w, fri)
    m = rb * gsig; books["四组都加趋势开关"] = sy.run(R, cash, sy.group_weights(R, m.fillna(0)), fri)
    T = pd.DataFrame({k: sy.stats(v, cash, np.nan) for k, v in books.items()}).T.drop(columns="turnover_y")
    # stand-alone: each group, hold vs trend switch (group NAV), 15 bp
    rows = []
    for g in G:
        x = gr[g].loc[sy.START:]; s = gsig[g].shift(1).loc[sy.START:].fillna(0)
        y = s * x + (1 - s) * cash.loc[x.index] - 0.0015 * s.diff().abs().fillna(0)
        for nm, z in (("持有", x), ("趋势开关", y)):
            cum = (1 + z).cumprod(); ex = z - cash.loc[z.index]
            rows.append({"group": g, "rule": nm, "ann": cum.iloc[-1] ** (252 / len(z)) - 1, "sharpe": ex.mean() / ex.std() * 252 ** 0.5,
                         "max_dd": (cum / cum.cummax() - 1).min()})
    S = pd.DataFrame(rows)
    T.to_csv(sy.OUT / "timing_by_group.csv"); S.to_csv(sy.OUT / "timing_by_group_standalone.csv", index=False)
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_12m"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    print("In the book (2020-02..2026-11, 15 bp):"); print(f.round(2).to_string())
    s = S.copy(); s["ann"] = (s.ann * 100).round(1); s["max_dd"] = (s.max_dd * 100).round(1)
    print("\nEach group alone:"); print(s.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
