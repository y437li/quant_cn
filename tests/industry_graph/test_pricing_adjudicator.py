from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.pricing_adjudicator import PricingAdjudicator

ARCH = {"A1": "大宗商品生产", "A7": "公用事业/基础设施"}
EVIDENCE = {
    "P1": "毛利率 35.1%，同三级行业分位 71%",
    "P2": "单季毛利率波动 1.9pp，同行中位 7.7pp",
    "A1": "年报：长协煤占比高，煤电一体化",
    "B": "研报：高分红、长协稳定盈利",
}


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content
        self.users: list[str] = []

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        self.users.append(user)
        return LlmReply(self.content, "fake", 80, 20)


def run(content: Any) -> Any:
    return PricingAdjudicator(FakeLlm(content), system="t").fetch_verdict(
        "中国神华", "A1", ARCH, EVIDENCE
    )


# TC-PAD-001
def test_tc_pad_001_valid() -> None:
    v = run(
        {
            "label": "lean_maker",
            "confidence": "medium",
            "archetype_ok": False,
            "archetype": "A7",
            "variant_note": "长协煤加煤电一体化",
            "reasons": [{"point": "毛利率稳定", "sources": ["P2", "A1"]}],
        }
    )
    assert v.label == "lean_maker" and v.confidence == "medium"
    assert v.archetype_ok is False and v.archetype == "A7"
    assert v.reasons == [{"point": "毛利率稳定", "sources": ["P2", "A1"]}] and v.tokens == 100


# TC-PAD-002
def test_tc_pad_002_citations() -> None:
    v = run(
        {
            "label": "middle",
            "confidence": "certain",
            "archetype": "A99",
            "reasons": [
                {"point": "有据", "sources": ["P1", "X9"]},
                {"point": "无据", "sources": ["Q7"]},
            ],
        }
    )
    assert v.reasons == [{"point": "有据", "sources": ["P1"]}] and v.dropped == 1
    assert v.archetype is None and v.confidence == "low"


# TC-PAD-003
def test_tc_pad_003_errors() -> None:
    with pytest.raises(DataSourceError):
        run({"label": "monopolist"})
    with pytest.raises(DataSourceError):
        run({"confidence": "high"})
