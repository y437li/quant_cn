from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.industry_graph.company_period_builder import CompanyPeriodBuilder
from quant_cn.industry_graph.counterparty_edge_reader import CounterpartyEdgeReader
from quant_cn.industry_graph.edge_span_builder import SPAN_COLUMNS, EdgeSpanBuilder
from quant_cn.industry_graph.graph_builder import GraphBuilder
from quant_cn.lake.graph_store import GraphStore
from quant_cn.lake.label_store import LabelStore
from quant_cn.lake.parquet_writer import ParquetWriter

FULL = [("300750.SZ", "宁德时代新能源科技股份有限公司")]
SHORT = [("300750.SZ", "宁德时代"), ("603906.SH", "龙蟠科技")]


def build_lake(root: Path) -> tuple[LabelStore, GraphStore]:
    writer = ParquetWriter(root)
    labels = LabelStore(writer, root, DateCodec())
    graph = GraphStore(writer, root)
    ev = {"quote": "q", "page": 1}
    items = [
        {"name": "宁德时代", "role": "customer", "stage": "volume", "evidence": ev},
        {"name": "上汽乘用车", "role": "customer", "evidence": ev},
        {"name": "某头部客户", "role": "customer", "evidence": ev},
        {"name": "电气类厂商", "role": "customer", "evidence": ev},
    ]
    row = {"ts_code": "603906.SH", "doc_key": "irm:1", "doc_type": "irm_qa",
           "period": "20250630", "known_on": "20250701",
           "payload": json.dumps({"items": items}, ensure_ascii=False)}  # fmt: skip
    rows = pd.DataFrame([row])
    labels.write("ir_counterparties", rows)
    emap = pd.DataFrame({
        "name": ["上汽乘用车", "电气类厂商"],
        "entity_id": ["a:600104.SH", "x:电气类厂商"],
        "canonical": ["上汽集团", "电气类厂商"],
        "kind": ["company", "generic"],
        "is_member": [True, False],
    })  # fmt: skip
    graph.write("entity_map", emap)
    return labels, graph


def build_builder(labels: LabelStore, graph: GraphStore) -> GraphBuilder:
    readers = {"ir_counterparties": CounterpartyEdgeReader(), "deals": CounterpartyEdgeReader()}
    spans = EdgeSpanBuilder(DateCodec())
    return GraphBuilder(labels, graph, readers, spans, CompanyPeriodBuilder(labels))


# TC-GB-001
def test_tc_gb_001_build(tmp_path: Path) -> None:
    labels, graph = build_lake(tmp_path)
    counts = build_builder(labels, graph).build(FULL, SHORT, [])
    edges = graph.read("company_edge")
    assert counts == {"company_edge": 2, "edge_span": 2, "company_period": 1}
    pairs = zip(edges["dst"], edges["is_group_member"], strict=True)
    got = dict(zip(edges["counterparty"], pairs, strict=True))
    assert got == {"宁德时代": ("a:300750.SZ", False), "上汽乘用车": ("a:600104.SH", True)}
    assert set(graph.read("edge_span")["kind"]) == {"sales"}


# TC-GB-002
def test_tc_gb_002_rebuild_identical(tmp_path: Path) -> None:
    labels, graph = build_lake(tmp_path)
    builder = build_builder(labels, graph)
    builder.build(FULL, SHORT, [])
    first = (tmp_path / "derived/graph/company_edge.parquet").read_bytes()
    span = (tmp_path / "derived/graph/edge_span.parquet").read_bytes()
    builder.build(FULL, SHORT, [])
    assert (tmp_path / "derived/graph/company_edge.parquet").read_bytes() == first
    assert (tmp_path / "derived/graph/edge_span.parquet").read_bytes() == span


# TC-GB-003
def test_tc_gb_003_empty(tmp_path: Path) -> None:
    writer = ParquetWriter(tmp_path)
    labels, graph = LabelStore(writer, tmp_path, DateCodec()), GraphStore(writer, tmp_path)
    counts = build_builder(labels, graph).build(FULL, SHORT, [])
    assert counts == {"company_edge": 0, "edge_span": 0, "company_period": 0}
    assert list(graph.read("edge_span").columns) == SPAN_COLUMNS


# TC-GB-004
def test_tc_gb_004_company_period(tmp_path: Path) -> None:
    labels, graph = build_lake(tmp_path)
    build_builder(labels, graph).build(FULL, SHORT, [])
    leaf = graph.read("company_period")
    assert leaf[["ts_code", "label_set", "n_items"]].values.tolist() == [
        ["603906.SH", "ir_counterparties", 4]
    ]
