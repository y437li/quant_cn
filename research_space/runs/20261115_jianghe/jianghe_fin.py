"""江河集团 601886.SH: segments, cash flow, balance sheet quality, Q3 single-quarter bridge, holder-trade detail, Aug-2026 move."""
import duckdb, pandas as pd
L="/Volumes/Treasury/quant_cn_lake/curated"; C="601886.SH"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
pd.set_option("display.width",250); pd.set_option("display.max_columns",40); pd.set_option("display.max_rows",120)
print("== 主营构成 ==");print(q(f"select end_date, bz_item, max(bz_sales)/1e8 rev, max(bz_profit)/1e8 gp from {s('documents/fina_mainbz_p')} where ts_code='{C}' and end_date>='20241231' group by 1,2 order by 1,3 desc").round(2).to_string(index=False))
print("== 利润表细项（单季拆分前，累计） ==")
inc=q(f"select end_date, arg_max(total_revenue,ann_date)/1e8 rev, arg_max(oper_cost,ann_date)/1e8 ocost, arg_max(sell_exp,ann_date)/1e8 sell, arg_max(admin_exp,ann_date)/1e8 adm, arg_max(rd_exp,ann_date)/1e8 rd, arg_max(fin_exp,ann_date)/1e8 fin, arg_max(assets_impair_loss,ann_date)/1e8 aimp, arg_max(credit_impa_loss,ann_date)/1e8 cimp, arg_max(invest_income,ann_date)/1e8 inv, arg_max(total_profit,ann_date)/1e8 tp, arg_max(income_tax,ann_date)/1e8 tax, arg_max(minority_gain,ann_date)/1e8 mino, arg_max(n_income_attr_p,ann_date)/1e8 np from {s('fundamentals/income')} where ts_code='{C}' and end_date>='20240101' group by 1 order by 1")
print(inc.round(2).to_string(index=False))
print("== 扣非 ==");print(q(f"select end_date, arg_max(profit_dedt,ann_date)/1e8 dedt, arg_max(debt_to_assets,ann_date) dta from {s('fundamentals/fina_indicator')} where ts_code='{C}' and end_date>='20240101' group by 1 order by 1").round(2).to_string(index=False))
print("== 现金流 ==");print(q(f"select end_date, arg_max(n_cashflow_act,ann_date)/1e8 ocf, arg_max(free_cashflow,ann_date)/1e8 fcf, arg_max(c_pay_acq_const_fiolta,ann_date)/1e8 capex from {s('fundamentals/cashflow')} where ts_code='{C}' and end_date>='20220101' group by 1 order by 1").round(2).to_string(index=False))
print("== 资产负债 ==");print(q(f"select end_date, arg_max(money_cap,ann_date)/1e8 cash, arg_max(accounts_receiv,ann_date)/1e8 ar, arg_max(inventories,ann_date)/1e8 inv, arg_max(lt_rec,ann_date)/1e8 ltrec, arg_max(st_borr,ann_date)/1e8 stb, arg_max(lt_borr,ann_date)/1e8 ltb, arg_max(bond_payable,ann_date)/1e8 bond, arg_max(goodwill,ann_date)/1e8 gw, arg_max(contract_liab,ann_date)/1e8 cl, arg_max(total_hldr_eqy_exc_min_int,ann_date)/1e8 eq, arg_max(total_assets,ann_date)/1e8 ta from {s('fundamentals/balancesheet')} where ts_code='{C}' and end_date>='20231231' group by 1 order by 1").round(2).to_string(index=False))
print("== 增减持明细 ==");print(q(f"select * from {s('events/stk_holdertrade')} where ts_code='{C}' and ann_date>='20240101' order by ann_date").to_string(index=False))
print("== 股本 ==");print(q(f"select trade_date,total_share/1e4 total_yi, float_share/1e4 float_yi from {s('daily_basic')} where ts_code='{C}' and trade_date='20261113'").to_string(index=False))
print("== 2026-07/08 日线大涨 ==");print(q(f"select d.trade_date,d.close,d.pct_chg,b.turnover_rate_f tov from {s('daily')} d join {s('daily_basic')} b using(ts_code,trade_date) where d.ts_code='{C}' and d.trade_date between '20260720' and '20260915' and abs(d.pct_chg)>=4 order by 1").to_string(index=False))
print("== 股价 vs 行业(装修装饰)对比 ==")
