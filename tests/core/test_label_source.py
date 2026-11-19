from __future__ import annotations

from pathlib import Path

import pydantic
import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.label_source import LabelSource

REPO = Path(__file__).resolve().parents[2]


# TC-LSR-001
def test_tc_lsr_001_loads() -> None:
    jsonl = LabelSource(label_set="applications", path="meta/runs/a.jsonl", key_field="key")
    parquet = LabelSource(label_set="report_parse", path="meta/runs/p.parquet", period="20251231")
    assert not jsonl.is_parquet and parquet.is_parquet


# TC-LSR-002
@pytest.mark.parametrize(
    "kwargs",
    [
        {"label_set": "Apps", "path": "a.jsonl"},
        {"label_set": "apps", "path": "a.csv"},
        {"label_set": "apps", "path": "../a.jsonl"},
        {"label_set": "apps", "path": "a.jsonl", "extra": 1},
    ],
)
def test_tc_lsr_002_refused(kwargs: dict[str, object]) -> None:
    with pytest.raises(pydantic.ValidationError):
        LabelSource.model_validate(kwargs)


# TC-LSR-003
def test_tc_lsr_003_read_all(tmp_path: Path) -> None:
    sources = LabelSource.read_all(REPO / "config" / "label_sources.yaml")
    assert sources[0].label_set == "report_parse" and sources[0].is_parquet
    first = {s.label_set: i for i, s in reversed(list(enumerate(sources)))}
    assert all(first[s.anchor_set] < i for i, s in enumerate(sources) if s.anchor_set)
    assert LabelSource.read_all(tmp_path / "missing.yaml") == []
    bad = tmp_path / "bad.yaml"
    bad.write_text("sources:\n  - {label_set: Bad, path: a.jsonl}\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        LabelSource.read_all(bad)


# TC-LSR-004
def test_tc_lsr_004_exclude_file() -> None:
    ok = LabelSource(label_set="notes", path="n.jsonl", key_field="key", exclude_file="x.csv")
    assert ok.exclude_file == "x.csv"
    for kwargs in (
        {"label_set": "notes", "path": "n.jsonl", "key_field": "key", "exclude_file": "x.txt"},
        {"label_set": "notes", "path": "n.jsonl", "exclude_file": "x.csv"},
    ):
        with pytest.raises(pydantic.ValidationError):
            LabelSource.model_validate(kwargs)
