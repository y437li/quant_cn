"""Stock-level small-cap screen (total cap 20–150亿, 20-day average turnover >= 0.5亿, no ST): two quarters of
y/y profit growth (Q2 and Q3 2026 > 20%, Q3 > 0), TTM profit > 0, TTM operating cash flow > 0, PE TTM <= 25 or
PEG (PE TTM / Q3 y/y growth) <= 0.8, own PB percentile since 2016, RetailGauge (veto >= 0.9), then winner rate and
chip cost for the finalists, plus the industry bucket from industries.csv. Writes smallcap_screen.csv."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

cfg = Config.load(Path(".")); LAKE = Path(cfg.lake.root)
OUT = LAKE / "meta/runs/research/20261117_all_industries"; OUT.mkdir(parents=True, exist_ok=True)
c = duckdb.connect(str(LAKE / "meta/quant_cn.duckdb"), read_only=True); q = lambda s: c.execute(s).df()
AS_OF = "20261116"
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 300)
mem = q("SELECT l3_name, ts_code, name FROM curated.index_member_all WHERE out_date IS NULL").drop_duplicates("ts_code")
db = q(f"SELECT ts_code, total_mv/1e4 mv, pe_ttm, pb FROM curated.daily_basic WHERE trade_date='{AS_OF}'").set_index("ts_code")
amt = q(f"""SELECT ts_code, avg(amount)/1e5 amt_yi FROM curated.daily WHERE trade_date IN
  (SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date<='{AS_OF}' ORDER BY trade_date DESC LIMIT 20) GROUP BY 1""").set_index("ts_code").amt_yi
u = mem.set_index("ts_code").join(db).join(amt)
u = u[(u.mv >= 20) & (u.mv <= 150) & (u.amt_yi >= 0.5) & ~u.name.str.contains("ST|退")]
codes = u.index.tolist(); IN = ",".join(repr(x) for x in codes)
inc = q(f"""SELECT ts_code, end_date, arg_max(n_income_attr_p, ann_date) np FROM curated.income_vip
  WHERE report_type='1' AND end_date>='20241231' AND ts_code IN ({IN}) GROUP BY 1,2""")
w = inc.pivot(index="ts_code", columns="end_date", values="np")
need = ["20250331", "20250630", "20250930", "20251231", "20260331", "20260630", "20260930"]
w = w.reindex(columns=need)
qq = lambda a, b: w[b] - w[a]
f = pd.DataFrame({"q2_25": qq("20250331", "20250630"), "q3_25": qq("20250630", "20250930"),
                  "q2_26": qq("20260331", "20260630"), "q3_26": qq("20260630", "20260930")})
f["ttm"] = w["20260930"] + w["20251231"] - w["20250930"]
f["g_q2"] = (f.q2_26 - f.q2_25) / f.q2_25.abs(); f["g_q3"] = (f.q3_26 - f.q3_25) / f.q3_25.abs()
cf = q(f"""SELECT ts_code, end_date, arg_max(n_cashflow_act, ann_date) ocf FROM curated.cashflow_vip
  WHERE report_type='1' AND end_date IN ('20250930','20251231','20260930') AND ts_code IN ({IN}) GROUP BY 1,2""").pivot(index="ts_code", columns="end_date", values="ocf")
f["ocf_ttm"] = cf["20260930"] + cf["20251231"] - cf["20250930"]
u = u.join(f)
u["peg"] = u.pe_ttm / (u.g_q3 * 100)
s = u[(u.g_q2 > 0.2) & (u.g_q3 > 0.2) & (u.q3_26 > 0) & (u.ttm > 0) & (u.ocf_ttm > 0) & ((u.pe_ttm <= 25) | (u.peg <= 0.8))].copy()
gauge = pd.read_parquet(LAKE / "meta/runs/holder_nowcast/holders_forecast_q4.parquet")["pct"]
s["gauge"] = gauge.reindex(s.index)
s = s[~(s.gauge >= 0.9)]
pbh = q(f"""SELECT ts_code, strftime(strptime(trade_date,'%Y%m%d'),'%Y%m') ym, arg_max(pb,trade_date) pb FROM curated.daily_basic
  WHERE trade_date>='20160101' AND ts_code IN ({",".join(repr(x) for x in s.index)}) GROUP BY 1,2""")
s["pb_pct"] = pd.Series({k: (g.pb < s.pb.get(k)).mean() for k, g in pbh[pbh.pb > 0].groupby("ts_code")})
ind = pd.read_csv(OUT / "industries.csv").set_index("l3")
s["ind_bucket"] = s.l3_name.map(ind.bucket)
cl = TushareClient(cfg.tushare, Clock())
for k in s.index:
    d = cl.query("cyq_perf", {"ts_code": k, "trade_date": AS_OF}, [])
    if not d.empty:
        s.loc[k, ["winner", "cost15", "cost50"]] = d.iloc[0][["winner_rate", "cost_15pct", "cost_50pct"]].astype(float).values
close = q(f"SELECT ts_code, close FROM curated.daily WHERE trade_date='{AS_OF}'").set_index("ts_code").close
s["close"] = close.reindex(s.index)
s["below_cost50"] = s.close <= s.cost50
s["score"] = (s.gauge <= 0.3).astype(int) + s.below_cost50.astype(int) + (s.pb_pct <= 0.5).astype(int) + (s.peg <= 0.5).astype(int)
for col in ["q3_25", "q3_26", "ttm", "ocf_ttm"]:
    s[col] = (s[col] / 1e8).round(2)
s = s.sort_values(["score", "peg"], ascending=[False, True])
s.to_csv(OUT / "smallcap_screen.csv")
print(f"universe {len(u)}, pass growth/value/cash {len(s)}")
cols = ["name", "l3_name", "ind_bucket", "mv", "amt_yi", "pe_ttm", "g_q2", "g_q3", "peg", "q3_25", "q3_26", "ocf_ttm", "pb_pct", "gauge", "winner", "close", "cost15", "cost50", "score"]
print(s[cols].round(2).to_string())
