"""Contract tests for lake.MarginSignalReader (plan 15 ph7m)."""

from __future__ import annotations

import math
from typing import Any, cast

import pandas as pd

from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.margin_signal_reader import MarginSignalReader

DAYS = [f"202610{d:02d}" for d in range(1, 26)]


class RowsQuery:
    def __init__(self, rows: pd.DataFrame) -> None:
        self.rows, self.params = rows, None

    def sql(self, query: str, params: Any = None) -> pd.DataFrame:
        self.params = params
        return self.rows


def test_tc_msr_001_signals() -> None:
    """TC-MSR-001"""
    base = {"ts_code": "A", "rzmre": 2e7, "rzche": 1e7, "circ_mv": 1e6}
    rows = pd.DataFrame(
        [
            base | {"trade_date": d, "rzye": 1e9 + 1e7 * i, "rqye": 4e6 if i == 10 else 2e6}
            for i, d in enumerate(DAYS)
        ]
    )
    q = RowsQuery(rows)
    out = MarginSignalReader(cast(LakeQuery, q)).read(["A", "B"], "20261026")
    assert q.params[-1] == "20261026"  # rows strictly before as_of (published after the close)
    a = out.loc["A"]
    assert a["rz_chg_20d"] == 1.24e9 / 1.04e9 - 1 and a["rz_net_20d_pct"] == 2e8 / 1e10 * 100
    assert a["rq_pct_float"] == 2e6 / 1e10 * 100 and a["rq_max_ratio"] == 0.5
    assert math.isnan(out.loc["B", "rz_chg_20d"])
