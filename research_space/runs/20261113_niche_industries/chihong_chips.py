"""驰宏锌锗 (600497.SH) 筹码 time series as of 2026-11-13, read from the curated parquet files
(the catalog may be locked by another writer) plus live Tushare cyq_perf; RetailGauge from the
holder_nowcast prototype output."""
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

CODE, AS_OF = "600497.SH", "20261113"
c = Config.load(Path("."))
L = Path(c.lake.root) / "curated"
OUT = Path(c.lake.root) / "meta/runs/research/20261113_niche_industries"
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 40)
src = lambda p: f"read_parquet('{L}/{p}/**/*.parquet', hive_partitioning=true, union_by_name=true)"

hn = duckdb.sql(f"""SELECT end_date, ann_date, holder_num FROM {src('events/stk_holdernumber')}
                    WHERE ts_code = '{CODE}' AND ann_date <= '{AS_OF}' ORDER BY end_date""").df()
hn = hn.drop_duplicates("end_date", keep="last").tail(9)
hn["chg_pct"] = (hn["holder_num"].pct_change() * 100).round(1)
print("股东户数"); print(hn.tail(8).to_string(index=False))

fh = duckdb.sql(f"""SELECT end_date, holder_name, hold_amount, hold_ratio FROM {src('events/top10_floatholders')}
                    WHERE ts_code = '{CODE}' AND end_date >= '20260331' AND ann_date <= '{AS_OF}'""").df()
fh = fh.drop_duplicates(["end_date", "holder_name"], keep="last")
piv = fh.pivot_table(index="holder_name", columns="end_date", values="hold_ratio").round(3)
piv["chg_q3"] = (piv.get("20260930", 0) - piv.get("20260630", 0)).round(3)
print("\n前十大流通股东（持股比例 %）"); print(piv.sort_values("chg_q3").to_string())

nb = duckdb.sql(f"""SELECT trade_date, ratio FROM {src('hk_hold')}
                    WHERE ts_code = '{CODE}' AND trade_date >= '20240101' ORDER BY trade_date""").df()
print("\n北向持股比例 %（披露日）"); print(nb.tail(8).to_string(index=False))

mg = duckdb.sql(f"""SELECT trade_date, rzye / 1e8 AS rzye_yi, rqye / 1e8 AS rqye_yi FROM {src('margin_detail')}
                    WHERE ts_code = '{CODE}' AND trade_date >= '20260501' ORDER BY trade_date""").df()
mg["d"] = pd.to_datetime(mg["trade_date"])
print("\n融资余额（亿，月末）"); print(mg.set_index("d").resample("ME").last()[["rzye_yi", "rqye_yi"]].round(2).to_string())

mf = duckdb.sql(f"""SELECT trade_date, (buy_lg_amount + buy_elg_amount - sell_lg_amount - sell_elg_amount) / 1e4 AS lg_net_yi,
                    (buy_sm_amount - sell_sm_amount) / 1e4 AS sm_net_yi
                    FROM {src('moneyflow')} WHERE ts_code = '{CODE}' AND trade_date >= '20260801' ORDER BY trade_date""").df()
mf["d"] = pd.to_datetime(mf["trade_date"])
wk = mf.set_index("d")[["lg_net_yi", "sm_net_yi"]].resample("W-FRI").sum().round(2)
print("\n每周资金（亿；大单 = 大单 + 特大单）"); print(wk.tail(14).to_string())

cl = TushareClient(c.tushare, Clock())
cy = cl.query("cyq_perf", {"ts_code": CODE, "start_date": "20260501", "end_date": AS_OF}, [])
cy = cy.sort_values("trade_date")
cy["d"] = pd.to_datetime(cy["trade_date"])
cols = ["winner_rate", "cost_5pct", "cost_15pct", "cost_50pct", "cost_85pct", "cost_95pct", "weight_avg"]
print("\n获利盘与成本分布（周末）"); print(cy.set_index("d").resample("W-FRI").last()[cols].dropna().tail(14).round(2).to_string())
px = duckdb.sql(f"""SELECT trade_date, close FROM {src('daily')} WHERE ts_code = '{CODE}' AND trade_date = '{AS_OF}'""").df()
print("\nclose", px["close"].iloc[0] if not px.empty else None)

g = pd.read_parquet(Path(c.lake.root) / "meta/runs/holder_nowcast/holders_forecast_q4.parquet").loc[CODE]
print("\n散户温度计（RetailGauge v5，预测 2026Q4 股东户数）"); print(g.round(4).to_string())
for name, frame in (("hn", hn), ("float10", piv), ("north", nb), ("margin", mg), ("flow_weekly", wk), ("cyq", cy)):
    frame.to_csv(OUT / f"chihong_{name}.csv")
