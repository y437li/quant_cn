"""The cheap side of the linear-pricing gap: decile excess vs the covered universe (fwd20 / fwd60),
long-only cheapest-decile record by year, industry mix of decile 1, and the current cheapest names.
Reads the panel written by pricing_gap_factor.py."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    cfg = Config.load(REPO)
    p = pd.read_parquet(Path(cfg.lake.root) / "meta/runs/research/20261118_linear_pricing_gap/panel_0.7_15.parquet")
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    mem = q.sql("SELECT DISTINCT ts_code, l1_name FROM curated.index_member_all WHERE is_new = 'Y'")
    names = q.sql("SELECT ts_code, name FROM curated.stock_basic")
    cat.close()
    pd.set_option("display.width", 220)
    p["dec"] = p.groupby("date")["gap"].transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False))
    for h in (20, 60):
        y = f"fwd{h}"
        s = p.dropna(subset=[y]).copy()
        s["ex"] = (s[y] - s.groupby("date")[y].transform("mean")) * 100
        by = s.groupby(["date", "dec"])["ex"].mean().unstack()
        step = 1 if h == 20 else 3  # non-overlapping months for 60d
        nb = by.iloc[::step]
        t = nb.mean() / nb.std() * np.sqrt(len(nb))
        print(f"\n## fwd{h} excess vs covered universe by decile (0 = cheapest): mean %, t, hit")
        print(pd.DataFrame({"mean": nb.mean().round(2), "t": t.round(2), "hit": (nb > 0).mean().round(2)}).T.to_string())
        if h == 20:
            yr = by[0].groupby(by.index.str[:4]).agg(["mean", "count"])
            yr["annual"] = ((1 + by[0] / 100).groupby(by.index.str[:4]).prod() - 1) * 100
            print("cheapest decile by year (monthly excess mean, compounded excess)\n", yr.round(2).to_string())
            print("top decile by year compounded", (((1 + by[9] / 100).groupby(by.index.str[:4]).prod() - 1) * 100).round(1).to_dict())
    d1 = p[p.dec == 0].merge(mem, on="ts_code", how="left")
    allm = p.merge(mem, on="ts_code", how="left")
    mix = pd.DataFrame({"cheap": d1["l1_name"].value_counts(normalize=True), "all": allm["l1_name"].value_counts(normalize=True)}).fillna(0) * 100
    mix["over"] = mix["cheap"] - mix["all"]
    print("\n## industry mix of the cheapest decile vs universe (%)\n", mix.sort_values("over", ascending=False).head(10).round(1).to_string())
    # within-industry: cheapest decile by industry-neutral rank
    s = allm.dropna(subset=["fwd20"]).copy()
    s["gi"] = s.groupby(["date", "l1_name"])["gap"].rank(pct=True)
    s["ex"] = (s["fwd20"] - s.groupby("date")["fwd20"].transform("mean")) * 100
    b = s.groupby(["date", pd.cut(s["gi"], [0, 0.1, 0.9, 1.0], labels=["cheap10", "mid", "dear10"])], observed=True)["ex"].mean().unstack()
    print("\n## industry-neutral (within L1) fwd20 excess %:", {c: (round(b[c].mean(), 2), round(b[c].mean() / b[c].std() * np.sqrt(len(b)), 2)) for c in b})
    last = p[p.date == p.date.max()].merge(names, on="ts_code").merge(mem, on="ts_code", how="left")
    last["pe_fy1"] = last["total_mv"] / last["f1"]
    last["g12"] = last["grow"] * 100
    print(f"\n## cheapest now ({p.date.max()}), market cap >= 100亿")
    print(last[last.total_mv >= 1e6].nsmallest(25, "gap")[["ts_code", "name", "l1_name", "gap", "pe_fy1", "g12", "mom", "rev20"]]
          .assign(mv_yi=lambda f: last.set_index("ts_code").loc[f.ts_code, "total_mv"].to_numpy() / 1e4).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
