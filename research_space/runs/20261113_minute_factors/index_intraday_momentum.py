"""Intraday momentum on A-share indices (Gao, Han, Li, Zhou 2018): does the first half hour
(prev close -> 10:00) or the middle of the day (10:00 -> 14:30) predict the last half hour (14:30 -> 15:00)?
Input: legacy 5-minute index cache from the chinese_market project (Tushare idx_mins, 2015-2026-08)."""
import numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache")
OUT = Path(Config.load().lake.root) / "meta/runs/research/20261113_minute_factors"; OUT.mkdir(parents=True, exist_ok=True)
rows = []
for f in sorted(SRC.glob("[0-9]*_5min.csv")):
    b = pd.read_csv(f, usecols=["trade_time", "close", "trade_date"])
    b["hm"] = b.trade_time.str[11:16]
    p = b.pivot_table(index="trade_date", columns="hm", values="close")
    need = ["10:00", "14:30", "15:00"]
    p = p.dropna(subset=need)
    d = pd.DataFrame({"first": p["10:00"] / p["15:00"].shift(1) - 1, "mid": p["14:30"] / p["10:00"] - 1,
                      "last": p["15:00"] / p["14:30"] - 1}).dropna()
    for era, g in [("2015-2019", d[d.index < "2020"]), ("2020-2026", d[d.index >= "2020"]), ("all", d)]:
        for x in ("first", "mid"):
            X = np.c_[np.ones(len(g)), g[x]]; beta, *_ = np.linalg.lstsq(X, g["last"], rcond=None)
            e = g["last"] - X @ beta; se = np.sqrt(e.var() / ((g[x] - g[x].mean())**2).sum())
            strat = np.sign(g[x]) * g["last"]
            rows.append({"index": f.name[:9], "era": era, "predictor": x, "n": len(g), "beta": beta[1], "t": beta[1] / se,
                         "R2_%": 100 * (1 - e.var() / g["last"].var()), "timing_bp/day": strat.mean() * 1e4,
                         "timing_sharpe": strat.mean() / strat.std() * np.sqrt(244), "hit": (strat > 0).mean()})
res = pd.DataFrame(rows).round(3); res.to_csv(OUT / "index_intraday_momentum.csv", index=False)
pd.set_option("display.width", 200); print(res.to_string(index=False))
