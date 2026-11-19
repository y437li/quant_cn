"""Contract tests for visualization.SmallCapReportSection (plan 30 ph2)."""

from __future__ import annotations

from typing import Any

from quant_cn.visualization.small_cap_report_section import SmallCapReportSection


def build_watch(new: bool = True) -> dict[str, Any]:
    rows = [
        {"key": "limit_downs", "group": "恐慌", "name": "跌停家数", "value": 84.0, "unit": "只",
         "trigger": 500, "state": "off", "note": "≥ 500 只为恐慌日", "date": "20261117"},
        {"key": "level_6075", "group": "点位", "name": "中证1000 跌到 6,075", "value": 6092.39,
         "unit": "点", "trigger": 6075.0, "state": "near", "note": "+0.3%", "date": "20261117"},
        {"key": "low_share", "group": "恐慌", "name": "创 60 日新低的股票占比", "value": None,
         "unit": "占比", "trigger": 0.7, "state": "off", "note": "", "date": "20261117"},
        {"key": "gap", "group": "波动", "name": "中证1000 - 沪深300 波动差", "value": 21.91,
         "unit": "%", "trigger": 0.9, "state": "on", "note": "", "date": "20261117", "pct": 0.972},
        {"key": "flow", "group": "资金", "name": "宽基 ETF 净申购(1 天)", "value": 170.68,
         "unit": "亿", "trigger": None, "state": "info", "note": "", "date": "20261116"},
    ]  # fmt: skip
    return {"as_of": "20261117", "rows": rows, "triggered": ["gap"],
            "new_triggered": ["gap"] if new else []}  # fmt: skip


# TC-SRS-001
def test_tc_srs_001_summary() -> None:
    s = SmallCapReportSection()
    assert s.build_summary(build_watch()) == (
        "小盘观察：已触发 中证1000 - 沪深300 波动差（新）；接近：中证1000 跌到 6,075 6,092。"
    )
    assert "（新）" not in s.build_summary(build_watch(new=False))
    quiet = build_watch()
    quiet["rows"] = [r | {"state": "off"} for r in quiet["rows"]]
    assert s.build_summary(quiet) == "小盘观察：没有触发。"
    assert s.build_summary(None) == ""
    assert s.build_summary({"rows": []}) == ""


# TC-SRS-002
def test_tc_srs_002_rows() -> None:
    s = SmallCapReportSection()
    html = s.build_rows(build_watch())
    assert "小盘观察" in html
    assert html.index("波动差") < html.index("跌停家数")  # triggered row first
    assert "#c4372d" in html and "#d08a2e" in html  # red triggered, amber near
    for text in (
        "84只",
        "6,092",
        "21.9%",
        "97%",
        "≥ 90% 分位",
        "≤ 6,075",
        "≥ 70%",
        "+170.7亿",
        "—",
        "已触发",
        "接近",
    ):
        assert text in html, text
    assert "数据缺失：没有 smallcap_watch.json" in s.build_rows(None)


# TC-SRS-003
def test_tc_srs_003_return_unit() -> None:
    row = {"key": "selloff", "value": -0.0188, "unit": "涨跌", "trigger": -0.03}
    assert SmallCapReportSection._format_value(row) == "-1.9%"
    assert SmallCapReportSection._format_trigger(row) == "≤ -3%"
