"""Does the 'dispersed chips' (wide 70% cost band) edge survive controls for prior 60-session return (reversal),
prior 60-session volatility and turnover, and size? Quarter-end panel from chip_score_bt.py (x60 = forward 60d excess).
Controls are computed only from data up to the signal date. Outputs: double sorts and Fama-MacBeth rank regressions."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_watch_conditions_bt"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
P=pd.read_parquet(f"{OUT}/chip_score_panel.parquet").dropna(subset=["gauge","band","x60"]).reset_index(drop=True)
cy=pd.read_parquet("/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast/cyq_qe.parquet"); cds=sorted(cy.trade_date.unique())
P["sd"]=P.q.map(lambda q: max(c for c in cds if c<=q))
d=duckdb.sql(f"""select d.ts_code,d.trade_date,d.pct_chg,b.turnover_rate_f tr from {s('daily')} d
 left join {s('daily_basic')} b using(ts_code,trade_date) where d.trade_date>='20210901' and d.trade_date<='20260930'""").df()
d=d.sort_values(["ts_code","trade_date"]); g=d.groupby("ts_code")
d["lr"]=np.log1p(d.pct_chg/100)
d["pr60"]=g.lr.transform(lambda x:x.rolling(60,min_periods=50).sum())
d["pr20"]=g.lr.transform(lambda x:x.rolling(20,min_periods=15).sum())
d["vol60"]=g.lr.transform(lambda x:x.rolling(60,min_periods=50).std())
d["to60"]=g.tr.transform(lambda x:x.rolling(60,min_periods=40).mean())
C=d[d.trade_date.isin(set(P.sd))][["ts_code","trade_date","pr60","pr20","vol60","to60"]].rename(columns={"trade_date":"sd"})
X=P.merge(C,on=["ts_code","sd"],how="left").dropna(subset=["pr60","vol60","to60"])
X["x60"]*=100; X["lcap"]=np.log(X.cmv)
print("obs",len(X),"quarters",X.q.nunique())
print("rank corr band vs controls (mean by q):",{k:round(X.groupby("q").apply(lambda g:g.band.corr(g[k],method="spearman")).mean(),2) for k in ["pr60","pr20","vol60","to60","lcap","trap","gauge"]})
def ter(col,lab): return X.groupby("q")[col].transform(lambda s: pd.qcut(s.rank(method="first"),3,labels=lab))
X["B"]=ter("band",["集中","中","分散"]); X["R"]=ter("pr60",["前60天跌","中","前60天涨"]); X["V"]=ter("vol60",["低波","中","高波"])
def dsort(row):
    m=X.groupby(["q",row,"B"],observed=True).x60.mean().reset_index()
    t=m.pivot_table(index=["q",row],columns="B",values="x60",observed=True); t["分散-集中"]=t["分散"]-t["集中"]
    o=t.groupby(row,observed=True).mean().round(2)
    o["t(分散-集中)"]=t.groupby(row,observed=True)["分散-集中"].apply(lambda x:x.mean()/x.std()*np.sqrt(len(x))).round(2)
    print(o.to_string()); print()
dsort("R"); dsort("V")
# Fama-MacBeth on cross-sectional percentile ranks
def fm(cols, sub=None):
    Z=X if sub is None else X[sub]; B=[]
    for q,g in Z.groupby("q"):
        A=np.column_stack([np.ones(len(g))]+[g[c].rank(pct=True)-0.5 for c in cols]); y=g.x60.values
        B.append(np.linalg.lstsq(A,y,rcond=None)[0][1:])
    B=pd.DataFrame(B,columns=cols); r=pd.DataFrame({"coef(底→顶 pct)":B.mean(),"t":B.mean()/B.std()*np.sqrt(len(B))}).round(2)
    print(r.T.to_string()); print()
print("FM: band only"); fm(["band"])
print("FM: band + gauge"); fm(["band","gauge"])
print("FM: band + gauge + pr60 + pr20 + vol60 + to60 + lcap"); fm(["band","gauge","pr60","pr20","vol60","to60","lcap"])
print("FM full, plus overhead"); fm(["band","trap","gauge","pr60","pr20","vol60","to60","lcap"])
print("FM full within gauge<=0.3"); fm(["band","pr60","pr20","vol60","to60","lcap"],X.gauge<=0.3)
X.to_parquet(f"{OUT}/band_controls_panel.parquet")
