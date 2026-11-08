# ruff: noqa: E501  (fixture rows kept on one line)
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.broker_view_synthesizer import BrokerViewSynthesizer, ReportDigest

DIGESTS = [
    ReportDigest("R1", "开源证券", "20261031", "龙头成本优势", "买入", "60", "PE 15x 2027E 目标",
                 "成本领先", "出栏量 8200万头"),
    ReportDigest("R2", "东海证券", "20261020", "量增价稳", "增持", "", "PE 13.6x 2026E 现价隐含",
                 "出栏增长", "完全成本 10.8元/公斤"),
]  # fmt: skip


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content
        self.users: list[str] = []

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        self.users.append(user)
        return LlmReply(self.content, "fake", 60, 20)


def build_content() -> dict[str, Any]:
    return {
        "summary": "龙头享有成本溢价。",
        "method_consensus": "多数用PE",
        "multiple_range": {"metric": "PE", "implied_low": 13.6, "target_low": 15},
        "multiple_reasons": [{"point": "成本领先给溢价", "sources": ["R1", "R9"]}],
        "drivers": [{"point": "出栏量决定收入", "metric": "出栏量", "unit": "万头", "sources": ["R1", "R2"]}],
        "bull": [{"point": "编造的观点", "sources": ["R7"]}],
        "risks": [],
    }  # fmt: skip


# TC-BVS-001
def test_tc_bvs_001_valid_reply() -> None:
    llm = FakeLlm(build_content())
    view = BrokerViewSynthesizer(llm, system="test").fetch_view("company", "牧原股份", DIGESTS)
    assert view.summary == "龙头享有成本溢价。" and view.method_consensus == "多数用PE"
    assert view.multiple_range == {"metric": "PE", "implied_low": 13.6, "target_low": 15}
    assert view.points["drivers"][0]["metric"] == "出栏量" and view.n_reports == 2
    assert "[R1] 开源证券" in llm.users[0] and "[R2] 东海证券" in llm.users[0]
    loss = ReportDigest("R1", "国金", "20261101", "t", forecasts="2026E -59亿；2027E 29.6亿")
    assert "盈利预测：2026E -59亿；2027E 29.6亿" in loss.format_text()
    assert view.tokens == 80


# TC-BVS-002
def test_tc_bvs_002_citation_check() -> None:
    view = BrokerViewSynthesizer(FakeLlm(build_content()), system="test").fetch_view(
        "product", "生猪", DIGESTS
    )
    assert view.points["multiple_reasons"][0]["sources"] == ["R1"]  # R9 removed
    assert view.points["bull"] == [] and view.dropped == 1
    small = BrokerViewSynthesizer(FakeLlm(build_content()), max_chars=10, system="test")
    view = small.fetch_view("product", "生猪", DIGESTS)
    assert view.n_reports == 1 and view.points["drivers"][0]["sources"] == ["R1"]


# TC-BVS-003
def test_tc_bvs_003_errors() -> None:
    with pytest.raises(DataSourceError):
        BrokerViewSynthesizer(FakeLlm({"drivers": [{"x": 1}]}), system="t").fetch_view(
            "product", "x", DIGESTS
        )
    with pytest.raises(DataSourceError):
        BrokerViewSynthesizer(FakeLlm({}), system="t").fetch_view("sector", "x", DIGESTS)
