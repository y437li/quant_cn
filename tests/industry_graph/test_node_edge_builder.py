from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import SchemaError
from quant_cn.industry_graph.node_edge_builder import NODE_EDGE_COLUMNS, NodeEdgeBuilder
from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy

TAXONOMY = """
sector: {sw_l1: "630000", name: 电力设备}
nodes:
  - {id: SEG_LI, type: segment, name: 锂矿}
  - {id: SEG_CELL, type: segment, name: 电池}
  - {id: SEG_CAR, type: segment, name: 整车}
  - {id: SEG_PART, type: segment, name: 零部件}
  - {id: PROD_LI, type: product, name: 碳酸锂, segment: SEG_LI}
  - {id: PROD_CELL, type: product, name: 电芯, segment: SEG_CELL}
  - {id: PROD_EV, type: product, name: 电动车, segment: SEG_CAR}
  - {id: PROD_SEAT, type: product, name: 座椅, segment: SEG_PART}
  - {id: MAT_CO, type: material, name: 钴}
edges:
  - [PROD_CELL, component_of, PROD_EV]
  - [PROD_CELL, uses_material, PROD_LI]
  - [PROD_CELL, uses_material, MAT_CO]
  - [PROD_EV, used_in, PROD_EV]
  - [PROD_SEAT, component_of, PROD_EV]
"""
EDGE_COLS = ["src", "dst", "relation", "period", "known_on"]
MEMBER_COLS = ["ts_code", "period", "known_on", "segment", "weight"]


def build(tmp_path: Path) -> NodeEdgeBuilder:
    (tmp_path / "630000_power.yaml").write_text(TAXONOMY, encoding="utf-8")
    return NodeEdgeBuilder(ProductTaxonomy(tmp_path), DateCodec())


def build_frame(rows: list[list[Any]], cols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=cols).astype({c: "string" for c in cols if c != "weight"})


MEMBERS = build_frame([
    ["300750.SZ", "20241231", "20250315", "SEG_CELL", 0.8],
    ["300750.SZ", "20241231", "20250315", "SEG_LI", 0.2],
    ["300750.SZ", "20241231", "20250315", None, 0.1],
    ["002594.SZ", "20241231", "20250327", "SEG_CAR", 1.0],
    ["002594.SZ", "20240331", "20240429", "SEG_CELL", 1.0],
], MEMBER_COLS)  # fmt: skip


def find_row(out: pd.DataFrame, src: str, dst: str, kind: str = "sales") -> dict[str, Any]:
    rows = out[(out["src_node"] == src) & (out["dst_node"] == dst) & (out["kind"] == kind)]
    assert len(rows) == 1, rows
    return dict(rows.iloc[0])


# TC-NEB-001
def test_tc_neb_001_evidenced(tmp_path: Path) -> None:
    edges = build_frame([
        ["a:300750.SZ", "a:002594.SZ", "customer", "20241231", "20250315"],
        ["a:300750.SZ", "a:002594.SZ", "supplier", "20241231", "20250327"],
        ["a:002594.SZ", "a:300750.SZ", "holds", "20241231", "20250327"],
        ["a:300750.SZ", "a:002594.SZ", "partner", "20241231", "20250315"],
        ["a:300750.SZ", "x:TSLA", "customer", "20241231", "20250315"],
    ], EDGE_COLS)  # fmt: skip
    out = build(tmp_path).build_node_edges(edges, MEMBERS)
    assert list(out.columns) == NODE_EDGE_COLUMNS
    assert set(out["kind"]) == {"sales", "invests"}
    cell_car = find_row(out, "SEG_CELL", "SEG_CAR")
    assert cell_car["weight"] == pytest.approx(0.8)
    assert (cell_car["n_pairs"], cell_car["n_obs"], cell_car["period"]) == (1, 2, "20241231")
    assert (cell_car["known_on"], cell_car["last_known_on"]) == ("20250315", "20250327")
    assert (cell_car["src_companies"], cell_car["dst_companies"]) == ("300750.SZ", "002594.SZ")
    assert cell_car["source"] == "both" and cell_car["prior_relations"] == "component_of"
    li_car = find_row(out, "SEG_LI", "SEG_CAR")
    assert li_car["weight"] == pytest.approx(0.2) and li_car["source"] == "evidenced"
    invest = find_row(out, "SEG_CAR", "SEG_CELL", "invests")
    assert invest["weight"] == pytest.approx(0.8) and invest["source"] == "evidenced"
    assert set(out["taxonomy_version"]) == {"v0"}


# TC-NEB-002
def test_tc_neb_002_member_period(tmp_path: Path) -> None:
    members = pd.concat([MEMBERS, build_frame([
        ["002594.SZ", "20250630", "20250829", "SEG_PART", 1.0],
    ], MEMBER_COLS)], ignore_index=True)  # fmt: skip
    edges = build_frame([
        ["a:300750.SZ", "a:002594.SZ", "customer", "20250630", "20250829"],  # 2025: interim
        ["a:300750.SZ", "a:002594.SZ", "customer", "20261231", "20260420"],  # late -> 2026
        ["a:300750.SZ", "a:002594.SZ", "customer", "20231231", "20240420"],  # earliest
    ], EDGE_COLS)  # fmt: skip
    out = build(tmp_path).build_node_edges(edges, members)
    evidenced = out[out["n_obs"] > 0]
    got = sorted(zip(evidenced["period"], evidenced["src_node"], evidenced["dst_node"],
                     strict=True))  # fmt: skip
    assert got == [
        ("20231231", "SEG_CELL", "SEG_CAR"),  # no earlier period: earliest later (FY2024)
        ("20231231", "SEG_LI", "SEG_CAR"),
        ("20251231", "SEG_CELL", "SEG_PART"),
        ("20251231", "SEG_LI", "SEG_PART"),
        ("20261231", "SEG_CELL", "SEG_PART"),
        ("20261231", "SEG_LI", "SEG_PART"),
    ]


# TC-NEB-003
def test_tc_neb_003_prior(tmp_path: Path) -> None:
    out = build(tmp_path).build_node_edges(build_frame([], EDGE_COLS), MEMBERS)
    prior = out[["period", "src_node", "dst_node", "source", "prior_relations", "weight"]]
    assert prior.astype(object).values.tolist() == [
        ["20241231", "SEG_CELL", "SEG_CAR", "prior", "component_of", 0.0],
        ["20241231", "SEG_LI", "SEG_CELL", "prior", "uses_material", 0.0],
        ["20241231", "SEG_PART", "SEG_CAR", "prior", "component_of", 0.0],
    ]
    assert out["known_on"].isna().all()


# TC-NEB-004
def test_tc_neb_004_as_of_and_empty(tmp_path: Path) -> None:
    builder = build(tmp_path)
    edges = build_frame([
        ["a:300750.SZ", "a:002594.SZ", "customer", "20241231", "20250315"],
        ["a:300750.SZ", "a:002594.SZ", "supplier", "20241231", "20250327"],
    ], EDGE_COLS)  # fmt: skip
    out = builder.build_node_edges(edges, MEMBERS, as_of="20250320")
    # 002594's FY2024 members are not known yet; its Q1 2024 row is not annual / interim
    assert (out["n_obs"] == 0).all()
    later = builder.build_node_edges(edges, MEMBERS, as_of="20250331")
    assert find_row(later, "SEG_CELL", "SEG_CAR")["n_obs"] == 2
    with pytest.raises(SchemaError):
        builder.build_node_edges(edges, MEMBERS, as_of="2025-03-31")
    empty = builder.build_node_edges(build_frame([], EDGE_COLS), build_frame([], MEMBER_COLS))
    assert empty.empty and list(empty.columns) == NODE_EDGE_COLUMNS
