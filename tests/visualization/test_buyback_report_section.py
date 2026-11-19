"""Contract tests for visualization.BuybackReportSection (plan 23 ph6)."""

from __future__ import annotations

from quant_cn.visualization.buyback_report_section import BuybackReportSection

DOC = {
    "days": 7,
    "large_plans": [
        {"code": "C", "name": "丙", "ann_date": "20261112", "amount_yi": 25.0, "pct": 5.0}
    ],
    "book_events": [
        {"code": "B", "name": "乙", "ann_date": "20261112", "proc": "实施", "amount_yi": 1.0}
    ],
}


def test_tc_brs_001_summary() -> None:
    """TC-BRS-001"""
    s = BuybackReportSection()
    assert s.build_summary(DOC) == "回购：乙实施进度；近 7 天全市场新增 ≥ 2% 市值的回购预案 1 只"
    assert (
        s.build_summary({"large_plans": [], "book_events": []}) == ""
        and s.build_summary(None) == ""
    )


def test_tc_brs_002_rows() -> None:
    """TC-BRS-002"""
    rows = BuybackReportSection().build_rows(DOC)
    assert "大额回购预案" in rows and "5.0%" in rows and "乙" in rows and "11-12" in rows
    assert BuybackReportSection().build_rows({"large_plans": [], "book_events": []}) == ""
