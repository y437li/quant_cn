"""Photoresist (光刻胶) names: price path, valuation, profit growth, RetailGauge (live 11-16), margin and holder trend.
Core list = semiconductor photoresist makers + PCB/LCD photoresist + key materials; purity from fina_mainbz_p."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
N={"603650.SH":"彤程新材","300346.SZ":"南大光电","300655.SZ":"晶瑞电材","300236.SZ":"上海新阳","300054.SZ":"鼎龙股份",
   "603306.SH":"华懋科技","002409.SZ":"雅克科技","688727.SH":"恒坤新材","300576.SZ":"容大感光","300429.SZ":"强力新材",
   "688181.SH":"八亿时空","300537.SZ":"广信材料"}
C=tuple(N); last="20261116"
px=duckdb.sql(f"select d.ts_code,d.trade_date,d.close,d.close*a.adj_factor c from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.ts_code in {C} and d.trade_date>='20250101'").df()
P=px.pivot(index="trade_date",columns="ts_code",values="c").sort_index()
db=duckdb.sql(f"select ts_code,total_mv/1e4 mv,pe_ttm,pb,turnover_rate_f from {s('daily_basic')} where trade_date='{last}' and ts_code in {C}").df().set_index("ts_code")
inc=duckdb.sql(f"select ts_code,end_date,arg_max(n_income_attr_p,ann_date) np,arg_max(revenue,ann_date) rev from {s('fundamentals/income')} where ts_code in {C} and end_date in ('20250930','20260930','20250630','20260630') and report_type='1' group by 1,2").df()
I=inc.pivot(index="ts_code",columns="end_date",values=["np","rev"])
def yoy(k,a,b): return (I[(k,b)]/I[(k,a)]-1)
G=pd.read_parquet("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_gauge_intraquarter/gauge_paths.parquet")
G=G[(G.q=="20261231")].drop_duplicates(["ts_code","asof"]).pivot(index="ts_code",columns="asof",values="pct")
rz=duckdb.sql(f"select ts_code,trade_date,rzye from {s('margin_detail')} where ts_code in {C} and trade_date>='20261010'").df().pivot(index="trade_date",columns="ts_code",values="rzye").sort_index()
rzl=rz.index[-1]; rz0=rz.index[max(0,len(rz)-21)]; print("margin", rz0, "->", rzl)
hn=duckdb.sql(f"select ts_code,end_date,arg_max(holder_num,ann_date) n from {s('events/stk_holdernumber')} where ts_code in {C} and end_date in ('20260630','20260930') group by 1,2").df().pivot(index="ts_code",columns="end_date",values="n")
T=pd.DataFrame(index=list(N)); T["名称"]=pd.Series(N)
T["收盘"]=px[px.trade_date==last].set_index("ts_code").close
T["市值亿"]=db.mv.round(0); T["PE_TTM"]=db.pe_ttm.round(0); T["PB"]=db.pb.round(1)
p=P.loc[:last]
T["2026年%"]=((p.iloc[-1]/p.loc[:"20251231"].iloc[-1]-1)*100).round(0)
T["20日%"]=((p.iloc[-1]/p.iloc[-21]-1)*100).round(1)
T["距年高%"]=((p.iloc[-1]/p.loc["20260101":].max()-1)*100).round(0)
T["前三季营收同比%"]=(yoy("rev","20250930","20260930")*100).round(0)
T["前三季净利同比%"]=(yoy("np","20250930","20260930")*100).round(0)
T["前三季净利亿"]=(I[("np","20260930")]/1e8).round(2)
T["温度计10-28"]=G.get("20261028").round(2); T["温度计11-16"]=G.get(last).round(2)
T["融资1月变化%"]=((rz.loc[rzl]/rz.loc[rz0]-1)*100).round(0)
T["Q3户数环比%"]=((hn["20260930"]/hn["20260630"]-1)*100).round(0)
pd.set_option("display.width",300); print(T.to_string())
idx=(P.loc["20260101":last].pct_change().mean(axis=1).fillna(0)+1).cumprod()
m=idx.resample("ME").last() if False else None
print("\n等权指数 2026 月末:", {d:round(v,2) for d,v in idx.groupby(idx.index.str[:6]).last().items()})
print("等权 2026 高点", idx.idxmax(), round(idx.max(),2), "现", round(idx.iloc[-1],2))
