"""Realized vol (10/20/60-day, annualised, close-to-close) of the option-underlying ETFs and US SPY proxy,
now vs 5 and 20 sessions ago, and against the option-implied VIX from volatility_monitor.json."""
import duckdb, pandas as pd, numpy as np, json
L="/Volumes/Treasury/quant_cn_lake/curated"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
E={"510050.SH":"50ETF","510300.SH":"300ETF","510500.SH":"500ETF","512100.SH":"中证1000","588000.SH":"科创50"}
P=duckdb.sql(f"select ts_code,trade_date,close from {s('fund_daily')} where trade_date>='20250601' and ts_code in {tuple(E)}").df()
C=P.pivot(index="trade_date",columns="ts_code",values="close").sort_index(); r=np.log(C).diff()
rv=lambda n,lag=0: r.iloc[:len(r)-lag].iloc[-n:].std()*np.sqrt(252)*100
V=json.load(open("research_space/prototypes/chain_view/volatility_monitor.json"))
iv={l["name"].replace(" VIX",""):l["value"] for l in V["lines"]}
T=pd.DataFrame({"RV10":rv(10),"RV20":rv(20),"RV20_5d前":rv(20,5),"RV20_20d前":rv(20,20),"RV60":rv(60),"RV250":rv(250)}).rename(index=E)
T["IV"]=[iv.get(k) for k in T.index]; T["IV-RV20"]=T.IV-T.RV20
print("last",C.index[-1]); print(T.round(1).to_string())
print((r.iloc[-10:]*100).round(2).rename(columns=E).to_string())
