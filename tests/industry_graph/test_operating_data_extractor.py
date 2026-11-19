from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.industry_graph.operating_data_extractor import OperatingDataExtractor

PAGES = [(1, "复合调味料\n37,990.76\n46.87%\n轻烹解决方案 39,270.74 销量同比增长8.1%")]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 10, 2)


# TC-ODX-001
def test_tc_odx_001_rows_checked() -> None:
    content = {"items": [
        {"metric_class": "revenue", "metric": "金额", "product": "复合调味料", "period": "2026Q2",
         "value": "37,990.76", "unit": "万元", "yoy": "15.7%", "quote": "复合调味料 37,990.76",
         "page": 1},
        {"metric_class": "mood", "metric": "金额", "value": 1, "quote": "复合调味料 37,990.76",
         "page": 1},
        {"metric_class": "revenue", "metric": " ", "value": 1, "quote": "复合调味料 37,990.76",
         "page": 1},
        {"metric_class": "revenue", "metric": "金额", "value": "不适用",
         "quote": "复合调味料 37,990.76", "page": 1},
    ]}  # fmt: skip
    result = OperatingDataExtractor(FakeLlm(content), system="t").fetch_items({}, PAGES)
    assert [(r["value"], r["yoy"]) for r in result.items] == [(37990.76, 15.7)]
    assert result.dropped == 3


# TC-ODX-002
def test_tc_odx_002_list_pages() -> None:
    pages = ["董事会保证公告内容真实", "产量与销量情况", "备查文件"]
    picked = OperatingDataExtractor(FakeLlm({}), system="t").list_pages(pages)
    assert [n for n, _ in picked] == [2]
