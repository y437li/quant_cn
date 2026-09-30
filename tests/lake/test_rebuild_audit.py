from __future__ import annotations

import json

from quant_cn.core.config import Config
from quant_cn.lake.rebuild_audit import RebuildAudit
from tests.support import MiniLake, Sample


# TC-RA-001
def test_tc_ra_001_orphans(lake: MiniLake) -> None:
    path = RebuildAudit(lake.lake_root, lake.clock).record_orphans({"daily": ["20260827"]})
    record = json.loads(path.read_text())
    assert record["removed"] == {"daily": ["20260827"]} and "checked_at" in record


# TC-RA-002
def test_tc_ra_002_rewrites(lake: MiniLake, config: Config) -> None:
    spec = config.get_dataset("daily")
    lake.writer.write_raw(spec, "20260828", Sample.build_bars("20260828"))
    path = lake.writer.write_raw(spec, "20260828", Sample.build_bars("20260828", ("000001.SZ",)))
    assert path is not None
    rewrites = RebuildAudit(lake.lake_root, lake.clock).record_rewrites()
    assert rewrites == [
        {"dataset": "daily", "file": path.name, "previous_rows": 2, "current_rows": 1}
    ]
    assert not path.with_name(path.name + ".prev").exists()
    manifest = json.loads((lake.lake_root / "meta" / "manifest" / "raw_rewrites.json").read_text())
    assert manifest["rewrites"] == rewrites
