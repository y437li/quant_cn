"""Can the first 10 minutes of the last quarter hour (14:45-14:55) be used to buy in the last 5 minutes?
Input: legacy 5-minute index cache, 6 indices, 2015-01 .. 2026-08. The 15:00 bar holds 14:55-14:57 continuous trading plus the
14:57-15:00 closing call auction. Signal at 14:55: r10 = ln(C_14:55 / C_14:45), v10 = volume of the 14:50 + 14:55 bars over its
20-day mean. 'push10' = r10 in the top 30% of its trailing 250 days and v10 > 1.2.
Outcomes: last 5 min ln(C_15:00 / C_14:55); next day from the close ln(C_{t+1} / C_15:00); entry at 14:55 to next close
ln(C_{t+1} / C_14:55); 5 days from the close. Excess = minus the unconditional mean of the same index and era."""
import numpy as np, pandas as pd
from pathlib import Path
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
NAMES = {"000001": "上证指数", "000016": "上证50", "000300": "沪深300", "000905": "中证500", "000852": "中证1000", "399006": "创业板指"}
rows = []
for f in sorted(SRC.glob("[0-9]*_5min.csv")):
    b = pd.read_csv(f, usecols=["trade_time", "close", "vol", "trade_date"]); b["hm"] = b.trade_time.str[11:16]
    c = lambda hm: b[b.hm == hm].set_index("trade_date").close
    d = pd.DataFrame({"c45": c("14:45"), "c55": c("14:55"), "c00": c("15:00"),
                      "v10": b[b.hm.isin(["14:50", "14:55"])].groupby("trade_date").vol.sum(), "v5": b[b.hm == "15:00"].set_index("trade_date").vol}).dropna()
    d["r10"] = np.log(d.c55 / d.c45); d["vr10"] = d.v10 / d.v10.rolling(20, min_periods=15).mean().shift(1)
    q = d.r10.rolling(250, min_periods=120).quantile(0.7).shift(1); ql = d.r10.rolling(250, min_periods=120).quantile(0.3).shift(1)
    d["push10"] = (d.r10 > q) & (d.vr10 > 1.2); d["dump10"] = (d.r10 < ql) & (d.vr10 > 1.2)
    d["last5"] = np.log(d.c00 / d.c55); d["next"] = np.log(d.c00.shift(-1) / d.c00); d["from55"] = np.log(d.c00.shift(-1) / d.c55)
    d["d5"] = np.log(d.c00.shift(-5) / d.c00); d["v5r"] = d.v5 / d.v5.rolling(20, min_periods=15).mean().shift(1)
    d["era"] = np.where(d.index < "2020", "2015-19", "2020-26"); d["index"] = NAMES[f.name[:6]]
    for k in ("last5", "next", "from55", "d5"): d["x_" + k] = d[k] - d.groupby("era")[k].transform("mean")
    rows.append(d.dropna(subset=["d5", "vr10"]))
D = pd.concat(rows)
pd.set_option("display.width", 220)
def st(g):
    o = {"n": len(g)}
    for k, h in (("last5", 1), ("next", 1), ("from55", 1), ("d5", 5)):
        x = g["x_" + k]; o[k + "_bp"] = x.mean() * 1e4; o[k + "_t"] = x.mean() / x.std() * np.sqrt(len(x) / h)
    o["last5_same"] = (np.sign(g.last5) == np.sign(g.r10)).mean(); o["next_up"] = (g.next > 0).mean()
    return pd.Series(o)
print("rank corr r10 -> last5, by index/era:"); print(D.groupby(["index", "era"]).apply(lambda g: g.r10.corr(g.last5, method="spearman"), include_groups=False).unstack().round(3).to_string())
D["q"] = D.groupby(["index"]).r10.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
print("\nby r10 quintile (0 = most down), pooled, excess"); print(D.groupby("q").apply(st, include_groups=False).round(2).to_string())
for flag in ("push10", "dump10"):
    print(f"\n[{flag}] pooled"); print(st(D[D[flag]]).round(2).to_string())
    print(D[D[flag]].groupby("era").apply(st, include_groups=False).round(2).to_string())
two = D.groupby("index").push10.transform(lambda s: s & s.shift(1).fillna(False).astype(bool))
print("\n[push10 two days running]"); print(st(D[two]).round(2).to_string())
print("\ndoes a 10-min push come with a big closing auction? last-5 volume ratio median: push10 %.2f vs all %.2f" % (D[D.push10].v5r.median(), D.v5r.median()))
