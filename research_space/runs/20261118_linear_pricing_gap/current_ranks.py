"""Current cheapest and dearest stocks by pricing_gap (derived.features, latest session): premium of
market value over the consensus value, its percentile within the SW L1 industry, forward PE, FY1 ->
FY2 growth, brokers, 1-month return; market value >= MIN_MV 亿. Usage: current_ranks.py [min_mv]."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.calculation.consensus_panel_builder import ConsensusPanelBuilder
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
TOP = 20


def main() -> None:
    min_mv = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    day = q.sql("SELECT max(trade_date) d FROM derived.features WHERE factor = 'pricing_gap'")["d"].iloc[0]
    f = q.sql("SELECT ts_code, value, value_raw FROM derived.features WHERE factor = 'pricing_gap' AND trade_date = ?", [day])
    basic = q.sql("SELECT ts_code, total_mv / 1e4 AS mv, pe_ttm FROM curated.daily_basic WHERE trade_date = ?", [day])
    names = q.sql("SELECT ts_code, name FROM curated.stock_basic")
    mem = q.sql("SELECT DISTINCT ts_code, l1_name, l2_name FROM curated.index_member_all WHERE is_new = 'Y'")
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date <= ? ORDER BY 1 DESC LIMIT 21", [day])["trade_date"].tolist()
    ret = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor px FROM curated.daily d JOIN curated.adj_factor a "
                "USING (ts_code, trade_date) WHERE d.trade_date IN (?, ?)", [day, days[-1]])
    cons = ConsensusPanelBuilder(q, DateCodec()).build([day], 90)
    cat.close()
    r = ret.pivot(index="ts_code", columns="trade_date", values="px")
    m = (f.merge(basic, on="ts_code").merge(names, on="ts_code").merge(mem, on="ts_code", how="left")
         .merge(cons[["ts_code", "np1", "np2", "n_brokers"]], on="ts_code", how="left"))
    m["ret1m"] = m["ts_code"].map((r[day] / r[days[-1]] - 1) * 100)
    m["premium%"] = (np.exp(-m["value_raw"]) - 1) * 100
    m["ind_pct"] = m.groupby("l1_name")["value"].rank(pct=True)  # 1 = cheapest in its industry
    m["pe_fy1"] = m["mv"] * 1e4 / m["np1"]
    m["g12%"] = (m["np2"] / m["np1"] - 1) * 100
    big = m[m["mv"] >= min_mv]
    cols = ["ts_code", "name", "l2_name", "mv", "premium%", "ind_pct", "pe_fy1", "g12%", "n_brokers", "ret1m"]
    pd.set_option("display.width", 220)
    print(f"as of {day}; {len(m)} stocks with a value, {len(big)} with mv >= {min_mv:.0f}亿")
    print("\n## cheapest (industry + size neutral, highest value)\n", big.nlargest(TOP, "value")[cols].round(1).to_string(index=False))
    print("\n## dearest\n", big.nsmallest(TOP, "value")[cols].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
