"""Does a 12-month trend rule avoid A-share index declines? (2026-11-14)

Rule: hold the index next month when its own past-12-month return is > 0, else cash (0%); no vol
scaling, monthly, 5 bp per switch. Price indices since 2010 (no dividends; cash earns nothing).
Reports max drawdown, return in the big declines and in the rebounds the rule missed.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_tsmom_robust"
I = duckdb.connect().execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
I["trade_date"] = pd.to_datetime(I.trade_date)
P = I.pivot(index="trade_date", columns="ts_code", values="close").sort_index()
M = P.resample("ME").last()
M = M[M.index < "2026-11-01"]
r = M.pct_change()
names = {"000300.SH": "沪深300", "000905.SH": "中证500", "000852.SH": "中证1000", "399006.SZ": "创业板指"}
periods = {"2015-06..2016-01 股灾": ("2015-06-30", "2016-01-31"), "2018 全年熊市": ("2018-01-31", "2018-12-31"),
           "2021-03..2024-01 慢熊": ("2021-03-31", "2024-01-31"), "2024-02..2024-12 反弹": ("2024-02-29", "2024-12-31"),
           "2019 反弹": ("2019-01-31", "2019-12-31")}
dd = lambda x: ((1 + x).cumprod() / (1 + x).cumprod().cummax() - 1).min()
rows = []
for code, nm in names.items():
    past = M[code] / M[code].shift(12) - 1
    on = (past > 0).astype(float).shift(1)
    strat = on * r[code] - 0.0005 * on.diff().abs()
    a = pd.concat([r[code], strat], axis=1, keys=["hold", "trend"]).dropna()
    a = a[a.index >= "2011-01-01"]
    row = {"index": nm, "ann_hold": (1 + a.hold).prod() ** (12 / len(a)) - 1, "ann_trend": (1 + a.trend).prod() ** (12 / len(a)) - 1,
           "maxdd_hold": dd(a.hold), "maxdd_trend": dd(a.trend), "time_in": on[a.index].mean(), "switches": on[a.index].diff().abs().sum()}
    for lab, (s, e) in periods.items():
        w = a[(a.index > s) & (a.index <= e)]
        row[f"{lab} hold"] = (1 + w.hold).prod() - 1
        row[f"{lab} trend"] = (1 + w.trend).prod() - 1
    rows.append(row)
T = pd.DataFrame(rows).set_index("index"); T.to_csv(OUT / "avoid_drawdown.csv")
pd.set_option("display.width", 250)
print((T * 100).round(0).T.to_string())
