"""Does the last 15 minutes (14:45-15:00, incl. the closing auction) of an index predict the next day?
Input: legacy 5-minute index cache (Tushare idx_mins via chinese_market), 6 indices, 2015-01 .. 2026-08.
Signal day t: last-bar return r_L = ln(C_15:00 / C_14:45); last-bar volume ratio = last-bar vol / its 20-day mean (no look-ahead).
Next day: overnight ln(open_{t+1} 09:35 bar open / C_t), first 30 min, and full day ln(C_{t+1} / C_t).
Buckets: r_L sign / quintile; 'closing push' = r_L in the top 10% of its 250-day history AND volume ratio > 1.5.
Also the recent ETF picture: daily amount of the main broad ETFs (fund_daily) for the last 8 sessions."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root)
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
NAMES = {"000001": "上证指数", "000016": "上证50", "000300": "沪深300", "000905": "中证500", "000852": "中证1000", "399006": "创业板指"}
pd.set_option("display.width", 220)
rows = []
for f in sorted(SRC.glob("[0-9]*_5min.csv")):
    b = pd.read_csv(f, usecols=["trade_time", "open", "close", "vol", "trade_date"]); b["hm"] = b.trade_time.str[11:16]
    g = b.groupby("trade_date")
    d = pd.DataFrame({"c1445": b[b.hm == "14:45"].set_index("trade_date").close, "c1500": b[b.hm == "15:00"].set_index("trade_date").close,
                      "o": g.open.first() if False else b[b.hm == "09:35"].set_index("trade_date").open,
                      "c1000": b[b.hm == "10:00"].set_index("trade_date").close,
                      "vL": b[b.hm.isin(["14:50", "14:55", "15:00"])].groupby("trade_date").vol.sum()}).dropna()
    d["rL"] = np.log(d.c1500 / d.c1445); d["vr"] = d.vL / d.vL.rolling(20, min_periods=15).mean().shift(1)
    d["on"] = np.log(d.o.shift(-1) / d.c1500); d["first30"] = np.log(d.c1000.shift(-1) / d.o.shift(-1)); d["day"] = np.log(d.c1500.shift(-1) / d.c1500)
    d["rest"] = np.log(d.c1500.shift(-1) / d.c1000.shift(-1))
    d["push"] = (d.rL > d.rL.rolling(250, min_periods=120).quantile(0.9).shift(1)) & (d.vr > 1.5)
    d["dump"] = (d.rL < d.rL.rolling(250, min_periods=120).quantile(0.1).shift(1)) & (d.vr > 1.5)
    d["q"] = pd.qcut(d.rL.rank(method="first"), 5, labels=["1 尾盘大跌", "2", "3", "4", "5 尾盘大涨"])
    d["index"] = NAMES[f.name[:6]]; d["era"] = np.where(d.index < "2020", "2015-19", "2020-26"); rows.append(d.dropna(subset=["day", "vr"]))
D = pd.concat(rows)
def st(x): return pd.Series({"n": len(x), "bp": x.mean() * 1e4, "t": x.mean() / x.std() * np.sqrt(len(x)), "up": (x > 0).mean()})
print("next-day return (bp) by last-15-min quintile, pooled 6 indices")
for col in ("on", "first30", "rest", "day"):
    print(f"\n[{col}]"); print(D.groupby(["q"], observed=True)[col].apply(st).unstack().round(2).to_string())
print("\nrank corr rL vs next day, by index and era")
print(D.groupby(["index", "era"]).apply(lambda g: pd.Series({"on": g.rL.corr(g.on, method="spearman"), "day": g.rL.corr(g.day, method="spearman"), "n": len(g)}), include_groups=False).round(3).to_string())
for flag in ("push", "dump"):
    x = D[D[flag]]; print(f"\n[{flag}] events {len(x)}; next-day bp")
    print(x.groupby("index")[["on", "first30", "rest", "day"]].mean().mul(1e4).round(1).assign(n=x.groupby("index").size()).to_string())
    print("pooled:", {c: st(x[c]).round(2).to_dict() for c in ("on", "day")})
r = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
E = ("510300.SH", "510310.SH", "510330.SH", "159919.SZ", "510050.SH", "510500.SH", "512100.SH", "159915.SZ", "588000.SH", "563360.SH")
a = duckdb.sql(f"select ts_code, trade_date, amount/1e5 amt_yi, pct_chg from {r('fund_daily')} where ts_code in {E} and trade_date >= '20261020'").df()
t = a.pivot(index="ts_code", columns="trade_date", values="amt_yi"); print("\nETF daily amount 亿"); print(t.iloc[:, -8:].round(1).to_string())
print(t.sum().iloc[-8:].round(1).to_string())
