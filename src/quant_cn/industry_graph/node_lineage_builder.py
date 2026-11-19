"""node_lineage: what each accepted taxonomy version changed, node by node (plan 28 ph3b-4)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.exceptions import ConfigError
from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy
from quant_cn.industry_graph.taxonomy_change_set import TaxonomyChange, TaxonomyChangeSet

LINEAGE_COLUMNS = [
    "version",
    "effective_period",
    "kind",
    "node_id",
    "from_node",
    "to_node",
    "detail",
    "reason",
]


class NodeLineageBuilder:
    """
    Purpose:
        Turn the accepted taxonomy versions into `node_lineage` rows (plan 28 ph3b-4, D-161)
        by comparing the taxonomy before and after each change: `new` (from_node the split
        source when split_from is given, else None), `rename` (detail "old → new name"),
        `move` (a node's segment changed: from_node the old segment, to_node the new one),
        `alias` (detail "+added -dropped"), `retire` / `merge` (from_node the node, to_node
        its successor). A version that retires a node into a missing successor, or retire
        chains that loop, raise ConfigError (lineage must be acyclic and every retired node
        must have a successor).

    Contract:
        Input:
            folder: Path  -- config/industry_chain (v0 files)
        Output:
            instance; `build_lineage(change_sets) -> DataFrame` (LINEAGE_COLUMNS)
        Raises:
            (none at construction)

    Used by:
        cli.DocumentCommands  -- `build-graph` writes node_lineage

    Test cases:
        TC-NLB-001  new, split, rename, move, alias and merge rows from one version
        TC-NLB-002  a missing successor or a retire loop raises ConfigError; no versions give
                    an empty frame with LINEAGE_COLUMNS
    """

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def build_lineage(self, change_sets: Sequence[TaxonomyChangeSet]) -> pd.DataFrame:
        """
        Purpose:
            Lineage rows of every version, in order.

        Contract:
            Input:
                change_sets: Sequence[TaxonomyChangeSet]  -- accepted versions, in order
            Output:
                pd.DataFrame  -- LINEAGE_COLUMNS
            Raises:
                ConfigError  -- missing successor or a retire loop
        """
        rows: list[dict[str, Any]] = []
        successors: dict[str, str] = {}
        for i, change_set in enumerate(change_sets):
            before = ProductTaxonomy(self._folder, change_sets[:i])
            after = ProductTaxonomy(self._folder, change_sets[: i + 1])
            for change in change_set.changes:
                base = {"version": change_set.version,
                        "effective_period": change_set.effective_period,
                        "reason": change.reason}  # fmt: skip
                if change.op == "retire":
                    self._check_successor(change, after, successors)
                    rows.append({**base, "kind": change.kind or "retire", "node_id": change.id,
                                 "from_node": change.id, "to_node": change.successor,
                                 "detail": None})  # fmt: skip
                    continue
                rows += [{**base, **r} for r in self._list_upsert_rows(change, before, after)]
        return pd.DataFrame(rows, columns=LINEAGE_COLUMNS)

    @staticmethod
    def _list_upsert_rows(
        change: TaxonomyChange, before: ProductTaxonomy, after: ProductTaxonomy
    ) -> list[dict[str, Any]]:
        node_id = change.node_id
        old = before.get_node(node_id)
        new = after.get_node(node_id)
        if new is None:
            return []
        if old is None or old.id != node_id:
            source = change.split_from[0] if change.split_from else None
            kind = "split" if change.split_from else "new"
            return [{"kind": kind, "node_id": node_id, "from_node": source, "to_node": node_id,
                     "detail": new.name}]  # fmt: skip
        rows: list[dict[str, Any]] = []
        if old.name != new.name:
            rows.append({"kind": "rename", "node_id": node_id, "from_node": node_id,
                         "to_node": node_id, "detail": f"{old.name} → {new.name}"})  # fmt: skip
        if old.segment != new.segment:
            rows.append({"kind": "move", "node_id": node_id, "from_node": old.segment,
                         "to_node": new.segment, "detail": None})  # fmt: skip
        added = [a for a in new.aliases if a not in old.aliases]
        dropped = [a for a in old.aliases if a not in new.aliases]
        if added or dropped:
            detail = " ".join([*(f"+{a}" for a in added), *(f"-{a}" for a in dropped)])
            rows.append({"kind": "alias", "node_id": node_id, "from_node": node_id,
                         "to_node": node_id, "detail": detail})  # fmt: skip
        return rows

    @staticmethod
    def _check_successor(
        change: TaxonomyChange, after: ProductTaxonomy, successors: dict[str, str]
    ) -> None:
        node_id, successor = str(change.id), str(change.successor)
        if after.get_node(successor) is None:
            raise ConfigError(f"{node_id}: successor {successor} does not exist")
        successors[node_id] = successor
        seen = {node_id}
        current = successor
        while current in successors:
            if current in seen:
                raise ConfigError(f"retire loop through {current}")
            seen.add(current)
            current = successors[current]
