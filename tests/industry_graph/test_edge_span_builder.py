from __future__ import annotations

import json

import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import SchemaError
from quant_cn.industry_graph.edge_span_builder import SPAN_COLUMNS, EdgeSpanBuilder

COLS = ["src", "dst", "relation", "stage", "period", "known_on", "share", "amount",
        "label_set", "doc_key"]  # fmt: skip


def build_edges(*rows: tuple[object, ...]) -> pd.DataFrame:
    return pd.DataFrame(list(rows), columns=COLS)


# TC-ESB-001
def test_tc_esb_001_one_sales_span() -> None:
    frame = build_edges(
        ("a:1", "a:2", "customer", "contact", "20231231", "20240301", None, None, "ir", "d1"),
        ("a:1", "a:2", "supplier", "sample", "20231231", "20240601", None, None, "inq", "d2"),
        ("a:1", "a:2", "customer", "contact", "20241231", "20240701", None, None, "ir", "d3"),
        ("a:1", "a:2", "customer", "volume", "20241231", "20250101", None, None, "ir", "d3"),
    )
    span = EdgeSpanBuilder(DateCodec()).build_spans(frame)
    assert list(span.columns) == SPAN_COLUMNS and len(span) == 1
    row = span.iloc[0]
    assert row["kind"] == "sales" and row["stage_path"] == (
        "contact@20240301 > sample@20240601 > volume@20250101"
    )
    assert (row["n_obs"], row["n_docs"], row["sources"]) == (4, 3, "inq,ir")
    assert (row["first_seen"], row["last_seen"], row["status"]) == (
        "20240301",
        "20250101",
        "active",
    )


# TC-ESB-002
def test_tc_esb_002_status() -> None:
    frame = build_edges(
        ("a:1", "x:华为", "partner", "volume", None, "20240101", None, None, "ir", "d1"),
        ("a:1", "x:华为", "partner", "denied", None, "20240301", None, None, "ir", "d2"),
        ("a:1", "x:华为", "partner", "denied", None, "20240401", None, None, "ir", "d6"),
        ("a:1", "x:a", "customer", "volume", None, "20240101", None, None, "ir", "d3"),
        ("a:1", "x:b", "customer", "volume", None, "20260101", None, None, "ir", "d4"),
        ("a:1", "x:c", "invests_in", "terminated", None, "20260101", None, None, "deals", "d5"),
    )
    span = EdgeSpanBuilder(DateCodec()).build_spans(frame).set_index("dst")
    assert span.loc["x:华为", "stage_path"] == "volume@20240101 > denied@20240301"
    assert span["status"].to_dict() == {
        "x:a": "silent",
        "x:b": "active",
        "x:c": "ended",
        "x:华为": "denied",
    }


# TC-ESB-003
def test_tc_esb_003_as_of_and_shares() -> None:
    frame = build_edges(
        ("a:1", "a:2", "customer", "volume", "20241231", "20250420", 10.0, 5.0, "top5", "d1"),
        ("a:1", "a:2", "customer", "volume", "20241231", "20250501", 12.0, None, "inq", "d2"),
        ("a:1", "a:2", "customer", "volume", "20251231", "20260420", 20.0, None, "top5", "d3"),
    )
    builder = EdgeSpanBuilder(DateCodec())
    early = builder.build_spans(frame, as_of="20250430").iloc[0]
    assert early["last_seen"] == "20250420" and early["n_obs"] == 1
    late = builder.build_spans(frame).iloc[0]
    assert json.loads(late["shares"]) == {"20241231": 12.0, "20251231": 20.0}
    based = frame.assign(share_base=["营业收入", "境外收入", None])
    assert json.loads(builder.build_spans(based).iloc[0]["shares"]) == {
        "20241231 境外收入": 12.0,
        "20241231 营业收入": 10.0,
        "20251231": 20.0,
    }
    assert json.loads(late["amounts"]) == {"20241231": 5.0}
    assert list(builder.build_spans(frame, as_of="20200101").columns) == SPAN_COLUMNS
    with pytest.raises(SchemaError):
        builder.build_spans(frame, as_of="2025-01-01")
