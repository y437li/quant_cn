from __future__ import annotations

import duckdb
import pytest

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import ZONES, LakeCatalog
from tests.support import MiniLake, Sample


def write_trade_cal(lake: MiniLake, config: Config) -> None:
    spec = config.get_dataset("trade_cal")
    lake.writer.write_raw(spec, "all", Sample.build_trade_cal(["20260827", "20260828"]))


# TC-LC-001
def test_tc_lc_001_views_return_rows(lake: MiniLake, config: Config) -> None:
    write_trade_cal(lake, config)
    spec = config.get_dataset("trade_cal")
    lake.writer.write_curated(
        spec, None, spec.build_schema().normalize(Sample.build_trade_cal(["20260828"]), strict=True)
    )
    lake.catalog.refresh_views()
    assert lake.query.sql("SELECT count(*) n FROM raw.trade_cal")["n"].iloc[0] == 2
    assert lake.query.sql("SELECT count(*) n FROM curated.trade_cal")["n"].iloc[0] == 1


# TC-LC-002
def test_tc_lc_002_no_files_no_view(lake: MiniLake, config: Config) -> None:
    lake.catalog.refresh_views()
    lake.catalog.refresh_views()
    assert not lake.query.has_view("raw.daily")
    assert lake.query.sql("SELECT count(*) n FROM meta.dataset_meta")["n"].iloc[0] == len(
        config.datasets
    )


# TC-LC-003
def test_tc_lc_003_rebuild(lake: MiniLake, config: Config) -> None:
    write_trade_cal(lake, config)
    lake.catalog.refresh_views()
    lake.catalog.close()
    lake.catalog.catalog_path.unlink()
    fresh = LakeCatalog(config.lake.root, config.datasets)
    fresh.rebuild()
    assert fresh.connection.execute("SELECT count(*) FROM raw.trade_cal").fetchone() == (2,)
    assert fresh.connection.execute("SELECT count(*) FROM meta.dataset_meta").fetchone() == (
        len(config.datasets),
    )
    fresh.close()


# TC-LC-004
def test_tc_lc_004_indexes(lake: MiniLake, config: Config) -> None:
    write_trade_cal(lake, config)
    written = lake.catalog.write_indexes()
    assert {p.parent.name for p in written} == {lake.lake_root.name, *ZONES}
    assert "trade_cal" in (lake.lake_root / "raw" / "INDEX.md").read_text()


# TC-LC-005
def test_tc_lc_005_read_only(lake: MiniLake, config: Config) -> None:
    write_trade_cal(lake, config)
    lake.catalog.refresh_views()
    lake.catalog.close()
    reader = LakeCatalog(config.lake.root, config.datasets, read_only=True)
    assert reader.connection.execute("SELECT count(*) FROM raw.trade_cal").fetchone() == (2,)
    with pytest.raises(duckdb.Error):
        reader.connection.execute("CREATE TABLE meta.x (a INT)")
    reader.close()
