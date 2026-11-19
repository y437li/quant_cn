"""Contract tests for visualization.EtfReportSection (plan 15 ph7g)."""

from __future__ import annotations

from quant_cn.visualization.etf_report_section import EtfReportSection


def test_tc_ers_001_summary() -> None:
    """TC-ERS-001"""
    doc = {
        "styles": [
            {"name": "银行", "status": "hot", "z": 1.99, "flow_pct": 0.165},
            {"name": "红利", "status": "normal", "z": None, "flow_pct": None},
        ]
    }
    s = EtfReportSection()
    assert (
        s.build_summary(doc)
        == "ETF 资金强度：银行 过热（z +2.0，20 日流入占规模 +16.5%） · 红利 正常"
    )
    assert s.build_summary({"styles": []}) == "" and s.build_summary(None) == ""
    assert s.build_rows(doc) == ""
