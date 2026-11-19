"""Walk-forward parameter search (what Bayesian optimisation would do, but exhaustive since the grid is small):
choose gauge cutoff, min band percentile, max overhead percentile on quarters before t, apply to quarter t.
Objective = mean per-quarter 60d excess of the selected group (min 30 names/quarter). Compares out-of-sample results
with the fixed simple rule gauge <= 0.3 and with in-sample best (to show the overfit gap).
Note: x60 spans 60 sessions (~1 quarter), so training uses only quarters whose 60d window ended before the test date (lag 1)."""
import itertools, pandas as pd, numpy as np
OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_watch_conditions_bt"
X=pd.read_parquet(f"{OUT}/band_controls_panel.parquet").dropna(subset=["gauge","band","trap","x60"])
X["bp"]=X.groupby("q").band.rank(pct=True); X["tp"]=X.groupby("q").trap.rank(pct=True)
Q=sorted(X.q.unique()); G=[0.2,0.3,0.4,0.5,0.6]; BP=[0,0.33,0.5,0.67]; TP=[1,0.67,0.5,0.33]
grid=list(itertools.product(G,BP,TP))
def sel(g,p): a,b,c=p; return g[(g.gauge<=a)&(g.bp>=b)&(g.tp<=c)]
M={}
for q,g in X.groupby("q"):
    base=g.x60.mean()
    for p in grid:
        s=sel(g,p); M[(q,p)]=s.x60.mean()-base if len(s)>=30 else np.nan
M=pd.Series({(q,str(p)):v for (q,p),v in M.items()}).unstack()   # rows q, cols params (relative to quarter universe mean of this panel)
ins=M.mean().sort_values(ascending=False)
print("in-sample best 5 (all 18 quarters, mean per-quarter excess vs panel mean %):"); print((ins.head(5)).round(2).to_string())
simple=str((0.3,0,1))
rows=[]
for i in range(8,len(Q)):
    train=M.loc[Q[:i-1]]      # lag one quarter: last train quarter's 60d window ends before Q[i]
    best=train.mean().idxmax(); rows.append((Q[i],best,M.loc[Q[i],best],M.loc[Q[i],simple]))
R=pd.DataFrame(rows,columns=["q","chosen","oos","simple"])
print(R.assign(oos=R.oos.round(2),simple=R.simple.round(2)).to_string(index=False))
d=R.oos-R.simple
tt=lambda x: x.mean()/x.std()*np.sqrt(len(x))
print("OOS optimised: mean %.2f t %.2f | simple gauge<=0.3: mean %.2f t %.2f | diff %.2f t %.2f (n=%d)"%(R.oos.mean(),tt(R.oos),R.simple.mean(),tt(R.simple),d.mean(),tt(d),len(R)))
print("in-sample best over same test quarters: %.2f"%M.loc[R.q,ins.index[0]].mean())
