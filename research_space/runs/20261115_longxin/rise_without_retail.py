"""一只在涨没有散户？ 隆鑫 quarterly order-size flows vs holder change; market-wide link between quarter return and holder change."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; C="603766.SH"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
pd.set_option("display.width",250); pd.set_option("display.max_columns",30)
f=q(f"""select case when trade_date<='20250930' then '2025Q3' when trade_date<='20251231' then '2025Q4' when trade_date<='20260331' then '2026Q1' when trade_date<='20260630' then '2026Q2' when trade_date<='20260930' then '2026Q3' else '2026Q4至今' end qtr,
 sum(buy_sm_amount-sell_sm_amount)/1e4 小单亿, sum(buy_md_amount-sell_md_amount)/1e4 中单亿, sum(buy_lg_amount-sell_lg_amount)/1e4 大单亿, sum(buy_elg_amount-sell_elg_amount)/1e4 特大单亿,
 sum(buy_sm_amount+sell_sm_amount+buy_md_amount+sell_md_amount+buy_lg_amount+sell_lg_amount+buy_elg_amount+sell_elg_amount)/2e4 成交亿
 from {s('moneyflow')} where ts_code='{C}' and trade_date>'20250630' group by 1 order by 1""")
p=q(f"select trade_date, close from {s('daily')} where ts_code='{C}' and trade_date in ('20250630','20250930','20251231','20260331','20260630','20260930','20261113') order by 1")
p["涨跌"]=p.close.pct_change().round(3)
print(f.round(2).to_string(index=False)); print(p.to_string(index=False))
# market-wide: quarter return vs holder change (cap-agnostic), 2022-2026
S="/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
F=pd.read_parquet(f"{S}/holders_v3_feats.parquet")[["ts_code","q","ret_q"]]
h=q(f"select ts_code,end_date q,arg_max(holder_num,ann_date) n from {s('events/stk_holdernumber')} where end_date>='20211231' group by 1,2").sort_values(["ts_code","q"])
h["y"]=h.groupby("ts_code").n.pct_change(); X=F.merge(h,on=["ts_code","q"]).dropna(subset=["y","ret_q"]); X=X[X.y.abs()<1]
X["rb"]=pd.qcut(X.groupby("q").ret_q.rank(pct=True),5,labels=["跌最多","2","3","4","涨最多"])
print("rank corr(ret_q, holder change) per quarter, median:",round(X.groupby("q").apply(lambda g:g.ret_q.rank().corr(g.y.rank())).median(),3))
print(X.groupby("rb",observed=True).agg(户数变化中位=("y","median"),户数降的比例=("y",lambda s:(s<0).mean()),季度涨幅中位=("ret_q","median")).round(3).to_string())
