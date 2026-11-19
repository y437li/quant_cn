"""Score gauge_paths.parquet: stability vs the quarter-end reading, holder-change IC, threshold flips, and 60-session
forward excess return from each as-of date (float cap >= 50亿, equal-weight universe mean). Also example paths."""
import duckdb, pandas as pd, numpy as np, json
L="/Volumes/Treasury/quant_cn_lake/curated"; OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_gauge_intraquarter"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
G=pd.read_parquet(f"{OUT}/gauge_paths.parquet")
asofs=tuple(sorted(G["asof"].unique()))
cap=duckdb.sql(f"select ts_code,trade_date as ad,circ_mv/1e4 cmv from {s('daily_basic')} where trade_date in {asofs}").df().rename(columns={"ad":"asof"})
G=G.merge(cap,on=["ts_code","asof"],how="left"); U=G[G.cmv>=50].copy()
P=duckdb.sql(f"select d.ts_code,d.trade_date,d.close*a.adj_factor c from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date>='20220101'").df().pivot(index="trade_date",columns="ts_code",values="c").sort_index()
dl=list(P.index)
def fwd(asof,h=60):
    i=dl.index(asof)
    return (P.iloc[i+h]/P.iloc[i]-1) if i+h<len(dl) else None
r={}
for a in asofs:
    f=fwd(a); 
    if f is not None: r[a]=f
U["r60"]=[r[a].get(c,np.nan) if a in r else np.nan for c,a in zip(U.ts_code,U["asof"])]
U["x60"]=(U.r60-U.groupby(["q","off"]).r60.transform("mean"))*100
tt=lambda x: x.mean()/x.std()*np.sqrt(len(x))
end=U[U.off==999].set_index(["ts_code","q"]).pct
U["pct_end"]=end.reindex(pd.MultiIndex.from_arrays([U.ts_code,U.q])).values
rows=[]
for off,g in U[U.off!=0].groupby("off"):
    by=g.groupby("q")
    st=by.apply(lambda z: z.pct.corr(z.pct_end,method="spearman")) if off!=999 else None
    ic=by.apply(lambda z: z.pct.corr(z.y,method="spearman")).dropna()
    hot=by.apply(lambda z: z[z.pct>=0.9].x60.mean()-z[z.pct<0.9].x60.mean()).dropna()
    cold=by.apply(lambda z: z[z.pct<=0.3].x60.mean()-z[z.pct>0.3].x60.mean()).dropna()
    hit=by.apply(lambda z: (z[z.pct>=0.9].y.rank(pct=True) if False else (z.y.rank(pct=True)[z.pct>=0.9]>=0.8).mean())).dropna()
    flip3=(((g.pct<=0.3)!=(g.pct_end<=0.3))).mean() if off!=999 else 0
    in3_out=((g.pct<=0.3)&(g.pct_end>0.3)).sum()/max(1,(g.pct<=0.3).sum()) if off!=999 else 0
    in9_out=((g.pct>=0.9)&(g.pct_end<0.9)).sum()/max(1,(g.pct>=0.9).sum()) if off!=999 else 0
    mad=(g.pct-g.pct_end).abs().mean() if off!=999 else 0
    rows.append(dict(off=off,quarters=g.q.nunique(),与季末相关=round(st.mean(),2) if st is not None else 1.0,平均偏离=round(mad,3),
        低组季末流失=round(in3_out,2),热组季末流失=round(in9_out,2),户数IC=round(ic.mean(),3),最热组命中=round(hit.mean(),2),
        最热组60日超额=round(hot.mean(),2),t热=round(tt(hot),2),低组60日超额=round(cold.mean(),2),t低=round(tt(cold),2),回报季数=len(hot)))
T=pd.DataFrame(rows); pd.set_option("display.width",300); print(T.to_string(index=False)); T.to_csv(f"{OUT}/intraquarter_summary.csv",index=False)
# consecutive change
W=U[U.off.isin([15,30,45,999])].pivot_table(index=["ts_code","q"],columns="off",values="pct")
for a,b in [(15,30),(30,45),(45,999)]:
    d=(W[b]-W[a]).abs(); print(f"step {a}->{b}: mean |Δ| {d.mean():.3f}, share |Δ|>0.2 {(d>0.2).mean():.2f}")
# examples
EX={"601888.SH":"中国中免","600176.SH":"中国巨石","603766.SH":"隆鑫通用","600111.SH":"北方稀土","000657.SZ":"中钨高新"}
E=G[G.ts_code.isin(EX)&G.q.isin(["20260630","20260930","20261231"])].copy(); E["name"]=E.ts_code.map(EX)
E=E.sort_values(["name","q","asof"])[["name","q","off","asof","pct"]]; E["pct"]=E.pct.round(2); print(E.to_string(index=False))
E.to_csv(f"{OUT}/example_paths.csv",index=False)
