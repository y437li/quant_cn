from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import SchemaError
from quant_cn.industry_graph.edge_span_builder import EdgeSpanBuilder
from quant_cn.industry_graph.graph_query import TIMELINE_COLUMNS, GraphQuery
from quant_cn.lake.graph_store import GraphStore
from quant_cn.lake.parquet_writer import ParquetWriter

TS = "603906.SH"


def build_query(root: Path) -> GraphQuery:
    graph = GraphStore(ParquetWriter(root), root)
    graph.write("company_period", pd.DataFrame({
        "ts_code": [TS, TS, TS],
        "period": ["20241231", "20251231", "20250930"],
        "label_set": ["business_modes", "business_modes", "quarterly_notes"],
        "doc_key": ["annual:1", "annual:2", "q3:1"],
        "doc_type": ["annual", "annual", "q3"],
        "known_on": ["20250420", "20260420", "20251030"],
        "n_items": [None, None, 3],
    }))  # fmt: skip
    graph.write("company_edge", pd.DataFrame({
        "src": [f"a:{TS}", f"a:{TS}"], "dst": ["x:lg", "x:lg"],
        "relation": ["customer", "customer"], "ts_code": [TS, TS],
        "counterparty": ["LGES", "LGES"], "stage": ["contact", "volume"],
        "period": ["20250630", "20260630"], "known_on": ["20250701", "20260701"],
        "share": [None, None], "amount": [None, None], "label_set": ["ir", "ir"],
        "doc_key": ["irm:1", "irm:2"], "quote": ["q1", "q2"],
    }))  # fmt: skip
    return GraphQuery(graph, EdgeSpanBuilder(DateCodec()), DateCodec())


# TC-GQ-001
def test_tc_gq_001_find_leaf(tmp_path: Path) -> None:
    query = build_query(tmp_path)
    before = query.find_leaf(TS, "20260101")
    assert sorted(zip(before["label_set"], before["period"], strict=True)) == [
        ("business_modes", "20241231"),
        ("quarterly_notes", "20250930"),
    ]
    after = query.find_leaf(TS, "20260501")
    assert "20251231" in set(after["period"])


# TC-GQ-002
def test_tc_gq_002_list_spans(tmp_path: Path) -> None:
    query = build_query(tmp_path)
    assert query.list_spans(TS, "20251231").iloc[0]["last_stage"] == "contact"
    assert query.list_spans(TS, "20261231").iloc[0]["last_stage"] == "volume"


# TC-GQ-003
def test_tc_gq_003_timeline(tmp_path: Path) -> None:
    query = build_query(tmp_path)
    line = query.list_timeline(TS, "20250101", "20251231")
    assert list(line.columns) == TIMELINE_COLUMNS
    assert line[["known_on", "kind"]].values.tolist() == [
        ["20250420", "label"],
        ["20250701", "edge"],
        ["20251030", "label"],
    ]
    with pytest.raises(SchemaError):
        query.list_timeline(TS, "2025", "20251231")


def build_node_query(root: Path) -> GraphQuery:
    graph = GraphStore(ParquetWriter(root), root)
    graph.write("node_member", pd.DataFrame({
        "ts_code": ["300750.SZ", "300750.SZ", "300014.SZ", "300014.SZ", "300750.SZ"],
        "period": ["20251231", "20251231", "20251231", "20241231", "20250630"],
        "known_on": ["20260310", "20260310", "20260420", "20250420", "20250730"],
        "item": ["动力电池", "储能电池", "消费电池", "消费电池", "动力电池"],
        "segment": ["SEG_CELL", "SEG_CELL", "SEG_CELL", "SEG_CELL", "SEG_CELL"],
        "sales": [300.0, 60.0, 400.0, 350.0, 150.0],
        "weight": [0.7, 0.15, 0.8, 0.8, 0.7],
    }))  # fmt: skip
    graph.write("node_edge", pd.DataFrame({
        "period": ["20251231"] * 4 + ["20241231"],
        "src_node": ["SEG_EQUIP", "SEG_CATHODE", "SEG_CELL", "SEG_CELL", "SEG_CATHODE"],
        "dst_node": ["SEG_CELL", "SEG_CELL", "SEG_CAR", "SEG_MINE", "SEG_CELL"],
        "kind": ["sales", "sales", "sales", "invests", "sales"],
        "source": ["both", "prior", "evidenced", "evidenced", "both"],
        "weight": [3.0, 0.0, 5.0, 1.0, 2.0],
    }))  # fmt: skip
    graph.write("node_lineage", pd.DataFrame({
        "version": ["v1", "v2", "v2"], "kind": ["rename", "merge", "new"],
        "node_id": ["SEG_CELL", "SEG_FC", "SEG_SSB"],
        "from_node": ["SEG_CELL", "SEG_FC", None], "to_node": ["SEG_CELL", "SEG_CELL", "SEG_SSB"],
    }))  # fmt: skip
    return GraphQuery(graph, EdgeSpanBuilder(DateCodec()), DateCodec())


# TC-GQ-004
def test_tc_gq_004_node_members(tmp_path: Path) -> None:
    query = build_node_query(tmp_path)
    members = query.list_node_members("SEG_CELL", "20251231")
    assert list(members["ts_code"]) == ["300014.SZ", "300750.SZ"]
    catl = members.iloc[1]
    assert catl["sales"] == pytest.approx(360.0) and catl["items"] == "动力电池；储能电池"
    assert query.list_node_members("SEG_NONE", "20251231").empty


# TC-GQ-005
def test_tc_gq_005_node_neighbours(tmp_path: Path) -> None:
    query = build_node_query(tmp_path)
    out = query.list_node_neighbours("SEG_CELL", "20251231")
    got = list(zip(out["direction"], out["other_node"], out["source"], strict=True))
    assert got == [
        ("upstream", "SEG_EQUIP", "both"),
        ("upstream", "SEG_CATHODE", "prior"),
        ("downstream", "SEG_CAR", "evidenced"),
    ]
    invests = query.list_node_neighbours("SEG_CELL", "20251231", kind="invests")
    assert list(invests["other_node"]) == ["SEG_MINE"]
    with pytest.raises(SchemaError):
        query.list_node_neighbours("SEG_CELL", "2025")


# TC-GQ-006
def test_tc_gq_006_node_history_and_lineage(tmp_path: Path) -> None:
    query = build_node_query(tmp_path)
    history = query.list_node_history("SEG_CELL")
    assert history.astype(object).values.tolist() == [
        ["20241231", 1, 350.0, 1, 0, 0],
        ["20251231", 2, 760.0, 1, 1, 1],
    ]
    lineage = query.list_node_lineage("SEG_CELL")
    assert list(lineage["version"]) == ["v1", "v2"]
