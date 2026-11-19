"""Parameter sensitivity of the plan 27 book (2026-11-14). User: "看看参数，然后optuna，贝恩斯优化怎么放进来？".

Base = 60/40, 股/金/商 equal risk (1 / 60-day vol, monthly), A股 plan-24 position (10/21/42/252, 20% vol target),
bonds 5y + 30y with switch 21/63/252, A股 : 港股 = 2 : 1, 15 bp, 2014-01..2026-11 (proxies as bond_mix.py).
One parameter at a time around the base; Sharpe full, 2014-19, 2020-26, ann, max dd. `book(params)` is the reusable
objective for a later Optuna walk-forward.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("bm", HERE / "bond_mix.py")
bm = importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)
fl, fs, sy, om = bm.fl, bm.fs, bm.sy, bm.om
pd.set_option("display.width", 240)
BASE = {"vol_window": 60, "trend": (10, 21, 42, 252), "vol_target": 0.20, "switch": (21, 63, 252), "hk": 1.0,
        "risk_share": 0.6, "rebalance": "M", "budget": (1.0, 1.0, 1.0)}
A = fs.A; HK = ["159920.SZ", "513050.SH", "513130.SH"]; BONDS = ["511010.SH", "511090.SH"]


def load() -> tuple[pd.DataFrame, pd.Series]:
    base = sy.GROUPS
    sy.GROUPS = {**base, "原油": {om.OIL: 1}, "债券": {k: 1 for k in bm.LEGS}}; R, cash = sy.load(); sy.GROUPS = base
    R = R.loc["2012-01-01":]; cash = cash.reindex(R.index).fillna(0)
    px = fl.futures_proxy(R.index)
    for etf in fl.PROXY:
        R[etf] = R[etf].where(R[etf].notna().cumsum() > 0, px[etf])
    bp = bm.curve_proxy(R.index)
    for etf in bm.LEGS:
        R[etf] = R[etf].where(R[etf].notna().cumsum() > 0, bp[etf])
    sy.START = fl.START
    return R, cash


def book(R: pd.DataFrame, cash: pd.Series, p: dict) -> pd.Series:
    idx = R.index; fri = pd.Series(idx.dayofweek == 4, index=idx)
    first = pd.Series(idx.to_period(p["rebalance"]) != idx.to_period(p["rebalance"]).to_series().shift(1).to_numpy(), index=idx)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    trend = lambda X, ns: sum((X > X.shift(n)).astype(float).where(X.shift(n).notna()) for n in ns) / len(ns)
    size = (p["vol_target"] / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0) if p["vol_target"] else 1.0
    a_pos = (trend(P[A], p["trend"]) * size).where(fri).ffill().fillna(0)
    stock = {**{x: 2.0 for x in A}, **{x: 2.0 * p["hk"] / 3 * 4 / 4 for x in HK}}
    stock = {**{x: 2.0 for x in A}, **{x: 4 / 3 * p["hk"] for x in HK}} if p["hk"] > 0 else {x: 2.0 for x in A}
    G = {"股票": stock, "黄金": {"518880.SH": 1}, "商品": {"159980.SZ": 1, "159981.SZ": 1, om.OIL: 1}}
    sy.GROUPS = {**G, "债券": {c: 1 for c in BONDS}}
    gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in sy.GROUPS}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
    gr = gr.where(pd.DataFrame({g: R[list(G[g])].notna().any(axis=1) for g in G}))
    iv = (1 / (gr.rolling(p["vol_window"], min_periods=min(40, p["vol_window"])).std() * 252 ** 0.5)) * pd.Series(dict(zip(G, p["budget"])))
    m = iv.div(iv.sum(axis=1), axis=0).where(first).ffill() * p["risk_share"]
    nav = (1 + R[BONDS].mean(axis=1).fillna(0)).cumprod()
    sw = trend(nav.to_frame("b"), p["switch"])["b"].where(fri).ffill().fillna(1.0) if p["switch"] else 1.0
    m["债券"] = (1 - p["risk_share"]) * sw
    w = sy.group_weights(R, m.reindex(columns=list(sy.GROUPS)).fillna(0)); w[A] = w[A] * a_pos
    return sy.run(R, cash, w, fri)


def score(x: pd.Series, cash: pd.Series) -> dict:
    def sh(z):
        e = z - cash.loc[z.index]; return e.mean() / e.std() * 252 ** 0.5
    cum = (1 + x).cumprod()
    return {"夏普": sh(x), "2014-19": sh(x.loc[:"2019"]), "2020-26": sh(x.loc["2020":]), "年化": cum.iloc[-1] ** (252 / len(x)) - 1,
            "最大回撤": (cum / cum.cummax() - 1).min()}


GRID = {"vol_window": [20, 40, 60, 120, 250], "trend": [(21,), (63,), (252,), (10, 21, 42, 252), (21, 63, 252), (5, 10, 21)],
        "vol_target": [0.10, 0.15, 0.20, 0.30, None], "switch": [None, (21,), (63,), (21, 63, 252), (63, 126, 252)],
        "hk": [0.0, 0.5, 1.0, 2.0], "rebalance": ["W", "M", "Q"], "budget": [(1.0, 1.0, 1.0), (1.5, 1.0, 1.0), (1.0, 0.7, 1.0), (1.0, 1.0, 0.7)]}


def main() -> None:
    R, cash = load(); rows = []
    for k, vals in GRID.items():
        for v in vals:
            p = {**BASE, k: v}; s = score(book(R, cash, p), cash)
            rows.append({"参数": k, "取值": str(v), "基准": v == BASE[k], **s})
    T = pd.DataFrame(rows); T.to_csv(sy.OUT / "param_sensitivity.csv", index=False)
    f = T.copy()
    for c in ("年化", "最大回撤"):
        f[c] = f[c].map(lambda v: f"{v*100:+.1f}%")
    print(f.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
