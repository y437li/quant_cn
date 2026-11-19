"""Sector scan for a list of Shenwan L3 industries (argv: run slug, then L3 names), as of 2026-11-13.

Per L3 (sums / medians over current members) and per leading member (top by market cap):
single-quarter revenue and net profit 2026Q3 vs 2025Q3, Q3 gross margin vs a year earlier, price
return 3 / 12 months (cap-weighted for the L3), PE TTM and PB now vs the member's 5-year median,
analyst reports and brokers in 12 months, holder-count change, 20-day large-order flow, RetailGauge,
winner rate (live Tushare cyq_perf, leaders only).
"""
import sys
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

SLUG, L3S, AS_OF, TOP = sys.argv[1], sys.argv[2:], "20261113", 5
c = Config.load(Path(".")); LAKE = Path(c.lake.root)
OUT = LAKE / "meta/runs/research" / SLUG; OUT.mkdir(parents=True, exist_ok=True)
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
mem = q(f"""SELECT DISTINCT l3_name, ts_code, name FROM read_parquet('{LAKE}/curated/reference/index_member_all.parquet')
           WHERE (out_date IS NULL OR out_date = '') AND list_contains({L3S}, l3_name)""").drop_duplicates("ts_code")
codes = mem["ts_code"].tolist()
inc = q(f"""SELECT ts_code, end_date, revenue, oper_cost, n_income_attr_p FROM (
           SELECT *, row_number() OVER (PARTITION BY ts_code, end_date ORDER BY ann_date) rn FROM {src('fundamentals/income')}
           WHERE report_type = '1' AND end_date IN ('20250630', '20250930', '20260630', '20260930') AND list_contains({codes}, ts_code)) WHERE rn = 1""")
w = inc.pivot_table(index="ts_code", columns="end_date", values=["revenue", "oper_cost", "n_income_attr_p"])
qv = lambda f, y: w[f][f"{y}0930"] - w[f][f"{y}0630"]
f = pd.DataFrame({"rev26": qv("revenue", 2026), "rev25": qv("revenue", 2025), "np26": qv("n_income_attr_p", 2026),
                  "np25": qv("n_income_attr_p", 2025), "gm26": 1 - qv("oper_cost", 2026) / qv("revenue", 2026),
                  "gm25": 1 - qv("oper_cost", 2025) / qv("revenue", 2025)})
db = q(f"""SELECT ts_code, trade_date, close, pe_ttm, pb, total_mv / 1e4 AS mv FROM {src('daily_basic')}
          WHERE trade_date >= '20211113' AND list_contains({codes}, ts_code)""")
now = db[db["trade_date"] == AS_OF].set_index("ts_code")
hist = db[db["pe_ttm"] > 0].groupby("ts_code").agg(pe_med=("pe_ttm", "median"), pb_med=("pb", "median"))
px = q(f"""SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS p FROM {src('daily')} d JOIN {src('adj_factor')} a USING (ts_code, trade_date)
          WHERE d.trade_date IN ('20251113', '20260813', '{AS_OF}') AND list_contains({codes}, d.ts_code)""").pivot(index="ts_code", columns="trade_date", values="p")
rc = q(f"""SELECT ts_code, count(DISTINCT report_title) AS reports, count(DISTINCT org_name) AS brokers FROM {src('analysts/report_rc')}
          WHERE report_date > '20251113' AND list_contains({codes}, ts_code) GROUP BY 1""").set_index("ts_code")
hn = q(f"""SELECT ts_code, end_date, arg_max(holder_num, ann_date) AS n FROM {src('events/stk_holdernumber')}
          WHERE ann_date <= '{AS_OF}' AND end_date >= '20260331' AND list_contains({codes}, ts_code) GROUP BY 1, 2""").sort_values(["ts_code", "end_date"])
hn["chg"] = hn.groupby("ts_code")["n"].pct_change(); hn = hn.groupby("ts_code")["chg"].last()
lg = q(f"""SELECT ts_code, sum(buy_lg_amount + buy_elg_amount - sell_lg_amount - sell_elg_amount) / 1e4 AS lg20 FROM {src('moneyflow')}
          WHERE trade_date > '20261016' AND list_contains({codes}, ts_code) GROUP BY 1""").set_index("ts_code")["lg20"]
gauge = pd.read_parquet(LAKE / "meta/runs/holder_nowcast/holders_forecast_q4.parquet")["pct"]
df = mem.set_index("ts_code").join(f).join(now[["close", "pe_ttm", "pb", "mv"]]).join(hist).join(rc).join(px)
df["ret3m"] = (df[AS_OF] / df["20260813"] - 1) * 100; df["ret12m"] = (df[AS_OF] / df["20251113"] - 1) * 100
df["holders_chg"] = hn * 100; df["lg20"] = lg; df["gauge"] = gauge
df[["reports", "brokers"]] = df[["reports", "brokers"]].fillna(0)
g = df.groupby("l3_name")
wret = lambda col: g.apply(lambda s: (s[col] * s["mv"]).sum() / s.loc[s[col].notna(), "mv"].sum())
ind = pd.DataFrame({"公司": g.size(), "市值亿": g["mv"].sum(), "Q3收入同比%": (g["rev26"].sum() / g["rev25"].sum() - 1) * 100,
                    "Q3利润亿": g["np26"].sum() / 1e8, "去年Q3利润亿": g["np25"].sum() / 1e8,
                    "Q3毛利率变化pp": g.apply(lambda s: ((s["gm26"] - s["gm25"]) * 100).median()),
                    "3月涨跌%": wret("ret3m"), "12月涨跌%": wret("ret12m"), "PE中位": g["pe_ttm"].median(),
                    "PE相对5年中位": g.apply(lambda s: (s["pe_ttm"] / s["pe_med"]).median()), "有研报公司": g["brokers"].apply(lambda s: int((s > 0).sum())),
                    "户数变化%中位": g["holders_chg"].median(), "20日大单亿合计": g["lg20"].sum(), "温度计中位": g["gauge"].median()})
pd.set_option("display.width", 250)
print("行业"); print(ind.round(2).T.to_string())
top = df.sort_values("mv", ascending=False).groupby("l3_name").head(TOP).copy()
cl = TushareClient(c.tushare, Clock())
for code in top.index:
    d = cl.query("cyq_perf", {"ts_code": code, "trade_date": AS_OF}, [])
    top.loc[code, "winner"] = float(d["winner_rate"].iloc[0]) if not d.empty else None
top["rev_yoy"] = (top["rev26"] / top["rev25"] - 1) * 100; top["np26_yi"] = top["np26"] / 1e8; top["np25_yi"] = top["np25"] / 1e8
top["gm26"] *= 100; top["gm25"] *= 100
cols = ["l3_name", "name", "mv", "rev_yoy", "np26_yi", "np25_yi", "gm26", "gm25", "pe_ttm", "pe_med", "pb", "ret3m", "ret12m",
        "brokers", "holders_chg", "lg20", "gauge", "winner"]
print("\n龙头"); print(top[cols].round(1).to_string(index=False))
df.to_csv(OUT / "members.csv"); ind.to_csv(OUT / "industries.csv"); top.to_csv(OUT / "leaders.csv")
