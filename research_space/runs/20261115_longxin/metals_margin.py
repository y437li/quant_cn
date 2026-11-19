"""Are copper / aluminium prices squeezing motorcycle margins? Single-quarter gross margins of 隆鑫, 春风, 宗申, 钱江, 涛涛 vs quarterly average SHFE CU / AL, 2020-2026Q3, with a lagged pooled regression."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; T={"603766.SH":"隆鑫","603129.SH":"春风","001696.SZ":"宗申","000913.SZ":"钱江","301345.SZ":"涛涛"}
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
pd.set_option("display.width",250); pd.set_option("display.max_columns",30); pd.set_option("display.max_rows",60)
inc=q(f"select ts_code,end_date,arg_max(total_revenue,ann_date) rev,arg_max(oper_cost,ann_date) oc from {s('fundamentals/income')} where ts_code in {tuple(T)} and report_type='1' and end_date>='20191231' group by 1,2").sort_values(["ts_code","end_date"])
rows=[]
for c,g in inc.groupby("ts_code"):
    g=g.set_index("end_date")
    for e in g.index:
        if e[4:]=="0331": r,o=g.at[e,"rev"],g.at[e,"oc"]
        else:
            p=e[:4]+{"0630":"0331","0930":"0630","1231":"0930"}[e[4:]]
            if p not in g.index: continue
            r,o=g.at[e,"rev"]-g.at[p,"rev"],g.at[e,"oc"]-g.at[p,"oc"]
        rows.append((T[c],e,(1-o/r)*100))
gm=pd.DataFrame(rows,columns=["co","q","gm"]).pivot(index="q",columns="co",values="gm")
f=q(f"select ts_code,trade_date,close from {s('fut_daily')} where ts_code in ('CU.SHF','AL.SHF') and trade_date>='20190901'")
f["q"]=f.trade_date.str[:4]+f.trade_date.str[4:6].map(lambda m:{1:"0331",2:"0331",3:"0331",4:"0630",5:"0630",6:"0630",7:"0930",8:"0930",9:"0930"}.get(int(m),"1231"))
mq=f.groupby(["q","ts_code"]).close.mean().unstack().rename(columns={"CU.SHF":"铜","AL.SHF":"铝"})
D=gm.join(mq,how="left"); D=D[D.index>="20200331"]
print(D.round(1).to_string())
print("\nmetal y/y (quarter avg): 2026Q3 vs 2025Q3", (mq.loc["20260930"]/mq.loc["20250930"]-1).round(3).to_dict(), "| latest month",
      q(f"select ts_code, last(close order by trade_date) c from {s('fut_daily')} where ts_code in ('CU.SHF','AL.SHF') and trade_date>='20261101' group by 1").set_index("ts_code").c.to_dict())
# pooled regression: y/y change in GM (pp) on y/y log change of CU and AL, contemporaneous and 1q lag
P=[]
for co in gm.columns:
    x=D[[co,"铜","铝"]].dropna().copy(); x["dgm"]=x[co].diff(4)
    for m in ("铜","铝"): x["d"+m]=np.log(x[m]).diff(4); x["d"+m+"1"]=x["d"+m].shift(1)
    x["co"]=co; P.append(x.dropna())
P=pd.concat(P)
import numpy.linalg as la
for cols in (["d铜","d铝"],["d铜1","d铝1"]):
    X=np.column_stack([np.ones(len(P))]+[P[c] for c in cols]); b,res,_,_=la.lstsq(X,P.dgm,rcond=None)
    e=P.dgm-X@b; se=np.sqrt(np.diag(np.var(e,ddof=X.shape[1])*la.inv(X.T@X)))
    print("pooled y/y ΔGM(pp) ~",cols,"coef",b[1:].round(2),"t",(b[1:]/se[1:]).round(2),"n",len(P),"R2",round(1-e.var()/P.dgm.var(),3))
for co in gm.columns:
    x=P[P.co==co]; print(co,"corr(ΔGM, dCU)=%.2f dAL=%.2f lag1 dCU=%.2f dAL=%.2f"%(x.dgm.corr(x["d铜"]),x.dgm.corr(x["d铝"]),x.dgm.corr(x["d铜1"]),x.dgm.corr(x["d铝1"])))
