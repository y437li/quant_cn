"""Bottoms without a panic day: does a breadth thrust (广度推力) confirm them? Signal: the share of A-shares above their 20-day
average rises above X% (60 / 70%) within 10 sessions of having been below 20%. Also a trend check: 中证1000 closes above its
60-day average after being ≥ 15% below its 250-day high. Entry at the signal close; per episode (≥ 20 sessions apart): 20 / 60 /
120-day 中证1000 return, worst within 120, and how far the entry is above the lowest close of the prior 60 sessions (what the
confirmation costs). Data 2016..2026-11 (curated daily + adj_factor; index cache extended with 512100)."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
L = "/Volumes/Treasury/quant_cn_lake/curated"; r = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
b = pd.read_csv(Path("/Volumes/Treasury/chinese_market/src/regime/cache/000852_SH_5min.csv"), usecols=["trade_time", "close", "trade_date"])
c = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close; c.index = c.index.astype(str).str.replace("-", "")
e = duckdb.sql(f"select trade_date, pct_chg from {r('fund_daily')} where ts_code = '512100.SH' and trade_date > '{c.index[-1]}'").df().set_index("trade_date").pct_chg.sort_index() / 100
p = pd.concat([c, c.iloc[-1] * (1 + e).cumprod()])
d = duckdb.sql(f"select d.ts_code, d.trade_date, d.close*a.adj_factor c from {r('daily')} d join {r('adj_factor')} a using (ts_code, trade_date) where d.trade_date >= '20150901'").df()
C = d.pivot(index="trade_date", columns="ts_code", values="c").sort_index()
ok = C.rolling(20, min_periods=20).count() >= 20
above = ((C > C.rolling(20).mean()) & ok).sum(axis=1) / ok.sum(axis=1)
F = pd.DataFrame({"p": p, "above": above}).dropna(); F = F[F.index >= "20160101"]
F["ma60"] = F.p.rolling(60).mean(); F["dd"] = F.p / F.p.rolling(250, min_periods=120).max() - 1
idx = list(F.index); pd.set_option("display.width", 220)
def episodes(flag):
    st = flag.index[flag & ~flag.shift(1, fill_value=False)]; ep = []
    for s in st:
        if not ep or idx.index(s) - idx.index(ep[-1]) > 20: ep.append(s)
    return ep
def ev(lab, flag):
    rows = []
    for s in episodes(flag.fillna(False)):
        i = idx.index(s); p0 = F.p.iloc[i]; o = {"signal": s, "above%": F.above.iloc[i] * 100, "above_low60": (p0 / F.p.iloc[max(0, i - 60):i + 1].min() - 1) * 100}
        for h in (20, 60, 120): o[f"r{h}"] = (F.p.iloc[i + h] / p0 - 1) * 100 if i + h < len(F) else np.nan
        w = F.p.iloc[i + 1:i + 121]; o["worst120"] = (w.min() / p0 - 1) * 100 if len(w) == 120 else np.nan; rows.append(o)
    X = pd.DataFrame(rows); print(f"\n[{lab}] episodes {len(X)}"); print(X.round(1).to_string(index=False))
    print("  ", {f"r{h}": f"{X[f'r{h}'].mean():+.1f} / {X[f'r{h}'].median():+.1f} / {int((X[f'r{h}'] > 0).sum())}of{X[f'r{h}'].notna().sum()}" for h in (20, 60, 120)},
          "worst120 median", round(X.worst120.median(), 1), "| paid above the 60-day low, median", round(X.above_low60.median(), 1))
was_low = F.above.rolling(10).min() < 0.20
for x in (0.6, 0.7): ev(f"breadth thrust: > {int(x*100)}% above MA20 within 10 days of < 20%", (F.above > x) & was_low)
ev("中证1000 back above its 60-day average after ≥ 15% down (dd at the cross)", (F.p > F.ma60) & (F.p.shift(1) <= F.ma60.shift(1)) & (F.dd.rolling(20).min() <= -0.15))
print("\ntoday: above MA20 %.0f%%, 10-day min %.0f%%, 中证1000 vs MA60 %.1f%%" % (F.above.iloc[-1] * 100, F.above.iloc[-10:].min() * 100, (F.p.iloc[-1] / F.ma60.iloc[-1] - 1) * 100))
print("unconditional:", {h: round((F.p.shift(-h) / F.p - 1).mean() * 100, 2) for h in (20, 60, 120)})
