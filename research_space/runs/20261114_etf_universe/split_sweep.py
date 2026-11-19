"""How much in 5-year bonds? (2026-11-14). User: "60 40？" after the 股金商 60% + 5年国债 40% proposal.
Same build as duration_return.py S3: 股票 / 黄金 / 商品 risk budget 1:1:1 scaled to (1 - b) of capital, b in 5-year 511010 with
the bond trend switch, A股 plan-24 timing, 15 bp, 2014-01..2026-11. Sweeps b = 0, 0.2 .. 0.7; reports duration today and by year.
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
    G = fs.layout({"511010.SH": 1}); G3 = {k: v for k, v in G.items() if k != "债券"}
    sy.GROUPS = G
    gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
    gr = gr.where(pd.DataFrame({g: R[list(G[g])].notna().any(axis=1) for g in G}))
    iv = 1 / (gr[list(G3)].rolling(60, min_periods=40).std() * 252 ** 0.5); m3 = iv.div(iv.sum(axis=1), axis=0).where(month).ffill()
    nav = (1 + gr["债券"].fillna(0)).cumprod()
    sw = (sum((nav > nav.shift(n)).astype(float).where(nav.shift(n).notna()) for n in (21, 63, 252)) / 3).where(fri).ffill().fillna(1.0)
    out, rows = {}, {}
    for b in (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
        m = m3 * (1 - b); m["债券"] = b * sw
        w = sy.group_weights(R, m.reindex(columns=list(G)).fillna(0)); w[A] = w[A] * a_pos.fillna(0)
        x = sy.run(R, cash, w, fri); k = f"风险资产{round((1-b)*100)}/债{round(b*100)}"; out[k] = x
        ex = x - cash.loc[x.index]; cum = (1 + x).cumprod(); Y = (1 + x).groupby(x.index.year).prod() - 1
        rows[k] = {"年化": cum.iloc[-1] ** (252 / len(x)) - 1, "波动": x.std() * 252 ** 0.5, "夏普": ex.mean() / ex.std() * 252 ** 0.5,
                   "最大回撤": (cum / cum.cummax() - 1).min(), "最差12月": ((1 + x).rolling(252).apply(np.prod, raw=True) - 1).min(),
                   "亏损年数": int((Y < 0).sum()), "最差年": Y.min(), "久期": w.iloc[-1].get("511010.SH", 0) * 4.5}
    sy.GROUPS = base
    T = pd.DataFrame(rows).T; T.to_csv(sy.OUT / "split_sweep.csv"); pd.DataFrame(out).to_csv(sy.OUT / "split_sweep_daily.csv")
    f = T.copy()
    for c in ("年化", "波动", "最大回撤", "最差12月", "最差年"):
        f[c] = f[c].map(lambda v: f"{v*100:+.1f}%")
    print(f.round(2).to_string())
    print((pd.DataFrame(out).groupby(lambda d: d.year).apply(lambda g: (1 + g).prod() - 1) * 100).round(1).T.to_string())


if __name__ == "__main__":
    main()
