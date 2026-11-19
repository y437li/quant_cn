"""Breadth and volume of the decline, last 25 sessions: advancers / decliners, share down > 5%, limit-ups / downs,
whole-market turnover (亿) vs its 60- and 250-session medians, and 中证1000 constituents' turnover share."""
import duckdb, pandas as pd
L="/Volumes/Treasury/quant_cn_lake/curated"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
D=duckdb.sql(f"""select trade_date, count(*) n, sum((pct_chg>0)::int) up, sum((pct_chg<0)::int) dn,
  sum((pct_chg<=-5)::int) dn5, sum((pct_chg>=5)::int) up5, sum(amount)/1e5 amt_yi
  from {s('daily')} where trade_date>='20250901' group by 1 order by 1""").df().set_index("trade_date")
LIM=duckdb.sql(f"""select l.trade_date, sum((d.close<=l.down_limit)::int) ld, sum((d.close>=l.up_limit)::int) lu
  from {s('stk_limit')} l join {s('daily')} d using(ts_code,trade_date) where l.trade_date>='20251001' group by 1""").df().set_index("trade_date")
D=D.join(LIM)
D["amt_vs60"]=D.amt_yi/D.amt_yi.rolling(60).median(); D["amt_vs250"]=D.amt_yi/D.amt_yi.rolling(250,min_periods=200).median()
I=duckdb.sql("select trade_date,close,pct_chg from read_parquet('/Volumes/Treasury/quant_cn_lake/curated/reference/index_daily.parquet') where ts_code='000852.SH'").df().set_index("trade_date")
D=D.join(I.pct_chg.rename("csi1000"))
T=D.tail(25).copy(); T["dn_share"]=T.dn/T.n
print(T[["csi1000","up","dn","dn_share","dn5","up5","ld","lu","amt_yi","amt_vs60","amt_vs250"]].round(2).to_string())
w=D.tail(20); print("20d: down days amt", round(w[w.csi1000<0].amt_yi.mean()), "up days", round(w[w.csi1000>0].amt_yi.mean()))
print("peak amt last 250", D.amt_yi.tail(250).max().round(), D.amt_yi.tail(250).idxmax())
