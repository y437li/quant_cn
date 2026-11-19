"""Backtest the two bottom signals as buy rules for 中证1000.
Panic (恐慌底): a day with ≥ N limit-downs (N = 300 / 500 / 1000) or ≥ 70% of stocks at a 60-day low; entry at that day's close
  (a buyer can see the count by 14:50) and, as a check, at the next day's close.
Drought (地量底): 20-day market turnover (amount / float cap) in the bottom 20% (or 10%) of its trailing 3 years AND 中证1000 20-day
  realized vol ≤ 25, while 中证1000 is ≥ 15% below its 250-day high; entry at the close of the first such day.
Episodes start ≥ 20 sessions apart. Per episode: return after 5 / 20 / 60 / 120 sessions, the worst point within 60 and 120,
and whether that day was within 5% of the lowest close of the next 120 sessions ('near the low'). Unconditional means for
comparison. Data: limit-downs and breadth from curated daily + stk_limit (from 2015-10), turnover from daily_basic (from 2018-10),
中证1000 from the index cache extended with 512100."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
L = "/Volumes/Treasury/quant_cn_lake/curated"; r = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
b = pd.read_csv(SRC / "000852_SH_5min.csv", usecols=["trade_time", "close", "trade_date"]); c = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close
c.index = c.index.astype(str).str.replace("-", "")
e = duckdb.sql(f"select trade_date, pct_chg from {r('fund_daily')} where ts_code = '512100.SH' and trade_date > '{c.index[-1]}'").df().set_index("trade_date").pct_chg.sort_index() / 100
p = pd.concat([c, c.iloc[-1] * (1 + e).cumprod()])
m = duckdb.sql(f"""select d.trade_date, sum(d.amount)*1000 amt, sum(b.circ_mv)*10000 cmv, sum(case when d.close <= l.down_limit then 1 else 0 end) limdown
  from {r('daily')} d left join {r('daily_basic')} b using (ts_code, trade_date) left join {r('stk_limit')} l using (ts_code, trade_date)
  where d.trade_date >= '20150101' group by 1 order by 1""").df().set_index("trade_date")
d = duckdb.sql(f"select d.ts_code, d.trade_date, d.close*a.adj_factor c from {r('daily')} d join {r('adj_factor')} a using (ts_code, trade_date) where d.trade_date >= '20150101'").df()
C = d.pivot(index="trade_date", columns="ts_code", values="c").sort_index()
ok = C.rolling(60, min_periods=60).count() >= 60
low60 = ((C <= C.rolling(60, min_periods=60).min()) & ok).sum(axis=1) / ok.sum(axis=1)
m["limdown"] = m.limdown.where(m.index >= m.limdown[m.limdown > 0].index.min())
tr = (m.amt / m.cmv * 100).where(m.cmv > 0).rolling(20).mean(); trp = tr.rolling(750, min_periods=500).apply(lambda x: (x <= x[-1]).mean(), raw=True)
rv = np.log(p / p.shift(1)).rolling(20).std() * np.sqrt(252) * 100; dd = p / p.rolling(250, min_periods=120).max() - 1
F = pd.DataFrame({"p": p, "limdown": m.limdown, "low60": low60, "trp": trp, "rv": rv, "dd": dd}).dropna(subset=["p"])
F = F[F.index >= "20151001"]; idx = list(F.index); pd.set_option("display.width", 240)
def episodes(flag):
    flag = flag.fillna(False); st = flag.index[flag & ~flag.shift(1, fill_value=False)]; ep = []
    for s in st:
        if not ep or idx.index(s) - idx.index(ep[-1]) > 20: ep.append(s)
    return ep
def evaluate(lab, flag, lag=0, show=True):
    rows = []
    for s in episodes(flag):
        i = idx.index(s) + lag
        if i >= len(F): continue
        p0 = F.p.iloc[i]; o = {"signal": s, "limdown": F.limdown.iloc[i - lag], "low60%": F.low60.iloc[i - lag] * 100}
        for h in (5, 20, 60, 120): o[f"r{h}"] = (F.p.iloc[i + h] / p0 - 1) * 100 if i + h < len(F) else np.nan
        for h in (60, 120):
            w = F.p.iloc[i + 1:i + h + 1]; o[f"worst{h}"] = (w.min() / p0 - 1) * 100 if len(w) == h else np.nan
        w = F.p.iloc[i:i + 121]; o["near_low"] = (p0 / w.min() - 1 <= 0.05) if len(w) == 121 else np.nan
        rows.append(o)
    X = pd.DataFrame(rows)
    print(f"\n[{lab}{' , entry next close' if lag else ''}] episodes {len(X)}")
    if show and len(X): print(X.round(1).to_string(index=False))
    if len(X):
        s = {f"r{h}": f"{X[f'r{h}'].mean():+.1f} / {X[f'r{h}'].median():+.1f} / {int((X[f'r{h}'] > 0).sum())}of{X[f'r{h}'].notna().sum()}" for h in (5, 20, 60, 120)}
        s["worst120 median"] = round(X.worst120.median(), 1); s["near_low"] = f"{int(X.near_low.fillna(False).sum())}of{X.near_low.notna().sum()}"
        print("  mean / median / positive:", s)
    return X
print("unconditional 中证1000 mean %:", {h: round((F.p.shift(-h) / F.p - 1).mean() * 100, 2) for h in (5, 20, 60, 120)})
for n in (300, 500, 1000): evaluate(f"panic: limit-downs ≥ {n}", F.limdown >= n, show=(n == 500))
evaluate("panic: ≥ 70% of stocks at a 60-day low", F.low60 >= 0.70)
evaluate("panic: limit-downs ≥ 500 or ≥ 70% at 60-day low", (F.limdown >= 500) | (F.low60 >= 0.70), show=False)
evaluate("panic: limit-downs ≥ 500", F.limdown >= 500, lag=1, show=False)
for q in (0.2, 0.1):
    evaluate(f"drought: turnover ≤ {int(q*100)}th pct & vol ≤ 25 & ≥ 15% below high", (F.trp <= q) & (F.rv <= 25) & (F.dd <= -0.15))
evaluate("drought: turnover ≤ 20th pct (no vol / depth filter)", F.trp <= 0.2, show=False)
print("\ntoday:", F.iloc[-1].round(3).to_dict(), F.index[-1])
