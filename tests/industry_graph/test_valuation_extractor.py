from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.quote_checker import QuoteChecker
from quant_cn.industry_graph.valuation_extractor import ValuationExtractor

PAGES = [
    "投资要点：维持买入评级。预计2026-2028年EPS分别为2.84、3.43、5.98元，当前股价对应PE分别为16.5、13.6、7.8倍",
    "盈利预测表：营业收入、归母净利润",
    "公司介绍：生猪养殖龙头",
    "关键假设：2026年出栏量8200万头，养殖完全成本10.8元/公斤。给予2027年15倍PE，目标价60元",
]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: dict[str, Any]) -> None:
        self.content = content
        self.users: list[str] = []

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        self.users.append(user)
        return LlmReply(self.content, "fake", 50, 10)


def build_content() -> dict[str, Any]:
    return {
        "rating": "买入",
        "target_price": {"value": 60, "currency": "CNY", "quote": "目标价60元", "page": 4},
        "methods": [
            {"method": "PE", "multiple": 13.6, "multiple_kind": "implied_at_price",
             "base_year": "2027E", "quote": "当前股价对应PE分别为16.5、13.6、7.8倍", "page": 1},
            {"method": "PE", "multiple": 15, "multiple_kind": "target", "base_year": "2027E",
             "quote": "给予2027年15倍PE", "page": 4},
        ],
        "forecasts": [{"year": "2026E", "eps": 2.84}],
        "comparables": [{"name": "温氏股份", "code": None, "multiple": 11.8, "metric": "PE"}],
        "assumptions": [
            {"segment": "生猪养殖", "metric": "出栏量", "year": "2026E", "value": "8200",
             "unit": "万头", "quote": "2026年出栏量8200万头", "page": 4},
        ],
        "logic": "PE估值，成本优势。",
    }  # fmt: skip


def run(content: dict[str, Any]) -> Any:
    extractor = ValuationExtractor(FakeLlm(content), system="test")
    return extractor.fetch_valuation(
        "开源证券 2026-10-31 《测试》", extractor.list_pages(PAGES), {"温氏股份": "300498.SZ"}
    )


# TC-VE-001
def test_tc_ve_001_valid_reply() -> None:
    result = run(build_content())
    assert result.rating == "买入" and result.target_price["value"] == 60
    assert [(m["multiple_kind"], m["multiple"]) for m in result.methods] == [
        ("implied_at_price", 13.6),
        ("target", 15),
    ]
    assert result.comparables[0]["ts_code"] == "300498.SZ"
    assert result.assumptions[0]["page"] == 4 and result.dropped == 0 and result.tokens == 60


# TC-VE-002
def test_tc_ve_002_dropped_items() -> None:
    content = build_content()
    content["methods"].append(
        {
            "method": "PB",
            "multiple": 2.0,
            "multiple_kind": "target",
            "quote": "给予2027年15倍PE",
            "page": 4,
        }
    )
    content["methods"].append(
        {
            "method": "PS",
            "multiple": 3.0,
            "multiple_kind": "guess",
            "base_year": "2026E",
            "quote": "给予2027年15倍PE",
            "page": 4,
        }
    )
    content["assumptions"][0]["quote"] = "原文没有这句话"
    content["target_price"]["quote"] = "目标价99元"
    result = run(content)
    assert len(result.methods) == 2 and result.assumptions == [] and result.target_price is None
    assert result.dropped == 4


# TC-VE-003
def test_tc_ve_003_malformed_and_pages() -> None:
    with pytest.raises(DataSourceError, match="shape"):
        run({"methods": "not a list"})
    pages = ValuationExtractor(FakeLlm({}), system="x").list_pages(PAGES)
    assert [p for p, _ in pages] == [1, 2, 4]


# TC-QC-001
def test_tc_qc_001_find_evidence() -> None:
    checker = QuoteChecker([(1, "第一页 内容\n跨行 的句子"), (3, "第三页有目标价60元")])
    assert checker.find_evidence("跨行的句子", 1).page == 1
    assert checker.find_evidence("目标价60元", 1).page == 3
    assert checker.find_evidence("不存在的句子", 1) is None
    assert checker.find_evidence("第三", 3) is None


# TC-QC-002
def test_tc_qc_002_prompt_text() -> None:
    text, used = QuoteChecker.build_prompt_text([(1, "a" * 10), (2, "b" * 10), (5, "c" * 10)], 25)
    assert [p for p, _ in used] == [1, 2] and text.startswith("[第1页]\n")
    _, used = QuoteChecker.build_prompt_text([(7, "x" * 100)], 10)
    assert [p for p, _ in used] == [7]
