"""Lower-band variants for 招商蛇口 and four developer peers (2026-11-18, ad hoc).

Signals on adjusted close, Bollinger 20 days:
  touch2  first close below mid - 2 sd;   touch25 / touch3  below 2.5 / 3 sd
  reenter first close back above the 2-sd lower band within 10 sessions of a touch
  two_day second consecutive close below the lower band
Forward 5/10/20/40/60-session return, raw and in excess of 申万房地产; t of the mean excess
(events at least 10 sessions apart, so overlapping windows do not inflate t).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bollinger_reversion import STOCKS, load  # same folder

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
N, HOR, GAP = 20, (5, 10, 20, 40, 60), 10


def signals(close: pd.Series) -> pd.DataFrame:
    mid, sd = close.rolling(N).mean(), close.rolling(N).std()
    out = {}
    for k, name in ((2.0, "touch2"), (2.5, "touch25"), (3.0, "touch3")):
        below = close < mid - k * sd
        out[name] = below & ~below.shift(1, fill_value=False)
    below = close < mid - 2 * sd
    out["two_day"] = below & below.shift(1, fill_value=False) & ~below.shift(2, fill_value=False)
    recent = below.rolling(GAP).max().shift(1).fillna(0).astype(bool)
    out["reenter"] = ~below & below.shift(1, fill_value=False) & recent
    return pd.DataFrame(out)


def thin(flags: pd.Series) -> pd.Series:
    """Keep events at least GAP sessions apart."""
    keep, last = [], -GAP
    for i, f in enumerate(flags.to_numpy()):
        if f and i - last >= GAP:
            keep.append(i)
            last = i
    out = pd.Series(False, index=flags.index)
    out.iloc[keep] = True
    return out


def main() -> None:
    config = Config.load(REPO)
    cat = LakeCatalog(config.lake.root, config.datasets, read_only=True)
    try:
        px, sec = load(LakeQuery(cat))
    finally:
        cat.close()
    rows = []
    for code, name in STOCKS.items():
        close = px[code].dropna()
        s = sec.reindex(close.index).ffill()
        sig = signals(close)
        fwd = pd.DataFrame({f"r{h}": (close.shift(-h) / close - 1) * 100 for h in HOR})
        for h in HOR:
            fwd[f"x{h}"] = fwd[f"r{h}"] - (s.shift(-h) / s - 1) * 100
        base = fwd.mean()
        for col in sig:
            ev = fwd[thin(sig[col])].assign(stock=name, signal=col, date=lambda d: d.index)
            rows.append(ev)
        rows.append(fwd.assign(stock=name, signal="all_days", date=fwd.index))
    allev = pd.concat(rows)
    pd.set_option("display.width", 230)

    def table(df: pd.DataFrame) -> pd.DataFrame:
        out = []
        for sig_name, g in df.groupby("signal", sort=False):
            row = {"signal": sig_name, "n": len(g.dropna(subset=["r20"]))}
            for h in HOR:
                x = g[f"x{h}"].dropna()
                row[f"r{h}"] = g[f"r{h}"].mean()
                row[f"x{h}"] = x.mean()
                if h in (20, 60) and sig_name != "all_days":
                    row[f"t{h}"] = x.mean() / (x.std() / np.sqrt(len(x))) if len(x) > 2 else np.nan
                    row[f"win{h}"] = (x > 0).mean() * 100
            out.append(row)
        return pd.DataFrame(out).round(2)

    print("招商蛇口:")
    print(table(allev[allev.stock == "招商蛇口"]).to_string(index=False))
    print("\n五家合计:")
    print(table(allev).to_string(index=False))
    print("\n五家合计, 2023 起:")
    print(table(allev[allev.date >= "20230101"]).to_string(index=False))
    sk = allev[(allev.stock == "招商蛇口") & (allev.signal == "reenter")]
    print("\n蛇口 reenter events:")
    print(sk[["r5", "r20", "x20", "r60", "x60"]].round(1).tail(15).to_string())


if __name__ == "__main__":
    main()
