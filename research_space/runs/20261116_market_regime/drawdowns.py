"""Maximum drawdowns: 中证1000 and 沪深300 (index cache 2015..2026-08 extended with 512100 / 510300 pct_chg to the latest close).
(1) Largest peak-to-trough drawdowns since 2015 (distinct episodes, price index, no dividends), with peak, trough and recovery.
(2) For the vol-gap entries (exit_rules.py episodes): worst point below the entry price within 20 / 60 sessions (max adverse excursion).
(3) Current drawdown from the running high."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
cl = {}
for code, f in (("c1000", "000852_SH_5min.csv"), ("c300", "000300_SH_5min.csv")):
    b = pd.read_csv(SRC / f, usecols=["trade_time", "close", "trade_date"]); cl[code] = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close
P = pd.DataFrame(cl).dropna(); P.index = P.index.astype(str).str.replace("-", "")
L = "/Volumes/Treasury/quant_cn_lake/curated"
e = duckdb.sql(f"select ts_code, trade_date, pct_chg from read_parquet('{L}/fund_daily/**/*.parquet', hive_partitioning=true) where ts_code in ('512100.SH','510300.SH') and trade_date > '{P.index[-1]}'").df()
g = (1 + e.pivot(index="trade_date", columns="ts_code", values="pct_chg").sort_index() / 100).cumprod()
P = pd.concat([P, pd.DataFrame({"c1000": P.c1000.iloc[-1] * g["512100.SH"], "c300": P.c300.iloc[-1] * g["510300.SH"]})])
pd.set_option("display.width", 200)
for c, nm in (("c1000", "中证1000"), ("c300", "沪深300")):
    s = P[c]; peak = s.cummax(); dd = s / peak - 1
    eps, i = [], 0
    while i < len(s):
        if dd.iloc[i] < 0:
            j = i
            while j < len(s) and dd.iloc[j] < 0: j += 1
            seg = dd.iloc[i:j]; t = seg.idxmin()
            eps.append({"peak": s.iloc[:i].idxmax() if i else s.index[0], "trough": t, "dd%": seg.min() * 100,
                        "days_to_trough": s.index.get_loc(t) - i + 1, "recovered": s.index[j] if j < len(s) else "not yet"})
            i = j
        else: i += 1
    D = pd.DataFrame(eps).sort_values("dd%").head(6)
    print(f"\n== {nm}: max drawdown since {s.index[0]}: {dd.min()*100:.1f}% (trough {dd.idxmin()}); now {dd.iloc[-1]*100:.1f}% from the high of {s[:].idxmax()} ==")
    print(D.round(1).to_string(index=False))
R = np.log(P / P.shift(1)); rv = R.rolling(20).std() * np.sqrt(252) * 100; gap = (rv.c1000 - rv.c300).dropna()
pct = gap.rolling(750, min_periods=250).apply(lambda x: (x <= x[-1]).mean(), raw=True).dropna()
idx = list(pct.index); hot = pct >= 0.9; ep = []
for s0 in pct.index[hot & ~hot.shift(1, fill_value=False)]:
    if not ep or idx.index(s0) - idx.index(ep[-1]) > 20: ep.append(s0)
rows = []
for s0 in ep:
    i0 = P.index.get_loc(s0); p0 = P.c1000.iloc[i0]
    w20 = P.c1000.iloc[i0 + 1:i0 + 21]; w60 = P.c1000.iloc[i0 + 1:i0 + 61]
    pair = (P.c1000 / P.c1000.iloc[i0]) / (P.c300 / P.c300.iloc[i0])   # long 1000 / short 300, equal notional, rebalanced at entry only
    q60 = pair.iloc[i0 + 1:i0 + 61]
    rows.append({"entry": s0, "w20": (w20.min() / p0 - 1) * 100, "w60": (w60.min() / p0 - 1) * 100, "end60": (w60.iloc[-1] / p0 - 1) * 100,
                 "pair_w60": (q60.min() - 1) * 100, "pair_end60": (q60.iloc[-1] - 1) * 100, "days_seen": len(w60)})
M = pd.DataFrame(rows); print("\n== after a vol-gap signal: worst point below entry (w20 / w60), 60-day end, and the long-1000 / short-300 pair =="); print(M.round(1).to_string(index=False))
done = M[M.days_seen == 60]
print("closed: long-only worst_60d median %.1f%%, worst %.1f%% | pair worst_60d median %.1f%%, worst %.1f%% | pair end60 mean %.1f%%, positive %d/%d"
      % (done.w60.median(), done.w60.min(), done.pair_w60.median(), done.pair_w60.min(), done.pair_end60.mean(), (done.pair_end60 > 0).sum(), len(done)))
print("1000 since 20261030:", P.c1000.loc["20261028":].round(1).to_dict())
for c in ("c1000", "c300"):
    s = P[c].loc["20190101":]; dd = s / s.cummax() - 1
    print(c, "max drawdown since 2019: %.1f%% (trough %s); by year:" % (dd.min() * 100, dd.idxmin()), (s.groupby(s.index.str[:4]).apply(lambda x: (x / x.cummax() - 1).min()) * 100).round(1).to_dict())
