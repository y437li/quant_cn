"""Long-short of the gap under heavier costs: 0.3% / 0.6% / 1.0% per unit of turnover per leg and a
6% / 10% a year borrow fee on the short leg, for the industry and industry + size neutral 10% legs,
equal weight, all covered stocks and large caps. Reuses neutral_compare.py's ranking."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from long_short import get_turnover, stats  # same folder
from neutral_compare import residualise  # same folder
from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    cfg = Config.load(REPO)
    p = pd.read_parquet(Path(cfg.lake.root) / "meta/runs/research/20261118_linear_pricing_gap/panel_0.7_15.parquet")
    try:
        cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
        mem = LakeQuery(cat).sql("SELECT DISTINCT ts_code, l1_name FROM curated.index_member_all WHERE is_new = 'Y'")
        cat.close()
    except LakeError:  # catalog locked by a writer (curate): read the curated file instead
        raw = pd.read_parquet(Path(cfg.lake.root) / "curated/reference/index_member_all.parquet")
        mem = raw.loc[raw["is_new"] == "Y", ["ts_code", "l1_name"]].drop_duplicates()
    p = p.dropna(subset=["fwd20"]).merge(mem, on="ts_code", how="inner")
    p["r"] = np.exp(p["fwd20"]) - 1
    p["s_ind"] = p.groupby(["date", "l1_name"])["gap"].rank(pct=True)
    p["res"] = p.groupby("date", group_keys=False).apply(residualise)
    p["s_ind_size"] = p.groupby("date")["res"].rank(pct=True)
    big = p.groupby("date")["size"].rank(pct=True) > 0.6
    rows = {}
    for uni, u in (("all", p), ("large", p[big])):
        bench = u.groupby("date")["r"].mean()
        for sc in ("s_ind", "s_ind_size"):
            lo, hi = u[u[sc] <= 0.1], u[u[sc] > 0.9]
            L = (lo.groupby("date")["r"].mean() - bench) * 100
            S = (hi.groupby("date")["r"].mean() - bench) * 100
            turn = get_turnover(lo) + get_turnover(hi)
            gross = (L - S).dropna()
            for cost in (0.003, 0.006, 0.010):
                for borrow in (0.0, 0.06, 0.10):
                    net = gross - turn * cost * 100 - borrow / 12 * 100
                    st = stats(net)
                    rows[(uni, sc[2:], f"{cost:.1%}", f"{borrow:.0%}")] = {"ann%": st["ann%"], "sharpe": st["sharpe"], "maxDD%": st["maxDD%"]}
    pd.set_option("display.width", 200)
    print(pd.DataFrame(rows).T.to_string())


if __name__ == "__main__":
    main()
