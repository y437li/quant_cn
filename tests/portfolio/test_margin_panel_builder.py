"""Contract tests for portfolio.MarginPanelBuilder (plan 15 ph7m)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pytest

from quant_cn.calculation.margin_ladder_estimator import MarginLadderEstimator
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.margin_panel_builder import MarginPanelBuilder

DAYS = [f"202610{d:02d}" for d in range(1, 26)]  # 25 sessions


class RowsQuery:
    def __init__(self, rows: pd.DataFrame) -> None:
        self.rows = rows

    def sql(self, query: str, params: Any = None) -> pd.DataFrame:
        return self.rows


def _build_rows() -> pd.DataFrame:
    rows = []
    for i, d in enumerate(DAYS):
        rows.append(
            {
                "ts_code": "A",
                "trade_date": d,
                "rzye": 1e9 + 1e7 * i,
                "rzmre": 2e7,
                "rzche": 1e7,
                "rqye": 5e6 if i < 24 else 8e6,
                "rqyl": 1e5,
                "rqmcl": 1e4,
                "close": 20.0,
                "circ_mv": 1e6,
            }
        )
    return pd.DataFrame(rows)  # circ_mv 1e6 万元 = 100 亿


def _build_builder() -> MarginPanelBuilder:
    return MarginPanelBuilder(
        cast(LakeQuery, RowsQuery(_build_rows())), MarginLadderEstimator(), "20261001"
    )


def test_tc_mpb_001_fields() -> None:
    """TC-MPB-001"""
    doc = _build_builder().build("20261031")["A"]
    assert doc["as_of"] == "20261025" and doc["float_mv_yi"] == 100.0
    assert doc["rz_yi"] == 12.4 and doc["rz_pct_float"] == 12.4
    assert doc["rz_chg_20d"] == round(1.24e9 / 1.04e9 - 1, 4) and doc["rz_net_20d_yi"] == 2.0
    assert doc["rq_wan"] == 800.0 and doc["rq_max_wan"] == 800.0 and doc["rq_sell_20d_wan"] == 20.0
    assert len(doc["daily"]) == 25


def test_tc_mpb_002_ladder() -> None:
    """TC-MPB-002"""
    lad = _build_builder().build("20261031")["A"]["ladder"]
    assert lad["first_liq"] == 13.0  # 20 x 1.3 / (1 + 1.0)
    assert lad["first_liq_low_margin"] == round(20 * 1.3 / 1.8, 2)
    forced = {f["fall_pct"]: f for f in lad["forced"]}
    assert forced[30.0]["debt_yi"] == 0.0 and forced[35.0]["share"] == 1.0  # 13.0 = 35% below 20


def test_tc_mpb_003_write(tmp_path: Path) -> None:
    """TC-MPB-003"""
    b = _build_builder()
    with pytest.raises(LakeError):
        b.write(tmp_path / "nope", "20261031")
    assert b.write(tmp_path, "20261031") == 1
    assert json.loads((tmp_path / "margin" / "A.json").read_text(encoding="utf-8"))["code"] == "A"
