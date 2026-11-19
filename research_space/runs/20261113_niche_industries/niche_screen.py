"""Little-covered Shenwan L3 industries whose fundamentals are turning up (as of 2026-11-13).

冷门 = few analyst reports per company in the last 12 months (report_rc) and a small industry.
Per industry (current members): median YTD revenue and deducted-profit growth at 20260930,
gross-margin change vs 20250930, share of members growing revenue > 20%, total market cap,
6-month price change, latest holder-count change (筹码: falling = concentrating).
"""
from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

AS_OF, Q, Q_LY, SIX_M = "20261113", "20260930", "20250930", "20260513"
c = Config.load(Path("."))
OUT = Path(c.lake.root) / "meta/runs/research/20261113_niche_industries"
OUT.mkdir(parents=True, exist_ok=True)
cat = LakeCatalog(c.lake.root, c.datasets, read_only=True)
q = LakeQuery(cat)
mem = q.sql("""SELECT l1_name, l2_name, l3_name, ts_code, name FROM curated.index_member_all
               WHERE out_date IS NULL OR out_date = '' OR out_date > ?""", [AS_OF]).drop_duplicates("ts_code")
fi = q.sql("""SELECT ts_code, end_date, or_yoy, dt_netprofit_yoy, grossprofit_margin, ann_date
              FROM curated.fina_indicator_vip WHERE end_date IN (?, ?) AND ann_date <= ?""", [Q, Q_LY, AS_OF])
fi = fi.sort_values("ann_date").drop_duplicates(["ts_code", "end_date"], keep="last")
now = fi[fi.end_date == Q].set_index("ts_code")
ly = fi[fi.end_date == Q_LY].set_index("ts_code")
rc = q.sql("""SELECT ts_code, count(DISTINCT report_title) n FROM curated.report_rc
              WHERE report_date > '20251113' AND report_date <= ? GROUP BY 1""", [AS_OF]).set_index("ts_code")["n"]
mv = q.sql("SELECT ts_code, total_mv / 1e4 AS mv FROM curated.daily_basic WHERE trade_date = ?", [AS_OF]).set_index("ts_code")["mv"]
px = q.sql("""SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS p FROM curated.daily d
              JOIN curated.adj_factor a USING (ts_code, trade_date) WHERE d.trade_date IN (?, ?)""", [SIX_M, AS_OF])
px = px.pivot_table(index="ts_code", columns="trade_date", values="p")
hn = q.sql("""SELECT ts_code, end_date, holder_num FROM curated.stk_holdernumber
              WHERE ann_date <= ? AND end_date >= '20250101'""", [AS_OF])
cat.close()
hn = hn.sort_values(["ts_code", "end_date"]).drop_duplicates(["ts_code", "end_date"], keep="last")
hn["chg"] = hn.groupby("ts_code")["holder_num"].pct_change()
hchg = hn.groupby("ts_code")["chg"].last()

df = mem.set_index("ts_code")
df["or_yoy"] = now["or_yoy"]
df["dedt_yoy"] = now["dt_netprofit_yoy"]
df["gm_chg"] = now["grossprofit_margin"] - ly["grossprofit_margin"]
df["reports"] = rc.reindex(df.index).fillna(0)
df["mv"] = mv
df["ret_6m"] = (px[AS_OF] / px[SIX_M] - 1) * 100
df["holders_chg"] = hchg * 100
df = df[df["mv"].notna()]
g = df.groupby(["l1_name", "l2_name", "l3_name"])
ind = pd.DataFrame({
    "n": g.size(),
    "reports_per_co": g["reports"].mean(),
    "covered_share": g["reports"].apply(lambda s: (s >= 3).mean()),
    "mv_yi": g["mv"].sum(),
    "or_yoy_med": g["or_yoy"].median(),
    "dedt_yoy_med": g["dedt_yoy"].median(),
    "gm_chg_med": g["gm_chg"].median(),
    "share_rev_gt20": g["or_yoy"].apply(lambda s: (s > 20).mean()),
    "ret_6m_med": g["ret_6m"].median(),
    "holders_chg_med": g["holders_chg"].median(),
    "names": g["name"].apply(lambda s: "、".join(s.head(6))),
}).reset_index()
ind.to_csv(OUT / "industries.csv", index=False)
cold = ind[(ind["n"] >= 3) & (ind["reports_per_co"] <= ind["reports_per_co"].quantile(0.35))]
hot = cold[(cold["or_yoy_med"] > 10) & (cold["gm_chg_med"] > 0)].sort_values("dedt_yoy_med", ascending=False)
pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 40)
cols = ["l1_name", "l3_name", "n", "reports_per_co", "mv_yi", "or_yoy_med", "dedt_yoy_med", "gm_chg_med",
        "share_rev_gt20", "ret_6m_med", "holders_chg_med", "names"]
print(f"{len(ind)} L3 industries; cold (coverage bottom 35%, n>=3): {len(cold)}; turning up: {len(hot)}")
print(hot[cols].round(1).head(25).to_string(index=False))
hot.to_csv(OUT / "cold_turning_up.csv", index=False)
print(f"\nwhole market: median 6m return {df['ret_6m'].median():.1f}%, median YTD revenue growth {df['or_yoy'].median():.1f}%")
top = df[df["l3_name"].isin(hot["l3_name"].head(6))].sort_values(["l3_name", "dedt_yoy"], ascending=[True, False])
cols = ["l3_name", "name", "mv", "or_yoy", "dedt_yoy", "gm_chg", "reports", "ret_6m", "holders_chg"]
print(top[cols].groupby("l3_name").head(4).round(1).to_string())
top[cols].to_csv(OUT / "members_top.csv")
