"""隆鑫 marginal economics: capex vs D&A, fixed assets, operating invested capital, incremental ROIC and incremental margins, 2021-2025 (+ 9M 2026)."""
import duckdb, pandas as pd
L="/Volumes/Treasury/quant_cn_lake/curated"; C="603766.SH"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
E="('20201231','20211231','20221231','20231231','20241231','20251231','20260930','20250930')"
cf=q(f"select end_date, arg_max(n_cashflow_act,ann_date)/1e8 ocf, arg_max(c_pay_acq_const_fiolta,ann_date)/1e8 capex, arg_max(depr_fa_coga_dpba,ann_date)/1e8 da from {s('fundamentals/cashflow')} where ts_code='{C}' and end_date in {E} group by 1")
bs=q(f"""select end_date, arg_max(fix_assets,ann_date)/1e8 fa, arg_max(cip,ann_date)/1e8 cip, arg_max(money_cap,ann_date)/1e8 cash, arg_max(total_hldr_eqy_exc_min_int,ann_date)/1e8 eq,
 coalesce(arg_max(st_borr,ann_date),0)/1e8+coalesce(arg_max(lt_borr,ann_date),0)/1e8+coalesce(arg_max(bond_payable,ann_date),0)/1e8 debt,
 arg_max(accounts_receiv,ann_date)/1e8 ar, arg_max(inventories,ann_date)/1e8 inv, arg_max(contract_liab,ann_date)/1e8 cl from {s('fundamentals/balancesheet')} where ts_code='{C}' and end_date in {E} group by 1""")
inc=q(f"select end_date, arg_max(total_revenue,ann_date)/1e8 rev, arg_max(oper_cost,ann_date)/1e8 oc, arg_max(operate_profit,ann_date)/1e8 op, arg_max(n_income_attr_p,ann_date)/1e8 np, arg_max(fin_exp,ann_date)/1e8 fin from {s('fundamentals/income')} where ts_code='{C}' and end_date in {E} and report_type='1' group by 1")
fi=q(f"select end_date, arg_max(profit_dedt,ann_date)/1e8 dedt, arg_max(roic,ann_date) roic_ts from {s('fundamentals/fina_indicator')} where ts_code='{C}' and end_date in {E} group by 1")
d=cf.merge(bs,on="end_date").merge(inc,on="end_date").merge(fi,on="end_date").sort_values("end_date").set_index("end_date")
d["gp"]=d.rev-d.oc; d["gm%"]=d.gp/d.rev*100
d["nopat"]=(d.op+d.fin)*0.85                                # operating profit ex financial items, ~15% tax
d["ic"]=d["eq"]+d["debt"]-d["cash"]                                  # operating invested capital (cash-netted)
d["ppe"]=d.fa+d.cip
d["capex/da"]=d.capex/d.da; d["rev/ppe"]=d.rev/d.ppe
pd.set_option("display.width",250); pd.set_option("display.max_columns",40)
print(d[["rev","gp","gm%","np","dedt","nopat","ocf","capex","da","capex/da","ppe","rev/ppe","ar","inv","cash","eq","ic","roic_ts"]].round(2).to_string())
y=d.loc[[i for i in d.index if i.endswith("1231")]]
inc_=pd.DataFrame({"Δrev":y.rev.diff(),"Δgp":y.gp.diff(),"增量毛利率%":y.gp.diff()/y.rev.diff()*100,"Δnopat":y.nopat.diff(),"增量经营利润率%":y.nopat.diff()/y.rev.diff()*100,"Δppe":y.ppe.diff(),"capex":y.capex})
print(inc_.round(2).to_string())
print("2021→2025: Δrev",round(y.rev.iloc[-1]-y.loc['20211231'].rev,1),"Δnopat",round(y.nopat.iloc[-1]-y.loc['20211231'].nopat,2),"cum capex 22-25",round(y.capex.loc['20221231':].sum(),1),"cum D&A 22-25",round(y.da.loc['20221231':].sum(),1),"Δppe",round(y.ppe.iloc[-1]-y.loc['20211231'].ppe,1))
