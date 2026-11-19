"""Is the market trending (单边) or range-bound right now? Snapshot as of the latest close.
Broad ETFs (fund_daily pct_chg chained): 510050 上证50, 510300 沪深300, 512100 中证1000, 159915 创业板, 588000 科创50.
Per ETF: returns 5 / 20 / 60 days and YTD, drawdown from the 250-day high, position vs 20 / 60 / 120-day averages, efficiency ratio
ER = |net move| / sum |daily moves| over 20 and 60 days (1 = straight line, ~0 = chop) with its percentile since 2019, and the
share of up days in the last 20. Breadth from all A-shares (curated daily, qfq via adj_factor): share up per day (last 10),
share above the 20 / 60-day average, count at a 60-day low, median 20-day return; plus the same breadth a month ago."""
import duckdb, numpy as np, pandas as pd
L = "/Volumes/Treasury/quant_cn_lake/curated"; r = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
E = {"510050.SH": "上证50", "510300.SH": "沪深300", "512100.SH": "中证1000", "159915.SZ": "创业板", "588000.SH": "科创50"}
px = duckdb.sql(f"select ts_code, trade_date, pct_chg from {r('fund_daily')} where ts_code in {tuple(E)} and trade_date >= '20190101'").df()
Rt = px.pivot(index="trade_date", columns="ts_code", values="pct_chg").sort_index() / 100; P = (1 + Rt).cumprod()
last = P.index[-1]; out = {}
def er(s, n): s = s.iloc[-n - 1:]; return abs(s.iloc[-1] / s.iloc[0] - 1) / (s.pct_change().abs().sum())
for c, nm in E.items():
    s = P[c].dropna(); ers = {n: pd.Series([er(s.iloc[:i], n) for i in range(n + 2, len(s) + 1, 5)]) for n in (20, 60)}
    out[nm] = {"5d%": (s.iloc[-1] / s.iloc[-6] - 1) * 100, "20d%": (s.iloc[-1] / s.iloc[-21] - 1) * 100, "60d%": (s.iloc[-1] / s.iloc[-61] - 1) * 100,
               "YTD%": (s.iloc[-1] / s[s.index < "20260101"].iloc[-1] - 1) * 100, "from_high%": (s.iloc[-1] / s.iloc[-250:].max() - 1) * 100,
               "high_date": s.iloc[-250:].idxmax(), "vsMA20%": (s.iloc[-1] / s.iloc[-20:].mean() - 1) * 100, "vsMA60%": (s.iloc[-1] / s.iloc[-60:].mean() - 1) * 100,
               "vsMA120%": (s.iloc[-1] / s.iloc[-120:].mean() - 1) * 100, "ER20": er(s, 20), "ER20_pct": (ers[20] <= er(s, 20)).mean(),
               "ER60": er(s, 60), "ER60_pct": (ers[60] <= er(s, 60)).mean(), "up_days20": (Rt[c].iloc[-20:] > 0).mean()}
pd.set_option("display.width", 220)
print("as of", last); print(pd.DataFrame(out).T.round(2).to_string())
d = duckdb.sql(f"""select d.ts_code, d.trade_date, d.close*a.adj_factor c, d.pct_chg from {r('daily')} d join {r('adj_factor')} a using (ts_code, trade_date)
  where d.trade_date >= '20260601'""").df()
C = d.pivot(index="trade_date", columns="ts_code", values="c").sort_index(); PC = d.pivot(index="trade_date", columns="ts_code", values="pct_chg").sort_index()
def breadth(i):
    c = C.iloc[: i + 1]; x = c.iloc[-1]; ok = c.iloc[-61:].notna().all()
    return {"date": c.index[-1], "above_ma20": (x > c.iloc[-20:].mean())[ok].mean(), "above_ma60": (x > c.iloc[-60:].mean())[ok].mean(),
            "at_60d_low": int(((x <= c.iloc[-60:].min()) & ok).sum()), "at_60d_high": int(((x >= c.iloc[-60:].max()) & ok).sum()),
            "median_20d%": ((x / c.iloc[-21] - 1)[ok].median()) * 100}
print("\nbreadth"); print(pd.DataFrame([breadth(len(C) - 1 - k) for k in (0, 5, 10, 20, 40)]).round(3).to_string(index=False))
print("\nshare of stocks up, last 10 sessions:", {k: round(v, 2) for k, v in (PC.iloc[-10:] > 0).mean(axis=1).items()})
print("median stock return, last 10 sessions %:", {k: round(v, 2) for k, v in PC.iloc[-10:].median(axis=1).items()})
