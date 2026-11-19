from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.industry_graph.broker_customer_extractor import BrokerCustomerExtractor

PAGES = [(2, "公司光模块已批量供货英伟达，并向谷歌送样800G产品。")]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 10, 2)


# TC-BCE-001
def test_tc_bce_001_rows_checked() -> None:
    content = {"items": [
        {"name": "英伟达", "role": "customer", "stage": "volume",
         "quote": "公司光模块已批量供货英伟达", "page": 2},
        {"name": "谷歌", "role": "customer", "stage": "sample", "quote": "并向谷歌送样800G产品",
         "page": 2},
        {"name": "谷歌", "role": "customer", "stage": "hoped", "quote": "并向谷歌送样800G产品",
         "page": 2},
    ]}  # fmt: skip
    result = BrokerCustomerExtractor(FakeLlm(content), system="t").fetch_items({}, PAGES)
    assert [(r["name"], r["stage"]) for r in result.items] == [
        ("英伟达", "volume"),
        ("谷歌", "sample"),
    ]
    assert result.dropped == 1


# TC-BCE-002
def test_tc_bce_002_list_pages() -> None:
    pages = [
        "盈利预测",
        "客户拓展顺利，已定点",
        "风险提示",
        "客户",
        "客户",
        "客户",
        "客户",
        "客户",
        "客户",
    ]
    picked = BrokerCustomerExtractor(FakeLlm({}), system="t").list_pages(pages)
    assert len(picked) == 6 and picked[0][0] == 2
