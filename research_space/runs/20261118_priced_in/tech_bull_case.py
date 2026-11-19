"""Tech bull case (2025-07..2026-11): SUE-quintile windows per quarter for 电子/通信/计算机, and the 12 largest tech names (peak, drawdown, PE, per-report pre/reaction/post). Reads events.parquet from priced_in.py."""
from pathlib import Path
import pandas as pd, numpy as np
from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
c=Config.load(Path("/Volumes/Treasury/quant_cn")); cat=LakeCatalog(c.lake.root,c.datasets,read_only=True); q=LakeQuery(cat); pd.set_option("display.width",250); pd.set_option("display.max_columns",30)
ev=pd.read_parquet(Path(c.lake.root)/"meta/runs/research/20261118_priced_in/events.parquet")
mem=q.sql("select distinct ts_code,l1_name,l2_name from curated.index_member_all where is_new='Y'")
ev=ev.merge(mem,on="ts_code",how="left")
tech=ev[ev.l1_name.isin(["电子","通信","计算机"])].copy()
tech["sq5"]=tech.groupby("end_date")["sue"].transform(lambda s: pd.qcut(s.rank(method="first"),5,labels=False))
for e in ["20250630","20250930","20251231","20260331","20260630","20260930"]:
    t=tech[tech.end_date==e]
    g=t.groupby("sq5")[["pre60","react","post20","post60"]].mean().round(1)
    print(e,"n",len(t),"first_ann median",t.first_ann.sort_values().iloc[len(t)//2]); print(g.T.to_string())
# leaders: biggest mv tech now/peak
mv=q.sql("select ts_code, max(total_mv)/1e4 mvmax from curated.daily_basic where trade_date between '20260101' and '20261117' group by 1")
mv=mv.merge(mem,on="ts_code"); lead=mv[mv.l1_name.isin(["电子","通信","计算机"])].nlargest(12,"mvmax")
codes=lead.ts_code.tolist()
names=q.sql("select ts_code,name from curated.stock_basic where list_contains(?,ts_code)",[codes]).set_index("ts_code").name
px=q.sql("select ts_code,trade_date,close_adj from derived.prices_adj where list_contains(?,ts_code) and trade_date>='20250101'",[codes]).pivot(index="trade_date",columns="ts_code",values="close_adj")
pe=q.sql("select ts_code,trade_date,pe_ttm from curated.daily_basic where list_contains(?,ts_code) and trade_date>='20250101'",[codes]).pivot(index="trade_date",columns="ts_code",values="pe_ttm")
rows=[]
for cd in codes:
    s=px[cd].dropna(); pk=s.idxmax()
    rows.append(dict(name=names[cd],start_2507=round(s[s.index>='20250701'].iloc[0],0),peak=pk,up=round((s.max()/s[s.index>='20250701'].iloc[0]-1)*100),down=round((s.iloc[-1]/s.max()-1)*100),pe_peak=round(pe[cd].get(pk,np.nan)),pe_now=round(pe[cd].iloc[-1])))
print(pd.DataFrame(rows,index=codes).to_string())
le=ev[ev.ts_code.isin(codes)&(ev.end_date>="20250630")].copy()
inc=q.sql("select ts_code,end_date,arg_min(n_income_attr_p,ann_date)/1e8 cum from curated.income_vip where report_type='1' and list_contains(?,ts_code) and end_date>='20240331' group by 1,2",[codes])
le["name"]=le.ts_code.map(names)
le["sq_yi"]=(le["sq"]/1e8).round(1); le["yoy"]=((le["sq"]/le["sq_ly"]-1)*100).round(0)
print(le.sort_values(["ts_code","end_date"])[["name","end_date","first_ann","sq_yi","yoy","sue","pre60","react","post20","post60"]].round(1).to_string())
cat.close()
