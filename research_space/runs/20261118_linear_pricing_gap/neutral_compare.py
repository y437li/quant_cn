"""Long-short of the gap under three neutralisations, 10% legs, monthly:
none (rank in the covered universe), industry (rank within SW L1), industry + size (residual of the
gap on L1 dummies and log market cap, per month). Equal weight and market-cap weight; whole covered
universe and large caps (top 40% size). Excess vs the covered universe (same weighting); net of
0.3% per unit of turnover per leg. Reads panel_0.7_15.parquet and the l1 map like long_short.py."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from long_short import get_turnover, stats  # same folder
from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
COST = 0.003


def residualise(f: pd.DataFrame) -> pd.Series:
    X = pd.get_dummies(f["l1_name"], dtype=float)
    X["size"] = f["size"] - f["size"].mean()
    beta = np.linalg.lstsq(X.to_numpy(), f["gap"].to_numpy(), rcond=None)[0]
    return pd.Series(f["gap"].to_numpy() - X.to_numpy() @ beta, index=f.index)


def main() -> None:
    cfg = Config.load(REPO)
    p = pd.read_parquet(Path(cfg.lake.root) / "meta/runs/research/20261118_linear_pricing_gap/panel_0.7_15.parquet")
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    mem = LakeQuery(cat).sql("SELECT DISTINCT ts_code, l1_name FROM curated.index_member_all WHERE is_new = 'Y'")
    cat.close()
    p = p.dropna(subset=["fwd20"]).merge(mem, on="ts_code", how="inner")
    p["r"] = np.exp(p["fwd20"]) - 1
    p["w_mv"] = p["total_mv"]
    p["s_none"] = p.groupby("date")["gap"].rank(pct=True)
    p["s_ind"] = p.groupby(["date", "l1_name"])["gap"].rank(pct=True)
    p["res"] = p.groupby("date", group_keys=False).apply(residualise)
    p["s_ind_size"] = p.groupby("date")["res"].rank(pct=True)
    big = p.groupby("date")["size"].rank(pct=True) > 0.6
    rows, yearly = {}, {}
    for uni, u in (("all", p), ("large", p[big])):
        for wt in ("ew", "mvw"):
            w = u["w_mv"] if wt == "mvw" else pd.Series(1.0, index=u.index)
            bench = (u["r"] * w).groupby(u["date"]).sum() / w.groupby(u["date"]).sum()
            for sc in ("s_none", "s_ind", "s_ind_size"):
                lo, hi = u[u[sc] <= 0.1], u[u[sc] > 0.9]

                def leg(x: pd.DataFrame) -> pd.Series:
                    ww = x["w_mv"] if wt == "mvw" else pd.Series(1.0, index=x.index)
                    return ((x["r"] * ww).groupby(x["date"]).sum() / ww.groupby(x["date"]).sum() - bench) * 100

                L, S = leg(lo), leg(hi)
                turn = get_turnover(lo) + get_turnover(hi)
                ls = (L - S).dropna()
                key = f"{uni}/{wt}/{sc[2:]}"
                rows[key] = stats(ls) | {"net ann%": stats(ls - turn * COST * 100)["ann%"], "long ann%": stats(L)["ann%"],
                                         "short ann%": stats(-S)["ann%"], "turnover": round(turn / 2, 2)}
                yearly[key] = ((1 + ls / 100).groupby(ls.index.str[:4]).prod() - 1).mul(100).round(1)
    pd.set_option("display.width", 220)
    print(pd.DataFrame(rows).T.to_string())
    print("\n## L-S compounded by year (%)\n", pd.DataFrame(yearly).T.to_string())


if __name__ == "__main__":
    main()
