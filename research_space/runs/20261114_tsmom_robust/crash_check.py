"""How much does the trend + volatility sizing rule hold going into sudden crashes? (2026-11-14)

Rule as in vol_sizing.py (12-month direction from the previous month end; size min(1, 20% / sigma)),
sigma = rolling 60-day std or EWMA com 10. For each crash window: position on the first day, loss of
the index over the first 5 sessions and over the whole window, and the rule's loss.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
D = duckdb.connect().execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
D["trade_date"] = pd.to_datetime(D.trade_date)
crashes = {"2015-06 股灾第一波": ("2015-06-15", "2015-07-08"), "2015-08 二次探底": ("2015-08-18", "2015-08-26"),
           "2016-01 熔断": ("2016-01-04", "2016-01-28"), "2018-10 质押危机": ("2018-10-08", "2018-10-18"),
           "2020-02 疫情开市": ("2020-02-03", "2020-02-03"), "2024-01/02 小盘踩踏": ("2024-01-22", "2024-02-07"),
           "2025-04 关税冲击": ("2025-04-07", "2025-04-08")}
rows = []
for code, nm in {"000300.SH": "沪深300", "000852.SH": "中证1000"}.items():
    d = D[D.ts_code == code].set_index("trade_date").sort_index()
    r = d.close.pct_change()
    me = d.close.resample("ME").last()
    on = (me / me.shift(12) - 1 > 0).astype(float).shift(1)
    on = on.reindex(d.index.to_period("M").to_timestamp("M")).set_axis(d.index)
    for lab, s in {"滚动60日": r.rolling(60).std() * 252 ** 0.5,
                   "EWMA10": (r.pow(2).ewm(com=10, min_periods=20).mean() * 252) ** 0.5}.items():
        w = (on * (0.20 / s.shift(1)).clip(upper=1.0)).fillna(0)
        for name, (a, b) in crashes.items():
            win = (r.index >= a) & (r.index <= b)
            if not win.any():
                continue
            first = r.index[win][0]
            i0 = r.index.get_loc(first)
            f5 = r.iloc[i0:i0 + 5]
            rows.append({"index": nm, "sigma": lab, "crash": name, "pos_day1": w.loc[first],
                         "trend_on": on.loc[first], "sigma_before": s.shift(1).loc[first],
                         "index_5d": (1 + f5).prod() - 1, "rule_5d": (1 + w.iloc[i0:i0 + 5] * f5).prod() - 1,
                         "index_all": (1 + r[win]).prod() - 1, "rule_all": (1 + (w * r)[win]).prod() - 1})
T = pd.DataFrame(rows)
T.to_csv(LAKE / "meta/runs/research/20261114_tsmom_robust/crash_check.csv", index=False)
pd.set_option("display.width", 250)
v = T[T.sigma == "滚动60日"].copy()
for c in ("pos_day1", "sigma_before", "index_5d", "rule_5d", "index_all", "rule_all"):
    v[c] = v[c].map(lambda x: f"{x*100:.0f}%")
print(v.drop(columns=["sigma", "trend_on"]).to_string(index=False))
e = T[T.sigma == "EWMA10"]
print("\nEWMA10 position on day 1:", ", ".join(f"{r['index']} {r.crash} {r.pos_day1*100:.0f}%" for _, r in e.iterrows()))
