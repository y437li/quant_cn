"""DeepSeek reads 主要经营数据 announcements into per-product figures (plan 28 ph2)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from quant_cn.industry_graph.base_quoted_extractor import BaseQuotedExtractor, QuotedItem

METRIC_CLASSES = ("revenue", "output", "sales_volume", "price", "orders", "backlog", "capacity",
                  "other")  # fmt: skip
PAGE_WORDS = re.compile(r"产量|销量|销售量|产能|价格|均价|订单|合同|营业收入|金额|吨|万元")
MAX_PAGES = 8


class OperatingDataItem(QuotedItem):
    """
    Purpose:
        One operating figure of the announcement's own period, before the checks.

    Contract:
        Input:
            metric_class: str (METRIC_CLASSES); metric: str (as written, e.g. 销量);
            product: str | None; segment: str | None (channel, region or business line);
            period: str | None (2026Q2, 2026-06, 2026H1, 2026); value: float; unit: str | None;
            yoy: float | None (percent change on a year earlier); quote; page
        Output:
            pydantic model (unknown keys ignored, numeric text parsed)
        Raises:
            pydantic.ValidationError  -- wrong types, or no number in value

    Used by:
        industry_graph.OperatingDataExtractor  -- item_model

    Test cases:
        TC-ODX-001  (via OperatingDataExtractor) rows kept and dropped
    """

    metric_class: str
    metric: str
    product: str | None = None
    segment: str | None = None
    period: str | None = None
    value: float
    unit: str | None = None
    yoy: float | None = None


class OperatingDataExtractor(BaseQuotedExtractor):
    """
    Purpose:
        Turn a 主要经营数据 announcement (monthly, quarterly, half-year or annual; the
        exchanges' industry disclosure rules) into quote-checked figures of its own period:
        revenue, output, sales volume, average price, new orders, backlog and capacity, per
        product, channel or region, with the year-on-year change when given (plan 28 ph2).
        Unlike ContractExtractor's period totals it covers volumes and prices, not only
        orders. The pages sent are the MAX_PAGES pages with the most figure words. A row is
        kept when its metric class is known and it names a metric.

    Contract:
        Input:
            llm: BaseLlmClient; max_chars: int > 0; system: str | None
            (default prompts/operating_data_extraction.txt)
        Output:
            instance; `list_pages`, `check_item`, `fetch_items` (BaseQuotedExtractor)
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/plan28_pilot.py (plan 28 phase 2 pilot)

    Test cases:
        TC-ODX-001  valid reply: rows kept with value and yoy parsed; unknown metric class,
                    empty metric and a value without a number dropped
        TC-ODX-002  list_pages keeps the pages with figure words only
    """

    PROMPT_FILE = "operating_data_extraction.txt"

    @property
    def item_model(self) -> type[QuotedItem]:
        """
        Purpose:
            The reply item model.

        Contract:
            Input:
                (none)
            Output:
                type[QuotedItem]  -- OperatingDataItem
            Raises:
                (none)
        """
        return OperatingDataItem

    def list_pages(self, pages: Sequence[str]) -> list[tuple[int, str]]:
        """
        Purpose:
            The MAX_PAGES pages with the most figure words, in page order.

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
            The stored fields of an item with a known metric class and a metric.

        Contract:
            Input:
                item: QuotedItem
            Output:
                dict[str, Any] | None  -- None for an unknown class or an empty metric
            Raises:
                (none)
        """
        if not isinstance(item, OperatingDataItem) or item.metric_class not in METRIC_CLASSES:
            return None
        if not item.metric.strip():
            return None
        return item.model_dump(exclude={"quote", "page"})
