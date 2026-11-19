"""The company leaf: every label of every period, one row per document (plan 28 ph4, D-161)."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from quant_cn.lake.label_store import LabelStore

LEAF_COLUMNS = [
    "ts_code",
    "period",
    "label_set",
    "doc_key",
    "doc_type",
    "known_on",
    "n_items",
]
LIST_KEYS = ("items", "counterparties", "claims", "lines")


class CompanyPeriodBuilder:
    """
    Purpose:
        Build `company_period`, the company leaf of plan 28 (D-161, CompanyCard of D-104 per
        period): one row per (company, period, label set, document) over every label set the
        LabelStore holds, with the document's doc type, known_on (when it became public) and
        n_items (the length of the payload's first list among LIST_KEYS; None when the payload
        has none). The payload itself stays in the LabelStore; a row points at it by
        (label_set, ts_code, doc_key). Rows are sorted by ts_code, period, label_set, known_on,
        doc_key.

    Contract:
        Input:
            labels: LabelStore
        Output:
            instance; `build_leaf(label_sets=None) -> DataFrame` (LEAF_COLUMNS)
        Raises:
            (none at construction)

    Used by:
        cli.DocumentCommands  -- `build-graph` wiring
        industry_graph.GraphBuilder  -- writes company_period

    Test cases:
        TC-CPB-001  rows of every set with period, known_on, doc type and n_items; sorted
        TC-CPB-002  label_sets limits the sets; no rows gives an empty frame with LEAF_COLUMNS;
                    a payload without a list or with bad JSON gives n_items None
    """

    def __init__(self, labels: LabelStore) -> None:
        self._labels = labels

    def build_leaf(self, label_sets: list[str] | None = None) -> pd.DataFrame:
        """
        Purpose:
            The leaf rows of all companies.

        Contract:
            Input:
                label_sets: list[str] | None  -- default every set of the store
            Output:
                pd.DataFrame  -- LEAF_COLUMNS
            Raises:
                SchemaError  -- a bad set name
        """
        parts = []
        for label_set in label_sets if label_sets is not None else self._labels.list_sets():
            rows = self._labels.read(label_set)
            if rows.empty:
                continue
            part = rows[["ts_code", "period", "doc_key", "doc_type", "known_on"]].copy()
            part.insert(2, "label_set", label_set)
            part["n_items"] = [self._compute_n_items(p) for p in rows["payload"]]
            parts.append(part)
        if not parts:
            return pd.DataFrame(columns=LEAF_COLUMNS)
        leaf = pd.concat(parts, ignore_index=True)[LEAF_COLUMNS]
        leaf["n_items"] = leaf["n_items"].astype("Int64")
        order = ["ts_code", "period", "label_set", "known_on", "doc_key"]
        return leaf.sort_values(order, kind="stable").reset_index(drop=True)

    @staticmethod
    def _compute_n_items(payload: Any) -> int | None:
        if not isinstance(payload, str):
            return None
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        for key in LIST_KEYS:
            if isinstance(data.get(key), list):
                return len(data[key])
        return None
