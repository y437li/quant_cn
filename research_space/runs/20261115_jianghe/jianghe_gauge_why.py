"""Why is 江河集团's RetailGauge ~0 for 2026Q4? Fit v5 on all quarter-end rows announced by 2026-11-13 (as in the live run),
predict the 11-13 row, and list LightGBM per-feature contributions (pred_contrib) plus the stock's feature ranks."""
import pandas as pd, numpy as np, json, lightgbm as lgb
R="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_gauge_intraquarter"; S="/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
F=pd.read_parquet(f"{R}/feature_rows.parquet"); FS=[c for c in F.columns if c not in ("ts_code","q","asof","off","y","ann_y")]
tr=F[(F.off==999)&F.y.notna()&(F.y.abs()<2)&(F.ann_y<="20261113")].copy(); te=F[(F.q=="20261231")&(F.off==0)].copy()
med=tr[FS].median(); tr[FS]=tr[FS].fillna(med); te[FS]=te[FS].fillna(med)
raw=te.set_index("ts_code")[FS].copy()
for c in FS: tr[c]=tr.groupby("q")[c].rank(pct=True); te[c]=te[c].rank(pct=True)
tr["t"]=tr.groupby("q").y.rank(pct=True)
m=lgb.LGBMRegressor(verbose=-1,random_state=0,**json.load(open(f"{S}/lgbm_best.json"))).fit(tr[FS],tr.t)
te=te.set_index("ts_code"); p=pd.Series(m.predict(te[FS]),index=te.index).rank(pct=True)
C="601886.SH"; print("gauge",round(p[C],3))
con=pd.Series(m.predict(te.loc[[C],FS],pred_contrib=True)[0][:-1],index=FS)
out=pd.DataFrame({"contrib":con,"rank_pct":te.loc[C,FS],"raw":raw.loc[C,FS]}).sort_values("contrib")
pd.set_option("display.width",200); print(out.head(15).round(3).to_string()); print(out.tail(6).round(3).to_string())
