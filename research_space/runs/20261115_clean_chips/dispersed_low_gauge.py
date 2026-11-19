"""Screen 2026-11-13: dispersed chips (70% cost band in the top third of float cap >= 50亿 names) and RetailGauge <= 0.3,
with turnover filter to drop low-turnover distortions (band inflated by stale costs, e.g. big banks), plus valuation context."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; M="/Volumes/Treasury/quant_cn_lake/meta/runs"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
c=pd.read_csv(f"{M}/research/20261115_clean_chips/all_chip_metrics_20261113.csv"); c=c[c["流通市值亿"]>=50].copy()
g=pd.read_parquet(f"{M}/holder_nowcast/holders_forecast_q4.parquet").pct; c["温度计"]=c.ts_code.map(g)
c["带宽分位"]=c["70%筹码带宽"].rank(pct=True)
b=duckdb.sql(f"""select ts_code, avg(turnover_rate_f) tov120 from {s('daily_basic')} where trade_date>'20260520' and trade_date<='20261113' group by 1""").df().set_index("ts_code").tov120
v=duckdb.sql(f"select ts_code,pe_ttm,pb,dv_ttm from {s('daily_basic')} where trade_date='20261113'").df().set_index("ts_code")
P=duckdb.sql(f"select d.ts_code,d.trade_date,d.close*a.adj_factor p from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date in ('20260814','20261113')").df().pivot(index="ts_code",columns="trade_date",values="p")
c["120日换手%"]=c.ts_code.map(b); c=c.join(v,on="ts_code"); c["近3月涨跌%"]=c.ts_code.map((P["20261113"]/P["20260814"]-1)*100)
tov_floor=c["120日换手%"].quantile(0.2)
sel=c[(c["带宽分位"]>=2/3)&(c["温度计"]<=0.3)&(c["120日换手%"]>=tov_floor)].copy()
sel=sel.sort_values("温度计")
cols=["ts_code","名称","行业","流通市值亿","温度计","70%筹码带宽","带宽分位","上方套牢(cost95/价-1)","获利盘%","距1年高点","近3月涨跌%","pe_ttm","pb","dv_ttm","120日换手%"]
out=sel[cols].round(2); print("universe",len(c),"turnover floor",round(tov_floor,2),"selected",len(out)); pd.set_option("display.width",300); print(out.to_string(index=False))
out.to_csv(f"{M}/research/20261115_clean_chips/dispersed_low_gauge_20261113.csv",index=False)
