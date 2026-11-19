"""Contract tests for visualization.MonitorReportRenderer (plan 15 ph7e)."""

from __future__ import annotations

from quant_cn.visualization.futures_report_section import FuturesReportSection
from quant_cn.visualization.macro_report_section import MacroReportSection
from quant_cn.visualization.monitor_report_renderer import MonitorReportRenderer
from tests.visualization.report_docs import build_docs, build_futures, build_macro


def test_tc_mrr_001_sections_and_alerts() -> None:
    """TC-MRR-001"""
    mail = MonitorReportRenderer().render(build_docs(), "20261113")
    assert mail.subject == "持仓监测 2026-11-13 · 5 条提醒"
    for line in (
        "示例甲：收盘 8.90 ≤ 止损 9.00",
        "示例甲：散户温度计 0.85，散户在进",
        "示例甲：条件已满足 1 条（毛利率 ≥ 22%；按 2026-09-30 财报）",
        "因子异动：贝塔 昨日 −2.4σ",
        "因子波动放大：成长 实际 / 预测波动 1.7 倍",
    ):
        assert line in mail.text and line in mail.html
    for title in ("持仓明细", "风格敞口", "因子表现", "行业因子", "国家队 ETF"):
        assert title in mail.html
    assert "数据缺失" not in mail.html and "1,000,000" in mail.html


def test_tc_mrr_002_missing_documents() -> None:
    """TC-MRR-002"""
    docs = build_docs() | {"factor_monitor": None, "etf_proxy": None}
    mail = MonitorReportRenderer().render(docs, "20261113")
    assert "数据缺失：没有 factor_monitor.json" in mail.html
    assert "数据缺失：没有 etf_proxy.json" in mail.html and "持仓明细" in mail.html
    empty = MonitorReportRenderer().render({}, "20261113")
    assert "今天没有提醒" in empty.text and "数据缺失：没有 holdings_risk.json" in empty.html


def test_tc_mrr_003_macro_block() -> None:
    """TC-MRR-003"""
    docs = build_docs() | {"macro_monitor": build_macro(), "futures_monitor": build_futures()}
    sections = [MacroReportSection(), FuturesReportSection()]
    mail = MonitorReportRenderer(sections).render(docs, "20261113")
    assert "宏观：CPI 同比 0.7%" in mail.text and "价格 · CPI 同比" in mail.html
    assert "期货：1 个信号，新增 1 个（铜）" in mail.text and "近月升水 +3.8%" in mail.html
    assert mail.subject.endswith("5 条提醒")  # the macro line is not an alert
    plain = MonitorReportRenderer().render(docs, "20261113")
    assert "宏观" not in plain.html


def test_tc_mrr_004_paid_back_position() -> None:
    """TC-MRR-004"""
    docs = build_docs()
    paid = {
        "code": "300304.SZ",
        "name": "示例丙",
        "weight": 0.05,
        "cost": -2.46,
        "pnl": 24700.0,
        "pnl_pct": None,
        "contrib": 0.1,
    }
    docs["holdings_risk"]["positions"].append(paid)
    assert "已回本" in MonitorReportRenderer().render(docs, "20261113").html


def test_tc_mrr_005_avoid_first() -> None:
    """TC-MRR-005"""
    docs = build_docs()
    review = docs["holdings_risk"]["reviews"]["600000.SH"]
    review["chips"] = review["chips"] | {"retail_gauge": 0.95, "gauge_avoid": 1.0}
    mail = MonitorReportRenderer().render(docs, "20261113")
    first = "示例甲：散户过热，温度计 0.95（≥ 0.9），注意回避"
    assert first in mail.text and mail.text.index(first) < mail.text.index("止损")
    assert "散户在进" not in mail.text
    review["chips"]["gauge_avoid_strong"] = 1.0
    strong = MonitorReportRenderer().render(docs, "20261113")
    assert "连续 3 次 ≥ 0.9，强烈回避" in strong.text
