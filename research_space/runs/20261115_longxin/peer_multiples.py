"""隆鑫通用 vs 春风动力 vs 钱江摩托: price multiples, consensus forward PE, growth, profitability, cash, as of the latest lake date."""
import duckdb, pandas as pd
L="/Volumes/Treasury/quant_cn_lake/curated"; T=("603766.SH","603129.SH","000913.SZ")
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
pd.set_option("display.width",250); pd.set_option("display.max_columns",40)
d=q(f"select max(trade_date) d from {s('daily_basic')}").d[0]
b=q(f"select ts_code, close, pe_ttm, pb, ps_ttm, dv_ttm, total_mv/1e4 mv, total_share from {s('daily_basic')} where trade_date='{d}' and ts_code in {T}").set_index("ts_code")
inc=q(f"""select ts_code, end_date, arg_max(total_revenue,ann_date)/1e8 rev, arg_max(n_income_attr_p,ann_date)/1e8 np, arg_max(oper_cost,ann_date)/1e8 oc, arg_max(rd_exp,ann_date)/1e8 rd, arg_max(sell_exp,ann_date)/1e8 se, arg_max(operate_profit,ann_date)/1e8 op, arg_max(fin_exp,ann_date)/1e8 fin
 from {s('fundamentals/income')} where ts_code in {T} and end_date in ('20250930','20260930','20241231','20251231') and report_type='1' group by 1,2""")
p=inc.pivot(index="ts_code",columns="end_date")
r=pd.DataFrame(index=list(T))
r["9M营收yoy%"]=(p["rev"]["20260930"]/p["rev"]["20250930"]-1)*100
r["9M净利yoy%"]=(p["np"]["20260930"]/p["np"]["20250930"]-1)*100
r["2025净利yoy%"]=(p["np"]["20251231"]/p["np"]["20241231"]-1)*100
r["9M毛利率%"]=(1-p["oc"]["20260930"]/p["rev"]["20260930"])*100
r["9M净利率%"]=p["np"]["20260930"]/p["rev"]["20260930"]*100
r["研发/营收%"]=p["rd"]["20260930"]/p["rev"]["20260930"]*100
r["销售费/营收%"]=p["se"]["20260930"]/p["rev"]["20260930"]*100
ttm_np=p["np"]["20251231"]-p["np"]["20250930"]+p["np"]["20260930"]; ttm_rev=p["rev"]["20251231"]-p["rev"]["20250930"]+p["rev"]["20260930"]
fi=q(f"select ts_code, arg_max(roe,ann_date) roe9m from {s('fundamentals/fina_indicator')} where ts_code in {T} and end_date='20260930' group by 1").set_index("ts_code")
bs=q(f"""select ts_code, arg_max(money_cap,ann_date)/1e8 cash, (coalesce(arg_max(st_borr,ann_date),0)+coalesce(arg_max(lt_borr,ann_date),0)+coalesce(arg_max(bond_payable,ann_date),0))/1e8 debt, arg_max(total_hldr_eqy_exc_min_int,ann_date)/1e8 eq
 from {s('fundamentals/balancesheet')} where ts_code in {T} and end_date='20260930' group by 1""").set_index("ts_code")
cf=q(f"""select ts_code, end_date, arg_max(n_cashflow_act,ann_date)/1e8 ocf, arg_max(c_pay_acq_const_fiolta,ann_date)/1e8 capex, arg_max(depr_fa_coga_dpba,ann_date)/1e8 da from {s('fundamentals/cashflow')} where ts_code in {T} and end_date in ('20251231','20250930','20260930') group by 1,2""").pivot(index="ts_code",columns="end_date")
ttm_ocf=cf["ocf"]["20251231"]-cf["ocf"]["20250930"]+cf["ocf"]["20260930"]; ttm_capex=cf["capex"]["20251231"]-cf["capex"]["20250930"]+cf["capex"]["20260930"]
# consensus: latest report per broker since Q3 results, FY2026 / FY2027 net profit
rc=q(f"""select ts_code, quarter, median(np)/1e4 np_med, count(distinct org_name) n from (
  select ts_code, org_name, quarter, arg_max(np, report_date) np from {s('analysts/report_rc')} where ts_code in {T} and report_date>='20261015' and quarter in ('2026Q4','2027Q4') and np>0 group by 1,2,3) group by 1,2""").pivot(index="ts_code",columns="quarter")
out=pd.DataFrame(index=list(T))
out["名称"]=["隆鑫通用","春风动力","钱江摩托"]; out["股价"]=b.close; out["市值亿"]=b.mv
out["净现金亿"]=bs.cash-bs.debt; out["EV亿"]=out["市值亿"]-out["净现金亿"]
out["PE_ttm"]=b.pe_ttm; out["PE_26E"]=out["市值亿"]/rc["np_med"]["2026Q4"]; out["PE_27E"]=out["市值亿"]/rc["np_med"]["2027Q4"]
out["EV/净利ttm(扣现金)"]=out["EV亿"]/ttm_np
out["PB"]=b.pb; out["PS_ttm"]=b.ps_ttm; out["股息率ttm%"]=b.dv_ttm
out["FCF收益率%"]=(ttm_ocf-ttm_capex)/out["市值亿"]*100
out["27E净利增速%"]=(rc["np_med"]["2027Q4"]/rc["np_med"]["2026Q4"]-1)*100
out["PEG(27E)"]=out["PE_26E"]/out["27E净利增速%"]
out["覆盖券商"]=rc["n"]["2026Q4"]
out=out.join(r).join(fi)
out["ttm净利亿"]=ttm_np; out["26E净利亿"]=rc["np_med"]["2026Q4"]; out["27E净利亿"]=rc["np_med"]["2027Q4"]
print("as of",d); print(out.set_index("名称").T.round(2).to_string())
