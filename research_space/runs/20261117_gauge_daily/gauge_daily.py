"""RetailGauge v5 read every 3rd trading day inside each quarter (2023Q1..2026Q3), to test short smoothing filters.
Reuses the feature, chip, label and fit code of research_space/runs/20261115_gauge_intraquarter/gauge_intraquarter.py
(executed in slices: header + matrices + feature functions, then chip/label/lag block, then fit_predict). Quarter-end
training rows come from that run's raw_rows.parquet; this run adds rows at day 3, 6, 9, ... and fits walk-forward per
as-of date (train quarters < target, labels announced by the as-of date). Output: meta/runs/research/20261117_gauge_daily/
gauge_daily.parquet (ts_code, q, asof, off = trading day in quarter, y, pct)."""
import os, time, pandas as pd, numpy as np
SRC="research_space/runs/20261115_gauge_intraquarter/gauge_intraquarter.py"
src=open(SRC).read().split("\n")
mark=lambda m: next(i for i,l in enumerate(src) if l.startswith(m))
g={}
exec("\n".join(src[:mark("OFF=(15,30,45)")]), g)                     # imports, matrices, feats(), QE, last
OUT2="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261117_gauge_daily"; os.makedirs(OUT2,exist_ok=True)
RAW2=f"{OUT2}/raw_daily.parquet"
dates=g["dates"]; feats=g["feats"]; QE=g["QE"]
base=pd.read_parquet(f"{g['OUT']}/raw_rows.parquet").drop_duplicates(["ts_code","q","asof","off"])
base=base[base.off==999]
done=pd.read_parquet(RAW2) if os.path.exists(RAW2) else None
have=set(zip(done.q,done["asof"])) if done is not None else set()
rows=[]; t0=time.time()
for a,q in zip(QE[:-1],QE[1:]):
    if not ("20230331"<=q<="20260930"): continue
    qi=np.where((dates>a)&(dates<=q))[0]
    for k in range(3,len(qi)+1,3):
        d=dates[qi[k-1]]
        if (q,d) in have: continue
        f=feats(a,d); f["q"]=q; f["asof"]=d; f["off"]=k; f.index.name="ts_code"; rows.append(f.reset_index())
    if rows:
        done=pd.concat(([done] if done is not None else [])+rows,ignore_index=True); done.to_parquet(RAW2); rows=[]
    print(q,"rows",0 if done is None else len(done),f"{time.time()-t0:.0f}s",flush=True)
g["F"]=pd.concat([base,done],ignore_index=True)
# chip, labels, PIT lags (intra rows: previous quarter-end chip state), then FEATS / fit_predict / TR
i0=mark("# chip:"); i1=mark("TR=F[")
g["F"].loc[g["F"].off!=999,"off"]=g["F"].loc[g["F"].off!=999,"off"]   # off kept as trading-day index
exec("\n".join(l for l in src[i0:i1+1] if not l.startswith("F.to_parquet")), g)
F,TR,fit_predict,FEATS=g["F"],g["TR"],g["fit_predict"],g["FEATS"]
out=[]; t0=time.time()
for (q,off,asof),te in F[F.off!=999].groupby(["q","off","asof"]):
    tr=TR[(TR.q<q)&(TR.ann_y<=asof)]
    if tr.q.nunique()<4: continue
    p=fit_predict(tr,te,FEATS); d=te[["ts_code","q","asof","off","y"]].copy(); d["pct"]=pd.Series(p,index=te.index).rank(pct=True).values
    out.append(d)
    if len(out)%20==0: print("fits",len(out),f"{time.time()-t0:.0f}s",flush=True)
G=pd.concat(out); G.to_parquet(f"{OUT2}/gauge_daily.parquet"); print("saved",G.shape,flush=True)
