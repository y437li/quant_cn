"""Raw edges of a counterparty-list label row: inquiry, prospectus, IR, broker, applications."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quant_cn.industry_graph.base_edge_reader import BaseEdgeReader, EdgeItem

RELATIONS = {
    "customer": "customer",
    "supplier": "supplier",
    "partner": "partner",
    "competitor": "competitor",
    "subsidiary": "holds",
}


class CounterpartyEdgeReader(BaseEdgeReader):
    """
    Purpose:
        List the named counterparties of one label row whose payload holds a list of
        {name, role, …, evidence {quote, page}} under `list_key` ("items" for the plan 28
        sets, "counterparties" for applications). Roles map by RELATIONS (subsidiary →
        holds); other roles (mention) and rows marked is_named false are skipped. An item's
        own period is parsed (build_period). When the payload has `dates` (IR Q&A chunks,
        one per page), an item's known_on is the date of its page.

    Contract:
        Input:
            list_key: str  -- payload key of the item list
        Output:
            instance; `list_items(payload) -> list[EdgeItem]`
        Raises:
            (none)

    Used by:
        cli.DocumentCommands  -- `build-graph` wiring
        lake meta/runs/plan28_edges.py (plan 28 phase 4)

    Test cases:
        TC-CER-001  items kept with relation, stage, amounts, share_base, quote and page;
                    mention and is_named false skipped; subsidiary becomes holds
        TC-CER-002  with dates, known_on is the date of the item's page; without, None
    """

    def __init__(self, list_key: str = "items") -> None:
        self._key = list_key

    def list_items(self, payload: Mapping[str, Any]) -> list[EdgeItem]:
        """
        Purpose:
            The named counterparties of one row.

        Contract:
            Input:
                payload: Mapping[str, Any]
            Output:
                list[EdgeItem]
            Raises:
                (none)
        """
        dates = payload.get("dates") or []
        out = []
        for it in payload.get(self._key) or []:
            relation = RELATIONS.get(str(it.get("role")))
            name = str(it.get("name") or "").strip()
            if relation is None or not name or it.get("is_named") is False:
                continue
            evidence = it.get("evidence") or {}
            page = evidence.get("page")
            known = dates[page - 1] if isinstance(page, int) and 0 < page <= len(dates) else None
            out.append(
                EdgeItem(
                    name=name,
                    relation=relation,
                    stage=it.get("stage"),
                    period=self.build_period(it.get("period")),
                    known_on=known,
                    amount=it.get("amount"),
                    unit=it.get("unit"),
                    share=it.get("share"),
                    share_base=it.get("share_base"),
                    product=it.get("product"),
                    quote=str(evidence.get("quote") or ""),
                    page=page if isinstance(page, int) else None,
                    detail=it.get("detail"),
                )
            )
        return out
