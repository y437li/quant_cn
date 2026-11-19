"""Raw invest / finance edges of an outside-investment or restructuring label row (plan 28 ph4)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quant_cn.industry_graph.base_edge_reader import BaseEdgeReader, EdgeItem

OUTWARD = (
    "new_company",
    "capital_increase",
    "stake_purchase",
    "acquisition",
    "joint_venture",
    "fund",
)


class DealEdgeReader(BaseEdgeReader):
    """
    Purpose:
        List the deals of one label row (label set deals; DealExtractor items) whose kind
        puts money into a target (OUTWARD: new company, capital increase, stake purchase,
        acquisition, joint venture, fund) as invests_in edges to the target; the deal kind is
        kept in `detail`, the status (proposed / approved / completed / terminated) in
        `stage`, the stake in `share` (share_base "持股比例"). Disposals and projects are not
        edges to a company and are skipped.

    Contract:
        Input:
            (none)
        Output:
            instance; `list_items(payload) -> list[EdgeItem]`
        Raises:
            (none)

    Used by:
        cli.DocumentCommands  -- `build-graph` wiring
        lake meta/runs/plan28_edges.py (plan 28 phase 4)

    Test cases:
        TC-DER-001  outward deals kept with kind, status, stake and amount; disposal,
                    project and an empty target skipped
    """

    def list_items(self, payload: Mapping[str, Any]) -> list[EdgeItem]:
        """
        Purpose:
            The outward deals of one row.

        Contract:
            Input:
                payload: Mapping[str, Any]
            Output:
                list[EdgeItem]
            Raises:
                (none)
        """
        out = []
        for it in payload.get("items") or []:
            target = str(it.get("target") or "").strip()
            if it.get("kind") not in OUTWARD or not target:
                continue
            evidence = it.get("evidence") or {}
            page = evidence.get("page")
            out.append(
                EdgeItem(
                    name=target,
                    relation="invests_in",
                    stage=it.get("status"),
                    amount=it.get("amount"),
                    unit=it.get("unit"),
                    share=it.get("stake"),
                    share_base="持股比例",
                    product=it.get("target_business"),
                    quote=str(evidence.get("quote") or ""),
                    page=page if isinstance(page, int) else None,
                    detail=it.get("kind"),
                )
            )
        return out
