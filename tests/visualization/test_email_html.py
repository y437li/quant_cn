"""Contract tests for visualization.EmailHtml (plan 15 ph7e)."""

from __future__ import annotations

from quant_cn.visualization.email_format import EmailFormat as F
from quant_cn.visualization.email_html import EmailHtml as H


def test_tc_eh_001_formats() -> None:
    """TC-EH-001"""
    assert F.format_ymd("20261113") == "2026-11-13" and F.format_ymd("") == "—"
    assert F.format_day("20261113") == "2026-11-13 星期五"
    assert [F.format_pct(0.0123), F.format_pct(-0.5, 1), F.format_pct(None)] == [
        "+1.23%",
        "−50.0%",
        "—",
    ]
    assert [F.format_vol(0.1637), F.format_yuan(-50000.4), F.format_yuan(1234567)] == [
        "16.4%",
        "−50,000",
        "1,234,567",
    ]
    assert [F.format_sigma(-2.31), F.format_sigma(None)] == ["−2.3σ", "—"]


def test_tc_eh_002_escape_and_page() -> None:
    """TC-EH-002"""
    assert "&lt;b&gt;" in H.build_td("<b>") and "<b>" not in H.build_td("<b>")
    page = H.build_page(
        "持仓监测", "2026-11-13 星期五", "数据截至", ["甲", "乙"], "<tr><td>x</td></tr>"
    )
    assert (
        page.startswith("<!doctype html>")
        and "· 甲<br>· 乙" in page
        and "<tr><td>x</td></tr>" in page
    )
    assert "数据缺失：没有 a.json" in H.build_missing("持仓", "a.json")
