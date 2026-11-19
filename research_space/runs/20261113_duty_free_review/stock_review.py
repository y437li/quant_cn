"""Compact holding review: fundamentals, consensus revisions, valuation, chip structure."""
import duckdb, pandas as pd, os, sys, requests
from pathlib import Path
from quant_cn.core.config import Config
L = str(Path(Config.load().lake.root) / "curated")
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
pd.set_option("display.width",250,"display.max_columns",30,"display.max_colwidth",50)
for C in sys.argv[1:]:
    print("\n########", C)
    inc=duckdb.sql(f"""with x as (select *, row_number() over (partition by end_date order by ann_date desc, update_flag desc) rn from {s('fundamentals/income')} where ts_code='{C}' and report_type='1' and end_date>='20250101')
    select end_date, revenue/1e8 rev, (revenue-oper_cost)/1e8 gp, n_income_attr_p/1e8 np from x where rn=1 order by 1""").df()
    inc["yr"]=inc.end_date.str[:4]
    for c in ["rev","gp","np"]: inc["q_"+c]=inc.groupby("yr")[c].diff().fillna(inc[c])
    inc["gm"]=inc.q_gp/inc.q_rev
    print(inc.set_index("end_date")[["q_rev","gm","q_np"]].round(2).T.to_string())
    rc=duckdb.sql(f"""select case when report_date>='20261020' then 'nov' else 'sep' end w, quarter, median(np)/1e4 np, count(distinct org_name) n, median(max_price) tp from {s('analysts/report_rc')}
      where ts_code='{C}' and report_date>='20260801' and quarter in ('2026Q4','2027Q4') group by 1,2 order by 2,1""").df(); print(rc.round(2).to_string(index=False))
    v=duckdb.sql(f"select close, pe_ttm, pb, dv_ttm, total_mv/1e4 mv from {s('daily_basic')} where ts_code='{C}' order by trade_date desc limit 1").df()
    h=duckdb.sql(f"select quantile_cont(pe_ttm,0.5) pe_med, quantile_cont(pb,0.1) pb10, quantile_cont(pb,0.5) pb_med from {s('daily_basic')} where ts_code='{C}' and trade_date>='20211101' and pe_ttm>0").df()
    print(pd.concat([v,h],axis=1).round(2).to_string(index=False))
    px=duckdb.sql(f"""select substr(d.trade_date,1,6) m, last(d.close*a.adj_factor order by d.trade_date) p from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.ts_code='{C}' and d.trade_date>='20251201' group by 1 order by 1""").df()
    print("rel px:", " ".join(f"{m[2:]}:{p/px.p.iloc[0]:.2f}" for m,p in zip(px.m,px.p)))
    hn=duckdb.sql(f"select end_date, arg_max(holder_num, ann_date) n from {s('events/stk_holdernumber')} where ts_code='{C}' and end_date>='20250630' group by 1 order by 1").df()
    print("holders:", " ".join(f"{e[2:6]}:{n/1e4:.1f}w" for e,n in zip(hn.end_date,hn.n)))
    tf=duckdb.sql(f"select distinct holder_name, round(hold_float_ratio,2) r, hold_change from {s('events/top10_floatholders')} where ts_code='{C}' and end_date='20260930' order by 2 desc").df()
    print(tf.to_string(index=False))
    ht=duckdb.sql(f"select in_de, count(*) n, round(sum(change_ratio),2) pct, min(ann_date) a0, max(ann_date) a1, string_agg(distinct holder_name, ';') who from {s('events/stk_holdertrade')} where ts_code='{C}' and ann_date>='20260301' group by 1").df(); print(ht.to_string(index=False))
    sf=duckdb.sql(f"select float_date, round(sum(float_ratio),2) r from (select distinct ts_code,float_date,holder_name,float_ratio from {s('events/share_float')} where ts_code='{C}' and float_date>'20261112' and float_date<'20271231') group by 1 order by 1").df(); print("unlocks:", sf.values.tolist())
    mo=duckdb.sql(f"""select substr(f.trade_date,1,6) m, sum(buy_lg_amount+buy_elg_amount-sell_lg_amount-sell_elg_amount)/1e4 big, last(m.rzye order by f.trade_date)/1e8 rz from {s('moneyflow')} f left join {s('margin_detail')} m using(ts_code,trade_date) where f.ts_code='{C}' and f.trade_date>='20260501' group by 1 order by 1""").df()
    print("bigflow/margin:", " ".join(f"{m[4:]}:{b:+.1f}/{r:.1f}" for m,b,r in zip(mo.m,mo.big,mo.rz.fillna(0))))
    r=requests.post("http://api.tushare.pro",json={"api_name":"cyq_perf","token":os.environ["TUSHARE_TOKEN"],"params":{"ts_code":C,"start_date":"20261110","end_date":"20261112"},"fields":"trade_date,his_low,cost_5pct,cost_15pct,cost_50pct,cost_85pct,cost_95pct,winner_rate"},timeout=30).json()
    print("cyq:", r["data"]["fields"], r["data"]["items"][:1])
