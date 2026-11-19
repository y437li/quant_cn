"""DeepSeek reads IPO prospectuses for top customers, suppliers and competitors (plan 28 ph2)."""

from __future__ import annotations

import re
from typing import ClassVar

from quant_cn.industry_graph.inquiry_customer_extractor import InquiryCustomerExtractor

ROLES = ("customer", "supplier", "competitor")
PAGE_WORDS = re.compile(
    r"前五名客户|前五名供应商|前五大客户|前五大供应商|主要客户|主要供应商|竞争对手|可比公司"
)
MAX_PAGES = 16


class ProspectusExtractor(InquiryCustomerExtractor):
    """
    Purpose:
        Turn an IPO prospectus (招股说明书) into quote-checked rows of its named top customers
        and suppliers for each reported year, and its named competitors and comparable
        companies (role competitor; amount and share null). Same item model and checks as
        InquiryCustomerExtractor; only the prompt, ROLES (adds competitor), the page words
        (前五名客户 / 主要供应商 / 竞争对手 / 可比公司 tables) and MAX_PAGES differ.

    Contract:
        Input:
            llm: BaseLlmClient; max_chars: int > 0; system: str | None
            (default prompts/prospectus_extraction.txt)
        Output:
            instance; `list_pages`, `check_item`, `fetch_items` (inherited)
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/plan28_pilot.py (plan 28 phase 2 pilot)

    Test cases:
        TC-PRE-001  competitor rows kept, unknown role dropped
        TC-PRE-002  list_pages prefers the top-5 and competitor pages
    """

    PROMPT_FILE = "prospectus_extraction.txt"
    ROLES: ClassVar[tuple[str, ...]] = ROLES
    PAGE_WORDS: ClassVar[re.Pattern[str]] = PAGE_WORDS
    MAX_PAGES: ClassVar[int] = MAX_PAGES
