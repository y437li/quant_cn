"""Tech leaders at the 2026 peak vs now: TTM profit, reverse-DCF growth (ImpliedExpectations, exit PE 12 / 25), consensus FY2026-28 medians (90 days, latest per broker), forward PE."""
from pathlib import Path
import pandas as pd, numpy as np
from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.calculation.implied_expectations import ImpliedExpectations
c=Config.load(Path("/Volumes/Treasury/quant_cn")); cat=LakeCatalog(c.lake.root,c.datasets,read_only=True); q=LakeQuery(cat); pd.set_option("display.width",250)
CODES={"300308.SZ":"中际旭创","300502.SZ":"新易盛","601138.SH":"工业富联","603986.SH":"兆易创新","688256.SH":"寒武纪","688041.SH":"海光信息","688981.SH":"中芯国际","002371.SZ":"北方华创"}
ie={pe:ImpliedExpectations(c.discovery.model_copy(update={"normal_pe":pe})) for pe in (12,25)}
db=q.sql("select ts_code,trade_date,total_mv/1e4 mv,pe_ttm from curated.daily_basic where list_contains(?,ts_code) and trade_date>='20250701'",[list(CODES)])
rc=q.sql("select ts_code,report_date,org_name,quarter,np/1e4 np from curated.report_rc where list_contains(?,ts_code) and report_date>='20250901' and quarter like '%Q4' and np is not null",[list(CODES)])
fy=q.sql("select ts_code, end_date, arg_min(n_income_attr_p,ann_date)/1e8 np from curated.income_vip where report_type='1' and list_contains(?,ts_code) and end_date in ('20241231','20251231') group by 1,2",[list(CODES)]).pivot(index="ts_code",columns="end_date",values="np")
rows=[]
for cd,nm in CODES.items():
    d=db[db.ts_code==cd].sort_values("trade_date").set_index("trade_date")
    pk=d.mv.idxmax()
    for lab,day in (("高点",pk),("现在",d.index[-1])):
        mv,pe=d.at[day,"mv"],d.at[day,"pe_ttm"]; ttm=mv/pe if pe and pe>0 else np.nan
        w=rc[(rc.ts_code==cd)&(rc.report_date<=day)&(rc.report_date>str(int(day)-10000+9000) if False else (rc.ts_code==cd)&(rc.report_date<=day)&(rc.report_date>(pd.Timestamp(day)-pd.Timedelta(days=90)).strftime("%Y%m%d")))]
        med=w.sort_values("report_date").drop_duplicates(["org_name","quarter"],keep="last").groupby("quarter").np.median()
        f25=fy.at[cd,"20251231"] if cd in fy.index else np.nan
        f28=med.get("2028Q4",np.nan)
        rows.append(dict(name=nm,when=lab,date=day,mv=round(mv),pe_ttm=round(pe,0),ttm=round(ttm,1),
            g12=round(ie[12].compute_implied_growth(mv*1e8,ttm*1e8)*100,0),g25=round(ie[25].compute_implied_growth(mv*1e8,ttm*1e8)*100,0),
            fy25=round(f25,1),c26=round(med.get("2026Q4",np.nan),0),c27=round(med.get("2027Q4",np.nan),0),c28=round(f28,0),
            pe27=round(mv/med.get("2027Q4",np.nan),1),pe28=round(mv/f28,1),cagr25_28=round(((f28/f25)**(1/3)-1)*100,0) if f25>0 else np.nan,n=w.org_name.nunique()))
print(pd.DataFrame(rows).to_string(index=False))
cat.close()
