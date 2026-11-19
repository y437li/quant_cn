"""Does a high valuation make the reaction to bad news harsher? (follows priced_in.py)

PE TTM (daily_basic) on the last session before the event; loss-makers (PE <= 0 or missing) are
their own group. Reaction [0,+1] and post [+2,+61] by SUE decile 0 / 9 and PE quintile.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    cfg = Config.load(REPO)
    root = Path(cfg.lake.root) / "meta/runs/research/20261118_priced_in"
    ev = pd.read_parquet(root / "events.parquet")
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    pe = q.sql("SELECT ts_code, trade_date, pe_ttm FROM curated.daily_basic WHERE trade_date >= '20181001'")
    cat.close()
    pe = pe.sort_values("trade_date")
    ev = ev.dropna(subset=["first_day"]).sort_values("first_day")
    ev["day"] = ev["first_day"].astype(str).astype(int)
    pe["day"] = pe["trade_date"].astype(int)
    ev = ev.sort_values("day")
    pe = pe.sort_values("day")
    m = pd.merge_asof(ev, pe[["ts_code", "day", "pe_ttm"]], on="day", by="ts_code",
                      allow_exact_matches=False)
    m["peq"] = "亏损"
    pos = m["pe_ttm"] > 0
    m.loc[pos, "peq"] = m[pos].groupby("end_date")["pe_ttm"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 5, labels=False)).astype(int).astype(str)
    pd.set_option("display.width", 200)
    for col in ["pre60", "react", "post60"]:
        t = m[m.dec.isin([0, 9])].pivot_table(index="peq", columns="dec", values=col, aggfunc="mean").round(2)
        t["n0"] = m[m.dec == 0].groupby("peq").size()
        print(f"\n## {col}: SUE decile 0 (worst) / 9 (best) by PE quintile (0 = cheapest)\n", t.to_string())


if __name__ == "__main__":
    main()
