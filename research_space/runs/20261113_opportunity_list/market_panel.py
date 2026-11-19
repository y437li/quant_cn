"""Whole-market L3 scan: deducted-profit acceleration, consensus revisions, price position, chip signals."""
import duckdb, pandas as pd, numpy as np
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root)
L = str(LAKE / "curated"); D = str(LAKE / "derived/risk_exposure/year=2026/*.parquet")
OUT = LAKE / "meta/runs/research/20261113_opportunity_list"; OUT.mkdir(parents=True, exist_ok=True)
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
pd.set_option("display.width",320,"display.max_rows",120,"display.max_columns",40)
m=duckdb.sql(f"select ts_code, any_value(name) AS name, any_value(l1_name) AS l1, any_value(l3_name) AS l3 from '{L}/reference/index_member_all.parquet' where out_date is null group by 1").df().set_index("ts_code")
q=duckdb.sql(f"""with x as (select *, row_number() over (partition by ts_code,end_date order by ann_date desc, update_flag desc) rn from {s('fundamentals/fina_indicator')} where end_date in ('20250331','20250630','20250930','20260331','20260630','20260930'))
 select ts_code,end_date,profit_dedt from x where rn=1""").df().pivot(index="ts_code",columns="end_date",values="profit_dedt")/1e8
d=pd.DataFrame({"q3":q["20260930"]-q["20260630"],"q2":q["20260630"]-q["20260331"],"q3ly":q["20250930"]-q["20250630"],"q2ly":q["20250630"]-q["20250331"]})
b=duckdb.sql(f"select ts_code, total_mv/1e4 mv, pe_ttm, pb, dv_ttm from read_parquet('{L}/daily_basic/**/*.parquet', hive_partitioning=true) where trade_date='20261112'").df().set_index("ts_code")
adj=duckdb.sql(f"select d.ts_code, d.trade_date, d.close*a.adj_factor p from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date in ('20251231','20260812','20261112')").df().pivot(index="ts_code",columns="trade_date",values="p")
r=pd.DataFrame({"ytd":adj["20261112"]/adj["20251231"]-1,"r3m":adj["20261112"]/adj["20260812"]-1})
e=duckdb.sql(f"select ts_code, factor, exposure from read_parquet('{D}') where trade_date='20261112' and factor in ('momentum','earnings_yield')").df().pivot(index="ts_code",columns="factor",values="exposure")
rc=duckdb.sql(f"""with r as (select ts_code, quarter, np, report_date from {s('analysts/report_rc')} where report_date>='20260801' and quarter in ('2026Q4','2027Q4') and np is not null)
 select ts_code, median(np) filter (where quarter='2027Q4' and report_date>='20261015')/1e4 e27, median(np) filter (where quarter='2027Q4' and report_date<'20261015')/1e4 e27o,
   median(np) filter (where quarter='2026Q4' and report_date>='20261015')/1e4 e26 from r group by 1""").df().set_index("ts_code")
hn=duckdb.sql(f"select ts_code, end_date, arg_max(holder_num, ann_date) n from {s('events/stk_holdernumber')} where end_date in ('20260630','20260930') group by 1,2").df().pivot(index="ts_code",columns="end_date",values="n")
tf=duckdb.sql(f"""select ts_code, end_date, sum(hold_float_ratio) FILTER (WHERE holder_name ILIKE '%基金%' OR holder_name ILIKE '%社保%' OR holder_name ILIKE '%保险%' OR holder_name ILIKE '%养老%' OR holder_name ILIKE '%香港中央结算%') inst
 from (select distinct ts_code,end_date,holder_name,hold_float_ratio from {s('events/top10_floatholders')} where end_date in ('20260630','20260930')) group by 1,2""").df().pivot(index="ts_code",columns="end_date",values="inst")
x=m.join(d,how="inner").join(b).join(r).join(e).join(rc).join(pd.DataFrame({"hold_chg":hn["20260930"]/hn["20260630"]-1,"inst_dq":tf["20260930"].fillna(0)-tf["20260630"].fillna(0)}))
x.to_parquet(OUT / "market_x.parquet")
def agg(g):
    w=g.mv.fillna(0); cov=g.dropna(subset=["e26","e27"]); cov=cov[cov.e26>0]; rv=cov.dropna(subset=["e27o"])
    y3=(g.q3.sum()-g.q3ly.sum())/abs(g.q3ly.sum()) if abs(g.q3ly.sum())>0.5 else np.nan
    y2=(g.q2.sum()-g.q2ly.sum())/abs(g.q2ly.sum()) if abs(g.q2ly.sum())>0.5 else np.nan
    return pd.Series({"n":len(g),"mv":w.sum(),"q3":g.q3.sum(),"y2":y2,"y3":y3,"g27":cov.e27.sum()/cov.e26.sum()-1 if len(cov)>=3 else np.nan,
      "rev27":rv.e27.sum()/rv.e27o.sum()-1 if len(rv)>=3 else np.nan,"pe_q3x4":w.sum()/(4*g.q3.sum()) if g.q3.sum()>0 else np.nan,
      "ytd":(g.ytd*w).sum()/w[g.ytd.notna()].sum(),"r3m":(g.r3m*w).sum()/w[g.r3m.notna()].sum(),"mom":(g.momentum*w).sum()/w[g.momentum.notna()].sum(),
      "hold":g.hold_chg.median(),"inst":g.inst_dq.median()})
t=x.groupby(["l1","l3"]).apply(agg)
t=t[(t.n>=5)&(t.mv>=300)&(t.q3>1)]
t["accel"]=t.y3-t.y2
cand=t[(t.y3>0.2)&(t.accel>0)&(t.r3m<0.10)&((t.rev27>-0.02)|t.rev27.isna())]
cand=cand.assign(score=cand.y3.clip(upper=2)+cand.accel.clip(upper=1)-cand.r3m-cand.mom.clip(lower=0)*0.3-cand.hold.fillna(0)*2+cand.rev27.fillna(0))
print(len(t),"L3 groups;",len(cand),"pass")
print(cand.sort_values("score",ascending=False).round(2).head(40).to_string())
t.to_csv(OUT / "l3_scan.csv")
