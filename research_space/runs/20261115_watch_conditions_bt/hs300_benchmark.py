"""Re-express the watchlist / chip backtests against the CSI 300 (000300.SH price index, no dividends) instead of the
equal-weight cap >= 50亿 universe mean. Same signal dates and 60-session windows as watch_conditions_bt.py.
A per-quarter constant benchmark leaves group differences, ICs and FM slopes unchanged; only levels move."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_watch_conditions_bt"
X=pd.read_parquet(f"{OUT}/band_controls_panel.parquet")
ix=duckdb.sql(f"select trade_date,close from '{L}/reference/index_daily.parquet' where ts_code='000300.SH' and trade_date>='20210901' order by 1").df().set_index("trade_date").close
cal=duckdb.sql(f"select distinct trade_date from read_parquet('{L}/daily/**/*.parquet',hive_partitioning=true,union_by_name=true) where trade_date>='20210901' order by 1").df().trade_date.tolist()
B=[]
for q in sorted(X.q.unique()):
    d=max(t for t in cal if t<=q); i=cal.index(d)
    hs=ix[cal[i+60]]/ix[d]-1 if i+60<len(cal) else np.nan
    B.append((q,d,hs))
B=pd.DataFrame(B,columns=["q","d","hs60"]).set_index("q")
X["hs60"]=X.q.map(B.hs60)*100; X["ew60"]=X.r60*100-X.x60; X["y"]=X.r60*100-X.hs60
X=X[X.hs60.notna()]
print("per quarter: CSI300 60d vs equal-weight universe 60d (%)"); print(B.assign(ew60=X.groupby("q").ew60.first()).round(2).to_string())
print("mean CSI300 %.2f%%, mean equal-weight universe %.2f%%, quarters %d"%(X.groupby("q").hs60.first().mean(), X.groupby('q').ew60.first().mean(), X.q.nunique()))
def st(lab,m):
    z=X[m]; pq=z.groupby("q").y.mean(); hit=(z.y>0).mean()
    return dict(组=lab,样本=int(m.sum()),均值=round(z.y.mean(),2),中位=round(z.y.median(),2),跑赢沪深300比例=round(hit,2),
                季均=round(pq.mean(),2),t=round(pq.mean()/pq.std()*np.sqrt(len(pq)),2),跑赢季数=f"{(pq>0).sum()}/{len(pq)}")
X["Bt"]=X.groupby("q").band.transform(lambda s: pd.qcut(s.rank(method="first"),3,labels=["集中","中","分散"]))
X["Tt"]=X.groupby("q").trap.transform(lambda s: pd.qcut(s.rank(method="first"),3,labels=["套牢少","中","套牢多"]))
R=[st("全部（流通≥50亿）",X.y.notna()),st("温度计 ≤ 0.3",X.gauge<=0.3),st("温度计 0.3–0.9",(X.gauge>0.3)&(X.gauge<0.9)),st("温度计 ≥ 0.9",X.gauge>=0.9),
   st("温度计≤0.3 且 筹码分散",(X.gauge<=0.3)&(X.Bt=="分散")),st("温度计≤0.3 且 分散 且 套牢不多",(X.gauge<=0.3)&(X.Bt=="分散")&(X.Tt!="套牢多")),
   st("温度计≥0.9 且 筹码集中",(X.gauge>=0.9)&(X.Bt=="集中"))]
pd.set_option("display.width",250); print(pd.DataFrame(R).to_string(index=False))
d=X.groupby("q").apply(lambda g:g[g.gauge<=0.3].y.mean()-g[g.gauge>=0.9].y.mean())
print("gauge<=0.3 minus >=0.9: %.2f%%, t %.2f (unchanged by benchmark)"%(d.mean(),d.mean()/d.std()*np.sqrt(len(d))))
