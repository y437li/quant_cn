"""Buy 中证1000 or 科创50 when their own volatility is extreme? Absolute level, not the gap.
Series: 中证1000 = index cache 2015..2026-08 extended with 512100 pct_chg; 科创50 = 588000 ETF pct_chg (from 2020-11).
Realized signal: 20-day realized vol at or above the 90th percentile of its trailing 3 years (min 1 year). Implied signal: the
option VIX line (vix_lines.csv from vix_divergence.py) at or above the 90th percentile of its history to date (min 120 days).
Episodes start ≥ 20 sessions apart; per episode: return after 20 / 60 / 120 sessions, worst point within 60. Unconditional
averages of the same horizons for comparison."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache"); OUT = Config.load().lake.root / "meta/runs/research/20261116_vix_divergence"
L = "/Volumes/Treasury/quant_cn_lake/curated"
b = pd.read_csv(SRC / "000852_SH_5min.csv", usecols=["trade_time", "close", "trade_date"]); c1000 = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close
c1000.index = c1000.index.astype(str).str.replace("-", "")
e = duckdb.sql(f"select ts_code, trade_date, pct_chg from read_parquet('{L}/fund_daily/**/*.parquet', hive_partitioning=true) where ts_code in ('512100.SH','588000.SH')").df()
E = e.pivot(index="trade_date", columns="ts_code", values="pct_chg").sort_index() / 100
ext = c1000.iloc[-1] * (1 + E["512100.SH"][E.index > c1000.index[-1]]).cumprod()
S = {"中证1000": pd.concat([c1000, ext]), "科创50": (1 + E["588000.SH"].dropna()).cumprod()}
iv = pd.read_csv(OUT / "vix_lines.csv", index_col=0); iv.index = iv.index.astype(str)
IV = {"中证1000": iv.cn_1000.dropna(), "科创50": iv.cn_star50.dropna()}
pd.set_option("display.width", 220)
def episodes(flag):
    idx = list(flag.index); st = flag.index[flag & ~flag.shift(1, fill_value=False)]; ep = []
    for s in st:
        if not ep or idx.index(s) - idx.index(ep[-1]) > 20: ep.append(s)
    return ep
for nm, p in S.items():
    r = np.log(p / p.shift(1)); rv = (r.rolling(20).std() * np.sqrt(252) * 100).dropna()
    pr = rv.rolling(750, min_periods=250).apply(lambda x: (x <= x[-1]).mean(), raw=True).dropna()
    v = IV[nm]; pv = v.expanding(min_periods=120).apply(lambda x: (x <= x[-1]).mean(), raw=True).dropna()
    print(f"\n==== {nm}: now realized vol {rv.iloc[-1]:.1f} (pct {pr.iloc[-1]:.0%} of 3y), implied VIX {v.iloc[-1]:.1f} (pct {pv.iloc[-1]:.0%} since {v.index[0]}) ====")
    base = {h: np.log(p.shift(-h) / p).dropna().mean() * 100 for h in (20, 60, 120)}
    print("unconditional mean %:", {h: round(x, 2) for h, x in base.items()})
    for lab, flag in (("realized ≥ 90%", pr >= 0.9), ("implied ≥ 90%", pv >= 0.9)):
        rows = []
        for s in episodes(flag):
            i = p.index.get_loc(s); o = {"start": s}
            for h in (20, 60, 120): o[f"r{h}%"] = (p.iloc[i + h] / p.iloc[i] - 1) * 100 if i + h < len(p) else np.nan
            w = p.iloc[i + 1:i + 61]; o["worst60%"] = (w.min() / p.iloc[i] - 1) * 100 if len(w) else np.nan; rows.append(o)
        D = pd.DataFrame(rows)
        print(f"\n[{lab}] episodes {len(D)}"); print(D.round(1).to_string(index=False))
        for h in (20, 60, 120):
            x = D[f"r{h}%"].dropna(); print(f"  {h}d: n {len(x)}, mean {x.mean():.1f}%, median {x.median():.1f}%, positive {int((x>0).sum())}/{len(x)}")
