"""Extra order-size flow features per stock-quarter (PIT), merged into the v3 panel."""
import duckdb, pandas as pd, numpy as np
S="/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
L="/Volumes/Treasury/quant_cn_lake/curated"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
def W(sql): d=duckdb.sql(sql).df(); return d.pivot(index="trade_date",columns="ts_code",values="v").sort_index()
CMV=W(f"select ts_code,trade_date,circ_mv v from {s('daily_basic')} where trade_date>='20191201'"); idx,cols=CMV.index,CMV.columns
R=lambda df: df.reindex(index=idx,columns=cols)
LG=R(W(f"select ts_code,trade_date,buy_lg_amount-sell_lg_amount v from {s('moneyflow')} where trade_date>='20191201'"))
EL=R(W(f"select ts_code,trade_date,buy_elg_amount-sell_elg_amount v from {s('moneyflow')} where trade_date>='20191201'"))
SM=R(W(f"select ts_code,trade_date,buy_sm_amount-sell_sm_amount v from {s('moneyflow')} where trade_date>='20191201'"))
def max_run(mask):
    m=mask.values.astype(np.int8); best=np.zeros(m.shape[1]); cur=np.zeros(m.shape[1])
    for row in m: cur=(cur+1)*row; best=np.maximum(best,cur)
    return pd.Series(best,index=mask.columns)
def feats(a,b):
    w=np.where((idx>a)&(idx<=b))[0]; first=w[:20]; last=w[-20:]; cmv=CMV.iloc[w].mean()
    f=pd.DataFrame(index=cols)
    f["lg_cum"]=LG.iloc[w].sum()/cmv; f["lg_last20"]=LG.iloc[last].sum()/cmv; f["lg_trend"]=(LG.iloc[last].sum()-LG.iloc[first].sum())/cmv
    f["lg_inrun"]=max_run(LG.iloc[w]>0); f["lg_outrun"]=max_run(LG.iloc[w]<0)
    f["elg_cum"]=EL.iloc[w].sum()/cmv; f["sm_cum"]=SM.iloc[w].sum()/cmv; f["sm_last20"]=SM.iloc[last].sum()/cmv
    return f.replace([np.inf,-np.inf],np.nan)
Q=[f"{y}{m}" for y in range(2020,2027) for m in ("0331","0630","0930","1231")]; Q=[q for q in Q if "20201231"<=q<="20260930"]
out=[]
for a,b in zip(Q[:-1],Q[1:]):
    f=feats(a,b); f["q"]=b; out.append(f)
f=feats("20260930","20261112"); f["q"]="20261112"; out.append(f)
X=pd.concat(out); X.index.name="ts_code"; X.reset_index().to_parquet(f"{S}/holders_v4_flow.parquet"); print("saved",X.shape)
