from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.application_extractor import ApplicationExtractor

PAGES = [
    (14, "公司动力电池产品主要应用于纯电动乘用车、插电式混合动力乘用车。"),
    (21, "报告期内持续获得VW、BMW等海外客户诸多定点。\n以谷歌为例，月均token调用量大幅增长。"),
]
CANDIDATES = [("PROD_AUTO_BEV_PASSENGER", "纯电动乘用车"), ("MKT_EV", "新能源汽车")]


class FakeLlm(BaseLlmClient):
    """Returns a scripted content dict; records the user message."""

    def __init__(self, content: dict[str, Any]) -> None:
        self.content = content
        self.users: list[str] = []

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        self.users.append(user)
        return LlmReply(self.content, "fake", 100, 20)


def build_content(**overrides: Any) -> dict[str, Any]:
    base = {
        "lines": [
            {
                "line": "动力电池系统",
                "applications": [
                    {"node_id": "PROD_AUTO_BEV_PASSENGER", "name": "纯电动乘用车", "weight": "主要",
                     "quote": "主要应用于纯电动乘用车", "page": 14},
                ],
                "customer_types": ["乘用车客户"],
            }
        ],
        "counterparties": [
            {"name": "BMW", "role": "customer", "detail": "定点",
             "quote": "VW、BMW等海外客户诸多定点", "page": 21},
            {"name": "谷歌", "role": "mention", "detail": "行业背景",
             "quote": "以谷歌为例", "page": 21},
        ],
    }  # fmt: skip
    base.update(overrides)
    return base


def run(content: dict[str, Any]) -> Any:
    return ApplicationExtractor(FakeLlm(content)).fetch_applications(
        "宁德时代", PAGES, ["动力电池系统"], CANDIDATES
    )


# TC-AE-001
def test_tc_ae_001_valid_reply() -> None:
    llm = FakeLlm(build_content())
    result = ApplicationExtractor(llm).fetch_applications(
        "宁德时代", PAGES, ["动力电池系统"], CANDIDATES
    )
    app = result.lines["动力电池系统"][0]
    assert app["node_id"] == "PROD_AUTO_BEV_PASSENGER" and app["weight"] == "主要"
    assert app["evidence"].page == 14
    assert result.customer_types["动力电池系统"] == ["乘用车客户"]
    assert [(p["name"], p["role"]) for p in result.counterparties] == [
        ("BMW", "customer"),
        ("谷歌", "mention"),
    ]
    assert result.dropped == 0 and result.tokens == 120
    assert "[第14页]" in llm.users[0] and "PROD_AUTO_BEV_PASSENGER: 纯电动乘用车" in llm.users[0]


# TC-AE-002
def test_tc_ae_002_quote_check() -> None:
    content = build_content()
    content["lines"][0]["applications"].append(
        {
            "node_id": "MKT_EV",
            "name": "储能",
            "weight": "次要",
            "quote": "原文中不存在的句子",
            "page": 14,
        }
    )
    content["counterparties"][0]["page"] = 14  # quote is really on page 21
    result = run(content)
    assert len(result.lines["动力电池系统"]) == 1 and result.dropped == 1
    assert result.counterparties[0]["evidence"].page == 21


# TC-AE-003
def test_tc_ae_003_unknown_node_bad_role_malformed() -> None:
    content = build_content()
    content["lines"][0]["applications"][0]["node_id"] = "PROD_NOT_A_CANDIDATE"
    content["counterparties"][1]["role"] = "investor"
    result = run(content)
    assert result.lines["动力电池系统"][0]["node_id"] is None
    assert [p["name"] for p in result.counterparties] == ["BMW"] and result.dropped == 1
    with pytest.raises(DataSourceError, match="shape"):
        run({"lines": "not a list"})
