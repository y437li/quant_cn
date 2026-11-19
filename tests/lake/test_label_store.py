from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import SchemaError
from quant_cn.lake.label_store import COLUMNS, LabelStore
from quant_cn.lake.parquet_writer import ParquetWriter


@pytest.fixture
def store(tmp_path: Path) -> LabelStore:
    return LabelStore(ParquetWriter(tmp_path), tmp_path, DateCodec())


def _build_rows(rows: list[tuple[str, str, str, str | None, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ts_code": c, "doc_key": k, "period": p, "known_on": d, "payload": x}
            for c, k, p, d, x in rows
        ]
    )


# TC-LBS-001
def test_tc_lbs_001_write_and_read(store: LabelStore, tmp_path: Path) -> None:
    paths = store.write(
        "applications",
        _build_rows(
            [
                ("600176.SH", "annual:2", "20251231", "20260420", "b"),
                ("000001.SZ", "annual:1", "20241231", "20250320", "a"),
            ]
        ),
    )
    assert sorted(p.parent.name for p in paths) == ["year=2024", "year=2025"]
    assert (tmp_path / "derived/labels/applications/year=2025/part-0.parquet").exists()
    out = store.read("applications")
    assert list(out.columns) == COLUMNS and list(out["payload"]) == ["a", "b"]
    assert str(out["payload"].dtype) == "string" and store.list_sets() == ["applications"]


# TC-LBS-002
def test_tc_lbs_002_upsert(store: LabelStore) -> None:
    first = [("600176.SH", "annual:2", "20251231", None, "old"),
             ("000001.SZ", "annual:1", "20251231", None, "keep")]  # fmt: skip
    store.write("moat", _build_rows(first))
    store.write("moat", _build_rows([("600176.SH", "annual:2", "20251231", None, "new")]))
    out = store.read("moat").set_index("ts_code")["payload"]
    assert out.to_dict() == {"000001.SZ": "keep", "600176.SH": "new"}


# TC-LBS-003
def test_tc_lbs_003_as_of_and_codes(store: LabelStore) -> None:
    store.write(
        "notes",
        _build_rows(
            [
                ("600176.SH", "q3:1", "20260930", "20261025", "late"),
                ("600176.SH", "q1:1", "20260331", "20260428", "early"),
                ("000001.SZ", "q1:2", "20260331", None, "undated"),
            ]
        ),
    )
    assert list(store.read("notes", as_of="20260601")["payload"]) == ["early"]
    assert list(store.read("notes", codes=["000001.SZ"])["payload"]) == ["undated"]
    empty = store.read("unknown_set")
    assert empty.empty and list(empty.columns) == COLUMNS


# TC-LBS-004
def test_tc_lbs_004_validation(store: LabelStore) -> None:
    good = _build_rows([("600176.SH", "annual:2", "20251231", None, "x")])
    with pytest.raises(SchemaError):
        store.write("Bad-Name", good)
    with pytest.raises(SchemaError):
        store.write("s", good.drop(columns=["payload"]))
    with pytest.raises(SchemaError):
        store.write("s", good.assign(doc_key=None))
    with pytest.raises(SchemaError):
        store.write("s", good.assign(period="2025Q4"))
    twice = _build_rows([("600176.SH", "k", "20251231", None, "a"),
                        ("600176.SH", "k", "20251231", None, "b")])  # fmt: skip
    store.write("s", twice)
    assert list(store.read("s")["payload"]) == ["b"]


# TC-LBS-005
def test_tc_lbs_005_replace_source(store: LabelStore) -> None:
    first = _build_rows([("600176.SH", "annual:1", "20221231", None, "stale"),
                         ("600176.SH", "q1:1", "20230331", None, "other year")])  # fmt: skip
    first["source"] = "run_a.jsonl"
    other = _build_rows([("000001.SZ", "annual:9", "20221231", None, "other source")])
    other["source"] = "run_b.jsonl"
    store.write("labels_x", first)
    store.write("labels_x", other)
    again = _build_rows([("600176.SH", "annual:2", "20221231", None, "chosen now")])
    again["source"] = "run_a.jsonl"
    paths = store.write("labels_x", again, replace_source="run_a.jsonl")
    assert sorted(p.parent.name for p in paths) == ["year=2022", "year=2023"]
    out = store.read("labels_x")
    assert sorted(out["payload"]) == ["chosen now", "other source"]
