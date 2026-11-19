from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.industry_graph.node_lineage_builder import LINEAGE_COLUMNS, NodeLineageBuilder
from quant_cn.industry_graph.taxonomy_change_set import TaxonomyChangeSet

BASE = """
sector: {sw_l1: "630000", name: 电力设备}
nodes:
  - {id: SEG_BAT, type: segment, name: 电池}
  - {id: SEG_LI, type: segment, name: 锂电池}
  - {id: SEG_FC, type: segment, name: 燃料电池}
  - {id: SEG_H2, type: segment, name: 氢能与燃料电池}
  - {id: PROD_CELL, type: product, name: 电芯, segment: SEG_BAT, aliases: [电池芯]}
"""


def build_folder(tmp_path: Path) -> Path:
    (tmp_path / "630000_power.yaml").write_text(BASE, encoding="utf-8")
    return tmp_path


def build_set(changes: list[dict[str, Any]], version: str = "v1") -> TaxonomyChangeSet:
    return TaxonomyChangeSet.model_validate(
        {"version": version, "effective_period": "20251231", "changes": changes}
    )


# TC-NLB-001
def test_tc_nlb_001_rows(tmp_path: Path) -> None:
    changes = build_set([
        {"op": "upsert", "kind": "rename",
         "node": {"id": "SEG_BAT", "type": "segment", "name": "电池产业"}},
        {"op": "upsert", "kind": "split", "split_from": ["SEG_BAT"],
         "node": {"id": "SEG_SSB", "type": "segment", "name": "固态电池"}},
        {"op": "upsert", "kind": "alias", "drop_aliases": ["电池芯"],
         "node": {"id": "PROD_CELL", "type": "product", "name": "电芯", "segment": "SEG_LI",
                  "aliases": ["锂电芯"]}},
        {"op": "retire", "kind": "merge", "id": "SEG_FC", "successor": "SEG_H2"},
    ])  # fmt: skip
    lineage = NodeLineageBuilder(build_folder(tmp_path)).build_lineage([changes])
    assert list(lineage.columns) == LINEAGE_COLUMNS
    cols = lineage[["kind", "node_id", "from_node", "to_node", "detail"]].astype(object)
    got = cols.where(cols.notna(), None).values.tolist()
    assert got == [
        ["rename", "SEG_BAT", "SEG_BAT", "SEG_BAT", "电池 → 电池产业"],
        ["split", "SEG_SSB", "SEG_BAT", "SEG_SSB", "固态电池"],
        ["move", "PROD_CELL", "SEG_BAT", "SEG_LI", None],
        ["alias", "PROD_CELL", "PROD_CELL", "PROD_CELL", "+锂电芯 -电池芯"],
        ["merge", "SEG_FC", "SEG_FC", "SEG_H2", None],
    ]


# TC-NLB-002
def test_tc_nlb_002_checks(tmp_path: Path) -> None:
    builder = NodeLineageBuilder(build_folder(tmp_path))
    with pytest.raises(ConfigError, match="successor"):
        builder.build_lineage([build_set([{"op": "retire", "id": "SEG_FC", "successor": "X"}])])
    loop = [
        build_set([{"op": "retire", "id": "SEG_FC", "successor": "SEG_H2"}], "v1"),
        build_set([{"op": "upsert", "node": {"id": "SEG_FC", "type": "segment", "name": "燃料"}},
                   {"op": "retire", "id": "SEG_H2", "successor": "SEG_FC"}], "v2"),
    ]  # fmt: skip
    with pytest.raises(ConfigError, match="loop"):
        builder.build_lineage(loop)
    empty = builder.build_lineage([])
    assert empty.empty and list(empty.columns) == LINEAGE_COLUMNS
