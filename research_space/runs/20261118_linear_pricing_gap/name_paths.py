"""Month-end path of pricing_gap for named stocks in 2026: percentile among stocks >= 100亿 (1 = cheapest,
industry + size neutral value) and the raw premium of market value over the consensus value."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
CODES = sys.argv[1:] or ["300502.SZ", "300308.SZ", "002384.SZ", "300476.SZ", "603228.SH", "300857.SZ",
                         "603083.SH", "001389.SZ", "688525.SH", "688981.SH", "688041.SH", "688256.SH", "603986.SH"]


def main() -> None:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20251201' ORDER BY 1")["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]]
    f = q.sql("SELECT trade_date, ts_code, value, value_raw FROM derived.features WHERE factor = 'pricing_gap' AND trade_date IN (SELECT UNNEST(?))", [ends])
    mv = q.sql("SELECT trade_date, ts_code, total_mv / 1e4 mv FROM curated.daily_basic WHERE trade_date IN (SELECT UNNEST(?))", [ends])
    names = q.sql("SELECT ts_code, name FROM curated.stock_basic").set_index("ts_code")["name"]
    cat.close()
    m = f.merge(mv, on=["trade_date", "ts_code"])
    m = m[m["mv"] >= 100]
    m["pct"] = m.groupby("trade_date")["value"].rank(pct=True)
    m["prem"] = (np.exp(-m["value_raw"]) - 1) * 100
    sel = m[m["ts_code"].isin(CODES)].assign(name=lambda x: x["ts_code"].map(names))
    pd.set_option("display.width", 250)
    print("## percentile (1 = cheapest)\n", sel.pivot(index="name", columns="trade_date", values="pct").round(2).to_string())
    print("\n## premium of market value over consensus value (%)\n", sel.pivot(index="name", columns="trade_date", values="prem").round(0).to_string())


if __name__ == "__main__":
    main()
