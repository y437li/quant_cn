"""Contract tests for visualization.FuturesReportSection (plan 15 ph7i, D-145)."""

from __future__ import annotations

from quant_cn.visualization.futures_report_section import FuturesReportSection
from tests.visualization.report_docs import build_futures


def test_tc_frs_001_summary() -> None:
    """TC-FRS-001"""
    s = FuturesReportSection()
    assert s.build_summary(build_futures()) == "期货：1 个信号，新增 1 个（铜）"
    assert s.build_summary(build_futures(new=False)) == "期货：1 个信号"
    assert s.build_summary(build_futures() | {"flags": []}) == "期货：没有异常信号。"
    assert s.build_summary(None) == ""


def test_tc_frs_002_rows() -> None:
    """TC-FRS-002"""
    s = FuturesReportSection()
    rows = s.build_rows(build_futures())
    assert "期货" in rows and "期限结构" in rows and "近月升水 +3.8%" in rows
    assert s.build_rows(build_futures(new=False)) == ""
    assert "数据缺失：没有 futures_monitor.json" in s.build_rows(None)
