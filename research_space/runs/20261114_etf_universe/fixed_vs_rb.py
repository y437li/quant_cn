"""Fixed stock / bond mixes (40:60, 60:40, ...) against the risk-budget book (2026-11-14). User: "那跟40:60比不就好了".

Same ETFs and groups as oil_metals.py L4o (股票 = A股 + 港股 2:1; 债券 4 国债 ETF; 黄金 518880; 商品 = 有色 + 能化 + 原油).
Fixed mixes rebalanced monthly; risk budget 1:1:1:1 (weights ∝ 1 / 60-day vol, monthly); long only, 15 bp, cash 511880.
Also each fixed mix with the plan-24 A股 position, and fixed mixes scaled to the risk-budget book's volatility (rest in cash)
so returns compare at equal risk.
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
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0); A = om.A
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()
    gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
    iv = 1 / (gr.rolling(60).std() * 252 ** 0.5); rb = iv.div(iv.sum(axis=1), axis=0)
    mixes = {"股40/债60": {"股票": .4, "债券": .6}, "股60/债40": {"股票": .6, "债券": .4}, "股20/债80": {"股票": .2, "债券": .8},
             "股30/债50/金10/商10": {"股票": .3, "债券": .5, "黄金": .1, "商品": .1},
             "股20/债60/金10/商10": {"股票": .2, "债券": .6, "黄金": .1, "商品": .1}}
    books = {}

    def add(name: str, m: pd.DataFrame, a24: bool) -> None:
        w = sy.group_weights(R, m.reindex(columns=list(G)).fillna(0)); decide = month
        if a24:
            w[A] = w[A] * a_pos.fillna(0); decide = fri
        books[name] = sy.run(R, cash, w, decide)

    for k, v in mixes.items():
        m = pd.DataFrame(v, index=idx)
        add(f"固定 {k}", m, False); add(f"固定 {k} + A股计划24", m, True)
    add("风险预算 1:1:1:1", rb, False); add("风险预算 1:1:1:1 + A股计划24", rb, True)
    T = pd.DataFrame({k: sy.stats(v, cash, np.nan) for k, v in books.items()}).T.drop(columns="turnover_y")
    # equal-risk comparison: scale each book to the risk-budget book's vol, excess over cash scaled, rest earns cash
    target = T.loc["风险预算 1:1:1:1", "vol"]
    eq = {}
    for k, x in books.items():
        ex = x - cash.loc[x.index]; k_ = target / (x.std() * 252 ** 0.5)
        y = cash.loc[x.index] + ex * min(k_, 1.0)
        cum = (1 + y).cumprod()
        eq[k] = {"同波动下年化": cum.iloc[-1] ** (252 / len(y)) - 1, "同波动下回撤": (cum / cum.cummax() - 1).min(), "需要的仓位": min(k_, 1.0)}
    T = T.join(pd.DataFrame(eq).T)
    T.to_csv(sy.OUT / "fixed_vs_rb.csv")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_12m", "同波动下年化", "同波动下回撤", "需要的仓位"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    print("2020-02..2026-11, 15 bp:"); print(f.round(2).to_string())
    Y = pd.DataFrame(books).groupby(lambda d: d.year).apply(lambda g: (1 + g).prod() - 1)
    print("\nBy year:"); print((Y * 100).round(1).T.to_string())


if __name__ == "__main__":
    main()
