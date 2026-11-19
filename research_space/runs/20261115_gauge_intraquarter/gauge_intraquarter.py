"""How stable is the RetailGauge (v5) inside a quarter, and how much does a mid-quarter reading lose?
For each target quarter 2022Q1-2026Q3 and the live 2026Q4, rebuild the v5 feature row at trading-day offsets 15/30/45 into the
quarter and at the quarter end, fit the v5 LightGBM walk-forward (train quarters < target, labels announced by the as-of date),
and score: rank corr with the quarter-end reading, rank IC vs the realised holder change, threshold flips (0.3 / 0.9), and
60-session forward excess return from the as-of date (float cap >= 50亿, equal-weight universe mean).
Feature code is copied from research_space/prototypes/holder_nowcast (v3 / v4 flow / v5 / chip / PIT lags).
Limitation: cost-distribution (cyq_perf) snapshots exist only at quarter ends, so mid-quarter rows use the previous
quarter-end chip state with zero chip deltas (the live 11-12 run had a fresh snapshot)."""
import duckdb, pandas as pd, numpy as np, json, lightgbm as lgb, sys
S="/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"; L="/Volumes/Treasury/quant_cn_lake/curated"
OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_gauge_intraquarter"
import os; os.makedirs(OUT,exist_ok=True)
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
def Wd(sql): d=duckdb.sql(sql).df(); return d.pivot(index="trade_date",columns="ts_code",values="v").sort_index()
P=Wd(f"select d.ts_code,d.trade_date,d.close*a.adj_factor v from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date>='20191001'")
dates,codes=P.index,P.columns; Rx=lambda df: df.reindex(index=dates,columns=codes)
TOV=Rx(Wd(f"select ts_code,trade_date,turnover_rate_f v from {s('daily_basic')} where trade_date>='20191001'"))
CMV=Rx(Wd(f"select ts_code,trade_date,circ_mv v from {s('daily_basic')} where trade_date>='20191001'"))
BIG=Rx(Wd(f"select ts_code,trade_date,(buy_lg_amount+buy_elg_amount-sell_lg_amount-sell_elg_amount) v from {s('moneyflow')} where trade_date>='20191001'"))
LG=Rx(Wd(f"select ts_code,trade_date,buy_lg_amount-sell_lg_amount v from {s('moneyflow')} where trade_date>='20191001'"))
EL=Rx(Wd(f"select ts_code,trade_date,buy_elg_amount-sell_elg_amount v from {s('moneyflow')} where trade_date>='20191001'"))
SM=Rx(Wd(f"select ts_code,trade_date,buy_sm_amount-sell_sm_amount v from {s('moneyflow')} where trade_date>='20191001'"))
RZraw=Rx(Wd(f"select ts_code,trade_date,rzye v from {s('margin_detail')} where trade_date>='20191001'"))
RZ5=RZraw.ffill(limit=5)
R=P.pct_change(); LR=np.log(P).diff()
TREL=np.log(TOV/TOV.rolling(250,min_periods=120).mean()); LGN=LG/CMV
print("matrices",P.shape,flush=True)
def max_run(mask):
    m=mask.values.astype(np.int8); best=np.zeros(m.shape[1]); cur=np.zeros(m.shape[1])
    for row in m: cur=(cur+1)*row; best=np.maximum(best,cur)
    return pd.Series(best,index=mask.columns)
def f_v3(a,b):
    idx=np.where((dates>a)&(dates<=b))[0]; e=idx[-1]; first=idx[:20]; last=idx[-20:]
    Pw=P.iloc[idx]; Rw=R.iloc[idx]; T=TOV.iloc[idx]; Bg=BIG.iloc[idx]; Z=RZraw.iloc[idx]; cmv=CMV.iloc[idx].mean()
    hist=P.iloc[max(0,e-251):e+1]; f=pd.DataFrame(index=codes); pb=P.iloc[e]
    f["ret_q"]=np.log(pb/P.iloc[idx[0]-1]); f["ret_6m"]=np.log(pb/P.iloc[max(0,e-125)]); f["ret_12m"]=np.log(pb/P.iloc[max(0,e-251)])
    f["dd_high252"]=pb/hist.max()-1; f["up_low252"]=pb/hist.min()-1; f["dd_qhigh"]=pb/Pw.max()-1
    f["ret_last20"]=np.log(pb/P.iloc[last[0]-1])
    f["n_bigup"]=(Rw>=0.05).sum(); f["n_bigdn"]=(Rw<=-0.05).sum(); f["limitups"]=(Rw>=0.095).sum()
    r5=np.log(Pw).diff(5); sig=np.sign(r5.where(r5.abs()>0.03)); f["reversals"]=(sig.ffill().diff().abs()>0).sum()
    f["vol_q"]=Rw.std(); f["vol_acc"]=R.iloc[last].std()/R.iloc[first].std()
    f["tov"]=T.mean(); f["tov_acc"]=np.log(TOV.iloc[last].mean()/TOV.iloc[first].mean())
    prevw=TOV.iloc[max(0,idx[0]-len(idx)):idx[0]]; f["dtov"]=np.log(T.mean()/prevw.mean())
    top=np.sort(T.fillna(0).values,axis=0)[-5:]; f["tov_top5"]=top.mean(0); f["tov_conc"]=top.sum(0)/T.sum().replace(0,np.nan)
    f["big_cum"]=Bg.sum()/cmv; f["big_last20"]=BIG.iloc[last].sum()/cmv; f["big_trend"]=(BIG.iloc[last].sum()-BIG.iloc[first].sum())/cmv
    f["out_frac"]=(Bg<0).sum()/Bg.notna().sum().replace(0,np.nan); f["out_maxrun"]=max_run(Bg<0)
    f["mchg"]=Z.ffill().iloc[-1]/Z.bfill().iloc[0]-1; f["m_last20"]=RZraw.iloc[last].ffill().iloc[-1]/RZraw.iloc[last].bfill().iloc[0]-1
    f["m_uprun"]=max_run(Z.diff()>0); f["lmv"]=np.log(cmv)
    # v4 flow
    f["lg_cum"]=LG.iloc[idx].sum()/cmv; f["lg_last20"]=LG.iloc[last].sum()/cmv; f["lg_trend"]=(LG.iloc[last].sum()-LG.iloc[first].sum())/cmv
    f["lg_inrun"]=max_run(LG.iloc[idx]>0); f["lg_outrun"]=max_run(LG.iloc[idx]<0)
    f["elg_cum"]=EL.iloc[idx].sum()/cmv; f["sm_cum"]=SM.iloc[idx].sum()/cmv; f["sm_last20"]=SM.iloc[last].sum()/cmv
    return f
def slope(M,n,e):
    Y=M.iloc[e-n+1:e+1]; x=np.arange(n)-(n-1)/2; return (Y.mul(x,axis=0)).sum()/(x**2).sum()
def f_v5(b):
    e=int(np.where(dates<=b)[0][-1]); f=pd.DataFrame(index=codes)
    for n in (5,20,60,120):
        f[f"tov_rel_{n}"]=TREL.iloc[e-n+1:e+1].mean(); f[f"ret_{n}"]=LR.iloc[e-n+1:e+1].sum()
        f[f"lg_{n}"]=LGN.iloc[e-n+1:e+1].sum(); f[f"vol_{n}"]=LR.iloc[e-n+1:e+1].std(); f[f"rz_{n}"]=np.log(RZ5.iloc[e]/RZ5.iloc[e-n])
    for h in (5,20,60):
        f[f"tov_ewm_{h}"]=TREL.iloc[max(0,e-600):e+1].ewm(halflife=h,min_periods=h).mean().iloc[-1]
        f[f"lg_ewm_{h}"]=LGN.iloc[max(0,e-600):e+1].ewm(halflife=h,min_periods=h).mean().iloc[-1]
    f["tov_slope60"]=slope(TREL,60,e); f["rz_slope60"]=slope(np.log(RZ5),60,e)
    return f
def feats(a,b): return pd.concat([f_v3(a,b),f_v5(b)],axis=1).replace([np.inf,-np.inf],np.nan)
QE=[f"{y}{m}" for y in range(2020,2027) for m in ("0331","0630","0930","1231")]; QE=[q for q in QE if "20201231"<=q<="20261231"]
last=lambda d: dates[dates<=d][-1]
# --- rows: quarter ends (training + eval) and intra-quarter offsets ---
OFF=(15,30,45)
rows=[]
RAW=f"{OUT}/raw_rows.parquet"
for a,q in (zip(QE[:-1],QE[1:]) if not os.path.exists(RAW) else []):
    qi=np.where(dates>a)[0]
    if q<="20260930":
        f=feats(a,q); f["q"]=q; f["asof"]=last(q); f["off"]=999; rows.append(f)
    for o in OFF:
        if len(qi)>o-1 and dates[qi[o-1]]<=min(q,"20261113"):
            d=dates[qi[o-1]]; f=feats(a,d); f["q"]=q; f["asof"]=d; f["off"]=o; rows.append(f)
    if q=="20261231":
        f=feats(a,"20261113"); f["q"]=q; f["asof"]="20261113"; f["off"]=0; rows.append(f)   # live as-of
    print(q,end=" ",flush=True)
if rows:
    F=pd.concat(rows); F.index.name="ts_code"; F=F.reset_index(); F.to_parquet(RAW)
F=pd.read_parquet(RAW).drop_duplicates(["ts_code","q","asof","off"])
# GAUGE_LIVE=YYYYMMDD appends one more live 2026Q4 row (cached) and refits only the live readings
LIVE=os.environ.get("GAUGE_LIVE")
if LIVE:
    LIVE=str(last(LIVE))
    if not ((F.off==0)&(F["asof"]==LIVE)).any():
        f=feats("20260930",LIVE); f["q"]="20261231"; f["asof"]=LIVE; f["off"]=0; f.index.name="ts_code"
        F=pd.concat([F,f.reset_index()],ignore_index=True); F.to_parquet(RAW)
print("\nrows",F.shape,flush=True)
# chip: quarter-end rows get the full snapshot + deltas; intra rows get previous quarter-end state, zero deltas
cyq=pd.read_parquet(f"{S}/cyq_qe.parquet"); cyq["conc"]=(cyq.cost_85pct-cyq.cost_15pct)/cyq.cost_50pct
cd=sorted(cyq.trade_date.unique()); snap=lambda d: max(x for x in cd if x<=d)
pxc=duckdb.sql(f"select ts_code,trade_date,close from {s('daily')} where trade_date in {tuple(cd)}").df()
def chip(d_b,d_a):
    cb=cyq[cyq.trade_date==d_b].set_index("ts_code"); pb=pxc[pxc.trade_date==d_b].set_index("ts_code").close
    c=pd.DataFrame({"win_b":cb.winner_rate,"conc_b":cb.conc,"pc50_b":np.log(pb/cb.cost_50pct)})
    ca=cyq[cyq.trade_date==d_a].set_index("ts_code"); pa=pxc[pxc.trade_date==d_a].set_index("ts_code").close
    c["dwin"]=cb.winner_rate-ca.winner_rate; c["dconc"]=cb.conc-ca.conc; c["dpc50"]=c.pc50_b-np.log(pa/ca.cost_50pct); c["wavg_gap"]=np.log(cb.weight_avg/ca.weight_avg)
    return c
parts=[]
for (q,off),g in F.groupby(["q","off"]):
    i=QE.index(q); a=QE[i-1]
    if off==999: c=chip(snap(q),snap(a))
    else: c=chip(snap(a),snap(a))
    parts.append(g.join(c,on="ts_code"))
F=pd.concat(parts)
# labels and PIT lags
h=duckdb.sql(f"select ts_code,end_date,arg_max(holder_num,ann_date) n,min(ann_date) ann from {s('events/stk_holdernumber')} where end_date>='20200630' group by 1,2").df()
N=h.pivot(index="ts_code",columns="end_date",values="n"); A=h.set_index(["ts_code","end_date"]).ann.to_dict()
allq=sorted(N.columns); Nd=N.to_dict()
def pq(q,k): return allq[allq.index(q)-k] if q in allq and allq.index(q)-k>=0 else None
def chg(c,q):
    p=pq(q,1)
    if p is None: return np.nan
    a,b=Nd.get(p,{}).get(c),Nd.get(q,{}).get(c)
    return np.log(b/a) if a and b and a>0 else np.nan
F["y"]=[chg(c,q) if q in allq else np.nan for c,q in zip(F.ts_code,F.q)]
F["ann_y"]=[A.get((c,q)) for c,q in zip(F.ts_code,F.q)]
def lagchg(c,q,k,asof):
    qq=QE[QE.index(q)-k]; a=A.get((c,qq))
    if a is None or a>asof: return np.nan
    return chg(c,qq)
F["prev"]=[lagchg(c,q,1,d) for c,q,d in zip(F.ts_code,F.q,F["asof"])]
F["prev2"]=[lagchg(c,q,2,d) for c,q,d in zip(F.ts_code,F.q,F["asof"])]
F["qtr"]=F.q.str[4:6].map({"03":1,"06":2,"09":3,"12":4}).astype(float)
# *_lag1 = previous quarter-end row's value
LAGC=["dtov","tov_acc","mchg","ret_q","big_cum","dd_qhigh","lg_cum","tov_rel_60","lg_60"]
qe_rows=F[F.off==999].set_index(["ts_code","q"])[LAGC]
prevq={q:QE[QE.index(q)-1] for q in QE[1:]}
key=pd.MultiIndex.from_arrays([F.ts_code,F.q.map(prevq)])
for c in LAGC: F[c+"_lag1"]=qe_rows[c].reindex(key).values
F["dtov_prev"]=F["dtov_lag1"]
F.to_parquet(f"{OUT}/feature_rows.parquet")
FEATS=[c for c in F.columns if c not in ("ts_code","q","asof","off","y","ann_y")]
print("features",len(FEATS),flush=True)
best=json.load(open(f"{S}/lgbm_best.json"))
def fit_predict(tr,te,fs):
    med=tr[fs].median(); tr=tr.copy(); te=te.copy(); tr[fs]=tr[fs].fillna(med); te[fs]=te[fs].fillna(med)
    for c in fs: tr[c]=tr.groupby("q")[c].rank(pct=True); te[c]=te[c].rank(pct=True)
    tr["t"]=tr.groupby("q").y.rank(pct=True)
    m=lgb.LGBMRegressor(verbose=-1,random_state=0,**best).fit(tr[fs],tr.t); return m.predict(te[fs])
TR=F[(F.off==999)&F.y.notna()&(F.y.abs()<2)]
trainq=sorted(TR.q.unique()); targets=["20261231"] if LIVE else [q for q in QE if q>="20220331"]
out=[]
for q in targets:
    for (off,asof),te in F[(F.q==q)&((F.off==0) if LIVE else True)].groupby(["off","asof"]):
        tr=TR[(TR.q<q)&(TR.ann_y<=asof)]
        if tr.q.nunique()<4: continue
        p=fit_predict(tr,te,FEATS); d=te[["ts_code","q","asof","off","y"]].copy(); d["pct"]=pd.Series(p,index=te.index).rank(pct=True).values
        out.append(d); print(q,off,asof,len(tr),flush=True)
G=pd.concat(out)
if LIVE:
    old=pd.read_parquet(f"{OUT}/gauge_paths.parquet"); G=pd.concat([old[~((old.off==0)&old["asof"].isin(G["asof"].unique()))],G])
G.to_parquet(f"{OUT}/gauge_paths.parquet"); print("saved",G.shape)
