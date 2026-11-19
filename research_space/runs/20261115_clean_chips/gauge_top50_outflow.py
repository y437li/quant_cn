"""Top 50 predicted retail outflow (RetailGauge v5, as-of 2026-11-12) among float cap >= 50亿 non-ST, with chips, flows and valuation."""
import duckdb, pandas as pd
L="/Volumes/Treasury/quant_cn_lake/curated"; OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_clean_chips"
m=pd.read_csv(f"{OUT}/all_chip_metrics_20261113.csv").set_index("ts_code")
rg=pd.read_csv("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_retail_gauge_q4_table/retail_gauge_q4_20261231.csv",dtype={"代码":str}).set_index("代码")
pe=duckdb.sql(f"select ts_code, pe_ttm, dv_ttm from read_parquet('{L}/daily_basic/**/*.parquet', hive_partitioning=true, union_by_name=true) where trade_date='20261113'").df().set_index("ts_code")
t=m.join(rg[["预测分位","Q3户数","Q4预测户数"]]).join(pe)
t=t[t["流通市值亿"].notna()].sort_values("预测分位").head(50)
cols=["名称","行业","流通市值亿","预测分位","Q3户数变化","Q4预测变化%","Q3户数","获利盘%","距1年高点","20日大单净流入%流通","70%筹码带宽","pe_ttm","dv_ttm"]
o=t[cols].rename(columns={"pe_ttm":"PE","dv_ttm":"股息率%"})
o["预测分位"]=o["预测分位"].round(3); o["PE"]=o.PE.round(1); o["股息率%"]=o["股息率%"].round(1); o["Q3户数"]=(o["Q3户数"]/1e4).round(2)
o.to_csv(f"{OUT}/gauge_top50_outflow_20261113.csv",encoding="utf-8-sig")
pd.set_option("display.width",300); pd.set_option("display.max_rows",60); pd.set_option("display.max_columns",20)
print(o.to_string())
print("industries:",o["行业"].value_counts().head(8).to_dict())
print("lg20>0:",int((o["20日大单净流入%流通"]>0).sum()),"| winner<=20:",int((o["获利盘%"]<=20).sum()),"| dd<=-30%:",int((o["距1年高点"]<=-0.3).sum()))
