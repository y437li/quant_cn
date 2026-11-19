"""Contract tests for calculation.HolderCountPanel (plan 21 ph2, D-142)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.calculation.holder_count_panel import HolderCountPanel
from quant_cn.core.config import Config
from tests.support import MiniLake, SampleFactorLake

A = "000001.SZ"
COUNTS = [  # end_date, ann_date, holder_num
    ("20241231", "20250120", 100),
    ("20250331", "20250420", 110),
    ("20250331", "20250501", 120),  # restated: the latest value, the first date
    ("20250630", "20250720", 132),
]


def write_counts(lake: MiniLake, config: Config) -> None:
    rows = [{"ts_code": A, "end_date": e, "ann_date": a, "holder_num": n} for e, a, n in COUNTS]
    SampleFactorLake.write(lake, config, "stk_holdernumber", rows)


# TC-HCP-001
def test_tc_hcp_001_labels(lake: MiniLake, config: Config) -> None:
    write_counts(lake, config)
    panel = HolderCountPanel(lake.query)
    panel.load("20251231")
    rows = pd.DataFrame({"ts_code": [A, A, A], "q": ["20250331", "20250630", "20241231"]})
    out = panel.compute_labels(rows)
    assert out["y"].iloc[0] == pytest.approx(math.log(1.2))
    assert out["ann_y"].iloc[0] == "20250420"
    assert out["y"].iloc[1] == pytest.approx(math.log(1.1))
    assert math.isnan(out["y"].iloc[2])  # 20240930 missing
    panel.load("20250430")  # the restatement is not out yet
    assert panel.compute_labels(rows)["y"].iloc[0] == pytest.approx(math.log(1.1))


# TC-HCP-002
def test_tc_hcp_002_lags_pit(lake: MiniLake, config: Config) -> None:
    write_counts(lake, config)
    panel = HolderCountPanel(lake.query)
    panel.load("20251231")
    rows = pd.DataFrame(
        {"ts_code": [A, A], "q": ["20250930", "20250930"], "as_of": ["20250719", "20250720"]}
    )
    out = panel.compute_lags(rows)
    assert math.isnan(out["prev"].iloc[0]) and out["prev"].iloc[1] == pytest.approx(math.log(1.1))
    assert out["prev2"].tolist() == pytest.approx([math.log(1.2)] * 2)
    assert HolderCountPanel.get_quarter_before("20250331", 1) == "20241231"
    assert HolderCountPanel.get_quarter_before("20241231", -1) == "20250331"
