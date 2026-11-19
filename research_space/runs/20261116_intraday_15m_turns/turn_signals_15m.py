"""Do 15-minute turning signals (变盘信号) on A-share indices predict the next moves?
Input: legacy 5-minute index cache (Tushare idx_mins via the chinese_market project), 6 indices, 2015-01 .. 2026-08,
resampled to 16 bars a day ending 09:45 .. 11:30, 13:15 .. 15:00 (the 09:30 call-auction print goes into the first bar).
Signals, each bar t, no look-ahead (uses bars <= t):
  autocorr   sign of r_t -> r_{t+1}                                (momentum > 0, reversal < 0)
  big        |r_t| > 2 x the slot's 60-day std; follow-up = sign(r_t) x next bar / rest of day
  run3       3 consecutive same-sign bars; follow-up = sign x next bar
  volrev     bar volume > 2 x slot 20-day mean AND sign(r_t) opposite to the previous 4 bars' return (放量反转 candle);
             follow-up = sign(r_t) x next 4 bars (positive = the turn holds)
  dip_turn   index down > 1% from prev close at some bar before 11:00, then the first up bar; follow-up = that bar -> close
Reported: n, mean follow-up in bp, t, hit rate, by era 2015-19 / 2020-26. Index level, before costs; broad ETFs are T+1."""
import numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
OUT = Path(Config.load().lake.root) / "meta/runs/research/20261116_intraday_15m_turns"; OUT.mkdir(parents=True, exist_ok=True)
NAMES = {"000001": "上证指数", "000016": "上证50", "000300": "沪深300", "000905": "中证500", "000852": "中证1000", "399006": "创业板指"}
ENDS = ["09:45", "10:00", "10:15", "10:30", "10:45", "11:00", "11:15", "11:30", "13:15", "13:30", "13:45", "14:00", "14:15", "14:30", "14:45", "15:00"]
def bars15(f):
    b = pd.read_csv(f, usecols=["trade_time", "close", "vol", "trade_date"])
    hm = b.trade_time.str[11:16]
    slot = pd.Series(np.searchsorted(ENDS, hm.values, side="left"), index=b.index).clip(upper=15)
    b["slot"] = slot.values
    g = b.groupby(["trade_date", "slot"]).agg(close=("close", "last"), vol=("vol", "sum")).reset_index()
    C = g.pivot(index="trade_date", columns="slot", values="close"); V = g.pivot(index="trade_date", columns="slot", values="vol")
    ok = C.notna().sum(axis=1) == 16
    return C[ok], V[ok]
def stat(x):
    x = pd.Series(x).dropna()
    return {"n": len(x), "bp": x.mean() * 1e4, "t": x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan, "hit": (x > 0).mean()}
rows = []; slot_ac = []
for f in sorted(SRC.glob("[0-9]*_5min.csv")):
    name = NAMES[f.name[:6]]; C, V = bars15(f)
    prev = C[15].shift(1); R = np.log(C / C.shift(1, axis=1)); R[0] = np.log(C[0] / prev); R = R.iloc[1:]; C = C.loc[R.index]; V = V.loc[R.index]
    sd = R.rolling(60, min_periods=40).std().shift(1); vm = V.rolling(20, min_periods=15).mean().shift(1)
    era = pd.Series(np.where(R.index < "2020", "2015-19", "2020-26"), index=R.index)
    rest = lambda t: R.loc[:, t + 1:].sum(axis=1)
    out = {k: [] for k in ("autocorr", "big_next", "big_rest", "run3", "volrev", "dip_turn")}
    for t in range(0, 15):
        s = np.sign(R[t]); nxt = R[t + 1]
        out["autocorr"].append(pd.DataFrame({"y": s * nxt, "era": era}))
        big = R[t].abs() > 2 * sd[t]
        out["big_next"].append(pd.DataFrame({"y": (s * nxt)[big], "era": era[big]}))
        out["big_rest"].append(pd.DataFrame({"y": (s * rest(t))[big], "era": era[big]}))
        if t >= 2:
            run = (np.sign(R[t]) == np.sign(R[t - 1])) & (np.sign(R[t]) == np.sign(R[t - 2])) & (R[t] != 0)
            out["run3"].append(pd.DataFrame({"y": (s * nxt)[run], "era": era[run]}))
        if 4 <= t <= 11:
            prior = R.loc[:, t - 4:t - 1].sum(axis=1)
            vr = (V[t] > 2 * vm[t]) & (np.sign(R[t]) == -np.sign(prior)) & (prior.abs() > sd[t])
            out["volrev"].append(pd.DataFrame({"y": (s * R.loc[:, t + 1:t + 4].sum(axis=1))[vr], "era": era[vr]}))
        sa = stat(s * nxt); sa.update({"index": name, "slot": ENDS[t]}); slot_ac.append(sa)
    # dip_turn: first up bar (slot <= 5, i.e. by 11:00) after the index is > 1% below the previous close
    lvl = np.log(C.div(prev.loc[C.index], axis=0)); ys, es = [], []
    for d in R.index:
        down = np.where(lvl.loc[d, :5].values < -0.01)[0]
        if len(down) == 0: continue
        k = down[0]; ups = [t for t in range(k + 1, 15) if R.loc[d, t] > 0]
        if not ups: continue
        t = ups[0]; ys.append(R.loc[d, t + 1:].sum()); es.append(era[d])
    out["dip_turn"].append(pd.DataFrame({"y": ys, "era": es}))
    for k, parts in out.items():
        D = pd.concat(parts)
        for e, g in [("all", D), *D.groupby("era")]:
            r = stat(g.y); r.update({"index": name, "signal": k, "era": e}); rows.append(r)
T = pd.DataFrame(rows); T.to_csv(OUT / "turn_signals_15m.csv", index=False)
A = pd.DataFrame(slot_ac); A.to_csv(OUT / "autocorr_by_slot.csv", index=False)
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
print(T[T.era == "all"].pivot_table(index="signal", columns="index", values="bp").round(1).to_string())
print(T[T.era == "all"].pivot_table(index="signal", columns="index", values="t").round(1).to_string())
print(T[T.era == "all"].pivot_table(index="signal", columns="index", values="hit").round(3).to_string())
print(T[T.era == "all"].pivot_table(index="signal", columns="index", values="n").to_string())
print(T[T.era != "all"].pivot_table(index=["signal", "era"], columns="index", values="bp").round(1).to_string())
print(A.pivot_table(index="slot", columns="index", values="t", sort=False).round(1).to_string())
