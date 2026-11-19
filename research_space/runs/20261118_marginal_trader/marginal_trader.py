"""Who is the marginal trader: weekly margin financing, order-size net flow, turnover and index, 2026-08..11."""
import duckdb

con = duckdb.connect("/Volumes/Treasury/quant_cn_lake/meta/quant_cn.duckdb", read_only=True)
SINCE = "20260801"
q = f"""
with cal as (select distinct trade_date d from curated.margin where trade_date >= '{SINCE}'),
wk as (select d, strftime(strptime(d,'%Y%m%d'),'%G-%V') w from cal),
m as (select trade_date d, sum(rzye)/1e8 rz, sum(rqye)/1e8 rq, sum(rzmre)/1e8 rzbuy from curated.margin
      where trade_date >= '{SINCE}' group by 1),
f as (select trade_date d,
        sum(buy_elg_amount - sell_elg_amount)/1e4 elg,
        sum(buy_lg_amount - sell_lg_amount)/1e4 lg,
        sum(buy_md_amount - sell_md_amount)/1e4 md,
        sum(buy_sm_amount - sell_sm_amount)/1e4 sm,
        sum(buy_sm_amount+buy_md_amount+buy_lg_amount+buy_elg_amount)/1e4 turnover
      from curated.moneyflow where trade_date >= '{SINCE}' group by 1),
i as (select trade_date d,
        max(case when ts_code='000300.SH' then close end) hs300,
        max(case when ts_code='000852.SH' then close end) zz1000,
        max(case when ts_code='399006.SZ' then close end) cyb
      from curated.index_daily where trade_date >= '{SINCE}' group by 1)
select w, max(wk.d) last_day,
  arg_max(rz, wk.d) rz_end, sum(rzbuy) rz_buy,
  sum(elg) elg, sum(lg) lg, sum(md) md, sum(sm) sm, avg(turnover) turnover_avg,
  arg_max(hs300, wk.d) hs300, arg_max(zz1000, wk.d) zz1000, arg_max(cyb, wk.d) cyb
from wk left join m using(d) left join f using(d) left join i using(d)
group by w order by w
"""
df = con.sql(q).df()
df["rz_chg"] = df["rz_end"].diff()
import pandas as pd
pd.set_option("display.width", 200)
print(df.round(0).to_string(index=False))
