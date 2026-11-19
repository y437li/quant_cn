from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.base_quoted_extractor import BaseQuotedExtractor, QuotedItem

PAGES = [(1, "公司向甲公司销售电池结构件3.5亿元。"), (2, "向乙公司采购铝材1.2亿元。")]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 30, 5)


class NameItem(QuotedItem):
    name: str
    amount: float | None = None


class NameExtractor(BaseQuotedExtractor):
    PROMPT_FILE = "inquiry_customer_extraction.txt"

    @property
    def item_model(self) -> type[QuotedItem]:
        return NameItem

    def list_pages(self, pages: Sequence[str]) -> list[tuple[int, str]]:
        return list(enumerate(pages, 1))

    def check_item(self, item: QuotedItem) -> dict[str, Any] | None:
        if not isinstance(item, NameItem) or item.name == "refused":
            return None
        return item.model_dump(exclude={"quote", "page"})


# TC-BQE-001
def test_tc_bqe_001_items_checked() -> None:
    content = {"items": [
        {"name": "甲公司", "amount": "3.5亿", "quote": "向甲公司销售电池结构件", "page": 1},
        {"name": "乙公司", "quote": "向乙公司采购铝材", "page": 1},
        {"name": "丙公司", "quote": "向丙公司采购铜材", "page": 2},
        {"name": "refused", "quote": "向乙公司采购铝材", "page": 2},
    ]}  # fmt: skip
    result = NameExtractor(FakeLlm(content), system="t").fetch_items({"公司": "某某"}, PAGES)
    assert [r["name"] for r in result.items] == ["甲公司", "乙公司"]
    assert result.items[0]["amount"] == pytest.approx(3.5)
    assert result.items[1]["evidence"] == {"quote": "向乙公司采购铝材", "page": 2}
    assert result.dropped == 2 and result.tokens == 35 and result.pages == [1, 2]


# TC-BQE-002
def test_tc_bqe_002_wrong_shape() -> None:
    quote = "向甲公司销售电池结构件"
    content = {
        "items": [{"quote": quote, "page": 1}, {"name": "甲公司", "quote": quote, "page": 1}]
    }
    result = NameExtractor(FakeLlm(content), system="t").fetch_items({}, PAGES)
    assert len(result.items) == 1 and result.dropped == 1
    with pytest.raises(DataSourceError):
        NameExtractor(FakeLlm({"rows": []}), system="t").fetch_items({}, PAGES)


# TC-BQE-003
def test_tc_bqe_003_list_top_pages() -> None:
    pages = ["客户", "无关", "客户客户客户", "客户客户", "客户"]
    picked = BaseQuotedExtractor.list_top_pages(pages, re.compile("客户"), 3)
    assert [n for n, _ in picked] == [1, 3, 4]


class AnswerExtractor(NameExtractor):
    def build_checked_text(self, text: str) -> str:
        return text.split("答：", 1)[-1]


# TC-BQE-004
def test_tc_bqe_004_checked_text() -> None:
    pages = [(1, "问：甲公司是客户吗？答：乙公司是公司客户。")]
    content = {"items": [{"name": "甲", "quote": "甲公司是客户吗", "page": 1},
                         {"name": "乙", "quote": "乙公司是公司客户", "page": 1}]}  # fmt: skip
    result = AnswerExtractor(FakeLlm(content), system="t").fetch_items({}, pages)
    assert [r["name"] for r in result.items] == ["乙"] and result.dropped == 1


class AnchoredExtractor(NameExtractor):
    def is_item_anchored(self, item: QuotedItem, page_text: str) -> bool:
        return isinstance(item, NameItem) and item.name in item.quote


# TC-BQE-005
def test_tc_bqe_005_anchor_hook() -> None:
    content = {"items": [
        {"name": "甲公司", "quote": "向甲公司销售电池结构件", "page": 1},
        {"name": "丁公司", "quote": "向乙公司采购铝材", "page": 2},
    ]}  # fmt: skip
    result = AnchoredExtractor(FakeLlm(content), system="t").fetch_items({}, PAGES)
    assert [r["name"] for r in result.items] == ["甲公司"] and result.dropped == 1
