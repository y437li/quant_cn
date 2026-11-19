"""Trend rules compared on A-share indices: single lookbacks, a multi-lookback average and moving
averages, with and without volatility sizing (2026-11-14).

Daily: the signal at close t sets the position for t+1; 5 bp per unit traded; cash earns 0; price
indices (no dividends). 沪深300, 中证500, 中证1000, 创业板指; 2011-01-04..2026-11-13.
Rules (position in [0, 1]):
  TS12 / TS6 / TS3 / TS1   price > price 252 / 126 / 63 / 21 sessions ago
  MULTI                    average of the four TS signals (0, 25, 50, 75, 100%)
  MA200                    price > 200-day simple moving average
  MA50/200                 50-day SMA > 200-day SMA
  MA200+band               enter above MA200 × 1.02, leave below MA200 × 0.98 (fewer whipsaws)
  + vol                    times min(1, 20% / rolling-60-day volatility)
Per rule: return, Sharpe, max drawdown, time in market, switches a year, and the drawdown episodes
(≥ 20%, month-end peaks as in signal_lag.py): days from peak to first exit below 50% position,
drawdown by then; rebound missed after the trough.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_tsmom_robust"
D = duckdb.connect().execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
D["trade_date"] = pd.to_datetime(D.trade_date)
names = {"000300.SH": "沪深300", "000905.SH": "中证500", "000852.SH": "中证1000", "399006.SZ": "创业板指"}
START, COST = "2011-01-04", 0.0005
periods = {"2015股灾": ("2015-06-12", "2016-01-31"), "2018熊市": ("2018-01-25", "2018-12-31"),
           "2021-24慢熊": ("2021-02-18", "2024-02-05"), "2026下跌": ("2026-06-30", "2026-11-13"),
           "2019反弹": ("2019-01-04", "2019-04-30"), "2024-09反弹": ("2024-09-18", "2024-12-31")}


def rules(p: pd.Series) -> dict[str, pd.Series]:
    ts = {L: (p > p.shift(n)).astype(float).where(p.shift(n).notna()) for L, n in ((12, 252), (6, 126), (3, 63), (1, 21))}
    ma50, ma200 = p.rolling(50).mean(), p.rolling(200).mean()
    band = pd.Series(np.nan, index=p.index); state = 0.0
    for t, (x, m) in enumerate(zip(p.values, ma200.values)):
        if np.isnan(m): continue
        if state == 0 and x > m * 1.02: state = 1.0
        elif state == 1 and x < m * 0.98: state = 0.0
        band.iloc[t] = state
    out = {"一直持有": pd.Series(1.0, index=p.index), "TS12": ts[12], "TS6": ts[6], "TS3": ts[3], "TS1": ts[1],
           "MULTI(1/3/6/12)": pd.concat(ts.values(), axis=1).mean(axis=1, skipna=False),
           "MA200": (p > ma200).astype(float).where(ma200.notna()),
           "MA50/200": (ma50 > ma200).astype(float).where(ma200.notna()), "MA200±2%": band}
    return out


rows, epis = [], []
for code, nm in names.items():
    p = D[D.ts_code == code].set_index("trade_date").close.sort_index()
    r = p.pct_change()
    vol = r.rolling(60).std() * 252 ** 0.5
    size = (0.20 / vol).clip(upper=1.0)
    me = p.resample("ME").last()
    for name, sig in rules(p).items():
        for sized in (False, True):
            if sized and name in ("TS6", "TS3", "TS1"):
                continue
            w = (sig * (size if sized else 1.0)).shift(1)
            ret = (w * r - COST * w.diff().abs()).loc[START:].fillna(0)
            ww = w.loc[START:].fillna(0)
            cum = (1 + ret).cumprod()
            label = name + (" + vol" if sized else "")
            row = {"index": nm, "rule": label, "ann_ret": cum.iloc[-1] ** (252 / len(ret)) - 1,
                   "sharpe": ret.mean() / ret.std() * 252 ** 0.5, "max_dd": (cum / cum.cummax() - 1).min(),
                   "in_market": ww.mean(), "trades_per_year": (ww.diff().abs() > 0).sum() / (len(ww) / 252)}
            for lab, (a, b) in periods.items():
                row[lab] = (1 + ret.loc[a:b]).prod() - 1
            rows.append(row)
            if sized:
                continue
            # drawdown episodes from month-end all-time peaks
            i, n = 0, len(me)
            while i < n:
                j = i + 1
                while j < n and me.iloc[j] < me.iloc[i]: j += 1
                seg = me.iloc[i:j]; ti = i + int(seg.values.argmin())
                dd = me.iloc[ti] / me.iloc[i] - 1
                if dd <= -0.20 and me.index[i] >= pd.Timestamp("2011-06-30") and name != "一直持有":
                    pk = p.loc[me.index[i] - pd.offsets.MonthBegin(1): me.index[i]].idxmax()
                    tr = p.loc[me.index[ti] - pd.offsets.MonthBegin(1): me.index[ti]].idxmin()
                    after = w.loc[pk:]
                    ex = after[after < 0.5].index
                    exit_d = ex[0] if len(ex) else None
                    back = w.loc[tr:]
                    en = back[back >= 0.5].index
                    in_d = en[0] if len(en) else None
                    epis.append({"index": nm, "rule": name, "peak": pk.date(), "decline": dd,
                                 "days_to_exit": None if exit_d is None else len(p.loc[pk:exit_d]) - 1,
                                 "dd_at_exit": None if exit_d is None else p[exit_d] / p[pk] - 1,
                                 "days_to_reenter": None if in_d is None else len(p.loc[tr:in_d]) - 1,
                                 "rebound_missed": None if in_d is None else p[in_d] / p[tr] - 1})
                i = j if j > i else i + 1
T = pd.DataFrame(rows); T.to_csv(OUT / "trend_rules.csv", index=False)
E = pd.DataFrame(epis); E.to_csv(OUT / "trend_rules_episodes.csv", index=False)
cols = ["ann_ret", "sharpe", "max_dd", "in_market", "trades_per_year", *periods]
avg = T.groupby("rule", sort=False)[cols].mean()
f = avg.copy()
for c in cols:
    f[c] = avg[c].map(lambda v: f"{v:.2f}" if c == "sharpe" else (f"{v:.1f}" if c == "trades_per_year" else f"{v*100:.0f}%"))
pd.set_option("display.width", 260)
print("Average of 沪深300, 中证500, 中证1000, 创业板指, 2011-01..2026-11, 5 bp per trade, cash 0")
print(f.to_string())
print("\nDrawdown episodes (7, as in signal_lag.py), medians:")
g = E.groupby("rule", sort=False).agg(days_to_exit=("days_to_exit", "median"), dd_at_exit=("dd_at_exit", "median"),
                                      days_to_reenter=("days_to_reenter", "median"), rebound_missed=("rebound_missed", "median"), n=("peak", "size"))
g["dd_at_exit"] = g.dd_at_exit.map(lambda x: f"{x*100:.0f}%"); g["rebound_missed"] = g.rebound_missed.map(lambda x: f"{x*100:.0f}%")
print(g.to_string())
