"""Score short smoothing filters on the every-3rd-day RetailGauge readings (gauge_daily.parquet).
Filters on each stock's within-quarter reading sequence (readings 3 trading days apart): raw, mean of last 2 / 3,
EMA (alpha 0.5 / 0.33), median of last 3, persistence (last 2 / 3 / 5 readings all <= 0.3 or all >= 0.9).
Scored at trading day 30 and 45 (and pooled over all days >= 15): holder-change IC, share of the <= 0.3 group whose
holder count fell, agreement with the quarter-end reading (20261115 run, off 999) on the <= 0.3 / >= 0.9 flags, 60-session
excess return of both groups (float cap >= 50亿), and flag count."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"
D=pd.read_parquet("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261117_gauge_daily/gauge_daily.parquet")
E=pd.read_parquet("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_gauge_intraquarter/gauge_paths.parquet")
E=E[E.off==999].drop_duplicates(["ts_code","q"]).set_index(["ts_code","q"]).pct
D=D.sort_values(["ts_code","q","off"]).reset_index(drop=True)
g=D.groupby(["ts_code","q"]).pct
F={"原始":D.pct,
   "近2次均值":g.transform(lambda x:x.rolling(2,min_periods=1).mean()),
   "近3次均值":g.transform(lambda x:x.rolling(3,min_periods=1).mean()),
   "EMA α=0.5":g.transform(lambda x:x.ewm(alpha=0.5).mean()),
   "EMA α=0.33":g.transform(lambda x:x.ewm(alpha=1/3).mean()),
   "近3次中位数":g.transform(lambda x:x.rolling(3,min_periods=1).median())}
PER={n:(g.transform(lambda x,n=n:x.rolling(n,min_periods=n).max()<=0.3),g.transform(lambda x,n=n:x.rolling(n,min_periods=n).min()>=0.9)) for n in (2,3,5)}
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
A=tuple(sorted(D["asof"].unique()))
cap=duckdb.sql(f"select ts_code,trade_date as ad,circ_mv/1e4 cmv from {s('daily_basic')} where trade_date in {A}").df().rename(columns={"ad":"asof"})
D=D.merge(cap,on=["ts_code","asof"],how="left")
P=duckdb.sql(f"select d.ts_code,d.trade_date,d.close*a.adj_factor c from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date>='20230101'").df().pivot(index="trade_date",columns="ts_code",values="c").sort_index()
fw=(P.shift(-60)/P-1); fw=fw.stack().rename("r60").reset_index().rename(columns={"trade_date":"asof"})
D=D.merge(fw,on=["ts_code","asof"],how="left")
D["end"]=E.reindex(pd.MultiIndex.from_arrays([D.ts_code,D.q])).values
U=(D.cmv>=50)
tt=lambda x: x.mean()/x.std()*np.sqrt(len(x)) if len(x)>2 else np.nan
def score(sc,lo,hi,mask):
    X=D[mask&U].assign(sc=sc[mask&U],lo=lo[mask&U],hi=hi[mask&U])
    X["x"]=(X.r60-X.groupby(["q","off"]).r60.transform("mean"))*100
    by=X.groupby(["q","off"])
    ic=by.apply(lambda z:z.sc.corr(z.y,method="spearman")).groupby(level=0).mean().dropna()
    cold=by.apply(lambda z:z[z.lo].x.mean()-z[~z.lo].x.mean()).groupby(level=0).mean().dropna()
    hot=by.apply(lambda z:z[z.hi].x.mean()-z[~z.hi].x.mean()).groupby(level=0).mean().dropna()
    return {"户数IC":round(ic.mean(),3),"低组户数降%":round((X[X.lo].y<0).mean()*100),"低组季末仍≤0.3%":round((X[X.lo].end<=0.3).mean()*100),
            "热组季末仍≥0.9%":round((X[X.hi].end>=0.9).mean()*100),"低组/季/日":int(X.lo.sum()/X.groupby(["q","off"]).ngroups),
            "低组60日超额%":round(cold.mean(),2),"t低":round(tt(cold),1),"热组60日超额%":round(hot.mean(),2),"t热":round(tt(hot),1)}
rows=[]
for lab,mask in (("第30天",D.off==30),("第45天",D.off==45),("第15天起全部",D.off>=15)):
    for n,v in F.items():
        sc=v.groupby([D.q,D.off]).rank(pct=True) if n!="原始" else v
        rows.append({"时点":lab,"方法":n,**score(sc,sc<=0.3,sc>=0.9,mask)})
    for n,(lo,hi) in PER.items():
        rows.append({"时点":lab,"方法":f"连续{n}次同侧",**score(D.pct,lo.fillna(False).astype(bool),hi.fillna(False).astype(bool),mask)})
T=pd.DataFrame(rows); pd.set_option("display.width",300); print(T.to_string(index=False))
T.to_csv("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261117_gauge_daily/filter_summary.csv",index=False)
# day-to-day jitter
j=g.diff().abs(); print("\n相邻两次（3 天）读数平均变化", round(j.mean(),3), " 变化>0.2 的比例", round((j>0.2).mean(),3))
