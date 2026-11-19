"""宗申动力 001696.SZ: chips, holders, gauge, valuation, segment mix, growth, consensus, monthly price."""
import duckdb, pandas as pd
L="/Volumes/Treasury/quant_cn_lake/curated"; C="001696.SZ"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
pd.set_option("display.width",250); pd.set_option("display.max_columns",30); pd.set_option("display.max_rows",80)
m=pd.read_csv("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_clean_chips/all_chip_metrics_20261113.csv").set_index("ts_code")
print(m.loc[[C]].T.to_string())
cy=q(f"select * from {s('cyq_perf')} where ts_code='{C}' and trade_date='20261113'"); print(cy.T.to_string())
h=q(f"select end_date, arg_max(holder_num,ann_date) n from {s('events/stk_holdernumber')} where ts_code='{C}' and end_date>='20241231' group by 1 order by 1"); h["chg"]=h.n.pct_change().round(3); print(h.to_string(index=False))
print(q(f"select substr(trade_date,1,6) m, last(close order by trade_date) cl, last(pe_ttm order by trade_date) pe, last(pb order by trade_date) pb, last(dv_ttm order by trade_date) dv, avg(turnover_rate_f) tov from {s('daily_basic')} where ts_code='{C}' and trade_date>='20250101' group by 1 order by 1").round(2).to_string(index=False))
b=q(f"select trade_date, pe_ttm from {s('daily_basic')} where ts_code='{C}' and trade_date>='20211113' and pe_ttm>0"); print("PE 5y pct of now:", round((b.pe_ttm<b.pe_ttm.iloc[-1]).mean(),2), "median", round(b.pe_ttm.median(),1))
print(q(f"select end_date,bz_item,round(bz_sales/1e8,2) sales,round(bz_profit/bz_sales*100,1) gm from {s('documents/fina_mainbz_p')} where ts_code='{C}' and end_date in ('20251231','20260630') order by end_date,bz_sales desc").to_string(index=False))
i=q(f"select end_date, round(arg_max(total_revenue,ann_date)/1e8,1) rev, round(arg_max(n_income_attr_p,ann_date)/1e8,2) np, round(arg_max(invest_income,ann_date)/1e8,2) inv from {s('fundamentals/income')} where ts_code='{C}' and report_type='1' and end_date in ('20221231','20231231','20241231','20250930','20251231','20260930') group by 1 order by 1"); print(i.to_string(index=False))
print(q(f"select end_date, arg_max(profit_dedt,ann_date)/1e8 dedt, arg_max(roe,ann_date) roe, arg_max(grossprofit_margin,ann_date) gm from {s('fundamentals/fina_indicator')} where ts_code='{C}' and end_date in ('20251231','20250930','20260930') group by 1 order by 1").round(2).to_string(index=False))
print(q(f"select quarter, median(np)/1e4 np, count(distinct org_name) n from (select org_name,quarter,arg_max(np,report_date) np from {s('analysts/report_rc')} where ts_code='{C}' and report_date>='20260701' and quarter in ('2026Q4','2027Q4') group by 1,2) group by 1").round(2).to_string(index=False))
print(q(f"select trade_date, rzye/1e8 rz from {s('margin_detail')} where ts_code='{C}' and trade_date in ('20260130','20260630','20260930','20261112')").round(2).to_string(index=False))
