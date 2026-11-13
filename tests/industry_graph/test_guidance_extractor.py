from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.guidance_extractor import GuidanceExtractor
from quant_cn.industry_graph.pdf_text_extractor import ReportPages
from quant_cn.industry_graph.section_detector import SectionDetector

ANNUAL = ReportPages([
    "目录\n第三节 管理层讨论与分析",
    "第三节 管理层讨论与分析\n一、报告期内公司从事的主要业务\n报告期内实现营业收入100亿元。",
    "十一、公司未来发展的展望\n（一）发展战略",
    "（二）经营计划\n2026年公司计划实现营业收入120亿元，同比增长20%。",
    "第四节 公司治理",
])  # fmt: skip
INCENTIVE = ReportPages(["释义", "激励对象", "公司层面业绩考核要求\n考核年度", "2026年 70%",
                         "个人层面", "附则"])  # fmt: skip


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 40, 10)


def build(content: Any = None) -> GuidanceExtractor:
    prompts = {t: "test" for t in ("annual_plan", "ir_record", "incentive_plan")}
    return GuidanceExtractor(FakeLlm(content or {}), SectionDetector(), prompts=prompts)


# TC-GE-001
def test_tc_ge_001_source_pages() -> None:
    extractor = build()
    assert [p for p, _ in extractor.list_source_pages("annual_plan", ANNUAL)] == [3, 4]
    assert [p for p, _ in extractor.list_source_pages("incentive_plan", INCENTIVE)] == [3, 4]
    assert len(extractor.list_source_pages("ir_record", INCENTIVE)) == 6
    no_outlook = ReportPages(["第三节 管理层讨论与分析", "第四节 公司治理"])
    assert extractor.list_source_pages("annual_plan", no_outlook) == []
    with pytest.raises(DataSourceError):
        extractor.list_source_pages("prospectus", ANNUAL)


# TC-GE-002
def test_tc_ge_002_items_checked() -> None:
    quote = "2026年公司计划实现营业收入120亿元"
    content = {"items": [
        {"metric": "营业收入", "metric_class": "revenue", "period": "2026年", "basis": "level",
         "value_low": "120", "value_high": 120, "unit": "亿元", "kind": "target", "quote": quote,
         "page": 4},
        {"metric": "营业收入", "metric_class": "sales", "period": "2026", "basis": "yoy",
         "value_low": "20%", "kind": "target", "quote": "同比增长20%", "page": 3},
        {"metric": "营业收入", "period": "2025", "value_low": 100, "kind": "target",
         "quote": "报告期内实现营业收入100亿元", "page": 2},
        {"metric": "营业收入", "period": None, "value_low": 1, "kind": "target", "quote": quote,
         "page": 4},
        {"metric": "营业收入", "period": "2026", "kind": "target", "quote": quote, "page": 4},
        {"metric": "营业收入", "period": "2026", "value_low": 1, "kind": "hope", "quote": quote,
         "page": 4},
        {"metric": "营业收入", "period": "2026", "value_low": 1, "kind": "target",
         "quote": "原文中没有的一句话内容", "page": 4},
    ]}  # fmt: skip
    extractor = build(content)
    pages = extractor.list_source_pages("annual_plan", ANNUAL)
    result = extractor.fetch_guidance("测试", "annual_plan", "20270420", pages)
    first, second = result.items
    assert first["period"] == "2026" and first["value_low"] == pytest.approx(120.0)
    assert first["evidence"].page == 4 and "quote" not in first
    assert second["value_low"] == pytest.approx(20.0) and second["evidence"].page == 4
    assert second["metric_class"] == "other" and second["basis"] == "level"
    assert result.dropped == 5 and result.tokens == 50


# TC-GE-003
def test_tc_ge_003_malformed_reply() -> None:
    extractor = build({"items": [{"metric": "营业收入"}]})
    with pytest.raises(DataSourceError):
        extractor.fetch_guidance("测试", "ir_record", "20261101", [(1, "正文")])
    with pytest.raises(DataSourceError):
        build().fetch_guidance("测试", "prospectus", "20261101", [(1, "正文")])
