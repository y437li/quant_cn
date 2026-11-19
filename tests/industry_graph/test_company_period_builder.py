from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.industry_graph.company_period_builder import LEAF_COLUMNS, CompanyPeriodBuilder
from quant_cn.lake.label_store import LabelStore
from quant_cn.lake.parquet_writer import ParquetWriter


def build_labels(root: Path) -> LabelStore:
    labels = LabelStore(ParquetWriter(root), root, DateCodec())
    labels.write("business_modes", pd.DataFrame([
        {"ts_code": "603906.SH", "doc_key": "annual:2", "doc_type": "annual", "period": "20251231",
         "known_on": "20260420", "payload": json.dumps({"archetype": "x"})},
        {"ts_code": "603906.SH", "doc_key": "annual:1", "doc_type": "annual", "period": "20241231",
         "known_on": "20250420", "payload": "{bad"},
    ]))  # fmt: skip
    labels.write("deals", pd.DataFrame([
        {"ts_code": "600000.SH", "doc_key": "inv:1", "doc_type": "investment",
         "period": "20250101", "known_on": "20250101",
         "payload": json.dumps({"items": [{}, {}]})},
    ]))  # fmt: skip
    return labels


# TC-CPB-001
def test_tc_cpb_001_rows(tmp_path: Path) -> None:
    leaf = CompanyPeriodBuilder(build_labels(tmp_path)).build_leaf()
    assert list(leaf.columns) == LEAF_COLUMNS
    got = leaf[["ts_code", "period", "label_set", "n_items"]].astype(object).values.tolist()
    assert got == [
        ["600000.SH", "20250101", "deals", 2],
        ["603906.SH", "20241231", "business_modes", pd.NA],
        ["603906.SH", "20251231", "business_modes", pd.NA],
    ]


# TC-CPB-002
def test_tc_cpb_002_sets_and_empty(tmp_path: Path) -> None:
    builder = CompanyPeriodBuilder(build_labels(tmp_path))
    assert set(builder.build_leaf(["deals"])["label_set"]) == {"deals"}
    empty = CompanyPeriodBuilder(
        LabelStore(ParquetWriter(tmp_path / "e"), tmp_path / "e", DateCodec())
    )
    assert list(empty.build_leaf().columns) == LEAF_COLUMNS and empty.build_leaf().empty
