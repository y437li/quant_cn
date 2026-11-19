"""Does a second condition add value inside the gap tail? Within dear (gi > 0.8) or cheap (gi <= 0.2)
names, fwd20 / fwd60 excess of names meeting the condition minus those not meeting it, per month;
t over months (fwd60 on every 3rd month). All covered stocks and large caps (top 40% size)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from nonlinear_use import load, tstat  # same folder


def diff(p: pd.DataFrame, tail: pd.Series, cond: pd.Series, y: str) -> tuple[float, float]:
    a = p[tail & cond].groupby("date")[y].mean()
    b = p[tail & ~cond].groupby("date")[y].mean()
    d = (a - b).dropna()
    if y == "ex60":
        d = d.iloc[::3]
    return round(d.mean(), 2), round(tstat(d), 2)


def main() -> None:
    p = load()
    rk = {c: p.groupby("date")[c].rank(pct=True) for c in ["rev20", "mom", "turn", "grow", "size"]}
    dear, cheap, big = p.gi > 0.8, p.gi <= 0.2, rk["size"] > 0.6
    tests = {
        "dear: rev20 top20%": (dear, rk["rev20"] > 0.8),
        "dear: mom top30%": (dear, rk["mom"] > 0.7),
        "dear: turnover top30%": (dear, rk["turn"] > 0.7),
        "dear: gauge>=0.7": (dear & p.gauge.notna(), p.gauge >= 0.7),
        "dear: growth bottom40%": (dear, rk["grow"] <= 0.4),
        "cheap: growth top40%": (cheap, rk["grow"] > 0.6),
        "cheap: mom not bottom20%": (cheap, rk["mom"] > 0.2),
        "cheap: rev20 bottom30%": (cheap, rk["rev20"] <= 0.3),
        "cheap: turnover not top30%": (cheap, rk["turn"] <= 0.7),
        "cheap: gauge<=0.3": (cheap & p.gauge.notna(), p.gauge <= 0.3),
    }
    rows = {}
    for k, (tail, cond) in tests.items():
        for lab, t in (("all", tail), ("large", tail & big)):
            m20, t20 = diff(p, t, cond, "ex20")
            m60, t60 = diff(p, t, cond, "ex60")
            rows[(k, lab)] = {"Δex20%": m20, "t20": t20, "Δex60%": m60, "t60": t60}
    pd.set_option("display.width", 200)
    print(pd.DataFrame(rows).T.unstack().swaplevel(axis=1).sort_index(axis=1).to_string())


if __name__ == "__main__":
    main()
