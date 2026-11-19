"""Odds that 601888.SH touches 48 / 46 / 44 within 21 / 63 / 126 sessions from the 2026-11-12 close."""
from math import erf, sqrt
from pathlib import Path

import duckdb
import numpy as np

from quant_cn.core.config import Config

L = str(Path(Config.load().lake.root) / "curated")
s = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
p = duckdb.sql(f"""select d.trade_date, d.close*a.adj_factor c from {s('daily')} d join {s('adj_factor')} a
  on d.ts_code=a.ts_code and d.trade_date=a.trade_date where d.ts_code='601888.SH' and d.trade_date>='20180101' order by 1""").df()
c = p.c.values
r = np.diff(np.log(c))
NOW = 51.53
k = np.searchsorted(p.trade_date.values, "20240101")
for lvl in (48, 46, 44):
    need, out = np.log(lvl / NOW), []
    for h in (21, 63, 126):
        mins = np.array([np.log(c[i + 1:i + 1 + h].min() / c[i]) for i in range(len(c) - h)])
        sig = r[-60:].std() * sqrt(h)
        model = 2 * 0.5 * (1 + erf(need / sig / sqrt(2)))  # zero-drift reflection principle
        out.append(f"{h}d: all {(mins <= need).mean():.0%} / 2024+ {(mins[k:] <= need).mean():.0%} / vol model {model:.0%}")
    print(lvl, f"({lvl / NOW - 1:+.1%})", " | ".join(out))
