"""Shared base of the readers that turn one label-store row into raw company edges (plan 28 ph4)."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

YEAR = re.compile(r"^(\d{4})(?:年|年度|FY)?$")
HALF = re.compile(r"^(\d{4})(?:H1|年?上半年|年?半年度|年?1-6月)$")
QUARTER = re.compile(r"^(\d{4})(?:Q|年?第?)([1-4])(?:季度)?$")
QUARTER_END = {"1": "0331", "2": "0630", "3": "0930", "4": "1231"}


@dataclass(frozen=True)
class EdgeItem:
    """
    Purpose:
        One raw edge a document states, before its counterparty is resolved.

    Contract:
        Input:
            name: str (counterparty as written); relation: str (customer / supplier /
            partner / competitor / holds / invests_in); stage: str | None; period: str |
            None (YYYYMMDD the item describes, None = the row's period); known_on: str |
            None (None = the row's known_on); amount: float | None; unit: str | None;
            share: float | None; share_base: str | None; product: str | None; quote: str;
            page: int | None; detail: str | None
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.BaseEdgeReader  -- returned by list_items
        industry_graph.CounterpartyEdgeReader  -- returned by list_items
        industry_graph.TopFiveEdgeReader  -- returned by list_items
        industry_graph.DealEdgeReader  -- returned by list_items
        industry_graph.CompanyEdgeBuilder  -- turns it into an edge row

    Test cases:
        TC-BER-001  (via BaseEdgeReader) build_period of an item period
    """

    name: str
    relation: str
    stage: str | None = None
    period: str | None = None
    known_on: str | None = None
    amount: float | None = None
    unit: str | None = None
    share: float | None = None
    share_base: str | None = None
    product: str | None = None
    quote: str = ""
    page: int | None = None
    detail: str | None = None


class BaseEdgeReader(ABC):
    """
    Purpose:
        Base of the readers of plan 28 phase 4 (D-161 update 7): each knows the payload of one
        kind of label set (counterparty lists, annual top-5 tables, deals) and lists the raw
        edges of one label-store row as EdgeItems. `build_period` turns an item's own period
        text ("2025", "2025H1", "2025Q3", "20251231") into a period end YYYYMMDD; a range or
        anything else gives None (the row's period is used).

    Contract:
        Input:
            (subclass constructors)
        Output:
            instance; `list_items(payload) -> list[EdgeItem]` (abstract);
            `build_period(text) -> str | None` (static)
        Raises:
            (none)

    Used by:
        industry_graph.GraphBuilder  -- readers per label set
        cli.DocumentCommands  -- `build-graph` wiring
        industry_graph.CounterpartyEdgeReader  -- base
        industry_graph.TopFiveEdgeReader  -- base
        industry_graph.DealEdgeReader  -- base
        industry_graph.CompanyEdgeBuilder  -- readers per label set

    Test cases:
        TC-BER-001  build_period: 2025, 2025年, 2025H1, 2025年上半年, 2025Q3, 20251231 give
                    period ends; 2024-2025, None and text give None
    """

    @abstractmethod
    def list_items(self, payload: Mapping[str, Any]) -> list[EdgeItem]:
        """
        Purpose:
            The raw edges of one label-store row.

        Contract:
            Input:
                payload: Mapping[str, Any]  -- the row's JSON payload, parsed
            Output:
                list[EdgeItem]  -- empty when the row states none
            Raises:
                (none)
        """

    @staticmethod
    def build_period(text: Any) -> str | None:
        """
        Purpose:
            The period end of an item's own period text.

        Contract:
            Input:
                text: Any  -- str or None
            Output:
                str | None  -- YYYYMMDD
            Raises:
                (none)
        """
        value = re.sub(r"\s+", "", str(text)) if text is not None else ""
        if re.fullmatch(r"\d{8}", value):
            return value
        for pattern, end in ((YEAR, "1231"), (HALF, "0630")):
            hit = pattern.match(value)
            if hit:
                return f"{hit.group(1)}{end}"
        hit = QUARTER.match(value)
        return f"{hit.group(1)}{QUARTER_END[hit.group(2)]}" if hit else None
