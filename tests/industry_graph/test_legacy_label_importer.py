from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.label_source import LabelSource
from quant_cn.core.ticker_normalizer import TickerNormalizer
from quant_cn.industry_graph.legacy_label_importer import LegacyLabelImporter
from quant_cn.lake.label_store import LabelStore
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter

DATES = {"111": "20260420", "AP9": "20261107"}


@pytest.fixture
def importer(tmp_path: Path) -> Iterator[LegacyLabelImporter]:
    store = LabelStore(ParquetWriter(tmp_path), tmp_path, DateCodec())
    catalog = LakeCatalog(tmp_path, {})
    yield LegacyLabelImporter(store, LakeQuery(catalog), tmp_path, TickerNormalizer())
    catalog.close()


# TC-LLI-001
def test_tc_lli_001_keyed(importer: LegacyLabelImporter) -> None:
    src = LabelSource(label_set="notes", path="n.jsonl", key_field="key", taxonomy_version="v0")
    rows = importer.build_rows(
        src, [{"key": "q1:111", "period": "2026Q1", "code": "600176", "items": []}], DATES, {}
    )
    r = rows.iloc[0]
    assert (r.ts_code, r.doc_key, r.doc_type, r.period) == ("600176.SH", "q1:111", "q1", "20260331")
    assert (r.known_on, r.taxonomy_version) == ("20260420", "v0")
    parse = LabelSource(label_set="report_parse", path="p.parquet", period="20251231",
                        doc_type="annual", key_field="ann_id", key_prefix="annual")  # fmt: skip
    p = importer.build_rows(parse, [{"code": "920819", "ann_id": "111"}], DATES, {}).iloc[0]
    assert (p.ts_code, p.doc_key, p.doc_type, p.known_on) == (
        "920819.BJ", "annual:111", "annual", "20260420"
    )  # fmt: skip


# TC-LLI-002
def test_tc_lli_002_date_field(importer: LegacyLabelImporter) -> None:
    src = LabelSource(label_set="broker_valuations", path="v.jsonl", key_field="doc_id",
                      date_field="date", doc_type="stock_report")  # fmt: skip
    r = importer.build_rows(
        src, [{"doc_id": "em_stock:AP9", "code": "601658", "date": "20261106"}], DATES, {}
    ).iloc[0]
    assert (r.period, r.known_on, r.doc_type) == ("20261106", "20261106", "stock_report")
    failed = importer.build_rows(src, [{"doc_id": "em_stock:AP9", "code": "601658"}], DATES, {})
    assert (failed.iloc[0].period, failed.iloc[0].known_on) == ("20261107", "20261107")


# TC-LLI-003
def test_tc_lli_003_anchor(importer: LegacyLabelImporter) -> None:
    src = LabelSource(label_set="moat_claims", path="m.jsonl", period="20251231",
                      anchor_set="report_parse")  # fmt: skip
    anchors = {"report_parse": {("600176.SH", "20251231"): ("annual:111", "annual", "20260420")}}
    rows = importer.build_rows(src, [{"code": "600176"}, {"code": "000001"}], DATES, anchors)
    assert list(rows["doc_key"]) == ["annual:111", "moat_claims:20251231"]
    assert list(rows["known_on"].fillna("-")) == ["20260420", "-"]
    assert list(rows["doc_type"].fillna("-")) == ["annual", "-"]


# TC-LLI-004
def test_tc_lli_004_run(
    importer: LegacyLabelImporter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pd.DataFrame({"code": ["600176", "bad"], "ann_id": ["111", "112"]}).to_parquet(
        tmp_path / "p.parquet"
    )
    record = {"code": "600176", "claims": [{"type": "cost"}], "summary": "规模"}
    (tmp_path / "m.jsonl").write_text(json.dumps(record, ensure_ascii=False) + "\n")
    sources = [
        LabelSource(label_set="report_parse", path="p.parquet", period="20251231",
                    key_field="ann_id", key_prefix="annual"),
        LabelSource(label_set="moat_claims", path="m.jsonl", period="20251231",
                    anchor_set="report_parse"),
    ]  # fmt: skip
    monkeypatch.setattr(importer, "read_dates", lambda: DATES)
    assert importer.run(sources) == {"report_parse": 1, "moat_claims": 1}
    store = LabelStore(ParquetWriter(tmp_path), tmp_path, DateCodec())
    moat = store.read("moat_claims").iloc[0]
    assert moat.doc_key == "annual:111" and moat.known_on == "20260420"
    assert json.loads(moat.payload) == record


# TC-LLI-005
def test_tc_lli_005_early_document(importer: LegacyLabelImporter) -> None:
    src = LabelSource(label_set="notes", path="n.jsonl", key_field="key")
    record = {"key": "q3:111", "period": "2026Q3", "code": "600176"}
    assert importer.build_rows(src, [record], {"111": "20260112"}, {}).empty
    assert len(importer.build_rows(src, [record], {"111": "20261025"}, {})) == 1


# TC-LLI-006
def test_tc_lli_006_dates_without_lists(importer: LegacyLabelImporter) -> None:
    assert importer.read_dates() == {}


# TC-LLI-007
def test_tc_lli_007_exclude_and_replace(
    importer: LegacyLabelImporter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines = [{"key": f"q1:{i}", "period": "2026Q1", "code": "600176"} for i in ("111", "112")]
    path = tmp_path / "n.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in lines))
    (tmp_path / "x.csv").write_text("key\nq1:112\n")
    src = LabelSource(label_set="notes", path="n.jsonl", key_field="key", exclude_file="x.csv")
    assert [r["key"] for r in importer.read_records(src)] == ["q1:111"]
    monkeypatch.setattr(importer, "read_dates", lambda: DATES)
    plain = LabelSource(label_set="notes", path="n.jsonl", key_field="key")
    assert importer.run([plain]) == {"notes": 2}
    path.write_text(json.dumps(lines[1]) + "\n")
    importer.run([plain])
    store = LabelStore(ParquetWriter(tmp_path), tmp_path, DateCodec())
    assert list(store.read("notes")["doc_key"]) == ["q1:112"]
