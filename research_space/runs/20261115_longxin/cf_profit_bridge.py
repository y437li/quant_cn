"""春风 single-quarter profit bridge (revenue, GP, expenses, FX via fin_exp, impairments, non-recurring) and announcement scan for legal / guarantee / regulatory risk."""
import duckdb, pandas as pd, re
L="/Volumes/Treasury/quant_cn_lake/curated"; C="603129.SH"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
pd.set_option("display.width",250); pd.set_option("display.max_columns",30); pd.set_option("display.max_rows",300); pd.set_option("display.max_colwidth",90)
inc=q(f"""select end_date, arg_max(total_revenue,ann_date) rev, arg_max(oper_cost,ann_date) ocost, arg_max(sell_exp,ann_date) sell, arg_max(admin_exp,ann_date) adm, arg_max(rd_exp,ann_date) rd,
 arg_max(fin_exp,ann_date) fin, arg_max(invest_income,ann_date) inv, arg_max(assets_impair_loss,ann_date) aimp, arg_max(credit_impa_loss,ann_date) cimp, arg_max(non_oper_income,ann_date)-arg_max(non_oper_exp,ann_date) nonop,
 arg_max(total_profit,ann_date) tp, arg_max(income_tax,ann_date) tax, arg_max(minority_gain,ann_date) mino, arg_max(n_income_attr_p,ann_date) np from {s('fundamentals/income')} where ts_code='{C}' and end_date>='20221231' and report_type='1' group by 1 order by 1""")
fi=q(f"select end_date, arg_max(profit_dedt,ann_date) dedt from {s('fundamentals/fina_indicator')} where ts_code='{C}' and end_date>='20221231' group by 1 order by 1")
d=inc.merge(fi,on="end_date").set_index("end_date")
d.index=d.index.astype(str)
# single quarter = YTD minus previous YTD in same year
sq=d.copy()
for i,e in enumerate(d.index):
    if e[4:]!="0331":
        p=e[:4]+{"0630":"0331","0930":"0630","1231":"0930"}[e[4:]]
        if p in d.index: sq.loc[e]=d.loc[e]-d.loc[p]
        else: sq.loc[e]=float("nan")
sq=sq[sq.index>="20240331"]/1e8
sq["毛利率%"]=(1-sq.ocost/sq.rev)*100
out=sq[["rev","毛利率%","sell","adm","rd","fin","inv","aimp","cimp","nonop","tp","mino","np","dedt"]].round(2)
out["np_yoy%"]=(sq.np/sq.np.shift(4)-1).mul(100).round(0); out["dedt_yoy%"]=(sq.dedt/sq.dedt.shift(4)-1).mul(100).round(0)
print("== 单季 (亿) =="); print(out.to_string())
fy=d[d.index.str.endswith("1231")][["rev","np","dedt"]]/1e8; print("== 年度 =="); print(fy.round(2).to_string())
bs=q(f"select * from {s('fundamentals/balancesheet')} where ts_code='{C}' and end_date='20260930' limit 1")
print("bs cols sample:", [c for c in bs.columns][:60])
