"""After a late push (first10_last5.py signal), is the next-day gain gone by the open, or can one still buy the next morning?
Same signals (push10, dump10, push10 two days running) on the 6-index 5-minute cache. Next-day legs: overnight
ln(O_{t+1} / C_t) using the 09:35 bar open, open -> 10:00, 10:00 -> close; and entries: 14:55 on day t, the next open, the next
10:00, each held to the close of t+1 and of t+5. Excess vs the unconditional mean of the same leg, index and era."""
import numpy as np, pandas as pd
from pathlib import Path
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
NAMES = {"000001": "上证指数", "000016": "上证50", "000300": "沪深300", "000905": "中证500", "000852": "中证1000", "399006": "创业板指"}
rows = []
for f in sorted(SRC.glob("[0-9]*_5min.csv")):
    b = pd.read_csv(f, usecols=["trade_time", "open", "close", "vol", "trade_date"]); b["hm"] = b.trade_time.str[11:16]
    c = lambda hm: b[b.hm == hm].set_index("trade_date").close
    d = pd.DataFrame({"c45": c("14:45"), "c55": c("14:55"), "c00": c("15:00"), "c10": c("10:00"),
                      "o": b[b.hm == "09:35"].set_index("trade_date").open, "v10": b[b.hm.isin(["14:50", "14:55"])].groupby("trade_date").vol.sum()}).dropna()
    d["r10"] = np.log(d.c55 / d.c45); d["vr10"] = d.v10 / d.v10.rolling(20, min_periods=15).mean().shift(1)
    q = d.r10.rolling(250, min_periods=120).quantile(0.7).shift(1); ql = d.r10.rolling(250, min_periods=120).quantile(0.3).shift(1)
    d["push10"] = (d.r10 > q) & (d.vr10 > 1.2); d["dump10"] = (d.r10 < ql) & (d.vr10 > 1.2)
    d["push2"] = d.push10 & d.push10.shift(1).fillna(False).astype(bool)
    n = lambda s, k=1: s.shift(-k)
    legs = {"overnight": np.log(n(d.o) / d.c00), "open_1000": np.log(n(d.c10) / n(d.o)), "1000_close": np.log(n(d.c00) / n(d.c10)),
            "buy1455_to_t1": np.log(n(d.c00) / d.c55), "buyopen_to_t1": np.log(n(d.c00) / n(d.o)), "buy1000_to_t1": np.log(n(d.c00) / n(d.c10)),
            "buy1455_to_t5": np.log(n(d.c00, 5) / d.c55), "buyopen_to_t5": np.log(n(d.c00, 5) / n(d.o))}
    for k, v in legs.items(): d[k] = v
    d["era"] = np.where(d.index < "2020", "2015-19", "2020-26"); d["index"] = NAMES[f.name[:6]]
    for k in legs: d["x_" + k] = d[k] - d.groupby("era")[k].transform("mean")
    rows.append(d.dropna(subset=["buyopen_to_t5", "vr10"]))
D = pd.concat(rows); L = ["overnight", "open_1000", "1000_close", "buy1455_to_t1", "buyopen_to_t1", "buy1000_to_t1", "buy1455_to_t5", "buyopen_to_t5"]
pd.set_option("display.width", 240)
def st(g):
    o = {"n": len(g)}
    for k in L:
        x = g["x_" + k]; h = 5 if k.endswith("t5") else 1
        o[k] = f"{x.mean()*1e4:+.1f} ({x.mean()/x.std()*np.sqrt(len(x)/h):+.1f})"
    o["gap_up_share"] = round((g.overnight > 0).mean(), 2)
    return pd.Series(o)
print("excess bp (t), pooled 6 indices")
T = pd.DataFrame({k: st(D[D[k]]) for k in ("push10", "push2", "dump10")} | {"all days": st(D)}).T
print(T.to_string())
print("\n2020-26 only"); print(pd.DataFrame({k: st(D[D[k] & (D.era == "2020-26")]) for k in ("push10", "push2")}).T.to_string())
