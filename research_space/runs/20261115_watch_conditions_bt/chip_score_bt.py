"""Backtest of the composite chip score (chip_top50.py) at quarter ends 2022Q1-2026Q3, float cap >= 50亿, point in time.
Components: last and previous announced holder change (ann_date <= signal), walk-forward RetailGauge, 70% cost band at the quarter end,
band change vs the previous quarter end, overhead cost95 / close - 1. Filters as live: gauge < 0.9, last announced change <= +10%.
Forward 20/60/120-session excess return vs the whole cap >= 50亿 universe mean (panel from watch_conditions_bt.py)."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; M="/Volumes/Treasury/quant_cn_lake/meta/runs"; OUT=f"{M}/research/20261115_watch_conditions_bt"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
E=pd.read_parquet(f"{OUT}/panel.parquet").reset_index().rename(columns={"index":"ts_code"})
if "ts_code" not in E: E=E.rename(columns={E.columns[0]:"ts_code"})
hn=duckdb.sql(f"select ts_code,end_date,min(ann_date) ann,arg_max(holder_num,ann_date) n from {s('events/stk_holdernumber')} where end_date>='20201231' and ann_date is not null group by 1,2").df().sort_values(["ts_code","end_date"])
hn["chg"]=hn.groupby("ts_code").n.pct_change()
cy=pd.read_parquet(f"{M}/holder_nowcast/cyq_qe.parquet"); cy["band"]=(cy.cost_85pct-cy.cost_15pct)/cy.cost_50pct
cds=sorted(cy.trade_date.unique())
px=duckdb.sql(f"select ts_code,trade_date,close from {s('daily')} where trade_date in {tuple(cds)}").df()
rows=[]
for q,g in E.groupby("q"):
    d=g.trade_date.iloc[0] if "trade_date" in g else None
    sd=max(c for c in cds if c<=q)
    h=hn[(hn.ann<=q)&hn.chg.notna()].groupby("ts_code").tail(2)
    last=h.groupby("ts_code").chg.last(); prev=h.groupby("ts_code").chg.apply(lambda x:x.iloc[0] if len(x)==2 else np.nan)
    c=cy[cy.trade_date==sd].set_index("ts_code"); i=cds.index(sd); c0=cy[cy.trade_date==cds[i-1]].set_index("ts_code") if i>0 else None
    p=px[px.trade_date==sd].set_index("ts_code").close
    g=g.set_index("ts_code").copy()
    g["h1"]=last; g["h2"]=prev; g["band"]=c.band; g["dband"]=c.band-(c0.band if c0 is not None else np.nan); g["trap"]=c.cost_95pct/p-1
    rows.append(g.reset_index())
X=pd.concat(rows)
X=X[X.h1.notna()&X.h2.notna()&X.band.notna()&X.dband.notna()&X.trap.notna()]
X["ok"]=(X.gauge<0.9)&(X.h1<=0.10)
def score(g):
    f=g[g.ok]; r=pd.DataFrame({k:f[k].rank(pct=True) for k in ["h1","h2","gauge","band","dband","trap"]}); return r.mean(axis=1)
X["score"]=np.nan
for q,g in X.groupby("q"): X.loc[g[g.ok].index,"score"]=score(g).values if False else None
# (index-safe assignment)
X=X.reset_index(drop=True); parts=[]
for q,g in X.groupby("q"):
    f=g[g.ok]; r=pd.DataFrame({k:f[k].rank(pct=True) for k in ["h1","h2","gauge","band","dband","trap"]}); parts.append(r.mean(axis=1))
X.loc[pd.concat(parts).index,"score"]=pd.concat(parts)
X["rk"]=X.groupby("q").score.rank(method="first")
X["top50"]=X.rk<=50
X["qnt"]=X.groupby("q").score.transform(lambda s: pd.qcut(s.rank(method="first"),5,labels=[1,2,3,4,5]) if s.notna().sum()>=50 else np.nan)
print("obs",len(X),"| passing filters",int(X.ok.sum()),"| quarters",X.q.nunique())
def st(name,m):
    o={"组":name,"样本":int(m.sum())}
    for h in (20,60,120):
        x=X.loc[m,f"x{h}"].dropna(); o[f"x{h}%"]=round(x.mean()*100,2)
        if h==60: o["中位%"]=round(x.median()*100,2); o["胜率"]=round((x>0).mean(),2)
    pq=X[m&X.x60.notna()].groupby("q").x60.mean().dropna(); o["季均%"]=round(pq.mean()*100,2); o["t"]=round(pq.mean()/pq.std()*np.sqrt(len(pq)),2); o["正季数"]=f"{(pq>0).sum()}/{len(pq)}"
    return o
res=[st("全部（流通≥50亿）",X.x60.notna()|X.x20.notna()),st("被剔除：温度计≥0.9 或 户数增>10%",~X.ok),st("通过过滤",X.ok),st("评分前50",X.top50)]
for k in [1,2,3,4,5]: res.append(st(f"过滤后五分组 Q{k}（1=最好）",X.qnt==k))
pd.set_option("display.width",300); print(pd.DataFrame(res).to_string(index=False))
# top-50 vs rest of passing names, per quarter
d=X[X.ok&X.x60.notna()].groupby("q").apply(lambda g:g[g.top50].x60.mean()-g[~g.top50].x60.mean()).dropna()
print("top50 minus rest of passing, 60d: mean %.2f%%, t %.2f, positive %d/%d"%(d.mean()*100,d.mean()/d.std()*np.sqrt(len(d)),(d>0).sum(),len(d)))
# component ICs (rank IC with x60 among passing names)
ic={k:X[X.ok&X.x60.notna()].groupby("q").apply(lambda g:g[k].rank().corr(g.x60.rank())).mean() for k in ["h1","h2","gauge","band","dband","trap","score"]}
print("mean rank IC vs 60d excess (negative = low value better):",{k:round(v,3) for k,v in ic.items()})
X.to_parquet(f"{OUT}/chip_score_panel.parquet")
