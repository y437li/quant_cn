"""Is consumption weak across the board? Shenwan L1 industry factor returns (risk model) and Q3 2026
single-quarter revenue / profit growth by L1 (sum over members, first prints), consumer vs upstream."""
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
src = lambda t, r="curated": f"read_parquet('{LAKE}/{r}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
mem = q(f"""SELECT DISTINCT l1_code, l1_name, ts_code FROM read_parquet('{LAKE}/curated/reference/index_member_all.parquet')
           WHERE out_date IS NULL OR out_date = ''""")
inc = q(f"""SELECT ts_code, end_date, revenue, n_income_attr_p FROM (
           SELECT *, row_number() OVER (PARTITION BY ts_code, end_date ORDER BY ann_date) rn FROM {src('fundamentals/income')}
           WHERE report_type = '1' AND end_date IN ('20250630', '20250930', '20260630', '20260930')) WHERE rn = 1""")
w = inc.pivot_table(index="ts_code", columns="end_date", values=["revenue", "n_income_attr_p"])
q3 = pd.DataFrame({"rev26": w["revenue"]["20260930"] - w["revenue"]["20260630"], "rev25": w["revenue"]["20250930"] - w["revenue"]["20250630"],
                   "np26": w["n_income_attr_p"]["20260930"] - w["n_income_attr_p"]["20260630"], "np25": w["n_income_attr_p"]["20250930"] - w["n_income_attr_p"]["20250630"]}).dropna()
g = mem.merge(q3, left_on="ts_code", right_index=True).groupby(["l1_code", "l1_name"])[["rev26", "rev25", "np26", "np25"]].sum()
g["Q3收入同比%"] = (g["rev26"] / g["rev25"] - 1) * 100
g["Q3利润同比%"] = (g["np26"] / g["np25"] - 1) * 100
fr = q(f"SELECT trade_date, factor, ret FROM {src('risk_factor_return', 'derived')} WHERE trade_date >= '20251101' AND factor LIKE 'ind_%'")
fr = fr.pivot(index="trade_date", columns="factor", values="ret").sort_index()
cum = lambda n: ((1 + fr.iloc[-n:]).prod() - 1) * 100
g = g.reset_index()
g["因子3月%"] = g["l1_code"].map(lambda c: cum(63).get(f"ind_{c}"))
g["因子12月%"] = g["l1_code"].map(lambda c: cum(250).get(f"ind_{c}"))
consumer = {"食品饮料", "美容护理", "商贸零售", "社会服务", "家用电器", "纺织服饰", "轻工制造", "汽车"}
g["类别"] = g["l1_name"].map(lambda n: "消费" if n in consumer else "其他")
pd.set_option("display.width", 200)
cols = ["类别", "l1_name", "Q3收入同比%", "Q3利润同比%", "因子3月%", "因子12月%"]
print(g.sort_values(["类别", "因子12月%"])[cols].round(1).to_string(index=False))
g.to_csv(LAKE / "meta/runs/research/20261113_proya_review/consumption_l1.csv", index=False)
