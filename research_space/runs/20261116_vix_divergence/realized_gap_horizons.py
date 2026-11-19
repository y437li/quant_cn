"""Follow-up to realized_gap.py: longer horizons. Same realized-vol gap (中证1000 − 沪深300, 20-day) and trailing 3-year
percentile, 2016..2026-08 (index cache). For H = 20, 40, 60, 120, 250 sessions: relative return (1000 − 300) and each leg by gap
bucket, t on n / H effective observations, and per distinct episode (first day the percentile reaches 90%): share positive and
mean, with episodes too close to the data end dropped. Also the daily switching rule with a holding period: once the signal
fires, hold 1000 for H sessions (re-armed by new signals), else 300."""
import numpy as np, pandas as pd
from pathlib import Path
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
cl = {}
for code, f in (("c1000", "000852_SH_5min.csv"), ("c300", "000300_SH_5min.csv")):
    b = pd.read_csv(SRC / f, usecols=["trade_time", "close", "trade_date"]); cl[code] = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close
P = pd.DataFrame(cl).dropna(); R = np.log(P / P.shift(1))
rv = R.rolling(20).std() * np.sqrt(252) * 100; gap = (rv.c1000 - rv.c300).dropna()
pct = gap.rolling(750, min_periods=250).apply(lambda x: (x <= x[-1]).mean(), raw=True).dropna()
hot = pct >= 0.9; starts = pct.index[hot & ~hot.shift(1, fill_value=False)]
# merge starts closer than 20 sessions into one episode
idx = list(pct.index); ep = []
for s in starts:
    if not ep or idx.index(s) - idx.index(ep[-1]) > 20: ep.append(s)
pd.set_option("display.width", 220)
print(f"{pct.index[0]}..{pct.index[-1]}, episodes (starts ≥ 20 sessions apart): {len(ep)}")
rows, erows = [], []
nxt = R.shift(-1)
for H in (20, 40, 60, 120, 250):
    f = np.log(P.shift(-H) / P); rel = (f.c1000 - f.c300)
    D = pd.DataFrame({"pct": pct, "rel": rel, "f1000": f.c1000, "f300": f.c300}).dropna()
    D["b"] = pd.cut(D.pct, [0, .5, .8, .9, 1.0], labels=["<50%", "50-80%", "80-90%", "≥90%"], include_lowest=True)
    for b, g in D.groupby("b", observed=True):
        rows.append({"H": H, "bucket": b, "n_days": len(g), "rel%": g.rel.mean() * 100, "t": g.rel.mean() / g.rel.std() * np.sqrt(max(len(g) / H, 1)),
                     "rel_up": (g.rel > 0).mean(), "1000%": g.f1000.mean() * 100, "300%": g.f300.mean() * 100})
    e = D.rel.reindex([s for s in ep if s in D.index]).dropna()
    erows.append({"H": H, "episodes": len(e), "positive": int((e > 0).sum()), "mean%": e.mean() * 100, "median%": e.median() * 100, "worst%": e.min() * 100})
    on = pd.Series(0.0, index=pct.index); pos = [pct.index.get_loc(s) for s in starts]
    for p0 in [pct.index.get_loc(s) for s in pct.index[hot]]: on.iloc[p0:p0 + H] = 1.0
    s = (on * nxt.c1000.reindex(on.index) + (1 - on) * nxt.c300.reindex(on.index)).dropna()
    b300 = nxt.c300.reindex(s.index); b1000 = nxt.c1000.reindex(s.index)
    erows[-1].update({"rule_ann%": s.mean() * 252 * 100, "rule_sharpe": s.mean() / s.std() * np.sqrt(252), "300_ann%": b300.mean() * 252 * 100,
                      "1000_ann%": b1000.mean() * 252 * 100, "time_in_1000": on.mean()})
print(pd.DataFrame(rows).round(2).to_string(index=False))
print(pd.DataFrame(erows).round(2).to_string(index=False))
print("episode starts:", ep)
