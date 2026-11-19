"""Can the risk-parity ETF book be improved without leverage? (2026-11-14). User: "M3 风险平价 … 这个能提高吗？"

Reuses systematic.py (same ETFs, 15 bp, monthly risk weights from 60-day group vol, cash 511880).
Variants:
  RP0  4 groups, inverse vol (= M3)
  RP1  5 groups: 黄金 separate from 商品 (有色 / 能化)
  RP2  RP1 with long bonds only (10-year 511260 / 511020, 30-year 511090 when listed)
  RP3  RP1, equal risk contribution from the 60-day covariance (not just 1/vol)
  RP4  RP1 x trend on/off per group (group NAV above its 21/63/252-session levels, share of 3), freed to cash
  RP5  RP1 with the A股 group x plan-24 position (blend x vol size), freed to cash
  RP6  RP1 with risk budget tilted away from bonds: bonds get half a share of risk
Prints 2020-02..2026-11 and the halves, plus average group weights.
"""
from __future__ import annotations
import contextlib, importlib.util, io
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sy", HERE / "systematic.py")
sy = importlib.util.module_from_spec(spec); spec.loader.exec_module(sy)
pd.set_option("display.width", 240)


def erc(S: np.ndarray, budget: np.ndarray, iters: int = 500) -> np.ndarray:
    w = budget / np.sqrt(np.diag(S)); w /= w.sum()
    for _ in range(iters):
        rc = w * (S @ w); w = w * (budget / (rc / rc.sum())) ** 0.5; w /= w.sum()
    return w


def main() -> None:
    R, cash = sy.load(); idx = R.index
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    g4 = sy.GROUPS
    g5 = {"A股": g4["A股"], "债券": g4["债券"], "黄金": {"518880.SH": 1}, "商品": {"159980.SZ": 1, "159981.SZ": 1}, "港股": g4["港股"]}
    g5long = dict(g5, 债券={"511260.SH": 1, "511020.SH": 1, "511090.SH": 1})
    books, wts = {}, {}

    def spread(groups: dict, mix: pd.DataFrame) -> pd.DataFrame:
        sy.GROUPS = groups
        try:
            return sy.group_weights(R, mix)
        finally:
            sy.GROUPS = g4

    def group_returns(groups: dict) -> pd.DataFrame:
        return pd.DataFrame({g: (spread(groups, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in groups}, index=idx)) * R.fillna(0)).sum(axis=1)
                             for g in groups})

    def inv_vol(groups: dict, budget: dict | None = None) -> pd.DataFrame:
        gr = group_returns(groups); iv = 1 / (gr.rolling(60).std() * 252 ** 0.5)
        if budget:
            iv = iv * pd.Series(budget)
        return iv.div(iv.sum(axis=1), axis=0)

    def add(name: str, groups: dict, mix: pd.DataFrame, decide: pd.Series, scale: pd.DataFrame | None = None) -> None:
        w = spread(groups, mix.fillna(0))
        if scale is not None:
            w = w * scale.reindex(columns=w.columns).fillna(1.0)
        books[name] = sy.run(R, cash, w, decide)
        wts[name] = mix.loc[sy.START:].mean()

    add("RP0 4组 1/波动", g4, inv_vol(g4), month)
    rp5 = inv_vol(g5); add("RP1 5组(黄金单列)", g5, rp5, month)
    add("RP2 5组 + 只用长债", g5long, inv_vol(g5long), month)
    gr5 = group_returns(g5); ercw = []
    for d in idx:
        win = gr5.loc[:d].iloc[-60:]
        ercw.append(erc(win.cov().to_numpy(), np.ones(5) / 5) if len(win) == 60 and win.notna().all().all() else np.full(5, np.nan))
    add("RP3 5组 等风险贡献(协方差)", g5, pd.DataFrame(ercw, index=idx, columns=list(g5)), month)
    nav = (1 + gr5).cumprod()
    gsig = sum((nav > nav.shift(n)).astype(float).where(nav.shift(n).notna()) for n in (21, 63, 252)) / 3
    gsig = gsig.where(fri).ffill()
    add("RP4 5组 × 各组趋势开关", g5, rp5 * gsig, fri)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0); a = list(g4["A股"])
    blend = sum((P[a] > P[a].shift(n)).astype(float).where(P[a].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    size = (0.20 / (R[a].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)
    add("RP5 5组 + A股计划24仓位", g5, rp5, fri, scale=(blend * size).where(fri).ffill())
    add("RP6 5组 债券风险预算减半", g5, inv_vol(g5, {"A股": 1, "债券": 0.5, "黄金": 1, "商品": 1, "港股": 1}), month)
    T = pd.DataFrame({k: sy.stats(v, cash, np.nan) for k, v in books.items()}).T.drop(columns="turnover_y")
    W = pd.DataFrame(wts).T
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_12m"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    print(f.round(2).to_string())
    print("\naverage group weights (incl. trend-off share kept as cash where applicable):"); print((W * 100).round(0).to_string())
    T.join(W).to_csv(sy.OUT / "risk_parity_variants.csv")
    Y = pd.DataFrame(books).groupby(lambda d: d.year).apply(lambda g: (1 + g).prod() - 1)
    print("\nBy year:"); print((Y * 100).round(1).to_string())


if __name__ == "__main__":
    main()
