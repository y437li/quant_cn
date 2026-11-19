"""One row per observed company edge, with period, known_on and evidence (plan 28 ph4, D-161)."""

from __future__ import annotations

import json
import re
from collections.abc import Collection, Mapping
from typing import Any

import pandas as pd

from quant_cn.industry_graph.base_edge_reader import BaseEdgeReader, EdgeItem
from quant_cn.industry_graph.counterparty_name import CounterpartyName
from quant_cn.industry_graph.entity_resolver import EntityResolver

EDGE_COLUMNS = [
    "src",
    "dst",
    "relation",
    "ts_code",
    "counterparty",
    "entity_id",
    "resolve_method",
    "is_group_member",
    "stage",
    "period",
    "known_on",
    "amount",
    "unit",
    "share",
    "share_base",
    "product",
    "detail",
    "label_set",
    "doc_key",
    "doc_type",
    "quote",
    "page",
]
# the company sells to the counterparty (src = company) or buys from it (src = counterparty)
INWARD = ("supplier",)
# a share or amount of a stock (balance, margin), not of a flow (sales, purchases)
NOT_FLOW = re.compile(r"余额|应收|预付|合同负债|毛利|坏账|存货|净资产|市值")
NUMERIC = ("amount", "share")


class CompanyEdgeBuilder:
    """
    Purpose:
        Build `company_edge` rows (plan 28 ph4, D-161 update 7): one row per edge a document
        states, from label-store rows read by the label set's BaseEdgeReader. The
        counterparty is resolved by EntityResolver; names that are not one counterparty
        (CounterpartyName.is_named false, or in `skip_names`: kinds generic / unknown /
        person of the entity pass) are dropped, and so is a company naming itself. Orientation:
        src sells to dst for customer (src = company) and supplier (src = counterparty); src
        is the company for partner, competitor, holds and invests_in. An item's own period
        and known_on win over the row's; an item with its own known_on (an IR answer's date)
        and no period takes that date as its period. When share_base names a balance or margin
        (NOT_FLOW: 应收账款余额, 预付款项, 毛利率 …) amount and share are cleared.

    Contract:
        Input:
            resolver:   EntityResolver
            readers:    Mapping[str, BaseEdgeReader]  -- label set -> reader
            skip_names: Collection[str]               -- names that are not one counterparty
        Output:
            instance; `build_edges(label_set, rows) -> DataFrame` (EDGE_COLUMNS)
        Raises:
            KeyError  -- a label set without a reader

    Used by:
        industry_graph.GraphBuilder  -- builds the edges of each label set
        lake meta/runs/plan28_edges.py (plan 28 phase 4)

    Test cases:
        TC-CEB-001  customer and supplier rows oriented seller -> buyer with entity ids;
                    partner / invests_in from the company; self edges, unnamed and skipped
                    names dropped
        TC-CEB-002  item period and known_on win over the row's (an item date without a
                    period is the period); NOT_FLOW share_base clears
                    amount and share; columns are EDGE_COLUMNS
        TC-CEB-003  rows without a payload or with bad JSON give no edges; an unknown label
                    set raises KeyError
    """

    def __init__(
        self,
        resolver: EntityResolver,
        readers: Mapping[str, BaseEdgeReader],
        skip_names: Collection[str] = (),
    ) -> None:
        self._resolver = resolver
        self._readers = dict(readers)
        self._skip = set(skip_names)

    def build_edges(self, label_set: str, rows: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            The edges of the rows of one label set.

        Contract:
            Input:
                label_set: str           -- a key of readers
                rows:      pd.DataFrame  -- LabelStore.read output (ts_code, doc_key,
                                            doc_type, period, known_on, payload)
            Output:
                pd.DataFrame  -- EDGE_COLUMNS, one row per kept edge
            Raises:
                KeyError  -- no reader for label_set
        """
        reader = self._readers[label_set]
        out: list[dict[str, Any]] = []
        for record in rows.to_dict("records"):
            row = {str(k): v for k, v in record.items()}
            payload = self._read_payload(row.get("payload"))
            for item in reader.list_items(payload):
                edge = self._build_edge(label_set, row, item)
                if edge is not None:
                    out.append(edge)
        frame = pd.DataFrame(out, columns=EDGE_COLUMNS)
        for col in NUMERIC:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").astype("float64")
        return frame

    def _build_edge(
        self, label_set: str, row: Mapping[str, Any], item: EdgeItem
    ) -> dict[str, Any] | None:
        if item.name in self._skip or not CounterpartyName.is_named(item.name):
            return None
        match = self._resolver.find_entity(item.name)
        company = f"a:{row['ts_code']}"
        if match.entity_id == company:
            return None
        src, dst = (
            (match.entity_id, company) if item.relation in INWARD else (company, match.entity_id)
        )
        flow = not (item.share_base and NOT_FLOW.search(item.share_base))
        return {
            "src": src,
            "dst": dst,
            "relation": item.relation,
            "ts_code": row["ts_code"],
            "counterparty": item.name,
            "entity_id": match.entity_id,
            "resolve_method": match.method,
            "is_group_member": match.is_group_member,
            "stage": item.stage,
            "period": item.period or item.known_on or row.get("period"),
            "known_on": item.known_on or row.get("known_on"),
            "amount": item.amount if flow else None,
            "unit": item.unit,
            "share": item.share if flow else None,
            "share_base": item.share_base,
            "product": item.product,
            "detail": item.detail,
            "label_set": label_set,
            "doc_key": row.get("doc_key"),
            "doc_type": row.get("doc_type"),
            "quote": item.quote,
            "page": item.page,
        }

    @staticmethod
    def _read_payload(value: Any) -> dict[str, Any]:
        if not isinstance(value, str):
            return {}
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}
