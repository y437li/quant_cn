from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.business_mode_extractor import BusinessModeExtractor

PAGES = [
    (10, "公司坚持创新驱动，主要收入来自创新药销售，同时对外许可授权获得首付款与里程碑付款。"),
    (11, "产品价格受国家集采影响，部分仿制药中标价格下降约50%，原材料成本上升难以向下游传导。"),
]
VARIANTS = [
    ("innovative_pipeline", "创新管线", "收入来自自研创新药"),
    ("generic_vbp", "仿制药集采", "收入靠集采中标"),
]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content
        self.users: list[str] = []

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        self.users.append(user)
        return LlmReply(self.content, "fake", 70, 30)


def run(content: Any) -> Any:
    return BusinessModeExtractor(FakeLlm(content), system="t").fetch_mode(
        "恒瑞医药", "A10 医药产品组合", VARIANTS, PAGES
    )


# TC-BME-001
def test_tc_bme_001_valid() -> None:
    r = run(
        {
            "variant": {
                "value": "innovative_pipeline",
                "reason": "创新药为主",
                "quote": "主要收入来自创新药销售",
                "page": 10,
            },
            "pricing": {
                "value": "regulated",
                "reason": "集采",
                "quote": "产品价格受国家集采影响",
                "page": 11,
            },
            "pass_through": {
                "value": "none",
                "reason": "难传导",
                "quote": "原材料成本上升难以向下游传导",
                "page": 11,
            },
            "price_actions": [
                {
                    "direction": "down",
                    "item": "仿制药",
                    "magnitude": "约50%",
                    "quote": "部分仿制药中标价格下降约50%",
                    "page": 11,
                }
            ],
        }
    )
    assert r.variant["value"] == "innovative_pipeline" and r.variant["evidence"].page == 10
    assert r.pricing["value"] == "regulated" and r.pass_through["value"] == "none"
    assert r.price_actions[0]["direction"] == "down" and r.dropped == 0 and r.tokens == 100


# TC-BME-002
def test_tc_bme_002_dropped() -> None:
    r = run(
        {
            "variant": {
                "value": "licence_only",
                "reason": "x",
                "quote": "对外许可授权获得首付款与里程碑付款",
                "page": 10,
            },
            "proposed_variant": "授权驱动的创新药公司",
            "pricing": {
                "value": "auction",
                "reason": "x",
                "quote": "产品价格受国家集采影响",
                "page": 11,
            },
            "pass_through": {
                "value": "full",
                "reason": "x",
                "quote": "原文中没有的一句话内容",
                "page": 11,
            },
            "price_actions": [
                {
                    "direction": "sideways",
                    "item": "x",
                    "quote": "部分仿制药中标价格下降约50%",
                    "page": 11,
                }
            ],
        }
    )
    assert r.variant is None and r.proposed_variant == "授权驱动的创新药公司"
    assert r.pricing is None and r.pass_through is None and r.price_actions == []
    assert r.dropped == 4


# TC-BME-003
def test_tc_bme_003_malformed() -> None:
    with pytest.raises(DataSourceError):
        run({"price_actions": [{"direction": "up"}]})
    empty = run(
        {"variant": {"value": None, "reason": None, "quote": None, "page": None}, "pricing": None}
    )
    assert empty.variant is None and empty.pricing is None and empty.dropped == 0
