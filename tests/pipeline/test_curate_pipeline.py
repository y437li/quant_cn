from __future__ import annotations

import json

import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.lake.run_log import RunLog
from quant_cn.pipeline.curate_pipeline import DIGEST_FILE, CuratePipeline
from quant_cn.pipeline.runner import LocalRunner
from tests.support import FakeClock, MiniLake, SampleLake

ROWS = [("20251231", "20260320", "1", 1.0), ("20251231", "20260410", "1", 2.0)]


def build_curate(config: Config, catalog: LakeCatalog) -> CuratePipeline:
    clock, query = FakeClock(), LakeQuery(catalog)
    return CuratePipeline(
        config,
        Compactor(catalog, query, ParquetWriter(config.lake.root), clock),
        DerivedViews(catalog, query, config.datasets),
        PitAligner(catalog, query, DateCodec()),
        query,
        catalog,
        LocalRunner(RunLog(catalog, clock), show_progress=False),
    )


@pytest.fixture
def seeded(lake: MiniLake, config: Config) -> MiniLake:
    SampleLake.write_calendar(lake, config.get_dataset("trade_cal"))
    SampleLake.write_income(lake, config.get_dataset("income_vip"), ROWS)
    return lake


def read_digests(lake: MiniLake) -> dict[str, str]:
    return json.loads((lake.lake_root / "meta" / "manifest" / DIGEST_FILE).read_text())


# TC-CP-001
def test_tc_cp_001_curate(seeded: MiniLake, config: Config) -> None:
    report = build_curate(config, seeded.catalog).run()
    assert [s.name for s in report.steps] == ["compact", "derive"]
    digests = read_digests(seeded)
    assert set(digests) == {"derived.fundamentals_long", "derived.fundamentals_states"}
    assert all(len(h) == 32 for h in digests.values())
    assert (seeded.lake_root / "curated" / "INDEX.md").exists()


# TC-CP-002
def test_tc_cp_002_rebuild_identical(seeded: MiniLake, config: Config) -> None:
    build_curate(config, seeded.catalog).run()
    first = read_digests(seeded)
    seeded.catalog.rebuild()
    FetchLog(seeded.catalog).rebuild_from_mirror()
    build_curate(config, seeded.catalog).run()
    assert read_digests(seeded) == first


# TC-CP-003
def test_tc_cp_003_unknown_dataset(lake: MiniLake, config: Config) -> None:
    with pytest.raises(ConfigError):
        build_curate(config, lake.catalog).run(["nope"])
