"""4-group risk budgets with A股 + 港股 merged into one 股票 group (2026-11-14). User: "可以，测一下股票合并的4组风险预算".

Groups: 股票 (A股 510300 510500 512100 159915 + 港股 159920 513050 513130, A股 : 港股 = 2 : 1 inside),
债券 (511010 511260 511020 511090), 黄金 (518880), 商品 (159980 159981). Long only, no leverage, cash 511880, 15 bp.
Weights ∝ budget / 60-day group vol, monthly (naive risk budgeting); one ERC variant from the 60-day covariance.
Optional overlays (weekly): 股票 group x plan-24 A股 position on its A股 part; group trend on/off (21/63/252).
Optional bond cap 50%. Reports full period, halves, max dd, worst 12 m, weights and realised risk shares.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sy", HERE / "systematic.py")
sy = importlib.util.module_from_spec(spec); spec.loader.exec_module(sy)
pd.set_option("display.width", 260)
A = ["510300.SH", "510500.SH", "512100.SH", "159915.SZ"]
G = {"股票": {**{x: 2 for x in A}, "159920.SZ": 4 / 3, "513050.SH": 4 / 3, "513130.SH": 4 / 3},
     "债券": sy.GROUPS["债券"], "黄金": {"518880.SH": 1}, "商品": {"159980.SZ": 1, "159981.SZ": 1}}
NAMES = list(G)


def erc(S: np.ndarray, b: np.ndarray) -> np.ndarray:
    w = b / np.sqrt(np.diag(S)); w /= w.sum()
    for _ in range(300):
        rc = np.maximum(w * (S @ w), 1e-12); w = w * (b / (rc / rc.sum())) ** 0.5; w /= w.sum()
    return w


def main() -> None:
    R, cash = sy.load(); idx = R.index
    sy.GROUPS = G
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1)
                       for g in G})
    vol = gr.rolling(60).std() * 252 ** 0.5
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()
    nav = (1 + gr).cumprod()
    gsig = (sum((nav > nav.shift(n)).astype(float).where(nav.shift(n).notna()) for n in (21, 63, 252)) / 3).where(fri).ffill()

    def mix_of(budget: dict[str, float], cap: float | None) -> pd.DataFrame:
        iv = (1 / vol) * pd.Series(budget); m = iv.div(iv.sum(axis=1), axis=0)
        if cap is not None:
            over = (m["债券"] - cap).clip(lower=0)
            rest = m.drop(columns="债券"); m["债券"] = m["债券"] - over
            m[rest.columns] = rest.add(rest.div(rest.sum(axis=1), axis=0).mul(over, axis=0))
        return m

    books, wts, shares = {}, {}, {}

    def add(name: str, m: pd.DataFrame, overlay: str = "") -> None:
        decide = month
        mm = m.copy()
        if "trend" in overlay:
            mm = mm * gsig; decide = fri
        w = sy.group_weights(R, mm.fillna(0))
        if "a24" in overlay:
            w[A] = w[A] * a_pos.fillna(0); decide = fri
        books[name] = sy.run(R, cash, w, decide)
        wts[name] = mm.loc[sy.START:].mean()
        rc = []
        for d in m.loc[sy.START:].index[::21]:
            S = gr.loc[:d].iloc[-60:].cov().to_numpy() * 252; ww = m.loc[d].to_numpy()
            if not np.isnan(ww).any():
                x = ww * (S @ ww); rc.append(x / x.sum())
        shares[name] = pd.Series(np.mean(rc, axis=0), index=NAMES)

    budgets = {"1:1:1:1": {"股票": 1, "债券": 1, "黄金": 1, "商品": 1},
               "股2:债1:金1:商1": {"股票": 2, "债券": 1, "黄金": 1, "商品": 1},
               "股1:债0.5:金1:商1": {"股票": 1, "债券": 0.5, "黄金": 1, "商品": 1},
               "股2:债0.5:金1:商1": {"股票": 2, "债券": 0.5, "黄金": 1, "商品": 1},
               "股1:债1:金1:商0.5": {"股票": 1, "债券": 1, "黄金": 1, "商品": 0.5}}
    for k, b in budgets.items():
        add(f"预算 {k}", mix_of(b, None))
    add("预算 1:1:1:1 债≤50%", mix_of(budgets["1:1:1:1"], 0.5))
    ercw = []
    for d in idx:
        win = gr.loc[:d].iloc[-60:]
        ercw.append(erc(win.cov().to_numpy(), np.ones(4) / 4) if len(win) == 60 and win.notna().all().all() and d >= pd.Timestamp("2019-12-01") else np.full(4, np.nan))
    add("ERC 协方差等风险贡献", pd.DataFrame(ercw, index=idx, columns=NAMES))
    for k in ("1:1:1:1", "股1:债0.5:金1:商1"):
        add(f"预算 {k} + A股计划24", mix_of(budgets[k], None), "a24")
        add(f"预算 {k} + 各组趋势开关", mix_of(budgets[k], None), "trend")
    add("预算 1:1:1:1 债≤50% + A股计划24", mix_of(budgets["1:1:1:1"], 0.5), "a24")
    T = pd.DataFrame({k: sy.stats(v, cash, np.nan) for k, v in books.items()}).T.drop(columns="turnover_y")
    W = pd.DataFrame(wts).T.add_prefix("w_"); S = pd.DataFrame(shares).T.add_prefix("risk_")
    out = T.join(W).join(S); out.to_csv(sy.OUT / "risk_budget.csv")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_12m"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    f = f.join((W * 100).round(0)).join((S * 100).round(0))
    print(f.round(2).to_string())
    Y = pd.DataFrame(books).groupby(lambda d: d.year).apply(lambda g: (1 + g).prod() - 1)
    print("\nBy year:"); print((Y * 100).round(1).T.to_string())
    print("\ngroup vol (2020-02..):", (gr.loc[sy.START:].std() * 252 ** 0.5).round(3).to_dict())
    print("group corr:"); print(gr.loc[sy.START:].corr().round(2).to_string())


if __name__ == "__main__":
    main()
