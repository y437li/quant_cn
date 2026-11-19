"""Oil in the ETF book (2026-11-14). User: "石油呢？" after the 100/0 group breakdown.
Book as split_sweep.py b = 0 (股/金/商 risk budget + A股 timing, 15 bp, 2014-01..2026-11). Within 商品 the ETFs are 1:1:1
(有色 159980, 能化 159981, 原油 LOF 161129 from 2017-02). Reports per-ETF contribution by year, the book with 商品 = 有色 + 能化
only (no oil), oil LOF stand-alone stats, and the oil LOF premium to NAV (fund_nav) and liquidity (fund_daily amount).
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import duckdb, numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fl", HERE / "full_scheme_long.py")
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
fs, sy, om = fl.fs, fl.sy, fl.om
LAKE = Path("/Volumes/Treasury/quant_cn_lake")
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
    no_oil = {**full, "商品": {"159980.SZ": 1, "159981.SZ": 1}}
    res = {}
    for name, G in (("含原油", full), ("商品不含原油", no_oil)):
        sy.GROUPS = G
        gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
        gr = gr.where(pd.DataFrame({g: R[list(G[g])].notna().any(axis=1) for g in G}))
        iv = 1 / (gr.rolling(60, min_periods=40).std() * 252 ** 0.5); m = iv.div(iv.sum(axis=1), axis=0).where(month).ffill()
        w = sy.group_weights(R, m.fillna(0)); w[A] = w[A] * a_pos.fillna(0)
        res[name] = sy.run(R, cash, w, fri)
        if name == "含原油":
            held = w.where(fri).ffill().shift(1).loc[fl.START:]; cs = ["159980.SZ", "159981.SZ", om.OIL]
            c = (held[cs] * R[cs].fillna(0).loc[held.index]).rename(columns={"159980.SZ": "有色", "159981.SZ": "能化", om.OIL: "原油LOF"})
            print("商品内平均权重(%):", (held[cs].mean() * 100).round(1).tolist(), " 今天:", (held[cs].iloc[-1] * 100).round(1).tolist())
            print("商品内各品种贡献（年，百分点）:"); print((c.groupby(c.index.year).sum() * 100).round(1).T.to_string())
    sy.GROUPS = base
    for k, x in res.items():
        ex = x - cash.loc[x.index]; cum = (1 + x).cumprod(); Y = (1 + x).groupby(x.index.year).prod() - 1
        print(f"{k}: 年化 {cum.iloc[-1] ** (252 / len(x)) - 1:+.1%}, 夏普 {ex.mean() / ex.std() * 252 ** 0.5:.2f}, 最大回撤 {(cum / cum.cummax() - 1).min():+.1%}, 逐年 {(Y * 100).round(1).tolist()}")
    o = R[om.OIL].dropna(); oc = (1 + o).cumprod()
    print(f"原油LOF单独 {o.index[0].date()}..: 年化 {oc.iloc[-1] ** (252 / len(o)) - 1:+.1%}, 波动 {o.std() * 252 ** 0.5:.1%}, 最大回撤 {(oc / oc.cummax() - 1).min():+.1%}")
    c_ = duckdb.connect()
    q = c_.execute(f"""with p as (select trade_date, close, amount from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet') where ts_code='{om.OIL}'),
      n as (select nav_date trade_date, any_value(unit_nav) nav from read_parquet('{LAKE}/curated/fund_nav/**/*.parquet') where ts_code='{om.OIL}' group by 1)
      select p.trade_date, p.close/n.nav-1 prem, p.amount from p join n using(trade_date) order by 1""").df()
    q["y"] = q.trade_date.str[:4]
    print("原油LOF溢价与成交额（千元）按年:"); print(q.groupby("y").agg(溢价中位=("prem", "median"), 溢价最高=("prem", "max"), 成交额中位=("amount", "median")).round(3).to_string())
    print("最近10天:"); print(q.tail(10).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
