"""Exit rules for a 中证1000 position bought when the small-vs-large vol gap reaches its 90th percentile.
Realized-vol gap (1000 − 300, 20-day) and trailing 3-year percentile as in realized_gap.py; index cache 2016..2026-08, plus the
ETF series (512100 / 510300 pct_chg) for the live 2026-10-30 episode. Entry at the close of each episode start (starts ≥ 20
sessions apart). Exit rules: fixed 20 / 60 / 120 sessions; gap percentile back below 50% or 70% (checked at each close, max 250
sessions); 'normalise or 60d' = whichever first; each with and without a −10% stop on the 1000 leg. Per rule: mean absolute 1000
return, mean relative to 300 over the same days, share positive, worst, mean days held."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
cl = {}
for code, f in (("c1000", "000852_SH_5min.csv"), ("c300", "000300_SH_5min.csv")):
    b = pd.read_csv(SRC / f, usecols=["trade_time", "close", "trade_date"]); cl[code] = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close
P = pd.DataFrame(cl).dropna(); P.index = P.index.astype(str).str.replace("-", "")
L = "/Volumes/Treasury/quant_cn_lake/curated"
e = duckdb.sql(f"select ts_code, trade_date, pct_chg from read_parquet('{L}/fund_daily/**/*.parquet', hive_partitioning=true) where ts_code in ('512100.SH','510300.SH') and trade_date > '{P.index[-1]}'").df()
if len(e):  # extend the index closes with the ETF daily returns after the cache ends
    g = (1 + e.pivot(index="trade_date", columns="ts_code", values="pct_chg").sort_index() / 100).cumprod()
    ext = pd.DataFrame({"c1000": P.c1000.iloc[-1] * g["512100.SH"], "c300": P.c300.iloc[-1] * g["510300.SH"]}); P = pd.concat([P, ext])
R = np.log(P / P.shift(1)); rv = R.rolling(20).std() * np.sqrt(252) * 100; gap = (rv.c1000 - rv.c300).dropna()
pct = gap.rolling(750, min_periods=250).apply(lambda x: (x <= x[-1]).mean(), raw=True).dropna()
idx = list(pct.index); hot = pct >= 0.9; starts = [d for d in pct.index[hot & ~hot.shift(1, fill_value=False)]]
ep = []
for s in starts:
    if not ep or idx.index(s) - idx.index(ep[-1]) > 20: ep.append(s)
def run(s, rule, stop):
    i0 = idx.index(s); p0 = P.loc[s]
    for k in range(1, 251):
        if i0 + k >= len(idx): return None
        d = idx[i0 + k]; r1000 = P.c1000[d] / p0.c1000 - 1
        if stop and r1000 <= -0.10: break
        if rule[0] == "fixed" and k >= rule[1]: break
        if rule[0] == "pct" and pct[d] < rule[1]: break
        if rule[0] == "pct_or" and (pct[d] < rule[1] or k >= rule[2]): break
    return {"abs": r1000, "rel": r1000 - (P.c300[d] / p0.c300 - 1), "days": k, "exit": d}
rules = {"fixed 20d": ("fixed", 20), "fixed 60d": ("fixed", 60), "fixed 120d": ("fixed", 120), "pct < 70%": ("pct", 0.7),
         "pct < 50%": ("pct", 0.5), "pct < 50% or 60d": ("pct_or", 0.5, 60), "pct < 70% or 60d": ("pct_or", 0.7, 60)}
rows, detail = [], []
for name, rule in rules.items():
    for stop in (False, True):
        res = [x | {"start": s} for s in ep if (x := run(s, rule, stop))]
        Rr = pd.DataFrame(res)
        rows.append({"rule": name + (" + stop −10%" if stop else ""), "episodes": len(Rr), "abs_mean%": Rr["abs"].mean() * 100, "abs_pos": (Rr["abs"] > 0).mean(),
                     "abs_worst%": Rr["abs"].min() * 100, "rel_mean%": Rr.rel.mean() * 100, "rel_pos": (Rr.rel > 0).mean(), "days": Rr.days.mean()})
        if name == "pct < 50% or 60d" and not stop: detail = Rr
pd.set_option("display.width", 220)
print(f"episodes {len(ep)}: {ep}")
print(pd.DataFrame(rows).round(2).to_string(index=False))
print("\n'pct < 50% or 60d' per episode"); print(detail.assign(abs=detail["abs"] * 100, rel=detail.rel * 100).round(2).to_string(index=False))
print("\nlive: gap", round(gap.iloc[-1], 1), "pct", round(pct.iloc[-1], 2), "on", pct.index[-1], "| gap 3y median", round(gap.iloc[-750:].median(), 1),
      "| gap at the 70th / 50th pct of the last 3y:", round(gap.iloc[-750:].quantile(0.7), 1), round(gap.iloc[-750:].quantile(0.5), 1))
