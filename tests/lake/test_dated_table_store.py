"""Contract tests for lake.DatedTableStore (plan 21)."""

from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.dated_table_store import DatedTableStore
from tests.support import MiniLake


# TC-DTW-001
def test_tc_dtw_001_replace_dates(lake: MiniLake) -> None:
    store = DatedTableStore(lake.writer)
    rows = pd.DataFrame(
        {
            "ts_code": ["A", "B", "A"],
            "as_of": ["20241231", "20250102", "20250103"],
            "pct": [0.1, 0.2, 0.3],
        }
    )
    paths = store.write("retail_gauge_features", rows, "as_of")
    assert sorted(p.parent.name for p in paths) == ["year=2024", "year=2025"]
    store.write("retail_gauge_features", rows.iloc[[1]].assign(pct=0.9), "as_of")
    out = store.read("retail_gauge_features", ["2024", "2025"]).sort_values("as_of")
    assert out[["as_of", "ts_code", "pct"]].values.tolist() == [
        ["20241231", "A", 0.1],
        ["20250102", "B", 0.9],
        ["20250103", "A", 0.3],
    ]


# TC-DTW-002
def test_tc_dtw_002_missing(lake: MiniLake) -> None:
    store = DatedTableStore(lake.writer)
    assert store.read("retail_gauge", ["2025"]).empty
    with pytest.raises(LakeError):
        store.read_report("reports/retail_gauge/backtest.parquet")
