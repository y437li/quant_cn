"""Top 50 most favourable chip structure (float cap >= 50亿, non-ST, as of 2026-11-13).
Score = mean of within-universe percentile ranks (lower is better) of: Q3 holder change, Q2 holder change, RetailGauge percentile,
70% cost band width, 60-day band change, overhead supply (cost95 / price - 1). Large-order flow left out (20261115_watch_conditions_bt: no edge).
Filters: gauge < 0.9 (veto), Q3 holder change <= +10% (drop post-rush mean-reversion names), Q2 holder data present."""
import duckdb, pandas as pd
L="/Volumes/Treasury/quant_cn_lake/curated"; OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_clean_chips"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
m=pd.read_csv(f"{OUT}/all_chip_metrics_20261113.csv").set_index("ts_code")
rg=pd.read_csv("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_retail_gauge_q4_table/retail_gauge_q4_20261231.csv",dtype={"代码":str}).set_index("代码")
h=duckdb.sql(f"""with h as (select ts_code,end_date,arg_max(holder_num,ann_date) n from {s('events/stk_holdernumber')} where end_date in ('20260331','20260630','20260930') group by 1,2)
 select ts_code, max(n) filter (where end_date='20260630')/max(n) filter (where end_date='20260331')-1 hq2, max(n) filter (where end_date='20260930') n3 from h group by 1""").df().set_index("ts_code")
v=duckdb.sql(f"select ts_code, pe_ttm, dv_ttm from {s('daily_basic')} where trade_date='20261113'").df().set_index("ts_code")
t=m.join(rg[["预测分位"]]).join(h).join(v)
t=t[t["流通市值亿"].notna()&t["预测分位"].notna()&t.hq2.notna()&t["Q3户数变化"].notna()]
t=t[(t["预测分位"]<0.9)&(t["Q3户数变化"]<=0.10)]
comp={"Q3户数变化":t["Q3户数变化"],"Q2户数变化":t.hq2,"温度计":t["预测分位"],"筹码带宽":t["70%筹码带宽"],"带宽60日变化":t["带宽60日变化"],"上方套牢":t["上方套牢(cost95/价-1)"]}
R=pd.DataFrame({k:x.rank(pct=True) for k,x in comp.items()})
t["score"]=R.mean(axis=1)
top=t.sort_values("score").head(50)
o=pd.DataFrame({"名称":top["名称"],"行业":top["行业"],"流通市值亿":top["流通市值亿"].round(0),"评分":top.score.round(3),
  "Q2户数":(top.hq2*100).round(0),"Q3户数":(top["Q3户数变化"]*100).round(0),"温度计":top["预测分位"].round(2),
  "筹码带宽%":(top["70%筹码带宽"]*100).round(1),"带宽60日":(top["带宽60日变化"]*100).round(1),"套牢%":(top["上方套牢(cost95/价-1)"]*100).round(0),
  "获利盘%":top["获利盘%"].round(0),"距高点%":(top["距1年高点"]*100).round(0),"PE":top.pe_ttm.round(1),"股息%":top.dv_ttm.round(1)})
o.to_csv(f"{OUT}/chip_top50_20261113.csv",encoding="utf-8-sig")
pd.set_option("display.width",300); pd.set_option("display.max_rows",60); pd.set_option("display.max_columns",20)
print("universe after filters:",len(t)); print(o.to_string())
print("industries:",o["行业"].value_counts().head(10).to_dict())
print("winner>=70:",int((o["获利盘%"]>=70).sum()),"winner<=20:",int((o["获利盘%"]<=20).sum()),"dd<=-30:",int((o["距高点%"]<=-30).sum()),"PE<=20:",int((o.PE<=20).sum()),"div>=3:",int((o["股息%"]>=3).sum()))
