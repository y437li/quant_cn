"""DeepSeek reads investment and restructuring announcements into deal rows (plan 28 ph2)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from quant_cn.industry_graph.base_quoted_extractor import BaseQuotedExtractor, QuotedItem

KINDS = ("new_company", "capital_increase", "stake_purchase", "acquisition", "disposal",
         "joint_venture", "fund", "project")  # fmt: skip
STATUSES = ("proposed", "approved", "completed", "terminated")
PAGE_WORDS = re.compile(
    r"标的|交易对方|投资金额|出资|持股比例|股权比例|主营业务|经营范围|交易价格|作价|增资"
)
MAX_PAGES = 10


class DealItem(QuotedItem):
    """
    Purpose:
        One investment, acquisition, disposal or restructuring the company announces, before
        the checks.

    Contract:
        Input:
            kind: str (KINDS); target: str (company, fund or project); target_business:
            str | None (its products or industry); counterparty: str | None (seller, buyer or
            partner); stake: float | None (percent the company holds afterwards, or sells);
            amount: float | None; unit: str | None; is_related_party: bool; status: str
            (STATUSES); quote; page
        Output:
            pydantic model (unknown keys ignored, numeric text parsed)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.DealExtractor  -- item_model

    Test cases:
        TC-DEX-001  (via DealExtractor) rows kept and dropped
    """

    kind: str
    target: str
    target_business: str | None = None
    counterparty: str | None = None
    stake: float | None = None
    amount: float | None = None
    unit: str | None = None
    is_related_party: bool = False
    status: str = "proposed"


class DealExtractor(BaseQuotedExtractor):
    """
    Purpose:
        Turn an outside-investment announcement (对外投资, 增资, 收购, 出售, 设立合资公司,
        产业基金) or a restructuring report (重大资产重组报告书) into quote-checked deal rows
        (plan 28 ph2): what kind of deal, the target and its business, the other party, the
        stake, the amount and the status. These become the finance / invest edges of the chain
        graph. The pages sent are the MAX_PAGES pages with the most deal words (all of a short
        announcement). A row is kept when kind and status are known and the target is not
        empty.

    Contract:
        Input:
            llm: BaseLlmClient; max_chars: int > 0; system: str | None
            (default prompts/deal_extraction.txt)
        Output:
            instance; `list_pages`, `check_item`, `fetch_items` (BaseQuotedExtractor)
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/plan28_pilot.py (plan 28 phase 2 pilot)

    Test cases:
        TC-DEX-001  valid reply: rows kept; unknown kind or status and empty target dropped
        TC-DEX-002  list_pages keeps the pages with deal words only
    """

    PROMPT_FILE = "deal_extraction.txt"

    @property
    def item_model(self) -> type[QuotedItem]:
        """
        Purpose:
            The reply item model.

        Contract:
            Input:
                (none)
            Output:
                type[QuotedItem]  -- DealItem
            Raises:
                (none)
        """
        return DealItem

    def list_pages(self, pages: Sequence[str]) -> list[tuple[int, str]]:
        """
        Purpose:
            The MAX_PAGES pages with the most deal words, in page order.

        Contract:
            Input:
                pages: Sequence[str]
            Output:
                list[tuple[int, str]]  -- (page from 1, text)
            Raises:
                (none)
        """
        return self.list_top_pages(pages, PAGE_WORDS, MAX_PAGES)

    def check_item(self, item: QuotedItem) -> dict[str, Any] | None:
        """
        Purpose:
            The stored fields of an item with a known kind and status and a target.

        Contract:
            Input:
                item: QuotedItem
            Output:
                dict[str, Any] | None  -- None for an unknown kind or status or an empty target
            Raises:
                (none)
        """
        if not isinstance(item, DealItem) or item.kind not in KINDS:
            return None
        if item.status not in STATUSES or not item.target.strip():
            return None
        row = item.model_dump(exclude={"quote", "page"})
        row["target"] = item.target.strip()
        return row
