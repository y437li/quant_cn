"""Quick profiles of 一拖股份 601038.SH and 思特威 688213.SH: business, segment mix, growth, valuation."""
import duckdb, pandas as pd
L="/Volumes/Treasury/quant_cn_lake/curated"; T=("601038.SH","688213.SH")
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
pd.set_option("display.width",250); pd.set_option("display.max_colwidth",300); pd.set_option("display.max_columns",30)
print(q(f"select ts_code, main_business, substr(introduction,1,260) intro from read_parquet('{L}/reference/stock_company.parquet') where ts_code in {T}").to_string(index=False))
print(q(f"select ts_code,end_date,bz_item,round(bz_sales/1e8,2) sales,round(bz_profit/bz_sales*100,1) gm from {s('documents/fina_mainbz_p')} where ts_code in {T} and end_date in ('20251231','20260630') order by ts_code,end_date,bz_sales desc").to_string(index=False))
print(q(f"""select ts_code,end_date, round(arg_max(total_revenue,ann_date)/1e8,2) rev, round(arg_max(n_income_attr_p,ann_date)/1e8,2) np from {s('fundamentals/income')} where ts_code in {T} and report_type='1' and end_date in ('20231231','20241231','20251231','20250930','20260930') group by 1,2 order by 1,2""").to_string(index=False))
print(q(f"select ts_code, close, pe_ttm, pb, dv_ttm, round(total_mv/1e4,0) mv from {s('daily_basic')} where trade_date=(select max(trade_date) from {s('daily_basic')}) and ts_code in {T}").to_string(index=False))
print(q(f"select ts_code, quarter, median(np)/1e4 np, count(distinct org_name) n from (select ts_code,org_name,quarter,arg_max(np,report_date) np from {s('analysts/report_rc')} where ts_code in {T} and report_date>='20260801' and quarter in ('2026Q4','2027Q4') group by 1,2,3) group by 1,2 order by 1,2").round(2).to_string(index=False))
