"""筹码干净 by the RetailGauge standard: predicted Q4 holder outflow (decile 0-1) confirmed by announced Q2->Q3 outflow; chip metrics alongside."""
import duckdb, pandas as pd
L="/Volumes/Treasury/quant_cn_lake/curated"; OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_clean_chips"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
m=pd.read_csv(f"{OUT}/all_chip_metrics_20261113.csv",dtype={"ts_code":str}).set_index("ts_code")
rg=pd.read_csv("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_retail_gauge_q4_table/retail_gauge_q4_20261231.csv",dtype={"代码":str}).set_index("代码")
h=duckdb.sql(f"""with h as (select ts_code,end_date,arg_max(holder_num,ann_date) n from {s('events/stk_holdernumber')} where end_date in ('20260331','20260630') group by 1,2)
 select ts_code, max(n) filter (where end_date='20260630')/max(n) filter (where end_date='20260331')-1 hq2 from h group by 1""").df().set_index("ts_code")
t=m.join(rg[["预测分位","Q3户数","Q4预测户数"]]).join(h)
t=t[t["流通市值亿"].notna()]
print("universe",len(t),"| decile counts:",t["Q4温度计组"].value_counts().sort_index().to_dict())
G=t[(t["Q4温度计组"]<=1)&(t["Q3户数变化"]<=-0.05)]
G2=G[G.hq2<=0]
print(f"decile 0-1: {int((t['Q4温度计组']<=1).sum())} | + Q3 ≤ -5%: {len(G)} | + Q2 also down (3 quarters out): {len(G2)}")
G2=G2.assign(Q2户数变化=G2.hq2.round(3)).sort_values("预测分位")
cols=["名称","行业","流通市值亿","Q2户数变化","Q3户数变化","预测分位","Q3户数","Q4预测户数","70%筹码带宽","带宽60日变化","获利盘%","上方套牢(cost95/价-1)","距1年高点","20日大单净流入%流通"]
pd.set_option("display.width",300); pd.set_option("display.max_rows",300); pd.set_option("display.max_columns",30)
print(G2[cols].round({"预测分位":3}).to_string())
G2[cols].to_csv(f"{OUT}/gauge_clean_20261113.csv",encoding="utf-8-sig")
