"""v5 multi-scale / EWMA / slope features at each as-of date (quarter ends + today), PIT."""
import duckdb, pandas as pd, numpy as np
S="/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
L="/Volumes/Treasury/quant_cn_lake/curated"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
def W(sql): d=duckdb.sql(sql).df(); return d.pivot(index="trade_date",columns="ts_code",values="v").sort_index()
P=W(f"select d.ts_code,d.trade_date,d.close*a.adj_factor v from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date>='20191001'")
idx,cols=P.index,P.columns; Rx=lambda df: df.reindex(index=idx,columns=cols)
TOV=Rx(W(f"select ts_code,trade_date,turnover_rate_f v from {s('daily_basic')} where trade_date>='20191001'"))
CMV=Rx(W(f"select ts_code,trade_date,circ_mv v from {s('daily_basic')} where trade_date>='20191001'"))
LG=Rx(W(f"select ts_code,trade_date,buy_lg_amount-sell_lg_amount v from {s('moneyflow')} where trade_date>='20191001'"))
RZ=Rx(W(f"select ts_code,trade_date,rzye v from {s('margin_detail')} where trade_date>='20191001'")).ffill(limit=5)
R=np.log(P).diff()
TREL=np.log(TOV/TOV.rolling(250,min_periods=120).mean())       # turnover relative to own 1y mean
LGN=LG/CMV                                                      # daily big-order flow per float cap
def slope(M,n,e):
    Y=M.iloc[e-n+1:e+1]; x=np.arange(n)-(n-1)/2; return (Y.mul(x,axis=0)).sum()/ (x**2).sum()
def feats(asof):
    e=int(np.where(idx<=asof)[0][-1]); f=pd.DataFrame(index=cols)
    for n in (5,20,60,120):
        f[f"tov_rel_{n}"]=TREL.iloc[e-n+1:e+1].mean(); f[f"ret_{n}"]=R.iloc[e-n+1:e+1].sum()
        f[f"lg_{n}"]=LGN.iloc[e-n+1:e+1].sum(); f[f"vol_{n}"]=R.iloc[e-n+1:e+1].std()
        f[f"rz_{n}"]=np.log(RZ.iloc[e]/RZ.iloc[e-n])
    for h in (5,20,60):
        f[f"tov_ewm_{h}"]=TREL.iloc[:e+1].ewm(halflife=h,min_periods=h).mean().iloc[-1]
        f[f"lg_ewm_{h}"]=LGN.iloc[:e+1].ewm(halflife=h,min_periods=h).mean().iloc[-1]
    f["tov_slope60"]=slope(TREL,60,e); f["rz_slope60"]=slope(np.log(RZ),60,e)
    return f.replace([np.inf,-np.inf],np.nan)
Q=[f"{y}{m}" for y in range(2020,2027) for m in ("0331","0630","0930","1231")]; Q=[q for q in Q if "20210331"<=q<="20260930"]
out=[]
for q in Q+["20261112"]:
    f=feats(q); f["q"]=q; out.append(f); print(q, end=" ", flush=True)
X=pd.concat(out); X.index.name="ts_code"; X.reset_index().to_parquet(f"{S}/holders_v5_feats.parquet"); print("\nsaved",X.shape)
