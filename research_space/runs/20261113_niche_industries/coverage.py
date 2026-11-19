"""Analyst coverage of the 8 little-covered industries that are turning up (report_rc, as of 2026-11-13).

Per company: reports and distinct brokers in 12 months, reports in the last 3 months vs the
9 before (attention arriving?), first report in the lake, latest rating, median consensus
net profit for FY2026 / FY2027 from reports of the last 6 months (亿元), forecast growth,
PE on FY2027, median target price vs today's close.
"""
from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

AS_OF = "20261113"
c = Config.load(Path("."))
OUT = Path(c.lake.root) / "meta/runs/research/20261113_niche_industries"
hot = pd.read_csv(OUT / "cold_turning_up.csv")
cat = LakeCatalog(c.lake.root, c.datasets, read_only=True)
q = LakeQuery(cat)
mem = q.sql("""SELECT l3_name, ts_code, name FROM curated.index_member_all
               WHERE (out_date IS NULL OR out_date = '' OR out_date > ?) AND list_contains(?, l3_name)""",
            [AS_OF, hot["l3_name"].tolist()]).drop_duplicates("ts_code")
codes = mem["ts_code"].tolist()
rc = q.sql("""SELECT ts_code, report_date, report_title, org_name, quarter, np, rating, max_price, min_price
              FROM curated.report_rc WHERE list_contains(?, ts_code) AND report_date <= ?""", [codes, AS_OF])
basic = q.sql("SELECT ts_code, close, total_mv / 1e4 AS mv FROM curated.daily_basic WHERE trade_date = ?", [AS_OF])
cat.close()
rc["report_date"] = rc["report_date"].astype(str)
reports = rc.drop_duplicates(["ts_code", "report_date", "org_name", "report_title"])
y12 = reports[reports.report_date > "20251113"]
g12 = y12.groupby("ts_code")
recent = y12[y12.report_date > "20260813"].groupby("ts_code").size()
older = y12[y12.report_date <= "20260813"].groupby("ts_code").size()
first = reports.groupby("ts_code")["report_date"].min()
last = reports.sort_values("report_date").groupby("ts_code").last()
fc = rc[(rc.report_date > "20260513") & rc["quarter"].astype(str).str.match(r"^202[67]Q4$")]
cons = fc.groupby(["ts_code", "quarter"])["np"].median().unstack()
tp = rc[rc.report_date > "20260513"].assign(tp=lambda d: d[["max_price", "min_price"]].mean(axis=1))
tp = tp.groupby("ts_code")["tp"].median()

df = mem.set_index("ts_code").join(basic.set_index("ts_code"))
df["reports_12m"] = g12.size().reindex(df.index).fillna(0).astype(int)
df["brokers_12m"] = g12["org_name"].nunique().reindex(df.index).fillna(0).astype(int)
df["last_3m"] = recent.reindex(df.index).fillna(0).astype(int)
df["prior_9m_per_3m"] = (older.reindex(df.index).fillna(0) / 3).round(1)
df["first_report"] = first
df["last_rating"] = last["rating"]
df["last_org"] = last["org_name"]
df["np26_yi"] = (cons.get("2026Q4") / 1e4).round(2) if "2026Q4" in cons else None
df["np27_yi"] = (cons.get("2027Q4") / 1e4).round(2) if "2027Q4" in cons else None
df["g27"] = ((df["np27_yi"] / df["np26_yi"] - 1) * 100).round(0)
df["pe27"] = (df["mv"] / df["np27_yi"]).round(1)
df["tp_upside"] = ((tp.reindex(df.index) / df["close"] - 1) * 100).round(0)
df = df.sort_values(["l3_name", "brokers_12m"], ascending=[True, False])
df.to_csv(OUT / "coverage.csv")
pd.set_option("display.width", 250)
summ = df.groupby("l3_name").agg(
    cos=("name", "size"), covered=("brokers_12m", lambda s: int((s > 0).sum())),
    brokers_med=("brokers_12m", "median"), last_3m=("last_3m", "sum"),
    prior_per_3m=("prior_9m_per_3m", "sum"), new_since_2026=("first_report", lambda s: int((s > "20260101").sum())))
print("industry coverage (12 months)"); print(summ.to_string())
cols = ["l3_name", "name", "mv", "reports_12m", "brokers_12m", "last_3m", "prior_9m_per_3m", "first_report",
        "last_rating", "np26_yi", "np27_yi", "g27", "pe27", "tp_upside"]
print("\ncovered companies"); print(df[df.brokers_12m > 0][cols].round(1).to_string(index=False))
