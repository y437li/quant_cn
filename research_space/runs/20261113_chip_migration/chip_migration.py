"""How a chip distribution migrates down when the price stays below it (argv code, default 巨人网络
002558.SZ): weekly close, winner rate and cost bands (Tushare cyq_perf, live), turnover since the
first close below the 5% cost line, large / small order flow, holders, RetailGauge."""
import sys
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

CODE = sys.argv[1] if len(sys.argv) > 1 else "002558.SZ"
c = Config.load(Path(".")); LAKE = Path(c.lake.root)
OUT = LAKE / "meta/runs/research/20261113_chip_migration"
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
cy = TushareClient(c.tushare, Clock()).query("cyq_perf", {"ts_code": CODE, "start_date": "20260501", "end_date": "20261113"}, [])
d = q(f"""SELECT d.trade_date, d.close, b.turnover_rate_f AS tov,
          (m.buy_lg_amount + m.buy_elg_amount - m.sell_lg_amount - m.sell_elg_amount) / 1e4 AS lg,
          (m.buy_sm_amount - m.sell_sm_amount) / 1e4 AS sm
          FROM {src('daily')} d JOIN {src('daily_basic')} b USING (ts_code, trade_date) LEFT JOIN {src('moneyflow')} m USING (ts_code, trade_date)
          WHERE d.ts_code = '{CODE}' AND d.trade_date >= '20260501' ORDER BY d.trade_date""")
d = d.merge(cy[["trade_date", "winner_rate", "cost_5pct", "cost_15pct", "cost_50pct", "cost_85pct", "cost_95pct"]], on="trade_date", how="left")
below = d[d["close"] < d["cost_5pct"]]
first = below["trade_date"].iloc[0] if not below.empty else None
if first:
    d["tov_since"] = d["tov"].where(d["trade_date"] >= first, 0).cumsum()
d["w"] = pd.to_datetime(d["trade_date"])
wk = d.set_index("w").resample("W-FRI").agg({"close": "last", "winner_rate": "last", "cost_5pct": "last", "cost_15pct": "last",
                                              "cost_50pct": "last", "cost_85pct": "last", "tov": "sum", "lg": "sum", "sm": "sum",
                                              **({"tov_since": "last"} if first else {})}).dropna(subset=["close"])
pd.set_option("display.width", 220)
print(CODE, "first close below the 5% cost line:", first)
print(wk.round(2).tail(26).to_string())
hn = q(f"SELECT end_date, arg_max(holder_num, ann_date) AS n FROM {src('events/stk_holdernumber')} WHERE ts_code = '{CODE}' AND end_date >= '20250630' GROUP BY 1 ORDER BY 1")
print("\nholders:", " ".join(f"{e[2:6]}:{n / 1e4:.1f}万" for e, n in zip(hn["end_date"], hn["n"])))
g = pd.read_parquet(LAKE / "meta/runs/holder_nowcast/holders_forecast_q4.parquet").loc[CODE]
print("RetailGauge", round(float(g["pct"]), 3), "Q4 holders median", f"{g['50%']:+.1%}", "market", f"{g['mk_q4']:+.1%}")
wk.to_csv(OUT / f"weekly_{CODE}.csv")
