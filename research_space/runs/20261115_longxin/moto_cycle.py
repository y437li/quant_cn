"""Motorcycle sector cycle: SW 摩托车 L3 index relative to CSI 300 and valuation history; input costs (SHFE CU/AL), USD/CNH; member earnings growth."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
pd.set_option("display.width",250); pd.set_option("display.max_columns",30)
sw=q(f"select trade_date, close, pe, pb from {s('sw_daily')} where ts_code='858812.SI' order by 1").set_index("trade_date")
hs=q(f"select trade_date, close from read_parquet('{L}/reference/index_daily.parquet') where ts_code='000300.SH' order by 1").set_index("trade_date").close
d=sw.join(hs.rename("hs"),how="inner"); d["rel"]=d.close/d.hs; d["rel"]=d.rel/d.rel.iloc[0]
m=d.groupby(d.index.str[:6]).last()
print("SW 摩托车 L3 (858812) since",d.index[0])
print(m[m.index.str.endswith(("06","12"))|(m.index>="202607")][["close","rel","pe","pb"]].round(2).to_string())
pe=d.pe[d.pe>0]; print("PE now %.1f, pct since start %.0f%%, median %.1f, p10 %.1f, p90 %.1f"%(d.pe.iloc[-1],(pe<d.pe.iloc[-1]).mean()*100,pe.median(),pe.quantile(.1),pe.quantile(.9)))
print("PB now %.2f, pct %.0f%%"%(d.pb.iloc[-1],(d.pb<d.pb.iloc[-1]).mean()*100))
for k,n in ((1,"1y"),(3,"3y")):
    i=d.index[d.index>=str(int(d.index[-1][:4])-k)+d.index[-1][4:]][0]; print(n,"abs %.0f%% rel %.0f%%"%((d.close.iloc[-1]/d.close[i]-1)*100,(d.rel.iloc[-1]/d.rel[i]-1)*100))
# input costs and FX
f=q(f"select ts_code, substr(trade_date,1,6) m, last(close order by trade_date) c from {s('fut_daily')} where ts_code in ('CU.SHF','AL.SHF') and trade_date>='20240101' group by 1,2").pivot(index="m",columns="ts_code",values="c")
print(f.iloc[::3].join(f.iloc[[-1]],how="outer",rsuffix="_").iloc[:, :2].round(0).to_string())
fx=q(f"select substr(trade_date,1,6) m, last((bid_close+ask_close)/2 order by trade_date) usdcnh from {s('fx_daily')} where ts_code='USDCNH.FXCM' and trade_date>='20240101' group by 1 order by 1")
print(fx.iloc[::3].to_string(index=False), fx.tail(1).to_string(index=False,header=False))
# members' earnings growth: L3 members
mem=q(f"select ts_code, name from read_parquet('{L}/reference/index_member_all.parquet') where l3_code='858812.SI' and (out_date is null)") if 'l3_code' in q(f"select * from read_parquet('{L}/reference/index_member_all.parquet') limit 1").columns else None
if mem is not None:
    codes=tuple(mem.ts_code)
    inc=q(f"select ts_code,end_date,arg_max(total_revenue,ann_date)/1e8 rev,arg_max(n_income_attr_p,ann_date)/1e8 np from {s('fundamentals/income')} where ts_code in {codes} and report_type='1' and end_date in ('20250930','20260930','20250630','20260630') group by 1,2").pivot(index="ts_code",columns="end_date")
    t=pd.DataFrame({"9M rev yoy%":(inc.rev["20260930"]/inc.rev["20250930"]-1)*100,"9M np yoy%":(inc.np["20260930"]/inc.np["20250930"]-1)*100,"Q3 np yoy%":((inc.np["20260930"]-inc.np["20260630"])/(inc.np["20250930"]-inc.np["20250630"])-1)*100,"9M np":inc.np["20260930"]}).join(mem.set_index("ts_code")).round(1)
    print(t.sort_values("9M np",ascending=False).to_string())
    print("sector 9M rev yoy %.1f%%, np yoy %.1f%%"%((inc.rev["20260930"].sum()/inc.rev["20250930"].sum()-1)*100,(inc.np["20260930"].sum()/inc.np["20250930"].sum()-1)*100))
