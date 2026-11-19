"""地量底 or 恐慌底: what did past 中证1000 lows look like, and which does today resemble?
Major lows (2018-10..): a trough at least 20% below its trailing 250-day high that is followed by a ≥ 15% rally within 60 sessions
(lows within 60 sessions of a deeper one are merged). For each low and for today: depth from the 250-day high, days since that
high, market turnover (amount / float cap, 20-day mean and its 3-year pct), the most limit-downs on one day in the 10 sessions up
to the low, 中证1000 20-day realized vol, margin financing change over the 20 sessions before, share of stocks at a 60-day low.
Type: 恐慌底 if the 10-day max limit-downs ≥ 500, 地量底 if the turnover pct ≤ 20%, else 混合."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
L = "/Volumes/Treasury/quant_cn_lake/curated"; r = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
b = pd.read_csv(SRC / "000852_SH_5min.csv", usecols=["trade_time", "close", "trade_date"]); c = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close
c.index = c.index.astype(str).str.replace("-", "")
e = duckdb.sql(f"select trade_date, pct_chg from {r('fund_daily')} where ts_code = '512100.SH' and trade_date > '{c.index[-1]}'").df().set_index("trade_date").pct_chg.sort_index() / 100
p = pd.concat([c, c.iloc[-1] * (1 + e).cumprod()])
m = duckdb.sql(f"""select d.trade_date, sum(d.amount)*1000 amt, sum(b.circ_mv)*10000 cmv,
   sum(case when d.close <= l.down_limit then 1 else 0 end) limdown
  from {r('daily')} d join {r('daily_basic')} b using (ts_code, trade_date) left join {r('stk_limit')} l using (ts_code, trade_date)
  where d.trade_date >= '20151001' group by 1 order by 1""").df().set_index("trade_date")
mg = duckdb.sql(f"select trade_date, sum(rzye) rz, count(distinct exchange_id) nx from {r('margin')} group by 1 order by 1").df().set_index("trade_date")
mg = mg[mg.nx == mg.nx.max()].rz
d = duckdb.sql(f"select d.ts_code, d.trade_date, d.close*a.adj_factor c from {r('daily')} d join {r('adj_factor')} a using (ts_code, trade_date) where d.trade_date >= '20180101'").df()
C = d.pivot(index="trade_date", columns="ts_code", values="c").sort_index()
low60 = (C <= C.rolling(60, min_periods=60).min()).sum(axis=1) / C.notna().sum(axis=1)
tr = (m.amt / m.cmv * 100).rolling(20).mean(); trp = tr.rolling(750, min_periods=500).apply(lambda x: (x <= x[-1]).mean(), raw=True)
p = p[p.index >= "20181001"]; rv = (np.log(p / p.shift(1)).rolling(20).std() * np.sqrt(252) * 100)
hi = p.rolling(250, min_periods=120).max(); dd = p / hi - 1
cand = []
for i in range(len(p) - 1):
    if dd.iloc[i] <= -0.20 and p.iloc[i] == p.iloc[max(0, i - 20):i + 21].min():
        fut = p.iloc[i + 1:i + 61]
        if len(fut) and fut.max() / p.iloc[i] - 1 >= 0.15: cand.append(p.index[i])
lows = []
for s in cand:
    if lows and p.index.get_loc(s) - p.index.get_loc(lows[-1]) <= 60:
        if p[s] < p[lows[-1]]: lows[-1] = s
    else: lows.append(s)
def feat(day):
    i = p.index.get_loc(day); hd = p.iloc[max(0, i - 250):i + 1].idxmax()
    w = m.limdown.loc[:day].iloc[-10:]; mgs = mg.loc[:day]
    o = {"date": day, "depth%": dd[day] * 100, "days_from_high": i - p.index.get_loc(hd), "turn20%": tr.get(day), "turn_pct3y": trp.get(day),
         "max_limdown10d": int(w.max()), "limdown_day": w.idxmax(), "rv20": rv[day], "margin_chg20d%": (mgs.iloc[-1] / mgs.iloc[-21] - 1) * 100 if len(mgs) > 21 else np.nan,
         "at_60d_low%": low60.get(day, np.nan) * 100, "rally60%": (p.iloc[i + 1:i + 61].max() / p[day] - 1) * 100 if i + 1 < len(p) else np.nan}
    o["type"] = "恐慌底" if o["max_limdown10d"] >= 500 else ("地量底" if o["turn_pct3y"] <= 0.2 else "混合")
    return o
pd.set_option("display.width", 250)
T = pd.DataFrame([feat(x) for x in lows] + [feat(p.index[-1])])
print(T.round(2).to_string(index=False))
