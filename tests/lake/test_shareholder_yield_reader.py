"""Contract tests for lake.ShareholderYieldReader (plan 23 phase 3, D-154)."""

from __future__ import annotations

import pandas as pd

from quant_cn.lake.shareholder_yield_reader import ShareholderYieldReader


def test_tc_syr_001_compute() -> None:
    """TC-SYR-001"""
    basic = pd.DataFrame(
        {"dv_ttm": [3.0, None, 0.0], "total_mv": [1e6, 2e6, 5e5]}, index=["A", "B", "C"]
    )
    executed = pd.Series({"B": 4e8, "C": 1e8})  # 元
    out = ShareholderYieldReader.compute(basic, executed)
    assert out.loc["A", "shareholder_yield"] == 0.03 and out.loc["A", "buyback_yield"] == 0.0
    assert out.loc["B", "dividend_yield"] == 0.0 and out.loc["B", "buyback_yield"] == 4e8 / 2e10
    assert out.loc["C", "shareholder_yield"] == 1e8 / 5e9


def test_tc_syr_002_plans() -> None:
    """TC-SYR-002"""
    programmes = pd.DataFrame(
        {
            "ts_code": ["A", "A", "B", "C"],
            "planned_amount": [1e8, 4e8, 2e8, 5e8],
            "executed_amount": [5e7, 1e8, 0.0, 5e8],
            "state": ["open", "open", "expired", "stopped"],
        }
    )
    mv = pd.Series({"A": 1e10, "B": 1e10, "C": 1e10})
    out = ShareholderYieldReader.compute_plans(programmes, mv)
    assert list(out.index) == ["A"]
    assert out.loc["A", "buyback_plan_pct"] == 4.0 and out.loc["A", "buyback_done_pct"] == 0.25
