from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.dataset_spec import CuratedSpec, DatasetSpec, SweepSpec
from quant_cn.data_loading.snapshot_fetcher import SnapshotFetcher
from tests.support import FakeTushareClient, MiniLake, Sample


def build_spec() -> DatasetSpec:
    sweep = SweepSpec(kind="snapshot", values=["cn", "us"], param_name="country",
                      key_field="capture_date", extra_params={"charts": "free"})  # fmt: skip
    return Sample.build_spec(
        name="charts", endpoint="rss", sweep=sweep, primary_key=["capture_date", "country", "rank"],
        known_on="capture_date", fields=["capture_date", "country", "rank"],
        text_fields=["capture_date", "country"],
        curated=CuratedSpec(path="charts", partition_by="capture_date"),
    )  # fmt: skip


@pytest.fixture
def client() -> FakeTushareClient:
    fake = FakeTushareClient()
    fake.add("rss", "all", pd.DataFrame({"country": ["cn", "cn"], "rank": [1, 2]}))
    return fake


@pytest.fixture
def fetcher(lake: MiniLake, client: FakeTushareClient) -> SnapshotFetcher:
    return SnapshotFetcher(build_spec(), client, lake.writer, lake.fetch_log, lake.run_log,
                           lake.clock, values=["cn", "us"])  # fmt: skip


# TC-SNF-001
def test_tc_snf_001_today_keys(fetcher: SnapshotFetcher) -> None:
    assert fetcher.list_keys("20190101", "20200101") == ["20260830_cn", "20260830_us"]


# TC-SNF-002
def test_tc_snf_002_params(fetcher: SnapshotFetcher) -> None:
    assert fetcher.build_params("20260830_us", "a", "b") == {"charts": "free", "country": "us"}


# TC-SNF-003
def test_tc_snf_003_run_skip_force(fetcher: SnapshotFetcher, lake: MiniLake) -> None:
    first = fetcher.run("r1", "20190101", "20260830")
    assert (first.fetched, first.rows) == (2, 4)
    raw = pd.read_parquet(next(lake.lake_root.rglob("country=20260830_cn.parquet")))
    assert set(raw["capture_date"]) == {"20260830"}
    again = fetcher.run("r2", "20190101", "20260830")
    assert (again.fetched, again.skipped) == (0, 2)
    forced = fetcher.run("r3", "20190101", "20260830", force=True)
    assert forced.fetched == 2
    assert len(list(lake.lake_root.rglob("country=20260830_*.parquet"))) == 2
