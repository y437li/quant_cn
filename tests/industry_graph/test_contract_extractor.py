from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.contract_extractor import ContractExtractor

PAGES = [(1, "公司收到与湖南省冶金规划设计院有限公司签订的商务合同，合同金额为人民币5,381.70万元。"
              "公司中标海外项目，中标金额1,200万美元。"),
         (2, "2026年1-9月新签合同额合计12.5亿元。签署战略合作框架协议。")]  # fmt: skip


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 30, 5)


# TC-CEX-001
def test_tc_cex_001_rows_checked() -> None:
    content = {"items": [
        {"kind": "contract", "counterparty": "湖南省冶金规划设计院有限公司", "amount": "5,381.70",
         "unit": "万元", "status": "签约", "quote": "合同金额为人民币5,381.70万元", "page": 1},
        {"kind": "contract", "amount": 1200, "amount_high": "1,500", "unit": "万美元",
         "currency": "USD", "status": "中标",
         "quote": "中标金额1,200万美元", "page": 1},
        {"kind": "period_total", "amount": 12.5, "unit": "亿元", "status": "签约",
         "period": "2026-01至2026-09", "quote": "新签合同额合计12.5亿元", "page": 2},
        {"kind": "contract", "status": "签约", "is_framework": True,
         "quote": "签署战略合作框架协议", "page": 2},
        {"kind": "contract", "amount": 1, "status": "签约", "quote": "原文没有的一句话内容",
         "page": 1},
        {"kind": "investment", "amount": 1, "status": "签约", "quote": "签署战略合作框架协议",
         "page": 2},
        {"kind": "contract", "amount": 1, "status": "意向", "quote": "签署战略合作框架协议",
         "page": 2},
    ]}  # fmt: skip
    result = ContractExtractor(FakeLlm(content), system="test").fetch_contracts(
        "博实股份", "20240601", PAGES
    )
    values = [row["amount_value"] for row in result.items]
    assert values[:3] == [pytest.approx(53_817_000.0), pytest.approx(12_000_000.0),
                          pytest.approx(1.25e9)]  # fmt: skip
    assert values[3] is None and result.items[3]["is_framework"]
    assert result.items[1]["currency"] == "USD" and result.items[0]["evidence"].page == 1
    assert result.items[1]["amount_high_value"] == pytest.approx(15_000_000.0)
    assert result.items[0]["amount_high_value"] is None and not result.items[0]["is_related_party"]
    assert result.dropped == 3 and result.tokens == 35


# TC-CEX-002
def test_tc_cex_002_malformed_reply() -> None:
    extractor = ContractExtractor(FakeLlm({"items": [{"kind": "contract"}]}), system="test")
    with pytest.raises(DataSourceError):
        extractor.fetch_contracts("测试", "20240601", PAGES)
