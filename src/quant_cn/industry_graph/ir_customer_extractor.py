"""DeepSeek reads IR Q&A and IR meeting records for named customers and suppliers (plan 28 ph2)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any, ClassVar

from quant_cn.industry_graph.base_quoted_extractor import BaseQuotedExtractor, QuotedItem
from quant_cn.industry_graph.counterparty_name import CounterpartyName

ROLES = ("customer", "supplier", "partner")
STAGES = (
    "contact",
    "sample",
    "qualified",
    "designated",
    "small_batch",
    "volume",
    "ended",
    "denied",
)
PAGE_WORDS = re.compile(r"客户|供应|送样|验证|认证|导入|定点|量产|批量|订单|合作|供货|配套")
ANSWER = "答："
# words by which an answer points back at a name the question gave (该公司, 上述, 您所说)
REFERS_BACK = re.compile(r"该|上述|您所?说|您提到|您所提|贵|双方|前述")
MAX_PAGES = 40


class IrCounterpartyItem(QuotedItem):
    """
    Purpose:
        One customer, supplier or partner the company names in an IR answer or meeting record,
        with how far the relationship has got, before the checks.

    Contract:
        Input:
            name: str; role: str (customer / supplier / partner); product: str | None;
            stage: str (STAGES); detail: str | None; quote; page
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.IrCustomerExtractor  -- item_model

    Test cases:
        TC-IRC-001  (via IrCustomerExtractor) rows kept and dropped
    """

    name: str
    role: str
    product: str | None = None
    stage: str
    detail: str | None = None


class IrCustomerExtractor(BaseQuotedExtractor):
    """
    Purpose:
        Turn IR Q&A (互动易 / e互动; each "page" is one 问 / 答 pair) or an IR meeting record
        (投资者关系活动记录表) into quote-checked rows: named customers, suppliers and partners,
        the product, and the stage reached (contact → sample → qualified → designated →
        small_batch → volume; ended; denied when the company says there is no such
        relationship). On a page holding ANSWER (答 + full-width colon) only the answer may
        be quoted: what an investor asks is not a company statement. The pages sent are the
        MAX_PAGES pages with the most customer / supply-chain words (PAGE_WORDS and MAX_PAGES
        are class attributes a subclass may change). A row is kept when role and stage are
        known, the name is a real name (CounterpartyName.is_named: not 头部车企, 某客户) and
        it is in the quote, or the quote points back (REFERS_BACK: 该公司, 上述, 您所说) and
        the name is elsewhere on the page (the investor's question).

    Contract:
        Input:
            llm: BaseLlmClient; max_chars: int > 0; system: str | None
            (default prompts/ir_customer_extraction.txt)
        Output:
            instance; `list_pages`, `is_item_anchored`, `check_item`, `build_checked_text`,
            `fetch_items`
        Raises:
            (none at construction)

    Used by:
        industry_graph.BrokerCustomerExtractor  -- base
        lake meta/runs/plan28_pilot.py (plan 28 phase 2 pilot)

    Test cases:
        TC-IRC-001  valid reply: rows kept; unknown role or stage, empty name, and a quote
                    taken from the question dropped
        TC-IRC-002  list_pages keeps pages with customer / supply-chain words only
        TC-IRC-003  unnamed rows (头部车企, 客户A) dropped, a letter name (GE) kept; a name only
                    in the question is kept when the answer points back, dropped otherwise
    """

    PROMPT_FILE = "ir_customer_extraction.txt"
    PAGE_WORDS: ClassVar[re.Pattern[str]] = PAGE_WORDS
    MAX_PAGES: ClassVar[int] = MAX_PAGES

    @property
    def item_model(self) -> type[QuotedItem]:
        """
        Purpose:
            The reply item model.

        Contract:
            Input:
                (none)
            Output:
                type[QuotedItem]  -- IrCounterpartyItem
            Raises:
                (none)
        """
        return IrCounterpartyItem

    def list_pages(self, pages: Sequence[str]) -> list[tuple[int, str]]:
        """
        Purpose:
            The MAX_PAGES pages with the most customer / supply-chain words, in page order.

        Contract:
            Input:
                pages: Sequence[str]  -- Q&A pairs or record pages
            Output:
                list[tuple[int, str]]  -- (page from 1, text)
            Raises:
                (none)
        """
        return self.list_top_pages(pages, self.PAGE_WORDS, self.MAX_PAGES)

    def build_checked_text(self, text: str) -> str:
        """
        Purpose:
            The answer part of a Q&A page (after ANSWER); a page without it, whole.

        Contract:
            Input:
                text: str
            Output:
                str
            Raises:
                (none)
        """
        return text.split(ANSWER, 1)[1] if ANSWER in text else text

    def is_item_anchored(self, item: QuotedItem, page_text: str) -> bool:
        """
        Purpose:
            True when the name is in the quote, or the quote points back and the name is
            elsewhere on the page.

        Contract:
            Input:
                item: QuotedItem; page_text: str  -- the whole page (question included)
            Output:
                bool
            Raises:
                (none)
        """
        if not isinstance(item, IrCounterpartyItem):
            return False
        if CounterpartyName.is_in_text(item.name, None, item.quote):
            return True
        return bool(REFERS_BACK.search(item.quote)) and CounterpartyName.is_in_text(
            item.name, None, page_text
        )

    def check_item(self, item: QuotedItem) -> dict[str, Any] | None:
        """
        Purpose:
            The stored fields of an item with a known role and stage and a real name.

        Contract:
            Input:
                item: QuotedItem
            Output:
                dict[str, Any] | None  -- None for an unknown role or stage or an unnamed row
            Raises:
                (none)
        """
        if not isinstance(item, IrCounterpartyItem) or item.role not in ROLES:
            return None
        if item.stage not in STAGES or not CounterpartyName.is_named(item.name):
            return None
        row = item.model_dump(exclude={"quote", "page"})
        row["name"] = item.name.strip()
        return row
