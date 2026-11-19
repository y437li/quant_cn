"""Current time-series momentum across liquid exchange ETFs (read-only on the lake).
Universe: ETFs with 20-day mean turnover >= 3亿. Per ETF: 1/3/6/12-1 month returns, the plan-24 blend
(share of 10/21/42/252-session windows up), 60-day vol, 12m return / vol (trend strength), 52-week high gap.
Category from fund_basic name keywords. Output tsmom_now.csv in meta/runs/research/20261118_tsmom_now/."""
import duckdb, pandas as pd, numpy as np, os
L="/Volumes/Treasury/quant_cn_lake/curated"
O="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261118_tsmom_now"; os.makedirs(O,exist_ok=True)
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
P=duckdb.sql(f"select ts_code,trade_date,close,amount from {s('fund_daily')} where trade_date>='20241001'").df()
nav=duckdb.sql(f"select ts_code, max(adj_nav/unit_nav) f from {s('fund_nav')} where nav_date>='20241001' group by 1").df() if False else None
last=P.trade_date.max(); days=sorted(P.trade_date.unique())[-20:]
liq=P[P.trade_date.isin(days)].groupby("ts_code").amount.mean()/1e5  # 亿
liq=liq[liq>=3]
names=duckdb.sql(f"select * from {s('reference')} limit 0").df() if False else None
fb=[p for p in os.listdir(f"{L}/reference")]
C=P[P.ts_code.isin(liq.index)].pivot(index="trade_date",columns="ts_code",values="close").sort_index()
# ETF splits: drop day returns beyond +-25% (unit splits), rebuild a clean index
r=C.pct_change(); r=r.where(r.abs()<0.25,0.0); I=(1+r.fillna(0)).cumprod()
def ret(n,skip=0): return I.iloc[-1-skip]/I.iloc[-1-skip-n]-1
D=pd.DataFrame({"amt_yi":liq,"r1m":ret(21),"r3m":ret(63),"r6m":ret(126),"r12_1":ret(231,21) if len(I)>253 else np.nan,
  "r12m":ret(252) if len(I)>253 else np.nan,"vol60":r.iloc[-60:].std()*np.sqrt(252)})
D["blend"]=sum((I.iloc[-1]>I.iloc[-1-n]).astype(float) for n in (10,21,42,252))/4
D["strength"]=D.r12m/D.vol60
D["off_high"]=I.iloc[-1]/I.iloc[-252:].max()-1
D.to_csv(f"{O}/tsmom_now.csv"); print(last, len(D), fb[:20])
fb=pd.read_parquet(f"{L}/reference/fund_basic.parquet")[["ts_code","name","benchmark"]].drop_duplicates("ts_code").set_index("ts_code")
D=D.join(fb)
# one ETF per benchmark: the most liquid
D=D.sort_values("amt_yi",ascending=False).drop_duplicates("benchmark")
D.to_csv(f"{O}/tsmom_now.csv")
pd.set_option("display.width",250); pd.set_option("display.max_rows",300)
show=D[["name","amt_yi","r1m","r3m","r6m","r12m","vol60","blend","strength","off_high"]].round(3)
print(len(D)); print(show.sort_values(["blend","strength"],ascending=False).to_string())
