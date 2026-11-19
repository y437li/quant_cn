"""Follow-up: does a 15-minute bar carry into the next half hour (next 2 bars)? Same index bars as turn_signals_15m.py.
Per signal bar: big (> 2x slot 60-day std) and ordinary (all bars), sign(r_t) x (r_{t+1} + r_{t+2}); by time slot for big bars;
and the 做T view: the share of big bars whose next-30-min follow-through exceeds 5 bp (about one 510300 tick plus fees)."""
import numpy as np, pandas as pd, importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("t", Path(__file__).with_name("turn_signals_15m.py"))
src = Path(__file__).with_name("turn_signals_15m.py").read_text().split("rows = []; slot_ac = []")[0]
exec(src)
rows = []
for f in sorted(SRC.glob("[0-9]*_5min.csv")):
    name = NAMES[f.name[:6]]; C, V = bars15(f)
    prev = C[15].shift(1); R = np.log(C / C.shift(1, axis=1)); R[0] = np.log(C[0] / prev); R = R.iloc[1:]
    sd = R.rolling(60, min_periods=40).std().shift(1)
    for t in range(0, 14):
        s = np.sign(R[t]); y = s * (R[t + 1] + R[t + 2]); big = R[t].abs() > 2 * sd[t]
        rows.append(pd.DataFrame({"index": name, "slot": ENDS[t], "big": big, "y": y, "era": np.where(R.index < "2020", "2015-19", "2020-26")}))
D = pd.concat(rows).dropna()
def st(x): return pd.Series({"n": len(x), "bp": x.mean() * 1e4, "t": x.mean() / x.std() * np.sqrt(len(x)), "hit": (x > 0).mean(), ">5bp": (x > 0.0005).mean()})
pd.set_option("display.width", 200)
print("next 30 min after a bar, by index (all bars vs big bars)")
print(D.groupby(["index", "big"]).y.apply(st).unstack().round(3).to_string())
print("\nbig bars by era"); print(D[D.big].groupby(["index", "era"]).y.apply(st).unstack().round(3).to_string())
print("\nbig bars by slot, all indices pooled"); print(D[D.big].groupby("slot", sort=False).y.apply(st).unstack().round(3).to_string())
