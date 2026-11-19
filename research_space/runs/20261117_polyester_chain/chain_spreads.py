"""Polyester chain price spreads from main futures (SC, PX, TA, EG, PF, PR): level, 3m / 1y change, percentile.

Spreads (元/吨, raw-material only, before processing cost):
  PX − crude:      PX − 7.33 × SC (SC 元/桶, 7.33 bbl/t)
  PTA fee:         TA − 0.655 × PX
  staple PF:       PF − 0.855 × TA − 0.335 × EG
  bottle chip PR:  PR − 0.855 × TA − 0.335 × EG
Writes spreads_daily.csv and spreads_summary.csv to the lake run folder.
"""
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261117_polyester_chain"; OUT.mkdir(parents=True, exist_ok=True)
c = duckdb.connect(str(LAKE / "meta/quant_cn.duckdb"), read_only=True)
CODES = ["SC.INE", "PX.ZCE", "TA.ZCE", "EG.DCE", "PF.ZCE", "PR.ZCE"]
px = c.execute(f"SELECT trade_date, ts_code, settle FROM curated.fut_daily WHERE ts_code IN ({','.join(repr(x) for x in CODES)}) AND trade_date>='20190101'").df()
w = px.pivot(index="trade_date", columns="ts_code", values="settle").sort_index()
w.columns = [x.split(".")[0] for x in w.columns]
w["PX_crude"] = w.PX - 7.33 * w.SC
w["PTA_fee"] = w.TA - 0.655 * w.PX
w["PF_margin"] = w.PF - 0.855 * w.TA - 0.335 * w.EG
w["PR_margin"] = w.PR - 0.855 * w.TA - 0.335 * w.EG
w.to_csv(OUT / "spreads_daily.csv")
rows = []
for col in ["SC", "PX", "TA", "EG", "PF", "PR", "PX_crude", "PTA_fee", "PF_margin", "PR_margin"]:
    s = w[col].dropna()
    if s.empty:
        continue
    last = s.iloc[-1]
    at = lambda d: s[s.index <= d].iloc[-1] if (s.index <= d).any() else float("nan")
    rows.append({"series": col, "since": s.index[0], "now": round(last), "3m_ago": round(at("20260816")), "1y_ago": round(at("20251116")),
                 "pct_since": round((s < last).mean(), 2), "median": round(s.median()), "min": round(s.min()), "max": round(s.max()),
                 "avg_2026Q3": round(s[(s.index >= "20260701") & (s.index <= "20260930")].mean()),
                 "avg_2025Q3": round(s[(s.index >= "20250701") & (s.index <= "20250930")].mean())})
res = pd.DataFrame(rows)
res.to_csv(OUT / "spreads_summary.csv", index=False)
print(res.to_string(index=False))
m = w[["PX_crude", "PTA_fee", "PF_margin", "PR_margin"]].copy()
m.index = pd.to_datetime(m.index)
print(m[m.index >= "2025-01-01"].resample("ME").mean().round(0).to_string())
