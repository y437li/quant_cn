from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quant_cn.core.exceptions import SchemaError
from quant_cn.lake.graph_store import GraphStore
from quant_cn.lake.parquet_writer import ParquetWriter


def build_store(root: Path) -> GraphStore:
    return GraphStore(ParquetWriter(root), root)


# TC-GS-001
def test_tc_gs_001_write_read_replace(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    frame = pd.DataFrame({"src": ["a:2", "a:1"], "dst": ["x:b", "x:a"], "n": [2, 1]})
    store.write("edge_span", frame)
    pd.testing.assert_frame_equal(store.read("edge_span"), frame)
    store.write("edge_span", frame.iloc[:1])
    assert len(store.read("edge_span")) == 1


# TC-GS-002
def test_tc_gs_002_missing_and_columns(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    assert store.read("company_edge").empty
    store.write("company_edge", pd.DataFrame({"src": ["a:1"], "dst": ["x:a"]}))
    assert list(store.read("company_edge", columns=["dst"]).columns) == ["dst"]


# TC-GS-003
def test_tc_gs_003_names(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    with pytest.raises(SchemaError):
        store.write("nodes", pd.DataFrame())
    with pytest.raises(SchemaError):
        store.read("../x")
    store.write("entity_map", pd.DataFrame({"name": ["华为"]}))
    assert store.list_tables() == ["entity_map"]
