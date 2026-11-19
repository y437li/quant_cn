"""DeepSeek reads broker stock reports for the customers they name (plan 28 ph2)."""

from __future__ import annotations

import re
from typing import ClassVar

from quant_cn.industry_graph.ir_customer_extractor import IrCustomerExtractor

PAGE_WORDS = re.compile(r"客户|供应链|供货|送样|认证|定点|量产|批量|订单|配套|合作")
MAX_PAGES = 6


class BrokerCustomerExtractor(IrCustomerExtractor):
    """
    Purpose:
        Turn a broker stock report (个股研报) into quote-checked rows of the customers,
        suppliers and partners it names for the covered company and the stage reached
        (plan 28 ph2; customer edges of D-102). Same item model, stages and checks as
        IrCustomerExtractor; its own prompt (the analyst's statements count; peers, investees
        and the analyst's forecasts do not), page words and MAX_PAGES. A report has no 问 / 答
        pages, so the whole page is quotable.

    Contract:
        Input:
            llm: BaseLlmClient; max_chars: int > 0; system: str | None
            (default prompts/broker_customer_extraction.txt)
        Output:
            instance; `list_pages`, `check_item`, `fetch_items` (inherited)
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/plan28_pilot.py (plan 28 phase 2 pilot)

    Test cases:
        TC-BCE-001  rows kept with their stage; unknown stage dropped
        TC-BCE-002  list_pages keeps the pages with customer words, at most MAX_PAGES
    """

    PROMPT_FILE = "broker_customer_extraction.txt"
    PAGE_WORDS: ClassVar[re.Pattern[str]] = PAGE_WORDS
    MAX_PAGES: ClassVar[int] = MAX_PAGES
