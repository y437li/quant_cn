from __future__ import annotations

from pathlib import Path

from quant_cn.core.config import Config
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from tests.support import Build, MiniLake


# TC-FL-001
def test_tc_fl_001_round_trip(lake: MiniLake) -> None:
    lake.fetch_log.mark_done("daily", "20260828", 5, Path("/x"))
    assert lake.fetch_log.is_done("daily", "20260828")
    assert not lake.fetch_log.is_done("daily", "20260827")


# TC-FL-002
def test_tc_fl_002_mirror_restore(lake: MiniLake, config: Config) -> None:
    lake.fetch_log.mark_done("daily", "20260828", 5, None)
    lake.fetch_log.save()
    lake.catalog.close()
    lake.catalog.catalog_path.unlink()
    catalog = LakeCatalog(config.lake.root, config.datasets)
    restored = FetchLog(catalog)
    assert restored.rebuild_from_mirror() == 1
    assert restored.is_done("daily", "20260828")
    catalog.close()


# TC-FL-003
def test_tc_fl_003_pending_order(lake: MiniLake) -> None:
    lake.fetch_log.mark_done("daily", "b", 1, None)
    assert lake.fetch_log.list_pending("daily", ["c", "b", "a"]) == ["c", "a"]


# TC-FL-004
def test_tc_fl_004_restore_adds_raw_files(lake: MiniLake, config: Config) -> None:
    lake.writer.write_raw(config.get_dataset("daily"), "20260828", Build.bars("20260828"))
    assert lake.fetch_log.rebuild_from_mirror() == 1
    assert lake.fetch_log.is_done("daily", "20260828")


# TC-FL-005
def test_tc_fl_005_upsert(lake: MiniLake) -> None:
    lake.fetch_log.mark_done("daily", "k", 1, None)
    lake.fetch_log.mark_done("daily", "k", 7, None)
    rows = lake.query.sql("SELECT n_rows FROM meta.fetch_log WHERE key = 'k'")
    assert rows["n_rows"].tolist() == [7]
