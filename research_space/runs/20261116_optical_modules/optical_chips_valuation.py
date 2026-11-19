"""中际旭创 300308.SZ / 新易盛 300502.SZ: chips (holders, RetailGauge, cost distribution, margin, top holders, insider trades)
and valuation (PE history percentiles, consensus 2026E/2027E from report_rc, results), as of 2026-11-13."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; M="/Volumes/Treasury/quant_cn_lake/meta/runs"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
pd.set_option("display.width",250); pd.set_option("display.max_columns",30)
gs=pd.read_parquet(f"{M}/holder_nowcast/holders_forecast_q4.parquet").pct
gp=pd.read_parquet(f"{M}/research/20261115_gauge_intraquarter/gauge_paths.parquet")
for C,N in [("300308.SZ","中际旭创"),("300502.SZ","新易盛")]:
    print(f"\n######## {N} {C}")
    print(q(f"select end_date, arg_max(holder_num,ann_date) n from {s('events/stk_holdernumber')} where ts_code='{C}' and end_date>='20250101' group by 1 order by 1").assign(chg=lambda d:d.n.pct_change().round(3)).to_string(index=False))
    g=gp[(gp.ts_code==C)&(gp.q>="20260630")].sort_values("asof")[["q","off","asof","pct"]]; print("gauge path:", [(r.asof,round(r.pct,2)) for r in g.itertuples()], "| 11-12 snapshot", round(gs.get(C,np.nan),2))
    print(q(f"select substr(trade_date,1,6) m, last(close order by trade_date) cl, last(pe_ttm order by trade_date) pe, last(pb order by trade_date) pb, last(total_mv order by trade_date)/1e4 mv, avg(turnover_rate_f) tov from {s('daily_basic')} where ts_code='{C}' and trade_date>='20251101' group by 1 order by 1").round(2).to_string(index=False))
    h=q(f"select trade_date, pe_ttm from {s('daily_basic')} where ts_code='{C}' and trade_date>='20211113' and pe_ttm>0")
    cur=h.pe_ttm.iloc[-1] if len(h) else np.nan; h=h.sort_values("trade_date"); cur=h.pe_ttm.iloc[-1]
    print(f"PE TTM now {cur:.1f}; 5y pct rank {(h.pe_ttm<cur).mean():.2f}; 5y median {h.pe_ttm.median():.1f}; 10/90% {h.pe_ttm.quantile(.1):.1f}/{h.pe_ttm.quantile(.9):.1f}")
    print(q(f"select end_date, arg_max(total_revenue,ann_date)/1e8 rev, arg_max(n_income_attr_p,ann_date)/1e8 np from {s('fundamentals/income')} where ts_code='{C}' and end_date>='20250101' group by 1 order by 1").round(2).to_string(index=False))
    print(q(f"select end_date, arg_max(grossprofit_margin,ann_date) gm, arg_max(or_yoy,ann_date) rev_yoy, arg_max(netprofit_yoy,ann_date) np_yoy, arg_max(roe,ann_date) roe from {s('fundamentals/fina_indicator')} where ts_code='{C}' and end_date>='20250630' group by 1 order by 1").round(1).to_string(index=False))
    rc=q(f"select report_date, org_name, quarter, np from {s('analysts/report_rc')} where ts_code='{C}' and report_date>='20260901' and np is not null and quarter in ('2026Q4','2027Q4','2028Q4')")
    rc=rc.sort_values("report_date").groupby(["org_name","quarter"]).tail(1)
    print("consensus (latest per broker since 09-01, 亿):", rc.groupby("quarter").np.agg(['count','median','min','max']).div([1,1e4,1e4,1e4]).round(1).to_dict('index'))
    print(q(f"select c.trade_date, b.close, c.winner_rate, c.cost_5pct, c.cost_15pct, c.cost_50pct, c.cost_85pct, c.cost_95pct from {s('cyq_perf')} c join {s('daily_basic')} b using(ts_code,trade_date) where c.ts_code='{C}' and c.trade_date in ('20260630','20260930','20261030','20261113') order by 1").to_string(index=False))
    print(q(f"select trade_date, round(rzye/1e8,1) rz from {s('margin_detail')} where ts_code='{C}' and trade_date in ('20260130','20260430','20260630','20260831','20260930','20261030','20261112','20261113') order by 1").to_string(index=False))
    print(q(f"select end_date, holder_name, round(hold_amount/1e4) wan from {s('events/top10_floatholders')} where ts_code='{C}' and end_date in ('20260630','20260930') order by end_date, hold_amount desc").pivot_table(index="holder_name",columns="end_date",values="wan").fillna(0).sort_values("20260930",ascending=False).to_string())
    print(q(f"select ann_date, holder_name, in_de, round(change_vol/1e4,1) wan, avg_price from {s('events/stk_holdertrade')} where ts_code='{C}' and ann_date>='20260101' order by ann_date").to_string(index=False))
    print(q(f"select float_date, round(sum(float_share)/1e4,1) wan from {s('events/share_float')} where ts_code='{C}' and float_date>='20261101' and float_date<='20270630' group by 1 order by 1").to_string(index=False))
    print(q(f"select substr(trade_date,1,6) m, round(sum(buy_elg_amount+buy_lg_amount-sell_elg_amount-sell_lg_amount)/1e4,1) big_yi, round(sum(buy_sm_amount-sell_sm_amount)/1e4,1) sm_yi from {s('moneyflow')} where ts_code='{C}' and trade_date>='20260801' group by 1 order by 1").to_string(index=False))
    print(q(f"select factor, round(exposure,2) e from {s('../derived/risk_exposure')} where ts_code='{C}' and trade_date='20261113' and factor in ('beta','momentum','usd_sensitivity','ai_dc_sensitivity','us_sensitivity','size','earnings_yield','growth')").to_string(index=False))
