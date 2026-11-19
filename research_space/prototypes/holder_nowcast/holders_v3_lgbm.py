"""LightGBM, point-in-time walk-forward: v3 path features + chip features + PIT lags; then nowcast holdings."""
import duckdb, pandas as pd, numpy as np, itertools, json, lightgbm as lgb
S="/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
L="/Volumes/Treasury/quant_cn_lake/curated"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
F=pd.read_parquet(f"{S}/holders_v3_feats.parquet")
# chip features per quarter (from cyq snapshots)
cyq=pd.read_parquet(f"{S}/cyq_qe.parquet"); cyq["conc"]=(cyq.cost_85pct-cyq.cost_15pct)/cyq.cost_50pct
cd=sorted(cyq.trade_date.unique()); Q=sorted(F.q.unique())
snap=lambda q: max(d for d in cd if d<=q)
px=duckdb.sql(f"select ts_code, trade_date, close from {s('daily')} where trade_date in {tuple(cd)}").df()
chip=[]
for i,q in enumerate(Q):
    a=Q[i-1] if i>0 else None
    cb=cyq[cyq.trade_date==snap(q)].set_index("ts_code"); pb=px[px.trade_date==snap(q)].set_index("ts_code").close
    c=pd.DataFrame({"win_b":cb.winner_rate,"conc_b":cb.conc,"pc50_b":np.log(pb/cb.cost_50pct)})
    if a is not None:
        ca=cyq[cyq.trade_date==snap(a)].set_index("ts_code"); pa=px[px.trade_date==snap(a)].set_index("ts_code").close
        c["dwin"]=cb.winner_rate-ca.winner_rate; c["dconc"]=cb.conc-ca.conc; c["dpc50"]=c.pc50_b-np.log(pa/ca.cost_50pct); c["wavg_gap"]=np.log(cb.weight_avg/ca.weight_avg)
    c["q"]=q; chip.append(c.reset_index())
F=F.merge(pd.concat(chip),on=["ts_code","q"],how="left")
# labels and PIT lags
hq=[q for q in Q if q!="20261112"]+["20201231"]
h=duckdb.sql(f"select ts_code, end_date, arg_max(holder_num, ann_date) n, min(ann_date) ann from {s('events/stk_holdernumber')} where end_date>='20200630' group by 1,2").df()
N=h.pivot(index="ts_code",columns="end_date",values="n"); A=h.set_index(["ts_code","end_date"]).ann
allq=sorted(N.columns); pq=lambda q,k: allq[allq.index(q)-k] if q in allq and allq.index(q)-k>=0 else None
def lab(c,q):
    p=pq(q,1); 
    return np.log(N.at[c,q]/N.at[c,p]) if (q in N.columns and p and c in N.index) else np.nan
F["y"]=[lab(c,q) if q!="20261112" else np.nan for c,q in zip(F.ts_code,F.q)]
F["ann_y"]=[A.get((c,q)) for c,q in zip(F.ts_code,F.q)]
def lagchg(c,q,k):   # change from quarter (q-k-1) to (q-k), only if announced by q (as-of)
    qq=pq(q if q in allq else "20260930",k-1 if q not in allq else k)  # for nowcast row, k=1 means Q3 change
    if qq is None or c not in N.index: return np.nan
    p=pq(qq,1); a=A.get((c,qq))
    if p is None or a is None or a>q: return np.nan
    return np.log(N.at[c,qq]/N.at[c,p])
F["prev"]=[lagchg(c,q,1) for c,q in zip(F.ts_code,F.q)]; F["prev2"]=[lagchg(c,q,2) for c,q in zip(F.ts_code,F.q)]
F["qtr"]=F.q.str[4:6].map({"03":1,"06":2,"09":3,"12":4,"11":4}).astype(float)
F["dtov_prev"]=F.groupby("ts_code").dtov.shift(1)
FEATS=[c for c in F.columns if c not in ("ts_code","q","y","ann_y")]
print("features:",len(FEATS),FEATS)
train_q=[q for q in Q if q!="20261112"]
def fit_predict(tr,te,params):
    med=tr[FEATS].median(); tr=tr.copy(); te=te.copy(); tr[FEATS]=tr[FEATS].fillna(med); te[FEATS]=te[FEATS].fillna(med)
    for c in FEATS: tr[c]=tr.groupby("q")[c].rank(pct=True); te[c]=te[c].rank(pct=True)
    tr["yr"]=tr.groupby("q").y.rank(pct=True)
    m=lgb.LGBMRegressor(verbose=-1,random_state=0,**params).fit(tr[FEATS],tr.yr)
    return m, m.predict(te[FEATS])
def wf(params, qs):
    ics=[];hits=[]
    for q in qs:
        k=train_q.index(q); tr=F[F.q.isin(train_q[:k])&(F.ann_y<=q)&F.y.notna()&(F.y.abs()<2)]; te=F[(F.q==q)&F.y.notna()]
        _,p=fit_predict(tr,te,params); yr=te.y.rank(pct=True)
        ics.append(pd.Series(p,index=te.index).corr(yr,method="spearman")); hits.append((yr[p>=np.quantile(p,0.9)]>=0.7).mean())
    return np.mean(ics),np.min(ics),np.mean(hits)
VAL=train_q[-10:-4]; TEST=train_q[-4:]
grid=[dict(n_estimators=n,learning_rate=lr,num_leaves=nl,min_child_samples=mc,subsample=0.8,subsample_freq=1,colsample_bytree=cs,reg_lambda=1.0)
      for n,lr,nl,mc,cs in itertools.product([400,800],[0.02,0.05],[31,63],[200,500],[0.7])]
res=sorted([(wf(g,VAL),g) for g in grid],key=lambda r:-r[0][0])
for (ic,mn,h),g in res[:3]: print(f"VAL IC {ic:.3f} min {mn:.2f} hit {h:.0%} {g}")
best=res[0][1]; json.dump(best,open(f"{S}/lgbm_best.json","w"))
ic,mn,h=wf(best,TEST); print(f"TEST {TEST[0]}..{TEST[-1]} LightGBM v3 PIT: IC {ic:.3f} min {mn:.2f} top-decile hit {h:.0%}")
ic,mn,h=wf(best,train_q[4:]); print(f"ALL walk-forward {train_q[4]}..{train_q[-1]}: IC {ic:.3f} min {mn:.2f} hit {h:.0%}")
# final model and nowcast
tr=F[F.q.isin(train_q)&F.y.notna()&(F.y.abs()<2)&(F.ann_y<="20261112")]; te=F[F.q=="20261112"].set_index("ts_code",drop=False)
m,p=fit_predict(tr,te,best); te["pct"]=pd.Series(p,index=te.index).rank(pct=True)
ys=F[F.q.isin(train_q[-4:])].y.dropna(); te["exp_dlog"]=np.quantile(ys,te.pct.clip(0.01,0.99))
imp=pd.Series(m.booster_.feature_importance("gain"),index=FEATS).sort_values(ascending=False); print("top gain:", (imp/imp.sum()).round(3).head(12).to_dict())
te.to_parquet(f"{S}/holders_nowcast_v3.parquet")
