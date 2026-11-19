"""Has the sell-off had its capitulation (止损盘砸完) yet? Market-wide margin financing balance (margin, both exchanges; 2026-11-06
lacks one exchange), daily A-share turnover and limit-down / limit-up counts (daily vs stk_limit) since 2026-10, monthly average
turnover in 2026, and the same counts on past panic lows (2024-02-05, 2024-10-09, 2025-04-07) for comparison."""
import duckdb, pandas as pd
L = "/Volumes/Treasury/quant_cn_lake/curated"; r = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
pd.set_option("display.width", 200)
print(duckdb.sql(f"select trade_date, round(sum(rzye)/1e8) rz_yi from {r('margin')} where trade_date >= '20260601' group by 1 order by 1").df().tail(15).to_string(index=False))
q = lambda w: duckdb.sql(f"""select d.trade_date, round(sum(d.amount)/1e5) amt_yi, sum(case when d.close <= l.down_limit then 1 else 0 end) limdown,
  sum(case when d.close >= l.up_limit then 1 else 0 end) limup from {r('daily')} d left join {r('stk_limit')} l using (ts_code, trade_date) where {w} group by 1 order by 1""").df()
print(q("d.trade_date >= '20261001'").to_string(index=False))
print(q("d.trade_date in ('20240202','20240205','20240206','20241008','20241009','20250407','20250408','20260730','20261030')").to_string(index=False))
print(duckdb.sql(f"select substr(trade_date,1,6) m, round(sum(amount)/1e5/count(distinct trade_date)) avg_amt_yi from {r('daily')} where trade_date >= '20260101' group by 1 order by 1").df().to_string(index=False))
