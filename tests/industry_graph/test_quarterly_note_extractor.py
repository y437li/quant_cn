from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.quarterly_note_extractor import QuarterlyNoteExtractor

PAGES = [
    "一、主要财务数据 营业收入 1,000",
    "主要会计数据、财务指标发生变动的情况及原因\n预付款项 增长50% 主要系预付货款增加\n"
    "营业收入增长35%，主要系光模块销量增加所致",
    "三、其他提醒事项 需提醒投资者关注的关于公司报告期经营情况的其他重要信息 √适用□不适用 "
    "公司与某运营商签订重大合同，金额12.5亿元。\n四、季度财务报表\n（一）审计意见类型",
    "合并资产负债表",
]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 40, 10)


# TC-QNE-001
def test_tc_qne_001_note_pages_and_chars() -> None:
    extractor = QuarterlyNoteExtractor(FakeLlm({}), system="test")
    pages = extractor.list_note_pages(PAGES)
    assert [p for p, _ in pages] == [2, 3]
    assert "合并资产负债表" not in pages[-1][1] and "季度财务报表" not in pages[-1][1]
    assert "预付款项" not in pages[0][1] and "营业收入增长35%" in pages[0][1]
    assert extractor.compute_note_chars(pages) == len("公司与某运营商签订重大合同，金额12.5亿元。")
    assert extractor.list_note_pages(["财务数据", "报表"]) == []
    empty = [(1, "三、其他提醒事项 □适用 √不适用")]
    assert extractor.compute_note_chars(empty) == 0


# TC-QNE-002
def test_tc_qne_002_quote_check() -> None:
    content = {"items": [
        {"kind": "order", "summary": "签重大合同", "value": "12.5", "unit": "亿元",
         "counterparty": "某运营商", "quote": "公司与某运营商签订重大合同，金额12.5亿元",
         "page": 3},
        {"kind": "driver", "summary": "销量增加", "quote": "主要系光模块销量增加所致", "page": 9},
        {"kind": "driver", "summary": "编造", "quote": "原文中不存在的一句话内容", "page": 2},
        {"kind": "governance", "summary": "高管", "quote": "营业收入增长35%，主要系光模块",
         "page": 2},
    ]}  # fmt: skip
    extractor = QuarterlyNoteExtractor(FakeLlm(content), system="test")
    result = extractor.fetch_notes("测试公司", "2026Q3", extractor.list_note_pages(PAGES))
    assert [i["kind"] for i in result.items] == ["order", "driver"]
    assert result.items[1]["evidence"].page == 2  # quote found on another page than claimed
    assert result.dropped == 2 and result.tokens == 50


# TC-QNE-003
def test_tc_qne_003_malformed() -> None:
    extractor = QuarterlyNoteExtractor(FakeLlm({"items": [{"kind": "order"}]}), system="test")
    with pytest.raises(DataSourceError):
        extractor.fetch_notes("测试公司", "2026Q3", [(1, "其他提醒事项 内容")])


# TC-QNE-004
def test_tc_qne_004_szse_wording() -> None:
    extractor = QuarterlyNoteExtractor(FakeLlm({}), system="test")
    pages = [
        "变动原因 营业收入 下降 主要系销量下降",
        "三、其他重要事项 √适用□不适用 公司中标某项目",
        "四、季度财务报表",
    ]
    note = extractor.list_note_pages(pages)
    assert extractor.compute_note_chars(note) == len("公司中标某项目")
