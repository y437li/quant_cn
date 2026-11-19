from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.industry_graph.deal_extractor import DealExtractor

PAGES = [(2, "公司拟以3.2亿元收购某某科技有限公司51%股权，标的主营车规级功率半导体。")]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 10, 2)


# TC-DEX-001
def test_tc_dex_001_rows_checked() -> None:
    quote = "公司拟以3.2亿元收购某某科技有限公司51%股权"
    content = {"items": [
        {"kind": "acquisition", "target": "某某科技有限公司", "stake": "51%", "amount": 3.2,
         "unit": "亿元", "status": "proposed", "quote": quote, "page": 2},
        {"kind": "loan", "target": "某某科技", "status": "proposed", "quote": quote, "page": 2},
        {"kind": "acquisition", "target": "某某", "status": "rumoured", "quote": quote, "page": 2},
        {"kind": "acquisition", "target": " ", "status": "proposed", "quote": quote, "page": 2},
    ]}  # fmt: skip
    result = DealExtractor(FakeLlm(content), system="t").fetch_items({}, PAGES)
    assert [(r["kind"], r["stake"]) for r in result.items] == [("acquisition", 51.0)]
    assert result.dropped == 3


# TC-DEX-002
def test_tc_dex_002_list_pages() -> None:
    pages = ["释义", "交易对方及标的公司情况", "风险提示"]
    picked = DealExtractor(FakeLlm({}), system="t").list_pages(pages)
    assert [n for n, _ in picked] == [2]
