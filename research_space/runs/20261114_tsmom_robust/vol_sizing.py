"""12-month trend rule plus volatility sizing with different volatility estimators (2026-11-14).

Direction: hold the index when its own past-12-month return (at the last month end) is > 0, else cash.
Size while held: min(1, 20% / sigma_{t-1}), updated daily (5 bp per unit traded). Estimators of the
annualised sigma, all from data up to the previous close:
  none (100% / 0%), EWMA com 60 and com 10, rolling std 20 and 60 days, Parkinson high-low 20 days,
  GARCH(1,1) with parameters fitted by MLE on 2010-2012 only. Evaluation 2013-01..2026-10 (GARCH
  out of sample). Also "always long + sizing" to separate the two effects. Price indices, cash at 0.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from scipy.optimize import minimize

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_tsmom_robust"
D = duckdb.connect().execute(f"select ts_code, trade_date, high, low, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
D["trade_date"] = pd.to_datetime(D.trade_date)
names = {"000300.SH": "沪深300", "000905.SH": "中证500", "000852.SH": "中证1000", "399006.SZ": "创业板指"}
TARGET, COST, START = 0.20, 0.0005, "2013-01-01"
periods = {"2015股灾": ("2015-06-12", "2016-01-31"), "2018熊市": ("2018-01-01", "2018-12-31"),
           "2021-24慢熊": ("2021-03-01", "2024-01-31"), "2019反弹": ("2019-01-01", "2019-12-31"),
           "2024反弹": ("2024-02-01", "2024-12-31")}


def garch_sigma(r: pd.Series, fit_end: str) -> pd.Series:
    x = r.dropna().to_numpy(); fit = r.dropna()[: fit_end].to_numpy()
    def nll(p):
        w, a, b = p
        if w <= 0 or a < 0 or b < 0 or a + b >= 1: return 1e10
        h = np.empty(len(fit)); h[0] = fit.var()
        for t in range(1, len(fit)): h[t] = w + a * fit[t - 1] ** 2 + b * h[t - 1]
        return 0.5 * np.sum(np.log(h) + fit ** 2 / h)
    w, a, b = minimize(nll, [fit.var() * 0.05, 0.08, 0.9], method="Nelder-Mead", options={"maxiter": 4000}).x
    h = np.empty(len(x)); h[0] = fit.var()
    for t in range(1, len(x)): h[t] = w + a * x[t - 1] ** 2 + b * h[t - 1]   # h[t] known at t-1 close
    return pd.Series(np.sqrt(h * 252), index=r.dropna().index), (w, a, b)


rows, params = [], {}
for code, nm in names.items():
    d = D[D.ts_code == code].set_index("trade_date").sort_index()
    r = d.close.pct_change()
    pk = np.log(d.high / d.low) ** 2 / (4 * np.log(2))
    g, params[nm] = garch_sigma(r, "2012-12-31")
    sig = {"无（全仓/空仓）": None,
           "EWMA 60": (r.pow(2).ewm(com=60, min_periods=20).mean() * 252) ** 0.5,
           "EWMA 10": (r.pow(2).ewm(com=10, min_periods=20).mean() * 252) ** 0.5,
           "滚动 20 日": r.rolling(20).std() * 252 ** 0.5,
           "滚动 60 日": r.rolling(60).std() * 252 ** 0.5,
           "Parkinson 20 日": (pk.rolling(20).mean() * 252) ** 0.5,
           "GARCH(1,1)": g}
    me = d.close.resample("ME").last()
    on_m = (me / me.shift(12) - 1 > 0).astype(float)
    on = on_m.reindex(d.index, method="ffill").shift(1)          # signal from the previous month end
    on = on.where(d.index.to_period("M") != on.index.to_period("M").min(), np.nan)
    on = on_m.shift(1).reindex(d.index.to_period("M").to_timestamp("M"), ).set_axis(d.index)  # month t uses month-end t-1
    for label, s in sig.items():
        for mode in ("趋势", "一直持有"):
            if mode == "一直持有" and label not in ("无（全仓/空仓）", "EWMA 60", "GARCH(1,1)"):
                continue
            direction = on if mode == "趋势" else pd.Series(1.0, index=d.index)
            size = 1.0 if s is None else (TARGET / s.shift(1)).clip(upper=1.0)
            w = (direction * size).fillna(0)
            ret = w * r - COST * w.diff().abs()
            ret = ret[ret.index >= START].fillna(0)
            cum = (1 + ret).cumprod()
            row = {"index": nm, "vol": label, "mode": mode, "ann_ret": cum.iloc[-1] ** (252 / len(ret)) - 1,
                   "sharpe": ret.mean() / ret.std() * 252 ** 0.5, "max_dd": (cum / cum.cummax() - 1).min(),
                   "exposure": w[w.index >= START].mean()}
            for lab, (a0, a1) in periods.items():
                row[lab] = (1 + ret[(ret.index >= a0) & (ret.index <= a1)]).prod() - 1
            rows.append(row)
T = pd.DataFrame(rows); T.to_csv(OUT / "vol_sizing.csv", index=False)
cols = ["ann_ret", "sharpe", "max_dd", "exposure", *periods]
avg = T.groupby(["mode", "vol"], sort=False)[cols].mean()
fmt = avg.copy()
for c in cols:
    fmt[c] = avg[c].map(lambda v: f"{v:.2f}" if c == "sharpe" else f"{v*100:.0f}%")
pd.set_option("display.width", 250)
print("Average over 沪深300, 中证500, 中证1000, 创业板指; 2013-01..2026-10; target vol 20%, size ≤ 100%, 5 bp per trade")
print(fmt.to_string())
print("\nGARCH(1,1) parameters fitted on 2010-2012 (omega, alpha, beta):", {k: tuple(round(x, 6) for x in v) for k, v in params.items()})
print("\n2015 股灾 by index (趋势 mode):")
print(T[T["mode"] == "趋势"].pivot(index="vol", columns="index", values="2015股灾").map(lambda v: f"{v*100:.0f}%").to_string())
