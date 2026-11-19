"""Do consecutive closing pushes (连续尾盘拉升) predict what comes next?
Input: legacy 5-minute index cache, 6 indices, 2015-01 .. 2026-08. Day t's last-15-min return rL = ln(C_15:00 / C_14:45).
Streaks ending on day t (counted only when day t+1 breaks or continues; signal is evaluated on every day the streak length
reaches k): 'up' = rL > 0; 'strong' = rL above the 70th percentile of its trailing 250 days; 'strong+vol' = strong and
last-15-min volume > 1.2x its 20-day mean. Forward returns from day t's close: 1, 5, 20 days (log), minus the unconditional
mean of the same index and era (excess). t uses n / h effective observations for the overlapping 5 / 20-day windows.
Also: what the day's return (09:30-14:45) was on the streak days, i.e. were pushes rescuing falling days."""
import numpy as np, pandas as pd
from pathlib import Path
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
NAMES = {"000001": "上证指数", "000016": "上证50", "000300": "沪深300", "000905": "中证500", "000852": "中证1000", "399006": "创业板指"}
rows = []
for f in sorted(SRC.glob("[0-9]*_5min.csv")):
    b = pd.read_csv(f, usecols=["trade_time", "close", "vol", "trade_date"]); b["hm"] = b.trade_time.str[11:16]
    c = lambda hm: b[b.hm == hm].set_index("trade_date").close
    d = pd.DataFrame({"c1445": c("14:45"), "c1500": c("15:00"), "vL": b[b.hm.isin(["14:50", "14:55", "15:00"])].groupby("trade_date").vol.sum()}).dropna()
    d["rL"] = np.log(d.c1500 / d.c1445); d["pre"] = np.log(d.c1445 / d.c1500.shift(1))
    d["vr"] = d.vL / d.vL.rolling(20, min_periods=15).mean().shift(1)
    q70 = d.rL.rolling(250, min_periods=120).quantile(0.7).shift(1)
    flags = {"up": d.rL > 0, "strong": d.rL > q70, "strong+vol": (d.rL > q70) & (d.vr > 1.2)}
    for h in (1, 5, 20): d[f"f{h}"] = np.log(d.c1500.shift(-h) / d.c1500)
    d["era"] = np.where(d.index < "2020", "2015-19", "2020-26")
    for h in (1, 5, 20): d[f"x{h}"] = d[f"f{h}"] - d.groupby("era")[f"f{h}"].transform("mean")
    for name, fl in flags.items():
        run = fl.groupby((~fl).cumsum()).cumsum()
        d[f"k_{name}"] = run
    d["index"] = NAMES[f.name[:6]]; rows.append(d.dropna(subset=["f20", "vr"]))
D = pd.concat(rows)
pd.set_option("display.width", 220)
def st(g):
    out = {"n": len(g)}
    for h in (1, 5, 20):
        x = g[f"x{h}"]; out[f"x{h}bp"] = x.mean() * 1e4; out[f"t{h}"] = x.mean() / x.std() * np.sqrt(max(len(x) / h, 1)) if len(x) > 2 else np.nan
    out["up20"] = (g.f20 > 0).mean(); out["pre_bp"] = g.pre.mean() * 1e4
    return pd.Series(out)
for name in ("up", "strong", "strong+vol"):
    k = D[f"k_{name}"].clip(upper=5).astype(int)
    print(f"\n== streak of '{name}' closing pushes (k = consecutive days, 5 = 5+), pooled 6 indices; excess vs unconditional ==")
    print(D.groupby(k).apply(st, include_groups=False).round(2).to_string())
k = D["k_strong"].clip(upper=4).astype(int)
print("\n== 'strong' streak >= 3 by index (excess bp) ==")
print(D[k >= 3].groupby("index").apply(st, include_groups=False).round(2).to_string())
print("\n== 'strong' streak >= 3 by era ==")
print(D[k >= 3].groupby("era").apply(st, include_groups=False).round(2).to_string())
print("\nbase rates: share of days with rL > 0:", round((D.rL > 0).mean(), 3))
