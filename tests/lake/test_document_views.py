from __future__ import annotations

import pandas as pd

from quant_cn.lake.document_views import DocumentViews
from tests.support import MiniLake


# TC-DOV-001
def test_tc_dov_001_latest_attempt(lake: MiniLake) -> None:
    views = DocumentViews(lake.lake_root, lake.catalog.connection)
    views.refresh()
    assert not lake.query.has_view("meta.documents")
    folder = lake.lake_root / "meta" / "document_manifest"
    folder.mkdir(parents=True)
    stamps = ["20261107 10:00:00", "20261107 11:00:00", "20261107 10:00:00"]
    rows = {"doc_id": ["a", "a", "b"], "status": ["failed", "ok", "ok"],
            "downloaded_at": stamps}  # fmt: skip
    pd.DataFrame(rows).to_parquet(folder / "part-1.parquet")
    views.refresh()
    out = lake.query.sql("SELECT doc_id, status FROM meta.documents ORDER BY doc_id")
    assert out.values.tolist() == [["a", "ok"], ["b", "ok"]]
    assert len(lake.query.sql("SELECT * FROM meta.document_attempts")) == 3
