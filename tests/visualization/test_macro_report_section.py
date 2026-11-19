"""Contract tests for visualization.MacroReportSection (plan 15 ph7h, D-143)."""

from __future__ import annotations

from quant_cn.visualization.macro_report_section import MacroReportSection
from tests.visualization.report_docs import build_macro


def test_tc_mrs_001_summary() -> None:
    """TC-MRS-001"""
    line = MacroReportSection().build_summary(build_macro())
    assert line == "宏观：CPI 同比 0.7%（10月，−0.2%）（2 项新发布）"
    assert MacroReportSection().build_summary(None) == ""
    assert "新发布" not in MacroReportSection().build_summary(build_macro(new=False))


def test_tc_mrs_002_rows() -> None:
    """TC-MRS-002"""
    rows = MacroReportSection().build_rows(build_macro())
    for text in ("宏观", "价格 · CPI 同比", "35,476", "+18,895", "95%", "缺 cn_m", "●"):
        assert text in rows
    assert MacroReportSection().build_rows(build_macro(new=False)) == ""
    assert "数据缺失：没有 macro_monitor.json" in MacroReportSection().build_rows(None)
