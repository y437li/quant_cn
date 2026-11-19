"""Buy-level inputs for 隆鑫通用 and 春风动力: price lows, chip cost percentiles, 5y PE / PB percentiles, PE on 2026E/2027E consensus, dividend-yield-implied prices."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; T=("603766.SH","603129.SH")
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
for c in T:
    b=q(f"select trade_date, close, pe_ttm, pb, dv_ttm, total_share from {s('daily_basic')} where ts_code='{c}' and trade_date>='20211113' order by 1")
    last=b.iloc[-1]; y1=b[b.trade_date>='20251113']; m3=b[b.trade_date>='20260813']
    cy=q(f"select * from {s('cyq_perf')} where ts_code='{c}' and trade_date=(select max(trade_date) from {s('cyq_perf')})").iloc[0]
    rc=q(f"select quarter, median(np) np, median(eps) eps from (select org_name,quarter,arg_max(np,report_date) np, arg_max(eps,report_date) eps from {s('analysts/report_rc')} where ts_code='{c}' and report_date>='20261015' and quarter in ('2026Q4','2027Q4') group by 1,2) group by 1").set_index("quarter")
    sh=last.total_share*1e4
    eps26=rc.np["2026Q4"]*1e4/sh; eps27=rc.np["2027Q4"]*1e4/sh
    pe=b.pe_ttm.dropna(); pe=pe[pe>0]
    print(f"\n==== {c} close {last.close} ({last.trade_date})")
    print(f"1y low {y1.close.min()} ({y1.loc[y1.close.idxmin(),'trade_date']}), 1y high {y1.close.max()}, 3m low {m3.close.min()} ({m3.loc[m3.close.idxmin(),'trade_date']})")
    print("chip cost 5/15/50/85/95:",cy.cost_5pct,cy.cost_15pct,cy.cost_50pct,cy.cost_85pct,cy.cost_95pct,"winner",cy.winner_rate)
    print("PE ttm now %.1f | 5y pct10/25/50/75: %s"%(last.pe_ttm, np.percentile(pe,[10,25,50,75]).round(1)))
    print("PB now %.2f | 5y pct10/25/50: %s"%(last.pb, np.percentile(b.pb.dropna(),[10,25,50]).round(2)))
    print("EPS 26E %.2f 27E %.2f | price at 27E PE 10/11/12/13/14/15/16: %s"%(eps26,eps27,[round(eps27*k,1) for k in (10,11,12,13,14,15,16)]))
    print("price at ttm PE 5y pct10/25:", [round(last.close/last.pe_ttm*x,1) for x in np.percentile(pe,[10,25])])
