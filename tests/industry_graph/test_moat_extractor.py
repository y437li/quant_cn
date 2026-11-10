from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.moat_extractor import MoatExtractor

PAGES = [
    (20, "公司品牌历史悠久，茅台酒为国家地理标志产品，核心产区面积有限。"),
    (21, "公司拥有专利1200项，产品通过主要客户认证，替换周期长达三年。"),
]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 50, 25)


def run(content: Any) -> Any:
    return MoatExtractor(FakeLlm(content), system="t").fetch_claims("测试公司", PAGES)


# TC-ME-001
def test_tc_me_001_valid() -> None:
    r = run(
        {
            "claims": [
                {"type": "intangible", "claim": "地理标志品牌", "figure": None,
                 "quote": "茅台酒为国家地理标志产品", "page": 20},
                {"type": "switching", "claim": "客户认证", "figure": "替换周期三年",
                 "quote": "产品通过主要客户认证，替换周期长达三年", "page": 21},
            ],
            "summary": "品牌与认证",
        }
    )  # fmt: skip
    assert [c["type"] for c in r.claims] == ["intangible", "switching"]
    assert r.claims[1]["figure"] == "替换周期三年" and r.claims[0]["evidence"].page == 20
    assert r.summary == "品牌与认证" and r.dropped == 0 and r.tokens == 75


# TC-ME-002
def test_tc_me_002_dropped() -> None:
    r = run(
        {
            "claims": [
                {"type": "culture", "claim": "文化", "quote": "公司品牌历史悠久", "page": 20},
                {"type": "cost", "claim": "规模", "quote": "原文没有的一句话内容", "page": 20},
                {"type": "intangible", "claim": "专利", "quote": None, "page": None},
            ]
        }
    )  # fmt: skip
    assert r.claims == [] and r.dropped == 3


# TC-ME-003
def test_tc_me_003_malformed() -> None:
    with pytest.raises(DataSourceError):
        run({"claims": [{"claim": "no type"}]})
