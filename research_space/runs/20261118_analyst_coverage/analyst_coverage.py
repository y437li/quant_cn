"""Plan 37 ph1 coverage: per year-end session 2019 .. 2026, the share of A shares (excluding BJ) with
each analyst descriptor, by count and by circ_mv weight (the risk model's regression weight base)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.calculation.consensus_panel_builder import ConsensusPanelBuilder
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.risk.analyst_descriptors import AnalystDescriptors

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20190101' ORDER BY 1")["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:4] != n[:4]]
    cons = ConsensusPanelBuilder(q, DateCodec()).build(ends, 90)
    basic = q.sql("SELECT trade_date, ts_code, total_mv, circ_mv FROM curated.daily_basic WHERE trade_date IN (SELECT UNNEST(?)) "
                  "AND ts_code NOT LIKE '%.BJ'", [ends])
    cat.close()
    out = AnalystDescriptors().compute(basic[["trade_date", "ts_code", "total_mv"]], cons)
    m = basic.merge(out, on=["trade_date", "ts_code"])
    rows = {}
    for d, f in m.groupby("trade_date"):
        w = f["circ_mv"].fillna(0)
        rows[d] = {"stocks": len(f)} | {
            f"{c} %n": round(f[c].notna().mean() * 100, 1) for c in ("epfwd", "egrsf", "egrlf")
        } | {f"{c} %w": round(float(np.sum(w * f[c].notna()) / w.sum() * 100), 1) for c in ("epfwd", "egrsf", "egrlf")}
    pd.set_option("display.width", 200)
    print(pd.DataFrame(rows).T.to_string())


if __name__ == "__main__":
    main()
