"""Which SW L2 industries have their margins squeezed by the 2026 upstream price surge (PPI mining +27.9% in Oct).
Single-quarter gross and operating margins, aggregated per SW L2 (sum of cost / sum of revenue), balanced sample:
Q3 2026 vs Q3 2025 (YoY, no seasonality) and Q3 2026 vs Q2 2026 (sequential, PPI accelerated Aug-Oct).
Financials excluded. Output: lake meta/runs/research/20261113_margin_squeeze/l2_margins.csv"""
import duckdb
import pandas as pd

L = "/Volumes/Treasury/quant_cn_lake"
OUT = f"{L}/meta/runs/research/20261113_margin_squeeze/l2_margins.csv"
ENDS = ["20250630", "20250930", "20260331", "20260630", "20260930"]
c = duckdb.connect()
inc = c.sql(f"""
  SELECT ts_code, end_date, revenue, oper_cost, operate_profit FROM (
    SELECT *, row_number() OVER (PARTITION BY ts_code, end_date ORDER BY ann_date DESC, f_ann_date DESC, update_flag DESC) rn
    FROM read_parquet('{L}/curated/fundamentals/income/**/*.parquet', hive_partitioning=1)
    WHERE report_type = '1' AND end_date IN ({",".join(repr(e) for e in ENDS)}) AND ann_date <= '20261113')
  WHERE rn = 1""").df()
mem = c.sql(f"""SELECT ts_code, l1_name, l2_name FROM read_parquet('{L}/curated/reference/index_member_all.parquet')
  WHERE out_date IS NULL AND l1_name NOT IN ('银行', '非银金融')""").df().drop_duplicates("ts_code")
w = {f: inc.pivot(index="ts_code", columns="end_date", values=f) for f in ["revenue", "oper_cost", "operate_profit"]}


def single(f, end, prev):
    return w[f][end] - w[f][prev]


q = {"q3_25": ("20250930", "20250630"), "q2_26": ("20260630", "20260331"), "q3_26": ("20260930", "20260630")}
rows = pd.DataFrame(index=w["revenue"].index)
for k, (e, p) in q.items():
    for f in ["revenue", "oper_cost", "operate_profit"]:
        rows[f"{f}_{k}"] = single(f, e, p)
rows = rows.dropna()
rows = rows[(rows.filter(like="revenue_") > 0).all(axis=1)].join(mem.set_index("ts_code"), how="inner")
g = rows.groupby(["l1_name", "l2_name"]).sum(numeric_only=True)
g["n"] = rows.groupby(["l1_name", "l2_name"]).size()
for k in q:
    g[f"gm_{k}"] = (1 - g[f"oper_cost_{k}"] / g[f"revenue_{k}"]) * 100
    g[f"om_{k}"] = g[f"operate_profit_{k}"] / g[f"revenue_{k}"] * 100
g["gm_yoy_pp"] = g.gm_q3_26 - g.gm_q3_25
g["gm_qoq_pp"] = g.gm_q3_26 - g.gm_q2_26
g["om_yoy_pp"] = g.om_q3_26 - g.om_q3_25
g["rev_yoy"] = (g.revenue_q3_26 / g.revenue_q3_25 - 1) * 100
g["op_yoy"] = (g.operate_profit_q3_26 / g.operate_profit_q3_25.where(g.operate_profit_q3_25 > 0) - 1) * 100
g["rev_q3_26_yi"] = g.revenue_q3_26 / 1e8
cols = ["n", "rev_q3_26_yi", "rev_yoy", "gm_q3_26", "gm_yoy_pp", "gm_qoq_pp", "om_q3_26", "om_yoy_pp", "op_yoy"]
g = g[g.n >= 8][cols].round(1).sort_values("gm_yoy_pp")
g.to_csv(OUT)
pd.set_option("display.width", 200)
print(f"companies {len(rows)}, L2 industries {len(g)}")
print("== most squeezed (gross margin YoY, pp)"); print(g.head(25).to_string())
print("== biggest gainers"); print(g.tail(12).to_string())
print("== L1 totals")
t = rows.groupby("l1_name").sum(numeric_only=True)
t["gm_yoy_pp"] = ((1 - t.oper_cost_q3_26 / t.revenue_q3_26) - (1 - t.oper_cost_q3_25 / t.revenue_q3_25)) * 100
t["om_yoy_pp"] = (t.operate_profit_q3_26 / t.revenue_q3_26 - t.operate_profit_q3_25 / t.revenue_q3_25) * 100
t["rev_yoy"] = (t.revenue_q3_26 / t.revenue_q3_25 - 1) * 100
print(t[["gm_yoy_pp", "om_yoy_pp", "rev_yoy"]].round(1).sort_values("gm_yoy_pp").to_string())
