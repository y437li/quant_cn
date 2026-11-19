"""Contract tests for visualization.RatesFxReportSection (plan 34 ph4)."""

from __future__ import annotations

from typing import Any

from quant_cn.visualization.email_format import RED
from quant_cn.visualization.rates_fx_report_section import RatesFxReportSection


def _build_row(
    key: str, name: str, unit: str, value: float, w: float, alerts: bool = False
) -> dict:
    return {"key": key, "name": name, "group": "债市", "unit": unit, "value": value,
            "chg": {"1w": w, "1m": None, "1y": None}, "pct": 0.01,
            "alerts": ["x"] if alerts else []}  # fmt: skip


def build_doc(new: bool = True) -> dict[str, Any]:
    rows = [
        _build_row("usdcnh", "美元/离岸人民币", "rate", 6.6661, -0.0011),
        _build_row("credit_bank", "信用利差", "bp", 27.45, 10.9, alerts=True),
        _build_row("cn_10y", "10年国债", "yield", 1.6055, 0.9),
        _build_row("fix_gap", "离岸−中间价", "gap", -0.0071, 0.0004),
    ]
    flags = [{"key": "credit_bank:week_widen", "message": "信用利差 一周走阔 +11bp"}]
    return {"as_of": "20261117", "rows": rows, "flags": flags,
            "new_flags": ["credit_bank:week_widen"] if new else []}  # fmt: skip


# TC-RRS-001
def test_tc_rrs_001_summary() -> None:
    s = RatesFxReportSection()
    assert s.build_summary(build_doc()) == (
        "利率汇率：10年国债 1.6055%（一周 +1bp，5年分位 1%）；美元/离岸人民币 6.6661（一周 "
        "-0.11%，5年分位 1%）。提醒：信用利差 一周走阔 +11bp（新）。"
    )
    assert "（新）" not in s.build_summary(build_doc(new=False))
    quiet = build_doc() | {"flags": []}
    assert s.build_summary(quiet).endswith("没有提醒。")
    assert s.build_summary(None) == ""


# TC-RRS-002
def test_tc_rrs_002_rows() -> None:
    html = RatesFxReportSection().build_rows(build_doc())
    assert html.index("10年国债") < html.index("信用利差") < html.index("美元/离岸人民币")
    assert html.index("美元/离岸人民币") < html.index("离岸−中间价")
    assert "+27.4bp" in html and "+11bp" in html and "-0.71%" in html and "+0.04pp" in html
    assert RED in html
    assert "数据缺失" in RatesFxReportSection().build_rows(None)
