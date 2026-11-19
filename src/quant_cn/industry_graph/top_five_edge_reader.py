"""Raw edges of an annual report's top-5 customer and supplier tables (plan 28 ph4)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from quant_cn.industry_graph.base_edge_reader import BaseEdgeReader, EdgeItem

TABLES = {"customers": "customer", "suppliers": "supplier"}
SHARE_BASE = {"customer": "营业收入", "supplier": "采购总额"}


class TopFiveEdgeReader(BaseEdgeReader):
    """
    Purpose:
        List the named rows of the rule-parsed top-5 customer and supplier tables of one
        annual report (label set report_parse; plan 12 ph3 CounterpartyTableParser). A table
        is stored as JSON text or a dict with `rows` of {rank, name, amount (元), pct, anon};
        anonymous rows (客户二) are skipped. share = pct of revenue (customers) or of total
        purchases (suppliers); unit 元; the quote is "<rank> <name> <pct>%" (the table row,
        not a sentence) and page None.

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
        TC-TFR-001  named rows of both tables kept with share, share_base and amount;
                    anonymous rows, a missing table and bad JSON skipped
    """

    def list_items(self, payload: Mapping[str, Any]) -> list[EdgeItem]:
        """
        Purpose:
            The named top-5 rows of one annual report.

        Contract:
            Input:
                payload: Mapping[str, Any]  -- report_parse record
            Output:
                list[EdgeItem]
            Raises:
                (none)
        """
        out = []
        for key, relation in TABLES.items():
            for row in self._read_rows(payload.get(key)):
                name = str(row.get("name") or "").strip()
                if not name or row.get("anon"):
                    continue
                out.append(
                    EdgeItem(
                        name=name,
                        relation=relation,
                        stage="volume",
                        amount=row.get("amount"),
                        unit="元",
                        share=row.get("pct"),
                        share_base=SHARE_BASE[relation],
                        quote=f"{row.get('rank')} {name} {row.get('pct')}%",
                    )
                )
        return out

    @staticmethod
    def _read_rows(table: Any) -> list[dict[str, Any]]:
        if isinstance(table, str):
            try:
                table = json.loads(table)
            except json.JSONDecodeError:
                return []
        rows = table.get("rows") if isinstance(table, dict) else None
        return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []
