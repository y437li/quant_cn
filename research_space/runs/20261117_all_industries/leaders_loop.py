"""Leader loop for other buckets (argv: bucket letters, e.g. N C E; default N C E). Reads industries.csv
from all_industries.py and applies the same leader checks; writes leaders_<letters>.csv. Growth names are
judged with PEG = 2027E PE / 2026E→2027E growth as well, since PE <= 15 alone excludes them."""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

cfg = Config.load(Path(".")); LAKE = Path(cfg.lake.root)
OUT = LAKE / "meta/runs/research/20261117_all_industries"
c = duckdb.connect(str(LAKE / "meta/quant_cn.duckdb"), read_only=True); q = lambda s: c.execute(s).df()
AS_OF = "20261116"
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 400)
BUCKETS = sys.argv[1:] or ["N", "C", "E"]
ind = pd.read_csv(OUT / "industries.csv")
mem = q("SELECT l1_name, l3_name, ts_code, name FROM curated.index_member_all WHERE out_date IS NULL").drop_duplicates("ts_code")
db = q(f"SELECT ts_code, total_mv/1e4 mv, pb FROM curated.daily_basic WHERE trade_date='{AS_OF}'").set_index("ts_code")
pbh = q("""SELECT ts_code, strftime(strptime(trade_date,'%Y%m%d'),'%Y%m') ym, arg_max(pb,trade_date) pb
  FROM curated.daily_basic WHERE trade_date>='20160101' GROUP BY 1,2""")
pbh = pbh[pbh.pb > 0]
gauge = pd.read_parquet(LAKE / "meta/runs/holder_nowcast/holders_forecast_q4.parquet")["pct"]

cand = ind[ind.bucket.str[0].isin(BUCKETS) & (ind.mv_yi >= 300)]
lead = (mem[mem.l3_name.isin(cand.l3)].assign(mv=lambda x: db.reindex(x.ts_code).mv.values)
        .sort_values("mv", ascending=False).groupby("l3_name").head(3).dropna(subset=["mv"]))
codes = lead.ts_code.tolist(); IN = ",".join(repr(x) for x in codes)
rc = q(f"SELECT ts_code, report_date, org_name, quarter, np FROM curated.report_rc WHERE ts_code IN ({IN}) AND quarter IN ('2026Q4','2027Q4') AND report_date>='20260501'")
cons = lambda d0, d1, qt: rc[(rc.report_date > d0) & (rc.report_date <= d1) & (rc.quarter == qt)].sort_values("report_date").groupby(["ts_code", "org_name"]).np.last().groupby("ts_code").median() / 1e4
c27, c27o, c26 = cons("20260816", AS_OF, "2027Q4"), cons("20260501", "20260816", "2027Q4"), cons("20260816", AS_OF, "2026Q4")
pbs = {k: (g.pb < db.pb.get(k, np.nan)).mean() for k, g in pbh[pbh.ts_code.isin(codes)].groupby("ts_code")}
r = q(f"SELECT trade_date, ts_code, pct_chg FROM curated.daily WHERE ts_code IN ({IN}) AND trade_date>'20251116'").pivot(index="trade_date", columns="ts_code", values="pct_chg")
m = q("SELECT trade_date, pct_chg m FROM curated.index_daily WHERE ts_code='000300.SH' AND trade_date>'20251116'").set_index("trade_date").m
sc = q("SELECT trade_date, settle FROM curated.fut_daily WHERE ts_code='SC.INE' AND trade_date>'20251110' ORDER BY 1").set_index("trade_date").settle.pct_change() * 100
cl = TushareClient(cfg.tushare, Clock())
y = cl.query("us_tycr", {"start_date": "20251101", "end_date": AS_OF}, ["date", "y10"]).dropna().sort_values("date")
y["dy"] = y.y10.astype(float).diff() * 100; y["d"] = pd.to_datetime(y.date)
cal = pd.DataFrame({"d": pd.to_datetime(m.index)}).sort_values("d")
dy = pd.merge_asof(cal, y[["d", "dy"]].rename(columns={"d": "ud"}), left_on="d", right_on="ud", allow_exact_matches=False)
dy = pd.Series(dy.dy.values, index=m.index, name="dy")

def beta(code, f):
    d = pd.concat([r.get(code), m, f], axis=1).dropna()
    if len(d) < 120:
        return np.nan, np.nan
    X = np.column_stack([np.ones(len(d)), d.m, d.iloc[:, 2]]); b, *_ = np.linalg.lstsq(X, d.iloc[:, 0], rcond=None)
    e = d.iloc[:, 0] - X @ b; se = np.sqrt(e @ e / (len(d) - 3) * np.linalg.inv(X.T @ X)[2, 2])
    return round(b[2], 2), round(b[2] / se, 1)

sr = lambda x, d=0: round(x, d) if pd.notna(x) and np.isfinite(x) else np.nan
out = []
for _, x in lead.iterrows():
    k = x.ts_code
    d = cl.query("cyq_perf", {"ts_code": k, "trade_date": AS_OF}, [])
    cy = d.iloc[0] if not d.empty else {}
    close = q(f"SELECT close FROM curated.daily WHERE ts_code='{k}' AND trade_date='{AS_OF}'").close
    ob, ot = beta(k, sc.rename("sc")); rb, rt = beta(k, dy * 0.1)  # per 10bp
    out.append(dict(l3=x.l3_name, name=x["name"], code=k, mv=round(x.mv), close=close.iloc[0] if len(close) else np.nan,
                    pe27=sr(x.mv / c27[k], 1) if k in c27 and c27[k] > 0 else np.nan,
                    rev27_3m=sr((c27[k] / c27o[k] - 1) * 100) if k in c27 and k in c27o and c27o[k] > 0 else np.nan,
                    g27=sr((c27[k] / c26[k] - 1) * 100) if k in c27 and k in c26 and c26[k] > 0 else np.nan,
                    pb_pct=round(pbs.get(k, np.nan), 2), gauge=round(gauge.get(k, np.nan), 2),
                    winner=round(float(cy["winner_rate"]), 1) if len(cy) else np.nan,
                    cost15=round(float(cy["cost_15pct"]), 2) if len(cy) else np.nan, cost50=round(float(cy["cost_50pct"]), 2) if len(cy) else np.nan,
                    oil_b=ob, oil_t=ot, us10y_b=rb, us10y_t=rt))
L = pd.DataFrame(out).merge(cand[["l3", "bucket", "yoy_q3", "ttm_vs_peak", "pb_pct"]].rename(columns={"pb_pct": "ind_pb_pct"}), on="l3")
L["veto"] = L.gauge >= 0.9
L["below_cost50"] = L.close <= L.cost50
L["peg"] = (L.pe27 / L.g27).where(L.g27 > 0).round(2)
L.to_csv(OUT / f"leaders_{''.join(BUCKETS)}.csv", index=False)
print(L.to_string(index=False))
