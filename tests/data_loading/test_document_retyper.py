from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import ConfigError
from quant_cn.data_loading.document_manifest_writer import (
    MANIFEST_COLUMNS,
    DocumentManifestWriter,
)
from quant_cn.data_loading.document_retyper import DocumentRetyper
from tests.support import FakeClock, MiniLake

PDF = b"%PDF-1.7 body"
TITLES = {
    "a": "2025年年度报告",
    "b": "关于2025年年度报告的问询函的回复公告",
    "c": "H股公告-2025年年度报告",
}


def build_rows(lake: MiniLake) -> list[dict[str, object]]:
    rows = []
    for key, title in TITLES.items():
        path = f"documents/cninfo/annual/2026/03/300750_{key}.pdf"
        (lake.lake_root / path).parent.mkdir(parents=True, exist_ok=True)
        (lake.lake_root / path).write_bytes(PDF)
        rows.append({"doc_id": f"cninfo:{key}", "source": "cninfo", "doc_type": "annual",
                     "code": "300750", "title": title, "publish_date": "20260310", "url": "u",
                     "local_path": path, "bytes": 3, "sha256": "x", "status": "ok", "message": "",
                     "downloaded_at": "20260310 10:00:00"})  # fmt: skip
    return rows


# TC-DMW-001
def test_tc_dmw_001_write_part(lake: MiniLake) -> None:
    writer = DocumentManifestWriter(lake.lake_root)
    assert writer.write_part([], "x") is None and not writer.has_parts()
    path = writer.write_part(build_rows(lake), "20260310-00000")
    assert path is not None and writer.has_parts()
    frame = pd.read_parquet(path)
    assert list(frame.columns) == MANIFEST_COLUMNS and frame["bytes"].dtype == "int64"


# TC-DRT-001
def test_tc_drt_001_retype(config: Config, lake: MiniLake, clock: FakeClock) -> None:
    writer = DocumentManifestWriter(lake.lake_root)
    writer.write_part(build_rows(lake), "old")
    retyper = DocumentRetyper(lake.lake_root, lake.query, config.documents, clock, writer)
    report = retyper.run("cninfo")
    assert (report.keys_total, report.fetched, report.empty) == (3, 1, 1)
    root = lake.lake_root / "documents/cninfo"
    assert (root / "inquiry_reply/2026/03/300750_b.pdf").exists()
    assert not (root / "annual/2026/03/300750_b.pdf").exists()
    assert (root / "annual/2026/03/300750_c.pdf").exists()
    latest = lake.query.sql(
        "SELECT doc_id, doc_type, status FROM read_parquet(?) QUALIFY row_number() OVER "
        "(PARTITION BY doc_id ORDER BY downloaded_at DESC) = 1 ORDER BY doc_id",
        [writer.get_glob()],
    )
    assert latest.values.tolist() == [
        ["cninfo:a", "annual", "ok"], ["cninfo:b", "inquiry_reply", "ok"],
        ["cninfo:c", "annual", "excluded"],
    ]  # fmt: skip
    assert retyper.run("cninfo").fetched == 0
    with pytest.raises(ConfigError):
        retyper.run("nope")
