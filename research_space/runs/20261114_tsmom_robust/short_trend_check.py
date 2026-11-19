"""Is the short (≈1-month) trend rule on A-share indices robust? (2026-11-14)

Rule: hold when price > price n sessions ago (daily, next-day position), cash otherwise.
Checks: n = 5..126; halves 2011-2018 / 2019-2026; costs 5 / 15 / 30 bp per trade; each index;
tradable ETFs since 2020 (510300 / 510500 / 512100 / 159915, returns from close / pre_close) and the
same rule on the matching index over the same dates (gap = index-only effect, e.g. stale prices).
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_tsmom_robust"
c = duckdb.connect()
D = c.execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
D["trade_date"] = pd.to_datetime(D.trade_date)
P = D.pivot(index="trade_date", columns="ts_code", values="close").sort_index()
names = {"000300.SH": "沪深300", "000905.SH": "中证500", "000852.SH": "中证1000", "399006.SZ": "创业板指"}
etf = {"510300.SH": "000300.SH", "510500.SH": "000905.SH", "512100.SH": "000852.SH", "159915.SZ": "399006.SZ"}


def run(p: pd.Series, r: pd.Series, n: int, cost: float, a: str, b: str) -> dict:
    w = (p > p.shift(n)).astype(float).where(p.shift(n).notna()).shift(1)
    ret = (w * r - cost * w.diff().abs()).loc[a:b].dropna()
    hold = r.loc[a:b].dropna()
    cum = (1 + ret).cumprod()
    return {"sharpe": ret.mean() / ret.std() * 252 ** 0.5, "hold_sharpe": hold.mean() / hold.std() * 252 ** 0.5,
            "ann": cum.iloc[-1] ** (252 / len(ret)) - 1, "max_dd": (cum / cum.cummax() - 1).min(),
            "trades_y": (w.loc[a:b].diff().abs() > 0).sum() / (len(ret) / 252)}


rows = []
for code, nm in names.items():
    p = P[code].dropna(); r = p.pct_change()
    for n in (5, 10, 15, 21, 30, 42, 63, 126, 252):
        for cost in (0.0005, 0.0015, 0.0030):
            for half, (a, b) in {"2011-18": ("2011-01-04", "2018-12-31"), "2019-26": ("2019-01-01", "2026-11-13"),
                                 "all": ("2011-01-04", "2026-11-13")}.items():
                rows.append({"index": nm, "n": n, "cost_bp": cost * 1e4, "period": half, **run(p, r, n, cost, a, b)})
T = pd.DataFrame(rows); T.to_csv(OUT / "short_trend_check.csv", index=False)
pd.set_option("display.width", 220)
x = T[(T.cost_bp == 5) & (T.period != "all")].groupby(["n", "period"]).sharpe.mean().unstack().round(2)
x["all"] = T[(T.cost_bp == 5) & (T.period == "all")].groupby("n").sharpe.mean().round(2)
x["trades/yr"] = T[(T.cost_bp == 5) & (T.period == "all")].groupby("n").trades_y.mean().round(0)
x["all @15bp"] = T[(T.cost_bp == 15) & (T.period == "all")].groupby("n").sharpe.mean().round(2)
x["all @30bp"] = T[(T.cost_bp == 30) & (T.period == "all")].groupby("n").sharpe.mean().round(2)
hs = T[(T.cost_bp == 5)].groupby("period").hold_sharpe.mean().round(2).to_dict()
print(f"Average Sharpe over 4 indices (hold-or-cash vs n sessions ago); buy-and-hold: {hs}")
print(x.to_string())
print("\nn = 21 by index (5 bp, all):")
print(T[(T.n == 21) & (T.cost_bp == 5) & (T.period == "all")][["index", "sharpe", "hold_sharpe", "ann", "max_dd", "trades_y"]].round(2).to_string(index=False))

E = c.execute(f"""select ts_code, trade_date, close/pre_close-1 ret from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet')
  where ts_code in ({','.join(f"'{k}'" for k in etf)}) and pre_close > 0""").df()
E["trade_date"] = pd.to_datetime(E.trade_date)
R = E.pivot(index="trade_date", columns="ts_code", values="ret").sort_index().clip(-0.2, 0.2)
rows = []
for e, ix in etf.items():
    re_ = R[e].dropna(); pe = (1 + re_).cumprod()
    pi = P[ix].dropna(); ri = pi.pct_change()
    for n in (10, 21, 42, 252):
        a, b = "2020-01-02", "2026-11-13"
        rows.append({"etf": e, "index": names[ix], "n": n, "etf_sharpe": run(pe, re_, n, 0.0005, a, b)["sharpe"],
                     "etf_hold": run(pe, re_, n, 0.0005, a, b)["hold_sharpe"],
                     "index_sharpe": run(pi, ri, n, 0.0005, a, b)["sharpe"],
                     "etf_sharpe_15bp": run(pe, re_, n, 0.0015, a, b)["sharpe"]})
F = pd.DataFrame(rows); F.to_csv(OUT / "short_trend_etf.csv", index=False)
print("\nETFs vs their index, 2020-01..2026-11 (Sharpe, 5 bp unless noted):")
print(F.round(2).to_string(index=False))

# blends of short windows (position = share of signals that are "up"), optional vol sizing
print("\nBlends (average over 4 indices; Sharpe 2011-18 / 2019-26 / all; max_dd all; trades/yr; all @15bp):")
for label, ns in {"10/21/42": (10, 21, 42), "10/21/42/252": (10, 21, 42, 252), "21 only": (21,), "252 only": (252,)}.items():
    for sized in (False, True):
        out = []
        for code in names:
            p = P[code].dropna(); r = p.pct_change()
            w = pd.concat([(p > p.shift(n)).astype(float).where(p.shift(n).notna()) for n in ns], axis=1).mean(axis=1, skipna=False)
            if sized:
                w = w * (0.20 / (r.rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)
            w = w.shift(1)
            res = {}
            for k, (a, b) in {"h1": ("2011-01-04", "2018-12-31"), "h2": ("2019-01-01", "2026-11-13"), "all": ("2011-01-04", "2026-11-13")}.items():
                ret = (w * r - 0.0005 * w.diff().abs()).loc[a:b].dropna()
                res[k] = ret.mean() / ret.std() * 252 ** 0.5
            ret = (w * r - 0.0005 * w.diff().abs()).loc["2011-01-04":].dropna(); cum = (1 + ret).cumprod()
            ret15 = (w * r - 0.0015 * w.diff().abs()).loc["2011-01-04":].dropna()
            out.append([res["h1"], res["h2"], res["all"], (cum / cum.cummax() - 1).min(),
                        (w.loc["2011":].diff().abs() > 0.01).sum() / 15.9, ret15.mean() / ret15.std() * 252 ** 0.5])
        m = np.mean(out, axis=0)
        print(f"  {label:14s}{' + vol' if sized else '      '}  {m[0]:.2f} / {m[1]:.2f} / {m[2]:.2f}   max_dd {m[3]*100:.0f}%   trades/yr {m[4]:.0f}   @15bp {m[5]:.2f}")
