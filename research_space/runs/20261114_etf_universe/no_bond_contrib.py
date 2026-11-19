"""Where does the 100/0 (no bond) book's return come from? (2026-11-14). User: "100 0 感觉也还不错啊".
Same build as split_sweep.py b = 0: 股票 / 黄金 / 商品 risk budget 1:1:1, A股 plan-24 timing, 15 bp, 2014-01..2026-11.
Reports per group: average weight, return contribution by year (weight held x group return, before costs), today's weights,
and the book without gold (股票 / 商品 only) as a stress on gold dependence.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fl", HERE / "full_scheme_long.py")
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
fs, sy, om = fl.fs, fl.sy, fl.om
pd.set_option("display.width", 260)


def main() -> None:
    base = sy.GROUPS
    sy.GROUPS = {**base, "原油": {om.OIL: 1}}; R, cash = sy.load()
    R = R.loc["2012-01-01":]; cash = cash.reindex(R.index).fillna(0)
    px = fl.futures_proxy(R.index)
    for etf in fl.PROXY:
        R[etf] = R[etf].where(R[etf].notna().cumsum() > 0, px[etf])
    sy.START = fl.START; idx = R.index; A = fs.A
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()
    full = {k: v for k, v in fs.layout({"511010.SH": 1}).items() if k != "债券"}
    res = {}
    for name, G in (("股/金/商", full), ("股/商（去掉黄金）", {k: v for k, v in full.items() if k != "黄金"})):
        sy.GROUPS = G
        gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
        gr = gr.where(pd.DataFrame({g: R[list(G[g])].notna().any(axis=1) for g in G}))
        iv = 1 / (gr.rolling(60, min_periods=40).std() * 252 ** 0.5); m = iv.div(iv.sum(axis=1), axis=0).where(month).ffill()
        w = sy.group_weights(R, m.fillna(0)); w[A] = w[A] * a_pos.fillna(0)
        x = sy.run(R, cash, w, fri); res[name] = x
        if name == "股/金/商":
            held = w.where(fri).ffill().shift(1).loc[fl.START:]
            gw = pd.DataFrame({g: held[list(G[g])].sum(axis=1) for g in G}); gw["现金"] = 1 - gw.sum(axis=1)
            contrib = pd.DataFrame({g: (held[list(G[g])] * R[list(G[g])].fillna(0).loc[held.index]).sum(axis=1) for g in G})
            contrib["现金"] = gw["现金"] * cash.loc[held.index]
            print("平均权重:", (gw.mean() * 100).round(1).to_dict())
            print("今天权重:", (gw.iloc[-1] * 100).round(1).to_dict())
            print("各组贡献（年，%，简单加总）:"); print((contrib.groupby(contrib.index.year).sum() * 100).round(1).T.to_string())
            print("全期累计贡献（%，简单加总）:", (contrib.sum() * 100).round(1).to_dict())
    sy.GROUPS = base
    for k, x in res.items():
        ex = x - cash.loc[x.index]; cum = (1 + x).cumprod(); Y = (1 + x).groupby(x.index.year).prod() - 1
        print(f"{k}: 年化 {cum.iloc[-1] ** (252 / len(x)) - 1:+.1%}, 夏普 {ex.mean() / ex.std() * 252 ** 0.5:.2f}, 最大回撤 {(cum / cum.cummax() - 1).min():+.1%}, "
              f"亏损年 {(Y < 0).sum()}, 逐年 {(Y * 100).round(1).tolist()}")


if __name__ == "__main__":
    main()
