from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.industry_graph.prospectus_extractor import ProspectusExtractor

PAGES = [(188, "前五名客户：比亚迪股份有限公司 52,310.50 31.2%。主要竞争对手为科达利。")]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 10, 2)


# TC-PRE-001
def test_tc_pre_001_competitor_kept() -> None:
    content = {"items": [
        {"role": "customer", "name": "比亚迪股份有限公司", "period": "2024", "amount": "52,310.50",
         "share": 31.2, "quote": "比亚迪股份有限公司 52,310.50", "page": 188},
        {"role": "competitor", "name": "科达利", "quote": "主要竞争对手为科达利", "page": 188},
        {"role": "investor", "name": "科达利", "quote": "主要竞争对手为科达利", "page": 188},
    ]}  # fmt: skip
    result = ProspectusExtractor(FakeLlm(content), system="t").fetch_items({}, PAGES)
    assert [r["role"] for r in result.items] == ["customer", "competitor"]
    assert result.dropped == 1


# TC-PRE-002
def test_tc_pre_002_list_pages() -> None:
    pages = ["客户服务热线", "前五名客户情况", "目录", "竞争对手与可比公司"]
    picked = ProspectusExtractor(FakeLlm({}), system="t").list_pages(pages)
    assert [n for n, _ in picked] == [2, 4]
