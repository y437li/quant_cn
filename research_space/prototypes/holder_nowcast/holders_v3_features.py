"""v3 features: path / time-series features per stock-quarter from wide daily matrices (PIT: only data <= quarter end)."""
import duckdb, pandas as pd, numpy as np
S="/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
L="/Volumes/Treasury/quant_cn_lake/curated"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
START="20191201"
def wide(sql, val):
    df=duckdb.sql(sql).df(); return df.pivot(index="trade_date",columns="ts_code",values=val).sort_index()
P=wide(f"select d.ts_code,d.trade_date,d.close*a.adj_factor v from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date>='{START}'","v")
dates=P.index; codes=P.columns
def W(sql,val): return wide(sql,val).reindex(index=dates,columns=codes)
TOV=W(f"select ts_code,trade_date,turnover_rate_f v from {s('daily_basic')} where trade_date>='{START}'","v")
CMV=W(f"select ts_code,trade_date,circ_mv v from {s('daily_basic')} where trade_date>='{START}'","v")
BIG=W(f"select ts_code,trade_date,(buy_lg_amount+buy_elg_amount-sell_lg_amount-sell_elg_amount) v from {s('moneyflow')} where trade_date>='{START}'","v")
RZ=W(f"select ts_code,trade_date,rzye v from {s('margin_detail')} where trade_date>='{START}'","v")
R=P.pct_change()
print("matrices", P.shape)
def max_run(mask):  # longest consecutive True run per column
    m=mask.values.astype(np.int8); best=np.zeros(m.shape[1]); cur=np.zeros(m.shape[1])
    for row in m: cur=(cur+1)*row; best=np.maximum(best,cur)
    return pd.Series(best,index=mask.columns)
def feats(a,b):
    """window (a,b]; a,b = quarter-end dates (YYYYMMDD) or b = today."""
    w=(dates>a)&(dates<=b); idx=np.where(w)[0]
    if len(idx)<15: return None
    e=idx[-1]; first=idx[:20]; last=idx[-20:]
    Pw=P.iloc[idx]; Rw=R.iloc[idx]; T=TOV.iloc[idx]; Bg=BIG.iloc[idx]; Z=RZ.iloc[idx]
    cmv=CMV.iloc[idx].mean()*1e4  # 万元 -> 元... moneyflow amounts are 万元; keep ratio in same units:
    cmv=CMV.iloc[idx].mean()       # circ_mv 万元; moneyflow 万元 -> ratio unitless
    hist=P.iloc[max(0,e-251):e+1]
    f=pd.DataFrame(index=codes)
    pb=P.iloc[e]
    f["ret_q"]=np.log(pb/P.iloc[idx[0]-1]) if idx[0]>0 else np.nan
    f["ret_6m"]=np.log(pb/P.iloc[max(0,e-125)]); f["ret_12m"]=np.log(pb/P.iloc[max(0,e-251)])
    f["dd_high252"]=pb/hist.max()-1; f["up_low252"]=pb/hist.min()-1; f["dd_qhigh"]=pb/Pw.max()-1
    f["ret_last20"]=np.log(pb/P.iloc[last[0]-1]) if last[0]>0 else np.nan
    f["n_bigup"]=(Rw>=0.05).sum(); f["n_bigdn"]=(Rw<=-0.05).sum(); f["limitups"]=(Rw>=0.095).sum()
    r5=np.log(Pw).diff(5); sig=np.sign(r5.where(r5.abs()>0.03)); f["reversals"]=(sig.ffill().diff().abs()>0).sum()
    f["vol_q"]=Rw.std(); f["vol_acc"]=R.iloc[last].std()/R.iloc[first].std()
    f["tov"]=T.mean(); f["tov_acc"]=np.log(TOV.iloc[last].mean()/TOV.iloc[first].mean())
    prevw=TOV.iloc[max(0,idx[0]-len(idx)):idx[0]]; f["dtov"]=np.log(T.mean()/prevw.mean())
    top=np.sort(T.fillna(0).values,axis=0)[-5:]; f["tov_top5"]=top.mean(0); f["tov_conc"]=top.sum(0)/T.sum().replace(0,np.nan)
    f["big_cum"]=Bg.sum()/cmv; f["big_last20"]=BIG.iloc[last].sum()/cmv; f["big_trend"]=(BIG.iloc[last].sum()-BIG.iloc[first].sum())/cmv
    f["out_frac"]=(Bg<0).sum()/Bg.notna().sum().replace(0,np.nan); f["out_maxrun"]=max_run(Bg<0)
    f["mchg"]=Z.ffill().iloc[-1]/Z.bfill().iloc[0]-1; f["m_last20"]=RZ.iloc[last].ffill().iloc[-1]/RZ.iloc[last].bfill().iloc[0]-1
    f["m_uprun"]=max_run(Z.diff()>0)
    f["lmv"]=np.log(cmv)
    return f.replace([np.inf,-np.inf],np.nan)
if __name__=="__main__":
    cal=pd.Series(dates)
    Q=[f"{y}{m}" for y in range(2020,2027) for m in ("0331","0630","0930","1231")]; Q=[q for q in Q if "20201231"<=q<="20260930"]
    out=[]
    for a,b in zip(Q[:-1],Q[1:]):
        f=feats(a,b); f["q"]=b; out.append(f); print(b, f.notna().sum().min())
    now=feats("20260930","20261112"); now["q"]="20261112"; out.append(now)
    F=pd.concat(out); F.index.name="ts_code"; F.reset_index().to_parquet(f"{S}/holders_v3_feats.parquet"); print("saved", F.shape)
