"""Full ETF scheme with a bond trend switch (2026-11-14). User: "回测一下完整方案，债券加趋势开关".

Groups: 股票 (A股 510300 510500 512100 159915 : 港股 159920 513050 513130 = 2 : 1), 债券 (511010 511260 511020, 30-year
511090 optional), 黄金 518880, 商品 (有色 159980, 能化 159981, 原油 161129). Cash 511880. Long only, no leverage, 15 bp.
Risk budget 1:1:1:1: weights ∝ 1 / 60-day group vol, monthly. Overlays, weekly (Friday close, next session):
  A股 plan-24 position (blend 10/21/42/252 x min(1, 20% / 60-day vol)) on the A股 ETFs;
  bond trend switch: share of 21/63/252-session signals up on the bond group NAV, scales the bond weight;
  bond cap: bond weight ≤ 65% before the switch, the excess spread over the other groups by their weights.
Freed weight goes to cash. Steps added one at a time, 2020-02..2026-11 and the halves; today's ETF weights for the full scheme.
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
A = om.A
BOND_ALL = {"511010.SH": 1, "511260.SH": 1, "511020.SH": 1, "511090.SH": 1}
BOND_NO30 = {"511010.SH": 1, "511260.SH": 1, "511020.SH": 1}
CAP = 0.65


def layout(bonds: dict[str, float]) -> dict[str, dict[str, float]]:
    return {"股票": om.STOCK, "债券": bonds, "黄金": {"518880.SH": 1}, "商品": {"159980.SZ": 1, "159981.SZ": 1, om.OIL: 1}}


def main() -> None:
    base = sy.GROUPS
    sy.GROUPS = {**base, "原油": {om.OIL: 1}}; R, cash = sy.load(); idx = R.index
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()
    books, last = {}, {}

    def build(bonds: dict, a24: bool, switch: bool, cap: bool) -> tuple[pd.Series, pd.Series]:
        G = layout(bonds); sy.GROUPS = G
        gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
        iv = 1 / (gr.rolling(60).std() * 252 ** 0.5); m = iv.div(iv.sum(axis=1), axis=0).where(month).ffill()
        if cap:
            over = (m["债券"] - CAP).clip(lower=0); rest = m.drop(columns="债券")
            m["债券"] = m["债券"] - over
            m[rest.columns] = rest.add(rest.div(rest.sum(axis=1), axis=0).mul(over, axis=0))
        decide = month
        if switch:
            nav = (1 + gr["债券"]).cumprod()
            s = (sum((nav > nav.shift(n)).astype(float).where(nav.shift(n).notna()) for n in (21, 63, 252)) / 3).where(fri).ffill()
            m["债券"] = m["债券"] * s; decide = fri
        w = sy.group_weights(R, m.fillna(0))
        if a24:
            w[A] = w[A] * a_pos.fillna(0); decide = fri
        return sy.run(R, cash, w, decide if not (a24 or switch) else fri), w.iloc[-1]

    steps = [("① 风险预算 1:1:1:1（含30年）", BOND_ALL, False, False, False),
             ("② + A股计划24", BOND_ALL, True, False, False),
             ("③ + 债券趋势开关", BOND_ALL, True, True, False),
             ("④ + 去掉30年国债", BOND_NO30, True, True, False),
             ("⑤ + 债券上限65%（完整方案）", BOND_NO30, True, True, True),
             ("参考: ① + 债券开关（不加A股择时）", BOND_ALL, False, True, False),
             ("参考: 完整方案但保留30年", BOND_ALL, True, True, True)]
    for name, bonds, a24, sw, cap in steps:
        books[name], last[name] = build(bonds, a24, sw, cap)
    sy.GROUPS = base
    T = pd.DataFrame({k: sy.stats(v, cash, np.nan) for k, v in books.items()}).T.drop(columns="turnover_y")
    T["worst_month"] = [((1 + v).resample("ME").prod() - 1).min() for v in books.values()]
    T.to_csv(sy.OUT / "full_scheme.csv"); pd.DataFrame(books).to_csv(sy.OUT / "full_scheme_daily.csv")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_12m", "worst_month"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    print("2020-02..2026-11, 15 bp:"); print(f.round(2).to_string())
    Y = pd.DataFrame(books).groupby(lambda d: d.year).apply(lambda g: (1 + g).prod() - 1)
    print("\nBy year:"); print((Y * 100).round(1).T.to_string())
    w = last["⑤ + 债券上限65%（完整方案）"]; w = w[w > 0.0005].sort_values(ascending=False)
    names = {"510300.SH": "沪深300", "510500.SH": "中证500", "512100.SH": "中证1000", "159915.SZ": "创业板", "159920.SZ": "恒生",
             "513050.SH": "中概互联", "513130.SH": "恒生科技", "511010.SH": "5年国债", "511260.SH": "10年国债", "511020.SH": "5-10年国债",
             "518880.SH": "黄金", "159980.SZ": "有色期货", "159981.SZ": "能化期货", om.OIL: "原油LOF"}
    print(f"\nfull scheme weights for {idx[-1].date()} (traded next session):")
    for k, v in w.items():
        print(f"  {k} {names.get(k, k)}: {v*100:.1f}%")
    print(f"  511880 货币ETF: {(1 - w.sum())*100:.1f}%")


if __name__ == "__main__":
    main()
