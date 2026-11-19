"""Contract tests for visualization.BuybackMarketReportSection (plan 32 ph4)."""

from __future__ import annotations

from typing import Any

from quant_cn.visualization.buyback_market_report_section import (
    MAX_ROWS,
    BuybackMarketReportSection,
)


def _build_event(code: str, tags: list[str], funding: list[str], high: float, **kw: Any) -> dict:
    return {"code": code, "name": code, "event": "new", "tags": tags, "funding": funding,
            "loan_yi": None, "low_yi": high / 2, "high_yi": high, "mv_pct": 0.012} | kw  # fmt: skip


def build_doc() -> dict[str, Any]:
    bb = [_build_event(f"B{i}", ["注销"], ["自有"], float(i)) for i in range(MAX_ROWS + 2)]
    bb.append(_build_event("L", ["维护价值"], ["自有", "专项贷款"], 0.5, loan_yi=0.4))
    bb.append(_build_event("X", ["注销"], ["自有"], 99.0, event="completed"))
    inc = [_build_event("I", ["控股股东"], ["自有"], 2.0)]
    total = {"all": {"count": 775, "high_yi": 2398.7, "executed_yi": 1071.6}}
    return {"as_of": "20261117", "days": 7,
            "buyback": {"events": bb, "totals": total},
            "increase": {"events": inc, "totals": {"all": {"count": 3, "high_yi": 0.5,
                                                            "executed_yi": 0.1}}}}  # fmt: skip


# TC-BMR-001
def test_tc_bmr_001_summary() -> None:
    s = BuybackMarketReportSection().build_summary(build_doc())
    assert s == (
        "全市场回购增持（近 7 天）：新回购 11 个（注销 10、维护价值 1），其中专项贷款 1 个；"
        "在执行 775 个，计划上限 2,399亿、已执行 1,072亿。新增持 1 个（控股股东 1）；"
        "在执行 3 个，计划上限 5,000万、已执行 1,000万。"
    )
    assert BuybackMarketReportSection().build_summary(None) == ""


# TC-BMR-002
def test_tc_bmr_002_rows() -> None:
    html = BuybackMarketReportSection().build_rows(build_doc())
    assert html.index(">B9<") < html.index(">B8<") < html.index(">I<")
    assert ">B1<" not in html and ">X<" not in html  # beyond MAX_ROWS; not a new event
    assert "4.50亿–9.00亿" in html and "1.20%" in html and "控股股东" in html
    assert "数据缺失" in BuybackMarketReportSection().build_rows(None)
