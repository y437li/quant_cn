"""Does 招商蛇口 (001979.SZ) mean-revert at Bollinger bands? (2026-11-18, ad hoc)

Bands: 20-day mean +- 2 sd of adjusted close. Events: first close below the lower band (and above
the upper band). Forward 5/10/20-day returns of the stock and in excess of 申万房地产 (801180.SI),
against all days; hit rate of touching the middle band within 20 days. Peers as a check.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
STOCKS = {"001979.SZ": "招商蛇口", "600048.SH": "保利发展", "000002.SZ": "万科A", "600325.SH": "华发股份", "600383.SH": "金地集团"}
SECTOR = "801180.SI"
N, K, HOR = 20, 2.0, (5, 10, 20)
START = "20160101"


def load(q: LakeQuery) -> tuple[pd.DataFrame, pd.Series]:
    px = q.sql("SELECT ts_code, trade_date, close_adj FROM derived.prices_adj WHERE ts_code IN (SELECT UNNEST(?)) AND trade_date >= ?",
               [list(STOCKS), START]).pivot(index="trade_date", columns="ts_code", values="close_adj").sort_index()
    sec = q.sql("SELECT trade_date, close FROM curated.sw_daily WHERE ts_code = ? AND trade_date >= ?", [SECTOR, START])
    return px, sec.set_index("trade_date")["close"].sort_index()


def events(close: pd.Series, sec: pd.Series) -> pd.DataFrame:
    mid = close.rolling(N).mean()
    sd = close.rolling(N).std()
    lo, up = mid - K * sd, mid + K * sd
    below, above = close < lo, close > up
    out = pd.DataFrame({"close": close, "mid": mid, "lo": lo, "up": up, "pctb": (close - lo) / (up - lo)})
    out["low_evt"] = below & ~below.shift(1, fill_value=False)
    out["up_evt"] = above & ~above.shift(1, fill_value=False)
    s = sec.reindex(close.index).ffill()
    for h in HOR:
        out[f"r{h}"] = (close.shift(-h) / close - 1) * 100
        out[f"x{h}"] = out[f"r{h}"] - (s.shift(-h) / s - 1) * 100
    # touched the middle band within 20 sessions
    hit = pd.Series(False, index=close.index)
    for k in range(1, 21):
        hit |= close.shift(-k) >= mid.shift(-k)
    out["mid_hit"] = hit
    # worst drawdown within 20 sessions
    fut_min = pd.concat([close.shift(-k) for k in range(1, 21)], axis=1).min(axis=1)
    out["mae20"] = (fut_min / close - 1) * 100
    return out


def summarise(e: pd.DataFrame, flag: str) -> dict[str, float]:
    sel = e[e[flag]].dropna(subset=["r20"])
    base = e.dropna(subset=["r20"])
    row: dict[str, float] = {"n": len(sel)}
    for h in HOR:
        row[f"r{h}"] = sel[f"r{h}"].mean()
        row[f"x{h}"] = sel[f"x{h}"].mean()
        row[f"base_x{h}"] = base[f"x{h}"].mean()
    row["win20"] = (sel["r20"] > 0).mean() * 100
    row["xwin20"] = (sel["x20"] > 0).mean() * 100
    row["t_x20"] = sel["x20"].mean() / (sel["x20"].std() / np.sqrt(len(sel))) if len(sel) > 2 else np.nan
    row["mid_hit"] = sel["mid_hit"].mean() * 100
    row["mae20"] = sel["mae20"].median()
    return row


def main() -> None:
    config = Config.load(REPO)
    cat = LakeCatalog(config.lake.root, config.datasets, read_only=True)
    try:
        px, sec = load(LakeQuery(cat))
    finally:
        cat.close()
    pd.set_option("display.width", 220)
    rows = []
    for code, name in STOCKS.items():
        e = events(px[code].dropna(), sec)
        for flag, label in (("low_evt", "跌破下轨"), ("up_evt", "升破上轨")):
            rows.append({"stock": name, "event": label, **summarise(e, flag)})
        if code == "001979.SZ":
            sk = e
            r = px[code].pct_change().dropna()
            print("蛇口 daily ret autocorr lag1..5:", [round(r.autocorr(k), 3) for k in range(1, 6)])
            w = (px[code] / px[code].shift(5) - 1).dropna()
            print("蛇口 weekly(5d) ret autocorr lag1:", round(w.iloc[::5].autocorr(1), 3))
    print(pd.DataFrame(rows).round(2).to_string(index=False))
    # 蛇口 by period
    sk["yr"] = sk.index.str[:4]
    lows = sk[sk["low_evt"]].dropna(subset=["r20"])
    print("\n蛇口 跌破下轨 by year:")
    print(lows.groupby("yr")[["r20", "x20"]].agg(["count", "mean"]).round(2).to_string())
    print("\n蛇口 last 12 lower-band events:")
    print(sk[sk["low_evt"]].tail(12)[["close", "lo", "mid", "r5", "r10", "r20", "x20", "mid_hit", "mae20"]].round(2).to_string())
    last = sk.iloc[-1]
    print(f"\n蛇口 now {sk.index[-1]}: close {last.close:.2f} lo {last.lo:.2f} mid {last.mid:.2f} up {last.up:.2f} %B {last.pctb:.2f}")
    print(sk.tail(8)[["close", "lo", "mid", "up", "pctb"]].round(3).to_string())


if __name__ == "__main__":
    main()
