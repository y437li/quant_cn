"""EMA weight grid on the every-3rd-day RetailGauge readings: alpha 0.1..1.0 (1.0 = raw). Tune on 2023-2024 quarters,
check on 2025-2026Q3. Scores (from trading day 15 on): holder-change IC (mean over quarter x day), 60-session excess of
the >= 0.9 group (float cap >= 50亿)."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"
D=pd.read_parquet("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261117_gauge_daily/gauge_daily.parquet").sort_values(["ts_code","q","off"]).reset_index(drop=True)
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
A=tuple(sorted(D["asof"].unique()))
cap=duckdb.sql(f"select ts_code,trade_date as ad,circ_mv/1e4 cmv from {s('daily_basic')} where trade_date in {A}").df().rename(columns={"ad":"asof"})
P=duckdb.sql(f"select d.ts_code,d.trade_date,d.close*a.adj_factor c from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date>='20230101'").df().pivot(index="trade_date",columns="ts_code",values="c").sort_index()
fw=(P.shift(-60)/P-1).stack().rename("r60").reset_index().rename(columns={"trade_date":"asof"})
D=D.merge(cap,on=["ts_code","asof"],how="left").merge(fw,on=["ts_code","asof"],how="left")
g=D.groupby(["ts_code","q"]).pct
M=(D.off>=15)&(D.cmv>=50)
def score(v,qs):
    X=D[M&D.q.isin(qs)].assign(sc=v[M&D.q.isin(qs)]); X["sc"]=X.groupby(["q","off"]).sc.rank(pct=True)
    X["x"]=(X.r60-X.groupby(["q","off"]).r60.transform("mean"))*100
    by=X.groupby(["q","off"])
    ic=by.apply(lambda z:z.sc.corr(z.y,method="spearman")).mean()
    hot=by.apply(lambda z:z[z.sc>=0.9].x.mean()-z[z.sc<0.9].x.mean()).groupby(level=0).mean().mean()
    return round(ic,4),round(hot,2)
Q=sorted(D.q.unique()); TR=[q for q in Q if q<="20241231"]; TE=[q for q in Q if q>"20241231"]
rows=[]
for a in (0.1,0.2,0.33,0.5,0.6,0.7,0.8,0.9,1.0):
    v=D.pct if a==1.0 else g.transform(lambda x,a=a:x.ewm(alpha=a).mean())
    i1,h1=score(v,TR); i2,h2=score(v,TE)
    rows.append({"α":a,"2023-24 IC":i1,"2023-24 热组超额%":h1,"2025-26 IC":i2,"2025-26 热组超额%":h2})
print(pd.DataFrame(rows).to_string(index=False))
