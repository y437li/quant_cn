"""Does smoothing the mid-quarter RetailGauge reading help? Uses gauge_paths.parquet (20261115_gauge_intraquarter:
readings at trading day 15 / 30 / 45 and quarter end, 2022Q1..2026Q3, walk-forward). Filters at day 30 and day 45:
raw, mean of this quarter's readings so far, mean incl. last quarter's final reading, persistence (flag only when the
current AND previous reading are both on the same side). Scored on: holder-change IC, share of the <=0.3 group whose
holder count fell, how many <=0.3 flags survive to the quarter-end reading, 60-session excess return of the <=0.3 and
>=0.9 groups (float cap >= 50亿, minus the equal-weight universe mean)."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; IN="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_gauge_intraquarter"
OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261116_gauge_filter"; import os; os.makedirs(OUT,exist_ok=True)
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
G=pd.read_parquet(f"{IN}/gauge_paths.parquet").drop_duplicates(["ts_code","q","asof","off"])
G=G[G.off!=0]
W=G.pivot_table(index=["ts_code","q"],columns="off",values="pct")
A=G.pivot_table(index=["ts_code","q"],columns="off",values="asof",aggfunc="first")
Y=G.groupby(["ts_code","q"]).y.first()
QE=sorted(G.q.unique()); prevq={q:QE[i-1] for i,q in enumerate(QE) if i}
prev_end=W[999].reindex(pd.MultiIndex.from_arrays([W.index.get_level_values(0),W.index.get_level_values(1).map(prevq)])).values
W["prev"]=prev_end
cap=duckdb.sql(f"select ts_code,trade_date,circ_mv/1e4 cmv from {s('daily_basic')} where trade_date in {tuple(sorted(G['asof'].unique()))}").df()
cap=cap.set_index(["ts_code","trade_date"]).cmv
P=duckdb.sql(f"select d.ts_code,d.trade_date,d.close*a.adj_factor c from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date>='20220101'").df().pivot(index="trade_date",columns="ts_code",values="c").sort_index()
dl={d:i for i,d in enumerate(P.index)}
def r60(codes,asofs):
    out=np.full(len(codes),np.nan)
    for k,(c,a) in enumerate(zip(codes,asofs)):
        i=dl.get(a)
        if i is not None and i+60<len(P) and c in P.columns: out[k]=P.iat[i+60,P.columns.get_loc(c)]/P.iat[i,P.columns.get_loc(c)]-1
    return out
tt=lambda x: x.mean()/x.std()*np.sqrt(len(x))
rows=[]
for off,prior in ((30,[15]),(45,[15,30])):
    D=pd.DataFrame(index=W.index); D["asof"]=A[off]; D["y"]=Y; D["end"]=W[999]
    D["cmv"]=cap.reindex(pd.MultiIndex.from_arrays([D.index.get_level_values(0),D["asof"]])).values
    D["r60"]=r60(D.index.get_level_values(0),D["asof"])
    D=D[(D.cmv>=50)&W[off].notna()].copy(); Wd=W.loc[D.index]
    D["x60"]=(D.r60-D.groupby(level="q").r60.transform("mean"))*100
    filt={"原始读数":Wd[off],
          "本季均值":Wd[prior+[off]].mean(axis=1),
          "含上季末均值":pd.concat([Wd["prev"],Wd[prior+[off]]],axis=1).mean(axis=1),
          "0.7当前+0.3上一读数":0.7*Wd[off]+0.3*Wd[prior[-1]]}
    persist_lo=(Wd[off]<=0.3)&(Wd[prior[-1]]<=0.3); persist_hi=(Wd[off]>=0.9)&(Wd[prior[-1]]>=0.9)
    for name,v in list(filt.items())+[("连续两次同侧",None)]:
        if v is None: lo,hi,sc=persist_lo,persist_hi,Wd[off]
        else: sc=v.groupby(level="q").rank(pct=True); lo,hi=sc<=0.3,sc>=0.9
        D["lo"],D["hi"],D["sc"]=lo,hi,sc
        by=D.groupby(level="q")
        ic=by.apply(lambda z: z.sc.corr(z.y,method="spearman")).dropna()
        cold=by.apply(lambda z: z[z.lo].x60.mean()-z[~z.lo].x60.mean()).dropna()
        hot=by.apply(lambda z: z[z.hi].x60.mean()-z[~z.hi].x60.mean()).dropna()
        fell=(D[D.lo].y<0).mean(); base=(D.y<0).mean()
        keep=(D[D.lo].end<=0.3).mean(); keeph=(D[D.hi].end>=0.9).mean()
        rows.append({"第几天":off,"方法":name,"户数IC":round(ic.mean(),3),"低组户数下降比例":round(fell,2),"全体下降比例":round(base,2),
                     "低组到季末仍≤0.3":round(keep,2),"热组到季末仍≥0.9":round(keeph,2),"低组每季只数":int(D.lo.sum()/D.index.get_level_values(1).nunique()),
                     "低组60日超额%":round(cold.mean(),2),"t低":round(tt(cold),2),"热组60日超额%":round(hot.mean(),2),"t热":round(tt(hot),2),"季数":len(cold)})
T=pd.DataFrame(rows); pd.set_option("display.width",300); print(T.to_string(index=False)); T.to_csv(f"{OUT}/filter_summary.csv",index=False)
