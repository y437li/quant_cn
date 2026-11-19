"""LightGBM, point-in-time walk-forward: v3 path features + chip features + PIT lags; then nowcast holdings."""
import duckdb, pandas as pd, numpy as np, itertools, json, lightgbm as lgb
S="/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
L="/Volumes/Treasury/quant_cn_lake/curated"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
F=pd.read_parquet(f"{S}/holders_v3_feats.parquet").merge(pd.read_parquet(f"{S}/holders_v4_flow.parquet"),on=["ts_code","q"],how="left").merge(pd.read_parquet(f"{S}/holders_v5_feats.parquet"),on=["ts_code","q"],how="left")
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
F=F.sort_values(["ts_code","q"])
for c in ["dtov","tov_acc","mchg","ret_q","big_cum","dd_qhigh","lg_cum","tov_rel_60","lg_60"]:
    F[c+"_lag1"]=F.groupby("ts_code")[c].shift(1)
F["dtov_prev"]=F["dtov_lag1"]
FEATS=[c for c in F.columns if c not in ("ts_code","q","y","ann_y")]
print("features:",len(FEATS),FEATS)

NEW=["lg_cum","lg_last20","lg_trend","lg_inrun","lg_outrun","elg_cum","sm_cum","sm_last20"]
BASE=[c for c in FEATS if c not in NEW]
train_q=[q for q in Q if q!="20261112"]; best=json.load(open(f"{S}/lgbm_best.json"))
def fit_predict(tr,te,fs):
    med=tr[fs].median(); tr=tr.copy(); te=te.copy(); tr[fs]=tr[fs].fillna(med); te[fs]=te[fs].fillna(med)
    for c in fs: tr[c]=tr.groupby("q")[c].rank(pct=True); te[c]=te[c].rank(pct=True)
    tr["t"]=tr.groupby("q").y.rank(pct=True)
    m=lgb.LGBMRegressor(verbose=-1,random_state=0,**best).fit(tr[fs],tr.t); return m,m.predict(te[fs]),te

V5=[c for c in FEATS if c.startswith(("tov_rel_","ret_5","ret_20","ret_60","ret_120","lg_5","lg_20","lg_60","lg_120","vol_5","vol_20","vol_60","vol_120","rz_","tov_ewm","lg_ewm","tov_slope","rz_slope")) or c.endswith("_lag1")]
V4=[c for c in FEATS if c not in V5]
print("v4 feats",len(V4),"v5 feats",len(V4+V5))
rows=[]
for label,fs in (("v4",V4),("v5 (+多尺度/指数加权/斜率/滞后)",V4+V5)):
    for q in train_q[4:]:
        k=train_q.index(q); tr=F[F.q.isin(train_q[:k])&(F.ann_y<=q)&F.y.notna()&(F.y.abs()<2)]; te=F[(F.q==q)&F.y.notna()]
        _,p,_=fit_predict(tr,te,fs); yr=te.y.rank(pct=True); p=pd.Series(p,index=te.index)
        rows.append(dict(model=label,q=q,ic=p.corr(yr,method="spearman"),hit=(yr[p>=p.quantile(0.9)]>=0.7).mean(),hit_lo=(yr[p<=p.quantile(0.1)]<=0.3).mean()))
R=pd.DataFrame(rows); print(R.groupby("model").agg(IC=("ic","mean"),IC_min=("ic","min"),hit_top=("hit","mean"),hit_bottom=("hit_lo","mean")).round(3).to_string())
w=R.pivot(index="q",columns="model",values="ic"); print("v5 better in", int((w.iloc[:,1]>w.iloc[:,0]).sum()),"of",len(w),"quarters")
tr=F[F.q.isin(train_q)&F.y.notna()&(F.y.abs()<2)&(F.ann_y<="20261112")]; te0=F[F.q=="20261112"].set_index("ts_code",drop=False)
m,p,te=fit_predict(tr,te0,V4+V5); te["pct"]=pd.Series(p,index=te.index).rank(pct=True); te[["pct"]].to_parquet(f"{S}/holders_nowcast_v5.parquet")
contrib=pd.DataFrame(m.predict(te[V4+V5],pred_contrib=True),index=te.index,columns=V4+V5+["base"])
g=contrib[V4+V5].abs().mean().sort_values(ascending=False); print("top15 mean|SHAP|:", g.head(15).round(4).to_dict())
