"""Contract tests for visualization.SectorEarningsReportSection (plan 35)."""

from __future__ import annotations

from typing import Any

from quant_cn.visualization.email_format import RED
from quant_cn.visualization.sector_earnings_report_section import SectorEarningsReportSection


def build_doc(new: bool = True) -> dict[str, Any]:
    base = {"share": 1.0, "hchg": 2.0}
    rows = [
        base
        | {
            "code": "A",
            "name": "光伏设备",
            "status": "firing",
            "pre": 43.8,
            "react": -0.2,
            "back": 56.2,
        },
        base
        | {
            "code": "B",
            "name": "电池",
            "status": "provisional",
            "share": 0.5,
            "pre": 16.0,
            "react": 0.4,
            "back": None,
        },
        base
        | {"code": "C", "name": "白酒Ⅱ", "status": "none", "pre": 35.0, "react": 8.9, "back": 18.0},
    ]
    return {
        "as_of": "20211029",
        "season": "20210930",
        "rows": rows,
        "new_flags": ["A"] if new else [],
        "record": {"rally": {"n": 25, "fwd60": -6.1}},
    }


# TC-SER-001
def test_tc_ser_001_summary() -> None:
    s = SectorEarningsReportSection()
    assert s.build_summary(build_doc()) == (
        "财报季信号（2021Q3）：好消息涨不动：光伏设备（前60天 +43.8%，当天 -0.2%，此前120天 "
        "+56.2%）（新）。历史上大涨后触发 25 次，之后 60 天平均 -6.1%。"
    )
    assert "（新）" not in s.build_summary(build_doc(new=False))
    quiet = build_doc() | {"rows": build_doc()["rows"][1:]}
    assert s.build_summary(quiet) == "财报季信号（2021Q3）：没有行业触发。"
    assert s.build_summary(None) == "" and s.build_summary({"season": None}) == ""


# TC-SER-002
def test_tc_ser_002_rows() -> None:
    s = SectorEarningsReportSection()
    html = s.build_rows(build_doc())
    assert html.index("光伏设备") < html.index("电池") and "白酒" not in html
    assert RED in html and "临时" in html and "50%" in html and "+56.2%" in html
    assert s.build_rows(build_doc() | {"rows": build_doc()["rows"][2:]}) == ""
    assert "数据缺失" in s.build_rows(None) or "sector_earnings_signal.json" in s.build_rows(None)
