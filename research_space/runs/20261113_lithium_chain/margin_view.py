"""融资融券 of one stock (argv code, default 湖南裕能 301358.SZ) as of 2026-11-13: monthly and recent daily
financing / short-selling flows, balances as % of float market cap, and the FIFO forced-liquidation
ladder (calculation.MarginLadderEstimator, plan 09) with the debt forced at each further drawdown."""
import sys
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.calculation.margin_ladder_estimator import MarginLadderEstimator
from quant_cn.core.config import Config

CODE = sys.argv[1] if len(sys.argv) > 1 else "301358.SZ"
LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261113_lithium_chain"
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
det = q(f"SELECT * FROM {src('margin_detail')} WHERE ts_code = '{CODE}' AND trade_date >= '20250601' ORDER BY trade_date")
px = q(f"""SELECT d.ts_code, d.trade_date, d.close, b.circ_mv FROM {src('daily')} d JOIN {src('daily_basic')} b USING (ts_code, trade_date)
          WHERE d.ts_code = '{CODE}' AND d.trade_date >= '20250601'""")
df = det.merge(px, on=["ts_code", "trade_date"], how="left")
df["rz_net"] = (df["rzmre"] - df["rzche"]) / 1e8
df["rz_pct_float"] = df["rzye"] / (df["circ_mv"] * 1e4) * 100
df["d"] = pd.to_datetime(df["trade_date"])
m = df.set_index("d").resample("ME").agg({"close": "last", "rzye": "last", "rzmre": "sum", "rzche": "sum", "rqye": "last",
                                          "rqmcl": "sum", "rz_pct_float": "last"})
m = pd.DataFrame({"收盘": m["close"], "融资余额亿": m["rzye"] / 1e8, "融资买入亿": m["rzmre"] / 1e8, "融资偿还亿": m["rzche"] / 1e8,
                  "净增亿": (m["rzmre"] - m["rzche"]) / 1e8, "占流通市值%": m["rz_pct_float"],
                  "融券余额万元": m["rqye"] / 1e4, "融券卖出万股": m["rqmcl"] / 1e4})
pd.set_option("display.width", 200)
print(CODE, "按月"); print(m.round(2).to_string())
last = df.tail(10)[["trade_date", "close", "rzye", "rzmre", "rzche", "rqye", "rqmcl"]].assign(
    rzye=lambda d: d["rzye"] / 1e8, rzmre=lambda d: d["rzmre"] / 1e8, rzche=lambda d: d["rzche"] / 1e8, rqye=lambda d: d["rqye"] / 1e4,
    rqmcl=lambda d: d["rqmcl"] / 1e4)
print("\n最近 10 天（融资亿、融券余额万元、融券卖出万股）"); print(last.round(2).to_string(index=False))

as_of = str(df.dropna(subset=["close"])["trade_date"].max())
est = MarginLadderEstimator()
ladder = est.compute_ladder(det[["ts_code", "trade_date", "rzye", "rzmre", "rzche"]], px[["ts_code", "trade_date", "close"]], as_of)
price = float(df.loc[df["trade_date"] == as_of, "close"].iloc[0])
print(f"\n强平阶梯（{as_of} 收 {price}；平仓价 = 买入价 × 1.3 / (1 + 1.0)）")
print("ladder columns:", list(ladder.columns))
amt = [c for c in ladder.columns if "debt" in c or "amount" in c][0]
liq = [c for c in ladder.columns if "liq" in c][0]
lad = ladder.assign(debt_yi=ladder[amt] / 1e8)
lad["档"] = pd.cut(lad[liq], bins=[0, 25, 30, 35, 38, 40, 43, 46, 1e9], right=False)
print(lad.groupby("档", observed=True)["debt_yi"].sum().round(2).to_string())
curve = est.compute_curve(ladder, [5, 10, 15, 20, 25, 30, 35, 40])  # drawdowns in percent
print("\n再跌多少会被强平的融资（亿）"); print(curve.round(2).to_string(index=False))
m.to_csv(OUT / f"margin_{CODE}.csv"); ladder.to_csv(OUT / f"margin_ladder_{CODE}.csv")
