"""How long until a time-series momentum signal turns after a top (and back after a bottom)? (2026-11-14)

Month-end closes of 沪深300 / 中证500 / 中证1000 / 创业板指 since 2010. Episodes: peak-to-trough
declines of at least 20% (month-end). For lookbacks L = 1, 3, 6, 12 months: first month end at or after
the peak where price < price L months earlier (signal "down"), months from peak, and the drawdown
already suffered then; after the trough, first month end where the signal turns "up" again, months
from trough and how much of the rebound was missed.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
D = duckdb.connect().execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
D["trade_date"] = pd.to_datetime(D.trade_date)
names = {"000300.SH": "沪深300", "000905.SH": "中证500", "000852.SH": "中证1000", "399006.SZ": "创业板指"}
rows = []
for code, nm in names.items():
    p = D[D.ts_code == code].set_index("trade_date").close.resample("ME").last()
    p = p[p.index < "2026-11-01"]
    # find episodes: running peak, decline >= 20%, trough before a new high
    i, n = 0, len(p)
    while i < n:
        peak_i = i
        j = i + 1
        while j < n and p.iloc[j] < p.iloc[peak_i]:
            j += 1
        seg = p.iloc[peak_i:j]
        trough_i = peak_i + int(seg.values.argmin())
        dd = p.iloc[trough_i] / p.iloc[peak_i] - 1
        if dd <= -0.20 and p.index[peak_i] >= pd.Timestamp("2011-01-31"):
            for L in (1, 3, 6, 12):
                sig = p / p.shift(L) - 1
                down = [k for k in range(peak_i, n) if sig.iloc[k] < 0]
                k = down[0] if down else None
                up = [m for m in range(trough_i, n) if sig.iloc[m] > 0]
                m = up[0] if up else None
                rows.append({"index": nm, "peak": p.index[peak_i].strftime("%Y-%m"), "trough": p.index[trough_i].strftime("%Y-%m"),
                             "decline": dd, "months_to_trough": trough_i - peak_i,
                             "prior_12m_rise": p.iloc[peak_i] / p.iloc[peak_i - 12] - 1 if peak_i >= 12 else None,
                             "L": L, "months_to_exit": None if k is None else k - peak_i,
                             "dd_at_exit": None if k is None else p.iloc[k] / p.iloc[peak_i] - 1,
                             "months_to_reenter": None if m is None else m - trough_i,
                             "rebound_missed": None if m is None else p.iloc[m] / p.iloc[trough_i] - 1})
        i = j if j > i else i + 1
T = pd.DataFrame(rows)
T.to_csv(LAKE / "meta/runs/research/20261114_tsmom_robust/signal_lag.csv", index=False)
pd.set_option("display.width", 250)
v = T[T.L == 12][["index", "peak", "trough", "decline", "months_to_trough", "prior_12m_rise", "months_to_exit", "dd_at_exit", "months_to_reenter", "rebound_missed"]].copy()
for c in ("decline", "prior_12m_rise", "dd_at_exit", "rebound_missed"):
    v[c] = v[c].map(lambda x: "" if pd.isna(x) else f"{x*100:.0f}%")
print("12-month signal, declines >= 20% (month-end):"); print(v.to_string(index=False))
s = T.groupby("L").agg(exit_m=("months_to_exit", "median"), dd_exit=("dd_at_exit", "median"),
                       reenter_m=("months_to_reenter", "median"), missed=("rebound_missed", "median"), n=("peak", "size"))
s["dd_exit"] = s.dd_exit.map(lambda x: f"{x*100:.0f}%"); s["missed"] = s.missed.map(lambda x: f"{x*100:.0f}%")
print("\nMedian over episodes by lookback:"); print(s.to_string())
