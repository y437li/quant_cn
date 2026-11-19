from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.industry_graph.buyback_terms_extractor import BuybackTermsExtractor

QUOTE = "以自有资金不低于人民币10,000万元（含），不超过人民币16,000万元（含）进行回购"
LOAN = "取得中国工商银行出具的贷款承诺函，贷款金额不超过1.2亿元"
PAGES = [(1, f"（4）回购股份的资金总额及资金来源：{QUOTE}。"), (2, LOAN)]


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        return LlmReply(self.content, "fake", 10, 2)


def run(items: list[dict[str, Any]]) -> Any:
    return BuybackTermsExtractor(FakeLlm({"items": items}), system="t").fetch_items({}, PAGES)


# TC-BTX-001
def test_tc_btx_001_items_checked() -> None:
    result = run([
        {"kind": "回购", "purpose": ["维护价值", "回馈"], "holder_type": ["董监高"],
         "holders": ["某人"], "funding": ["自有", "专项贷款"], "loan_bank": "中国工商银行",
         "loan_amount": "1.2", "loan_unit": "亿元", "amount_low": "10,000",
         "amount_high": 16000, "amount_unit": "万元", "price_cap": "20.00元/股",
         "period_months": 12, "method": "集中竞价", "quote": QUOTE, "page": 1},
        {"kind": "增发", "amount_high": 1, "amount_unit": "元", "quote": QUOTE, "page": 1},
        {"kind": "增持", "holder_type": ["控股股东"], "quote": QUOTE, "page": 1},
    ])  # fmt: skip
    assert result.dropped == 2
    (row,) = result.items
    assert (row["amount_low"], row["amount_high"]) == (1e8, 1.6e8)
    assert row["loan_amount"] == 1.2e8 and row["price_cap"] == 20.0
    assert row["purpose"] == ["维护价值", "其他"]
    assert row["holder_type"] == [] and row["holders"] == []
    assert "amount_unit" not in row and row["evidence"]["page"] == 1


# TC-BTX-002
def test_tc_btx_002_list_pages() -> None:
    pages = ["方案", "价格", "期限", "风险提示", "专项贷款承诺函 贷款承诺", "备查文件"]
    picked = BuybackTermsExtractor(FakeLlm({}), system="t").list_pages(pages)
    assert [n for n, _ in picked] == [1, 2, 3, 5]


# TC-BTX-003
def test_tc_btx_003_unknown_unit() -> None:
    result = run([
        {"kind": "增持", "holder_type": ["国资平台", "控股股东"], "holders": [" 汇金 "],
         "funding": ["自有"], "amount_high": 5, "amount_unit": "美元", "ratio_low": 0.5,
         "ratio_high": "1%", "quote": QUOTE, "page": 1},
    ])  # fmt: skip
    (row,) = result.items
    assert row["amount_high"] is None and row["ratio_high"] == 1.0
    assert row["holder_type"] == ["国资平台", "控股股东"] and row["holders"] == ["汇金"]
    assert row["purpose"] == []
