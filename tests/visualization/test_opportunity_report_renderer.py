"""Contract tests for visualization.OpportunityReportRenderer (plan 15 ph7e)."""

from __future__ import annotations

from quant_cn.visualization.opportunity_report_renderer import OpportunityReportRenderer
from tests.visualization.report_docs import build_docs


def test_tc_orr_001_watchlist_order_and_marks() -> None:
    """TC-ORR-001"""
    mail = OpportunityReportRenderer().render(build_docs(), "20261113")
    assert mail.subject == "机会清单 2026-11-13 · 可以买 1 · 价到 0"
    html = mail.html
    assert html.index("示例甲") < html.index("示例乙")  # buy before wait
    assert "✓ 大单；? 获利盘" in html and "1/1" in html and "只看价格" in html
    assert "没有机会清单文件" in mail.text


def test_tc_orr_002_opportunities() -> None:
    """TC-ORR-002"""
    base = {"pct": 0.05, "np_yoy": 0.5, "val_value": 1.0, "val_median": 2.0, "lg_weeks_pos_4w": 3}
    opp = {
        "as_of": "20261112",
        "rows": [
            base | {"code": "000004.SZ", "name": "新面孔", "status": "listed", "is_new": True,
                    "missing": []},
            base | {"code": "000003.SZ", "name": "老面孔", "status": "listed", "is_new": False,
                    "missing": []},
            base | {"code": "000002.SZ", "name": "候补股", "status": "near", "is_new": False,
                    "missing": ["inflow"]},
        ],
        "dropped": [{"code": "000005.SZ", "name": "走掉的", "status": "listed"}],
    }  # fmt: skip
    mail = OpportunityReportRenderer().render(build_docs() | {"opportunities": opp}, "20261113")
    html = mail.html
    assert html.index("新面孔") < html.index("老面孔") < html.index("候补股")
    assert "缺：大单流入" in html and "今天移出：走掉的" in html and "+50%" in html
    assert "今日机会清单 2 只（新入选：新面孔），差一条的 1 只" in mail.text
    empty = OpportunityReportRenderer().render(
        build_docs() | {"opportunities": {"as_of": "20261112", "rows": [], "dropped": []}},
        "20261113",
    )
    assert "今天没有股票满足全部条件" in empty.html
