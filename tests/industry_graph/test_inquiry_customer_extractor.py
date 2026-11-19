from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.industry_graph.inquiry_customer_extractor import InquiryCustomerExtractor

PAGES = [(3, "客户一为宁德时代新能源科技股份有限公司，2025年销售额3.52亿元，占比18.6%。"
              "供应商A向公司供应铝材。西安某科技有限公司采购模块。")]  # fmt: skip


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 10, 2)


# TC-ICE-001
def test_tc_ice_001_rows_checked() -> None:
    content = {"items": [
        {"role": "customer", "name": "宁德时代新能源科技股份有限公司", "alias": "客户一",
         "period": "2025", "amount": "3.52", "unit": "亿元", "share": "18.6%",
         "quote": "客户一为宁德时代新能源科技股份有限公司", "page": 3},
        {"role": "supplier", "name": "供应商A", "quote": "供应商A向公司供应铝材", "page": 3},
        {"role": "customer", "name": "西安某科技有限公司", "quote": "西安某科技有限公司采购模块",
         "page": 3},
        {"role": "competitor", "name": "某公司", "quote": "供应商A向公司供应铝材", "page": 3},
        {"role": "customer", "name": "  ", "quote": "供应商A向公司供应铝材", "page": 3},
    ]}  # fmt: skip
    result = InquiryCustomerExtractor(FakeLlm(content), system="t").fetch_items({}, PAGES)
    assert [(r["role"], r["is_named"]) for r in result.items] == [
        ("customer", True), ("supplier", False), ("customer", False)]  # fmt: skip
    assert result.items[0]["share"] == 18.6 and result.dropped == 2


# TC-ICE-002
def test_tc_ice_002_list_pages() -> None:
    pages = ["目录", "前五名客户销售金额", "董事会决议", "主要供应商采购情况"]
    picked = InquiryCustomerExtractor(FakeLlm({}), system="t").list_pages(pages)
    assert [n for n, _ in picked] == [2, 4]


# TC-ICE-003
def test_tc_ice_003_name_in_quote() -> None:
    pages = [(5, "客户一为宁德时代，占境外收入97%。发行人与上述两家公司交易较小。")]
    content = {"items": [
        {"role": "customer", "name": "宁德时代新能源科技股份有限公司", "share": 97,
         "share_base": "境外收入", "quote": "客户一为宁德时代，占境外收入97%", "page": 5},
        {"role": "customer", "name": "陕西智安迅科技有限公司",
         "quote": "发行人与上述两家公司交易较小", "page": 5},
        {"role": "customer", "name": "比亚迪股份有限公司", "alias": "客户一",
         "quote": "客户一为宁德时代", "page": 5},
    ]}  # fmt: skip
    result = InquiryCustomerExtractor(FakeLlm(content), system="t").fetch_items({}, pages)
    assert [r["name"] for r in result.items] == [
        "宁德时代新能源科技股份有限公司",
        "比亚迪股份有限公司",
    ]
    assert result.items[0]["share_base"] == "境外收入" and result.dropped == 1
