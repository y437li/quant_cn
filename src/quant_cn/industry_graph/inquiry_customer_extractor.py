"""DeepSeek reads exchange inquiry replies for named customers and suppliers (plan 28 ph2)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any, ClassVar

from quant_cn.industry_graph.base_quoted_extractor import BaseQuotedExtractor, QuotedItem
from quant_cn.industry_graph.counterparty_name import CounterpartyName

ROLES = ("customer", "supplier")
PAGE_WORDS = re.compile(r"客户|供应商|采购|销售金额|销售收入")
MAX_PAGES = 12


class InquiryCounterpartyItem(QuotedItem):
    """
    Purpose:
        One customer or supplier named in an inquiry reply, before the checks.

    Contract:
        Input:
            role: str (customer / supplier); name: str (as written); alias: str | None (the
            masked label the reply resolves, e.g. 客户一); period: str | None; rank: int | None;
            amount: float | None; unit: str | None; share: float | None (percent);
            share_base: str | None (what share is a percent of: 营业收入, 境外收入, 采购总额 …);
            product: str | None; region: str | None
            (country or region of the counterparty); is_related_party: bool; quote; page
        Output:
            pydantic model (unknown keys ignored, numeric text parsed)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.InquiryCustomerExtractor  -- item_model

    Test cases:
        TC-ICE-001  (via InquiryCustomerExtractor) rows kept and dropped
    """

    role: str
    name: str
    alias: str | None = None
    period: str | None = None
    rank: int | None = None
    amount: float | None = None
    unit: str | None = None
    share: float | None = None
    share_base: str | None = None
    product: str | None = None
    region: str | None = None
    is_related_party: bool = False


class InquiryCustomerExtractor(BaseQuotedExtractor):
    """
    Purpose:
        Turn an exchange inquiry reply (年报问询函 / 再融资 / 重组审核问询 replies) into
        quote-checked customer and supplier rows (plan 28 ph2): the real names behind the
        annual report's 客户一…, amounts, shares, products, and the region of foreign
        suppliers (import dependence). ROLES, PAGE_WORDS and MAX_PAGES are class attributes a
        subclass may change. The pages sent are the MAX_PAGES pages with the most
        customer / supplier words. A row is kept when its role is known, its name is not
        empty and the name or alias is in the quote (CounterpartyName.is_in_text);
        `is_named` (CounterpartyName.is_named) is False when the name only numbers the
        counterparty (客户一, 供应商A), hides it (某) or names a class (境外客户).

    Contract:
        Input:
            llm: BaseLlmClient; max_chars: int > 0; system: str | None
            (default prompts/inquiry_customer_extraction.txt)
        Output:
            instance; `list_pages`, `is_item_anchored`, `check_item`, `fetch_items`
            (BaseQuotedExtractor)
        Raises:
            (none at construction)

    Used by:
        industry_graph.ProspectusExtractor  -- base
        lake meta/runs/plan28_pilot.py (plan 28 phase 2 pilot)

    Test cases:
        TC-ICE-001  valid reply: named and anonymous rows kept (is_named), unknown role and
                    empty name dropped
        TC-ICE-002  list_pages keeps the pages with customer / supplier words only
        TC-ICE-003  a row whose name and alias are not in its quote is dropped; one found by
                    alias or short form is kept with its share_base
    """

    PROMPT_FILE = "inquiry_customer_extraction.txt"
    ROLES: ClassVar[tuple[str, ...]] = ROLES
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
                type[QuotedItem]  -- InquiryCounterpartyItem
            Raises:
                (none)
        """
        return InquiryCounterpartyItem

    def list_pages(self, pages: Sequence[str]) -> list[tuple[int, str]]:
        """
        Purpose:
            The MAX_PAGES pages with the most customer / supplier words, in page order.

        Contract:
            Input:
                pages: Sequence[str]
            Output:
                list[tuple[int, str]]  -- (page from 1, text)
            Raises:
                (none)
        """
        return self.list_top_pages(pages, self.PAGE_WORDS, self.MAX_PAGES)

    def is_item_anchored(self, item: QuotedItem, page_text: str) -> bool:
        """
        Purpose:
            True when the counterparty's name or alias is in the item's quote.

        Contract:
            Input:
                item: QuotedItem; page_text: str (unused)
            Output:
                bool
            Raises:
                (none)
        """
        if not isinstance(item, InquiryCounterpartyItem):
            return False
        return CounterpartyName.is_in_text(item.name, item.alias, item.quote)

    def check_item(self, item: QuotedItem) -> dict[str, Any] | None:
        """
        Purpose:
            The stored fields of an item with a known role and a name, plus is_named.

        Contract:
            Input:
                item: QuotedItem
            Output:
                dict[str, Any] | None  -- None for an unknown role or an empty name
            Raises:
                (none)
        """
        if not isinstance(item, InquiryCounterpartyItem) or item.role not in self.ROLES:
            return None
        name = item.name.strip()
        if not name:
            return None
        row = item.model_dump(exclude={"quote", "page"})
        row["name"] = name
        row["is_named"] = CounterpartyName.is_named(name)
        return row
