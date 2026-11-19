"""Plan 21 rules applied by hand on 2026-11-12 data: top names and near-misses. Run market_panel.py first."""
import duckdb, pandas as pd, numpy as np
from pathlib import Path
from quant_cn.core.config import Config
from quant_cn.core.positions_book import PositionsBook
CFG = Config.load(); LAKE = Path(CFG.lake.root)
L = str(LAKE / "curated"); R = str(LAKE / "meta/runs/holder_nowcast")
S = str(LAKE / "meta/runs/research/20261113_opportunity_list")
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
x=pd.read_parquet(f"{S}/market_x.parquet")   # q2,q3,q2ly,q3ly (deducted, 亿), mv, pe_ttm, e26,e27,e27o, name,l1,l3
x["y3"]=(x.q3-x.q3ly)/x.q3ly.abs(); x["y2"]=(x.q2-x.q2ly)/x.q2ly.abs(); x["rev27"]=x.e27/x.e27o-1; x["g27"]=x.e27/x.e26-1
g=pd.read_parquet(f"{R}/holders_forecast_q4.parquet")[["pct","h_q3","h_exp"]]; x=x.drop(columns=[c for c in g.columns if c in x.columns]).join(g)
pe=duckdb.sql(f"select ts_code, quantile_cont(pe_ttm,0.5) pe_med from {s('daily_basic')} where trade_date>='20211101' and pe_ttm>0 group by 1").df().set_index("ts_code"); x=x.drop(columns=[c for c in pe.columns if c in x.columns]).join(pe)
b=duckdb.sql(f"select ts_code, circ_mv/1e4 cmv, dv_ttm from {s('daily_basic')} where trade_date='20261112'").df().set_index("ts_code"); x=x.drop(columns=[c for c in b.columns if c in x.columns]).join(b)
e=duckdb.sql(f"select ts_code, factor, exposure from read_parquet('/Volumes/Treasury/quant_cn_lake/derived/risk_exposure/year=2026/*.parquet') where trade_date='20261112' and factor in ('momentum','usd_sensitivity')").df().pivot(index="ts_code",columns="factor",values="exposure")
x=x.drop(columns=[c for c in e.columns if c in x.columns]).join(e)
mf=duckdb.sql(f"select ts_code, trade_date, (buy_lg_amount-sell_lg_amount)/1e4 lg from {s('moneyflow')} where trade_date>='20261013'").df()
mf["wk"]=pd.to_datetime(mf.trade_date).dt.to_period("W-FRI"); wk=mf.groupby(["ts_code","wk"]).lg.sum().unstack()
last4=wk.iloc[:,-4:]; x=x.join(pd.DataFrame({"lg_weeks_pos":(last4>0).sum(axis=1),"lg_4w":last4.sum(axis=1)}))
held=set(PositionsBook.load(CFG.repo_root).list_codes())  # private book, read at runtime
u=x[(x.cmv>=50)&~x.index.isin(held)&x.name.notna()].copy()
u["R1_利润拐点"]=((u.y3>0.15)&(u.y3>u.y2+0.05)&(u.q3>0.2)&(u.q3ly>0.03))|((u.g27>0.15)&(u.rev27>=0))
u["R2_散户离开"]=u.pct<=0.30
u["R3_大单流入"]=(u.lg_weeks_pos>=3)&(u.lg_4w>0)
u["R4_估值合理"]=(u.pe_ttm>0)&(u.pe_ttm<u.pe_med)
u["R5_因子不加重"]=(u.momentum>=-0.2)&(u.usd_sensitivity>=-0.3)
rules=[c for c in u.columns if c.startswith("R")]
u["hits"]=u[rules].sum(axis=1)
u["score"]=u.hits+0.5*(0.3-u.pct).clip(lower=0)+0.2*u.y3.clip(-1,2).fillna(0)
full=u[u.hits==5].sort_values("score",ascending=False)
near=u[u.hits==4].sort_values("score",ascending=False)
near["missing"]=near[rules].apply(lambda r: ",".join(c.split("_")[1] for c in rules if not r[c]),axis=1)
cols=["name","l1","l3","cmv","pe_ttm","pe_med","dv_ttm","y2","y3","g27","rev27","pct","lg_weeks_pos","lg_4w","momentum","usd_sensitivity"]
pd.set_option("display.width",300,"display.max_rows",60)
print("universe",len(u),"| all 5:",len(full),"| 4 of 5:",len(near))
print(full[cols].head(10).round(2).to_string()); print(near[cols+["missing"]].head(15).round(2).to_string())
print("rule hit counts:", u[rules].sum().to_dict())
full.to_parquet(f"{S}/opps_full.parquet"); near.to_parquet(f"{S}/opps_near.parquet")
