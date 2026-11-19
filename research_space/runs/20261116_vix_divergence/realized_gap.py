"""Longer test of the small-vs-large volatility gap using realized volatility (implied 中证1000 VIX only starts 2022-07).
Daily closes of 000852 (中证1000) and 000300 (沪深300) from the legacy 5-minute index cache (15:00 bar), 2015-01 .. 2026-08.
Gap = 20-day realized vol (annualised) of 1000 minus 300; percentile on a trailing 3-year window (no look-ahead).
Next 20 days: 1000 minus 300 log return, and each leg. Also a switching rule: hold 1000 when the gap percentile >= 90%, else 300,
vs always 300 and always 1000 (before costs, monthly-ish turnover). Also checks the implied gap (2022-07 on) against the realized gap."""
import numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
OUT = Config.load().lake.root / "meta/runs/research/20261116_vix_divergence"
cl = {}
for code, f in (("c1000", "000852_SH_5min.csv"), ("c300", "000300_SH_5min.csv")):
    b = pd.read_csv(SRC / f, usecols=["trade_time", "close", "trade_date"]); cl[code] = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close
P = pd.DataFrame(cl).dropna(); P.index = P.index.astype(str).str.replace("-", ""); R = np.log(P / P.shift(1))
rv = R.rolling(20).std() * np.sqrt(252) * 100; gap = (rv.c1000 - rv.c300).dropna()
pct = gap.rolling(750, min_periods=250).apply(lambda x: (x <= x[-1]).mean(), raw=True)
H = 20; f = np.log(P.shift(-H) / P); rel = (f.c1000 - f.c300)
D = pd.DataFrame({"gap": gap, "pct": pct, "rel": rel, "f1000": f.c1000, "f300": f.c300}).dropna()
D["b"] = pd.cut(D.pct, [0, .5, .8, .9, 1.0], labels=["<50%", "50-80%", "80-90%", "≥90%"], include_lowest=True)
D["era"] = np.where(D.index < "2020", "2015-19", "2020-26")
pd.set_option("display.width", 200)
agg = lambda g: pd.Series({"n": len(g), "rel%": g.rel.mean() * 100, "t": g.rel.mean() / g.rel.std() * np.sqrt(len(g) / H), "rel_up": (g.rel > 0).mean(), "1000%": g.f1000.mean() * 100, "300%": g.f300.mean() * 100})
print(f"days {len(D)} from {D.index[0]}; realized gap now (last in cache {gap.index[-1]}): {gap.iloc[-1]:.1f}, pct {pct.iloc[-1]:.0%}")
print(D.groupby("b", observed=True).apply(agg, include_groups=False).round(2).to_string())
print(D.groupby(["era", "b"], observed=True).apply(agg, include_groups=False).round(2).to_string())
# episodes: distinct runs of pct >= 90%
hot = D.pct >= 0.9; ep = (hot & ~hot.shift(1, fill_value=False)).cumsum()[hot]
E = D[hot].groupby(ep).apply(lambda g: pd.Series({"start": g.index[0], "days": len(g), "gap": g.gap.iloc[0], "rel20_from_start%": g.rel.iloc[0] * 100}), include_groups=False)
print(f"\nepisodes with pct >= 90%: {len(E)}; rel from the first day: mean {E['rel20_from_start%'].mean():.2f}%, positive {int((E['rel20_from_start%'] > 0).sum())}/{len(E)}")
print(E.round(2).to_string())
# switching rule, daily rebalance on the signal known at t (next-day returns)
nxt = R.shift(-1).reindex(D.index)
sig = (D.pct >= 0.9).astype(float)
strat = sig * nxt.c1000 + (1 - sig) * nxt.c300
for name, s in (("switch", strat), ("always 300", nxt.c300), ("always 1000", nxt.c1000)):
    s = s.dropna(); print(f"{name:12s} ann {s.mean()*252*100:6.2f}%  vol {s.std()*np.sqrt(252)*100:5.1f}%  sharpe {s.mean()/s.std()*np.sqrt(252):.2f}")
print("switches per year:", round(sig.diff().abs().sum() / (len(sig) / 252), 1))
try:
    iv = pd.read_csv(OUT / "vix_lines.csv", index_col=0); iv.index = iv.index.astype(str)
    ig = (iv.cn_1000 - iv.cn_300).dropna(); j = pd.concat([ig.rename("implied"), gap.rename("realized")], axis=1).dropna()
    print(f"\nimplied vs realized gap {j.index[0]}..{j.index[-1]}: corr {j.implied.corr(j.realized):.2f}, n {len(j)}")
except FileNotFoundError:
    pass
