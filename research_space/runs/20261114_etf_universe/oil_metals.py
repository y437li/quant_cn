"""Add oil (161129 易方达原油 QDII-LOF) and keep 有色 explicit in the risk-budget book (2026-11-14). User: "石油和有色也要加进去呀".

Same rules as risk_budget.py (long only, weights ∝ budget / 60-day group vol, monthly, 15 bp, cash 511880; plan-24 overlay on A股).
Layouts:
  L4   股票 / 债券 / 黄金 / 商品(有色 159980 + 能化 159981)                     (= risk_budget 1:1:1:1)
  L4o  股票 / 债券 / 黄金 / 商品(有色 + 能化 + 原油 161129)
  L5   股票 / 债券 / 黄金 / 有色(159980) / 能源(能化 159981 + 原油 161129)
  L5b  L5 with 债券 at half budget
Each with and without the plan-24 A股 position. Also the oil LOF alone (vol, corr with groups).
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
OIL = "161129.SZ"
STOCK = {**{x: 2 for x in A}, "159920.SZ": 4 / 3, "513050.SH": 4 / 3, "513130.SH": 4 / 3}
BOND = {"511010.SH": 1, "511260.SH": 1, "511020.SH": 1, "511090.SH": 1}
LAYOUTS = {
    "L4 商品=有色+能化": {"股票": STOCK, "债券": BOND, "黄金": {"518880.SH": 1}, "商品": {"159980.SZ": 1, "159981.SZ": 1}},
    "L4o 商品=有色+能化+原油": {"股票": STOCK, "债券": BOND, "黄金": {"518880.SH": 1}, "商品": {"159980.SZ": 1, "159981.SZ": 1, OIL: 1}},
    "L5 有色 / 能源(能化+原油)": {"股票": STOCK, "债券": BOND, "黄金": {"518880.SH": 1}, "有色": {"159980.SZ": 1}, "能源": {"159981.SZ": 1, OIL: 1}},
}


def main() -> None:
    sy_groups = sy.GROUPS
    sy.GROUPS = {**sy_groups, "原油": {OIL: 1}}           # make load() fetch the oil LOF too
    R, cash = sy.load(); idx = R.index
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()
    books, wts, now = {}, {}, {}
    for lname, G in LAYOUTS.items():
        sy.GROUPS = G
        gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
        vol = gr.rolling(60).std() * 252 ** 0.5
        budgets = {"等预算": {g: 1.0 for g in G}, "债券减半": {g: (0.5 if g == "债券" else 1.0) for g in G}}
        for bname, b in budgets.items():
            iv = (1 / vol) * pd.Series(b); m = iv.div(iv.sum(axis=1), axis=0)
            for ov in ("", " + A股计划24"):
                w = sy.group_weights(R, m.fillna(0))
                decide = month
                if ov:
                    w[A] = w[A] * a_pos.fillna(0); decide = fri
                name = f"{lname} | {bname}{ov}"
                books[name] = sy.run(R, cash, w, decide)
                wts[name] = m.loc[sy.START:].mean()
                now[name] = m.iloc[-1]
        if lname.startswith("L5"):
            print("group corr (L5):"); print(gr.loc[sy.START:].corr().round(2).to_string())
            print("group vol:", (gr.loc[sy.START:].std() * 252 ** 0.5).round(3).to_dict())
    sy.GROUPS = sy_groups
    T = pd.DataFrame({k: sy.stats(v, cash, np.nan) for k, v in books.items()}).T.drop(columns="turnover_y")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_12m"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    W = (pd.DataFrame(wts).T * 100).round(0).add_prefix("w_")
    print("\n2020-02..2026-11, 15 bp:"); print(f.round(2).join(W).to_string())
    print("\nweights on", idx[-1].date()); print((pd.DataFrame(now).T * 100).round(1).to_string())
    T.join(W).to_csv(sy.OUT / "oil_metals.csv")
    o = R[OIL].loc[sy.START:].dropna()
    print(f"\n原油 LOF alone: vol {o.std()*252**0.5:.1%}, ann {((1+o).prod())**(252/len(o))-1:+.1%}, "
          f"max dd {((1+o).cumprod()/(1+o).cumprod().cummax()-1).min():.1%}")


if __name__ == "__main__":
    main()
