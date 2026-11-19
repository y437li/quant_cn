"""Does daily northbound turnover (the only daily northbound number since 2024-08-19) lead 中证1000?

moneyflow_hsgt after 2024-08-19: hgt / sgt / north_money are buy+sell turnover (百万元), not net.
Share = north_money / A-share turnover (curated.daily amount, 千元). Tested: share level pct and
5-day change vs 中证1000 forward 5 / 20 / 60-day returns, 2024-08-19 .. as_of.
"""

import json
import os
import urllib.request

import duckdb
import pandas as pd

LAKE = "/Volumes/Treasury/quant_cn_lake/curated"
OUT = "/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261119_northbound"


def query(api: str, **params: str) -> pd.DataFrame:
    body = json.dumps({"api_name": api, "token": os.environ["TUSHARE_TOKEN"], "params": params, "fields": ""})
    req = urllib.request.Request("https://api.tushare.pro", body.encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=60))
    if r["code"]:
        raise RuntimeError(r)
    return pd.DataFrame(r["data"]["items"], columns=r["data"]["fields"])


chunks = [("20240819", "20250630"), ("20250701", "20260331"), ("20260401", "20261231")]
hs = pd.concat([query("moneyflow_hsgt", start_date=a, end_date=b) for a, b in chunks]).drop_duplicates("trade_date")
hs["north"] = pd.to_numeric(hs["north_money"]) / 100  # 亿元
c = duckdb.connect()
c.register("hs", hs[["trade_date", "north"]])
df = c.sql(f"""
with a as (select trade_date, sum(amount)/1e5 a_turn from read_parquet('{LAKE}/daily/**/*.parquet', hive_partitioning=1)
           where trade_date >= '20240801' group by 1),
i as (select trade_date, close from read_parquet('{LAKE}/reference/index_daily.parquet') where ts_code='000852.SH')
select hs.trade_date, north, a_turn, north / a_turn AS share, i.close from hs join a using(trade_date) join i using(trade_date)
order by 1""").df()
for h in (5, 20, 60):
    df[f"fwd{h}"] = df["close"].shift(-h) / df["close"] - 1
df["share_ma5"] = df["share"].rolling(5).mean()
df["share_chg"] = df["share_ma5"] - df["share_ma5"].shift(20)
df["share_pct"] = df["share_ma5"].rank(pct=True)
os.makedirs(OUT, exist_ok=True)
df.to_parquet(f"{OUT}/northbound_turnover.parquet")
print(df[["trade_date", "north", "a_turn", "share"]].tail(8).to_string())
print("share ma5 range", df["share_ma5"].min(), df["share_ma5"].median(), df["share_ma5"].max())
print("corr (spearman) with forward returns")
print(df[["share_ma5", "share_chg", "fwd5", "fwd20", "fwd60"]].corr("spearman").loc[["share_ma5", "share_chg"], ["fwd5", "fwd20", "fwd60"]].round(3))
df["q"] = pd.qcut(df["share_chg"], 4, labels=["Q1 falling", "Q2", "Q3", "Q4 rising"])
print(df.groupby("q", observed=True)[["fwd5", "fwd20", "fwd60"]].mean().mul(100).round(2))
print("now", df[["trade_date", "share_ma5", "share_pct", "share_chg"]].tail(1).to_string())
