"""Try the RetailGauge in the score: month ends 2023-01 .. 2026-10. Current score (derived.features,
7 factors) vs score8 = mean of the 7 processed factors and z(-gauge) (gauge percentile turned into a
cross-sectional z, sign flipped so a cold gauge scores high). Rank IC fwd20 / fwd60, quintile and decile
long-short Sharpe, top-quintile excess; all and large caps. Gauge history only from 2023."""
from __future__ import annotations

import numpy as np
import pandas as pd

from turnover_vs_gauge import load, tstat  # same folder: month-end panel with gauge and returns
from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SEVEN = ["dividend_yield", "roe_ttm", "profit_growth_ttm", "momentum_12_1", "reversal_1m", "turnover_60d", "pricing_gap"]


def main() -> None:
    m = load()
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    f = LakeQuery(cat).sql("SELECT trade_date, ts_code, factor, value FROM derived.features WHERE trade_date IN (SELECT UNNEST(?)) "
                           "AND factor IN (SELECT UNNEST(?))", [sorted(m["trade_date"].unique()), [*SEVEN, "score"]])
    cat.close()
    w = f.pivot_table(index=["trade_date", "ts_code"], columns="factor", values="value").reset_index()
    m = m.merge(w, on=["trade_date", "ts_code"])
    g = m.groupby("trade_date")["gauge"]
    m["zg"] = -(m["gauge"] - g.transform("mean")) / g.transform("std")
    m["score8"] = m[[*SEVEN, "zg"]].mean(axis=1)
    m["score7"] = m[SEVEN].mean(axis=1)
    pd.set_option("display.width", 200)
    for label, part in (("all", m), ("large caps", m[m.groupby("trade_date")["total_mv"].rank(pct=True) > 0.6])):
        rows = {}
        for col in ("score", "score8", "zg"):
            r = {}
            for h, step in ((20, 1), (60, 3)):
                ic = part.dropna(subset=[f"ex{h}"]).groupby("trade_date").apply(lambda x, c=col, hh=h: x[c].rank().corr(x[f"ex{hh}"].rank()))
                r[f"IC{h}"] = round(ic.mean(), 4)
                r[f"t{h}"] = round(tstat(ic, step), 2)
            for k, lab in ((5, "Q"), (10, "D")):
                grp = part.groupby("trade_date").apply(lambda x, c=col, kk=k: x.assign(b=pd.qcut(x[c].rank(method="first"), kk, labels=False)).groupby("b")["ex20"].mean())
                ls = grp[k - 1] - grp[0]
                r[f"{lab} LS %/m"] = round(ls.mean(), 2)
                r[f"{lab} Sharpe"] = round(ls.mean() / ls.std() * 12**0.5, 2)
                r[f"{lab} top %/m"] = round(grp[k - 1].mean(), 2)
            rows[col] = r
        print(f"\n## {label}: {part['trade_date'].nunique()} months\n", pd.DataFrame(rows).T.to_string())


if __name__ == "__main__":
    main()
