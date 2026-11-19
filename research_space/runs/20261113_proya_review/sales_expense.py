"""Selling-expense ratio of 珀莱雅 vs A-share cosmetics peers and other consumer brands, annual
2019-2025 plus 2026 Q1-Q3 (first prints, report_type 1)."""
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
peers = q(f"""SELECT DISTINCT ts_code, name, l3_name FROM read_parquet('{LAKE}/curated/reference/index_member_all.parquet')
             WHERE l2_name = '化妆品' AND (out_date IS NULL OR out_date = '')""")
others = {"600519.SH": "贵州茅台", "600887.SH": "伊利股份", "000333.SZ": "美的集团", "603288.SH": "海天味业",
          "300957.SZ": "贝泰妮", "603983.SH": "丸美生物", "600315.SH": "上海家化", "688363.SH": "华熙生物"}
codes = sorted(set(peers["ts_code"]) | set(others))
inc = q(f"""SELECT ts_code, end_date, revenue, sell_exp, oper_cost, n_income_attr_p FROM (
             SELECT *, row_number() OVER (PARTITION BY ts_code, end_date ORDER BY ann_date) rn FROM {src('fundamentals/income')}
             WHERE report_type = '1' AND (end_date LIKE '%1231' OR end_date = '20260930') AND end_date >= '20190101'
               AND list_contains({codes}, ts_code)) WHERE rn = 1""")
inc["p"] = inc["end_date"].str[:4].where(inc["end_date"].str.endswith("1231"), "26Q3累计")
inc["sell"] = inc["sell_exp"] / inc["revenue"] * 100
inc["gm"] = (1 - inc["oper_cost"] / inc["revenue"]) * 100
inc["npm"] = inc["n_income_attr_p"] / inc["revenue"] * 100
names = {**dict(zip(peers["ts_code"], peers["name"])), **others}
inc["name"] = inc["ts_code"].map(names)
pd.set_option("display.width", 230)
piv = inc.pivot_table(index="name", columns="p", values="sell").round(1)
last = inc[inc["p"] == "26Q3累计"].set_index("name")[["revenue", "gm", "npm"]]
last["revenue"] = last["revenue"] / 1e8
out = piv.join(last.round(1).rename(columns={"revenue": "26Q3收入亿", "gm": "毛利率", "npm": "净利率"}))
out = out[out["26Q3收入亿"].notna()].sort_values("26Q3收入亿", ascending=False)
print("销售费用率 %（年度；26Q3 为前三季度累计）"); print(out.to_string())
out.to_csv(LAKE / "meta/runs/research/20261113_proya_review/sales_expense.csv")
