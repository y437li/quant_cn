from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.industry_graph.ir_customer_extractor import IrCustomerExtractor

PAGES = [(1, "[20250312] 问：公司是否给华为供货？答：公司已向华为批量供应光模块。"),
         (2, "[20250401] 问：是否与英伟达合作？答：感谢关注，公司尚未与该公司合作。")]  # fmt: skip


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 10, 2)


# TC-IRC-001
def test_tc_irc_001_rows_checked() -> None:
    content = {"items": [
        {"name": "华为", "role": "customer", "stage": "volume", "product": "光模块",
         "quote": "公司已向华为批量供应光模块", "page": 1},
        {"name": "英伟达", "role": "partner", "stage": "denied",
         "quote": "公司尚未与该公司合作", "page": 2},
        {"name": "华为", "role": "customer", "stage": "volume", "quote": "公司是否给华为供货",
         "page": 1},
        {"name": "华为", "role": "rival", "stage": "volume", "quote": "公司已向华为批量供应光模块",
         "page": 1},
        {"name": "华为", "role": "customer", "stage": "maybe",
         "quote": "公司已向华为批量供应光模块", "page": 1},
        {"name": " ", "role": "customer", "stage": "volume", "quote": "公司已向华为批量供应光模块",
         "page": 1},
    ]}  # fmt: skip
    result = IrCustomerExtractor(FakeLlm(content), system="t").fetch_items({}, PAGES)
    assert [(r["name"], r["stage"]) for r in result.items] == [
        ("华为", "volume"),
        ("英伟达", "denied"),
    ]
    assert result.dropped == 4


# TC-IRC-002
def test_tc_irc_002_list_pages() -> None:
    pages = ["问：分红？答：按章程。", "问：客户情况？答：已送样验证。", "问：股价？答：谢谢。"]
    picked = IrCustomerExtractor(FakeLlm({}), system="t").list_pages(pages)
    assert [n for n, _ in picked] == [2]


# TC-IRC-003
def test_tc_irc_003_named_and_anchored() -> None:
    pages = [(1, "问：是否向宁德时代供货？答：公司和主要客户保持稳定合作。"),
             (2, "问：与蓝箭航天合作进展？答：相关业务按照双方签署的协议推进。"),
             (3, "问：客户情况？答：公司已向头部车企和GE批量供货。")]  # fmt: skip
    content = {"items": [
        {"name": "宁德时代", "role": "customer", "stage": "volume",
         "quote": "公司和主要客户保持稳定合作", "page": 1},
        {"name": "蓝箭航天", "role": "partner", "stage": "contact",
         "quote": "相关业务按照双方签署的协议推进", "page": 2},
        {"name": "头部车企", "role": "customer", "stage": "volume",
         "quote": "公司已向头部车企和GE批量供货", "page": 3},
        {"name": "GE", "role": "customer", "stage": "volume",
         "quote": "公司已向头部车企和GE批量供货", "page": 3},
    ]}  # fmt: skip
    result = IrCustomerExtractor(FakeLlm(content), system="t").fetch_items({}, pages)
    assert [r["name"] for r in result.items] == ["蓝箭航天", "GE"]
    assert result.dropped == 2
