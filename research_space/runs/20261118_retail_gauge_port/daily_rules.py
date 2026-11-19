"""Plan 21 ph3 check of the D-167 reading rules on the production daily gauge (derived/retail_gauge),
scored like research run 20261117_gauge_daily: readings every 3rd session of the quarter from day 15,
2023Q1..2026Q3, float cap >= 50亿.
- retail_leaving (3 checkpoints in a row <= 0.3): share whose holder count fell over the quarter (research ≈ 81%);
- avoid_strong (3 in a row >= 0.9): 60-session excess vs the others, mean over (quarter, day) (research ≈ -4.3%);
- raw single readings for comparison (research -3.7% / 79%)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.calculation.holder_count_panel import HolderCountPanel
from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
OUT = Path("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261118_retail_gauge_port")


def main() -> None:
    cfg = Config.load(REPO)
    q = LakeQuery(LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True))
    g = q.sql("SELECT * FROM derived.retail_gauge WHERE q BETWEEN '20230331' AND '20260930'")
    g["off"] = g.groupby(["ts_code", "q"])["as_of"].rank(method="first").astype(int)
    sessions = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20221201' ORDER BY 1")
    pos = {d: i for i, d in enumerate(sessions["trade_date"])}
    first = g.groupby("q")["as_of"].transform("min").map(pos)
    g["day"] = g["as_of"].map(pos) - first + 1
    g = g[(g["day"] >= 15) & (g["day"] % 3 == 0)]
    cap = q.sql("SELECT ts_code, trade_date AS as_of, circ_mv / 1e4 AS cmv FROM curated.daily_basic WHERE trade_date >= '20230101'")
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS v FROM curated.daily d "
               "JOIN curated.adj_factor a USING (ts_code, trade_date) WHERE d.trade_date >= '20230101'")
    wide = px.pivot(index="trade_date", columns="ts_code", values="v").sort_index()
    fwd = (wide.shift(-60) / wide - 1).rename_axis("as_of").reset_index().melt(id_vars="as_of", var_name="ts_code", value_name="r60")
    holders = HolderCountPanel(q)
    holders.load("99991231")
    g = g.merge(cap, on=["ts_code", "as_of"], how="left").merge(fwd, on=["ts_code", "as_of"], how="left")
    g = pd.concat([g.reset_index(drop=True), holders.compute_labels(g.reset_index(drop=True))], axis=1)
    g = g[g["cmv"] >= 50]
    g["x"] = (g["r60"] - g.groupby(["q", "day"])["r60"].transform("mean")) * 100
    rows = []
    for name, lo, hi in (("raw", g["pct"] <= 0.3, g["pct"] >= 0.9), ("3 in a row (D-167)", g["retail_leaving"], g["avoid_strong"])):
        by = g.assign(lo=lo, hi=hi).groupby(["q", "day"])
        hot = by.apply(lambda z: z[z.hi].x.mean() - z[~z.hi].x.mean()).groupby(level=0).mean().dropna()
        rows.append({"rule": name, "leaving_holders_fell_pct": round((g[lo].y < 0).mean() * 100, 1),
                     "hot_60d_excess": round(hot.mean(), 2), "t_hot": round(hot.mean() / hot.std() * np.sqrt(len(hot)), 1),
                     "hot_per_day": round(hi.sum() / g.groupby(["q", "day"]).ngroups, 1)})
    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / "daily_rules.csv", index=False)


if __name__ == "__main__":
    main()
