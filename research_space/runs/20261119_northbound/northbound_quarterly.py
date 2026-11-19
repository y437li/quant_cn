"""Northbound (沪深股通) quarterly active flow since 2024 from curated.hk_hold.

Since 2024-08-19 HKEX discloses northbound holdings only at quarter ends, so the flow is
estimated per quarter as sum((vol_t - vol_{t-1}) * close_t). 2026-06-30 rows carry
mis-mapped codes (ETFs, e.g. CCASS 31xxx, mapped to 300xxx/603xxx), so rows are kept only
when the CCASS code range matches the board (SH main 9xxxx, STAR 30xxx, SZ 7xxxx).
"""

import duckdb

LAKE = "/Volumes/Treasury/quant_cn_lake/curated"
QS = ("20231229", "20240628", "20240930", "20241231", "20250331", "20250630", "20250930",
      "20251231", "20260331", "20260630", "20260930")
c = duckdb.connect()
h = f"read_parquet('{LAKE}/hk_hold/**/*.parquet', hive_partitioning=1)"
d = f"read_parquet('{LAKE}/daily/**/*.parquet', hive_partitioning=1)"
w = f"read_parquet('{LAKE}/index_weight/**/*.parquet', hive_partitioning=1)"
c.sql(f"""create table hh as select trade_date, ts_code, vol from {h}
 where exchange in ('SH','SZ') and trade_date in {QS} and name not like '%ETF%' and (
  (ts_code like '688%' and cast(code as int) between 30000 and 30999)
  or (ts_code like '6%' and ts_code not like '688%' and cast(code as int) >= 90000)
  or (ts_code similar to '(0|3).*' and cast(code as int) between 70000 and 79999))""")
c.sql(f"create table px as select ts_code, trade_date, close from {d} where trade_date in {QS}")
for name, code in (("zz", "000852.SH"), ("hs", "000300.SH")):
    c.sql(f"""create table {name} as select con_code ts_code from {w} where index_code='{code}'
     and trade_date=(select max(trade_date) from {w} where index_code='{code}')""")
print(c.sql("""
with a as (select h.*, p.close from hh h join px p using(ts_code, trade_date)),
b as (select *, lag(vol) over (partition by ts_code order by trade_date) pv from a)
select trade_date, round(sum(vol*close)/1e8) mv_yi, round(sum((vol-coalesce(pv,0))*close)/1e8) flow_yi,
 round(sum(case when ts_code in (select * from hs) then (vol-coalesce(pv,0))*close end)/1e8) hs300,
 round(sum(case when ts_code in (select * from zz) then (vol-coalesce(pv,0))*close end)/1e8) zz1000
from b where trade_date > '20231229' group by 1 order by 1""").df().to_string())
