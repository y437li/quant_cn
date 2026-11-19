"""What happens after a close breaks below the modelled chip floor (cyq_perf cost_5pct)? Events: first close
below cost_5pct in 60 sessions, float cap >= 50 亿, 2021-03..2026-08. Entry at that close (raw close vs the
vendor's forward-adjusted cost is consistent on the event day: the adjustment basis only differs across
ex-dates before it). Forward 20 / 60 sessions: absolute and excess return (vs equal-weight universe), share
that fell another 10% at some point, by the 20-day large-order flow before the break (in / out)."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261113_cost_break"
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
piv = lambda d, v: d.pivot(index="trade_date", columns="ts_code", values=v).sort_index()
d = q(f"""SELECT d.ts_code, d.trade_date, d.close, d.close * a.adj_factor AS px, b.circ_mv, c.cost_5pct,
          (m.buy_lg_amount + m.buy_elg_amount - m.sell_lg_amount - m.sell_elg_amount) AS lg
          FROM {src('daily')} d JOIN {src('adj_factor')} a USING (ts_code, trade_date)
          JOIN {src('daily_basic')} b USING (ts_code, trade_date) JOIN {src('cyq_perf')} c USING (ts_code, trade_date)
          LEFT JOIN {src('moneyflow')} m USING (ts_code, trade_date) WHERE d.trade_date >= '20210101'""")
close, px, cap, c5, lg = (piv(d, v) for v in ("close", "px", "circ_mv", "cost_5pct", "lg"))
below = close < c5
first = below & ~below.shift(1).rolling(60, min_periods=1).max().fillna(0).astype(bool)
lg20 = lg.rolling(20, min_periods=15).sum()
big = cap >= 50e4
rows = []
for h in (20, 60):
    f = px.shift(-h) / px - 1
    mkt = f.where(big).mean(axis=1)
    low = px.rolling(h, min_periods=1).min().shift(-h) / px - 1  # worst close in the next h sessions
    m = (first & big & f.notna()).copy()
    m.loc[m.index < "20210301"] = False
    s = pd.DataFrame({"r": f[m].stack(), "x": f[m].sub(mkt, axis=0).stack(), "low": low[m].stack(), "lg": lg20[m].stack()})
    s = s.dropna(subset=["r", "x", "low"])
    base_m = (big & f.notna()).copy()
    base_m.loc[(base_m.index < "20210301") | ~base_m.index.isin(base_m.index[::20])] = False
    base = pd.DataFrame({"r": f[base_m].stack(), "x": f[base_m].sub(mkt, axis=0).stack(), "low": low[base_m].stack()}).dropna()
    base["lg"] = np.nan
    for name, g in (("对照：全部股票（每 20 天抽样）", base), ("全部跌破", s), ("跌破前20日大单净流入", s[s["lg"] > 0]), ("跌破前20日大单净流出", s[s["lg"] <= 0])):
        rows.append({"期限": h, "分组": name, "样本": len(g), "绝对均%": g["r"].mean() * 100, "超额均%": g["x"].mean() * 100,
                     "超额中位%": g["x"].median() * 100, "跑赢率": (g["x"] > 0).mean(), "期间再跌≥10%": (g["low"] <= -0.10).mean()})
res = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(res.round(3).to_string(index=False))
res.to_csv(OUT / "cost_break.csv", index=False)
