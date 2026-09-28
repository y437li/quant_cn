from __future__ import annotations

import pytest

from quant_cn.core.base_fetcher import BaseFetcher
from quant_cn.core.dataset_spec import DatasetSpec, SweepSpec
from quant_cn.core.exceptions import DataSourceError
from tests.support import Build, FakeTushareClient, MiniLake

DAYS = ["20260826", "20260827", "20260828"]


class ListFetcher(BaseFetcher):
    """Keys are a fixed list; params carry the key as trade_date."""

    def list_keys(self, start: str, end: str) -> list[str]:
        return [d for d in DAYS if start <= d <= end]

    def build_params(self, key: str, start: str, end: str) -> dict[str, str]:
        return {"trade_date": key}


def fetcher(
    lake: MiniLake, client: FakeTushareClient, spec: DatasetSpec | None = None
) -> ListFetcher:
    return ListFetcher(
        spec or Build.spec(), client, lake.writer, lake.fetch_log, lake.run_log, lake.clock
    )


@pytest.fixture
def client() -> FakeTushareClient:
    fake = FakeTushareClient()
    for day in DAYS[:2]:
        fake.add("daily", day, Build.bars(day))
    return fake  # DAYS[2] returns an empty frame


# TC-BF-001
def test_tc_bf_001_counts(lake: MiniLake, client: FakeTushareClient) -> None:
    lake.fetch_log.mark_done("bars", DAYS[0], 2, None)
    report = fetcher(lake, client).run("r1", DAYS[0], DAYS[-1])
    assert (report.keys_total, report.skipped, report.fetched, report.empty, report.rows) == (
        3,
        1,
        1,
        1,
        2,
    )


# TC-BF-002
def test_tc_bf_002_skip_and_force(lake: MiniLake, client: FakeTushareClient) -> None:
    fetcher(lake, client).run("r1", DAYS[0], DAYS[-1])
    client.calls.clear()
    fetcher(lake, client).run("r2", DAYS[0], DAYS[-1])
    assert client.calls == []
    fetcher(lake, client).run("r3", DAYS[0], DAYS[-1], force=True)
    assert len(client.calls) == 3


# TC-BF-003
def test_tc_bf_003_overwrite_refetches(lake: MiniLake, client: FakeTushareClient) -> None:
    spec = Build.spec(refresh="overwrite")
    fetcher(lake, client, spec).run("r1", DAYS[0], DAYS[-1])
    client.calls.clear()
    fetcher(lake, client, spec).run("r2", DAYS[0], DAYS[-1])
    assert len(client.calls) == 3


# TC-BF-004
def test_tc_bf_004_refetch_recent(lake: MiniLake, client: FakeTushareClient) -> None:
    spec = Build.spec(sweep=SweepSpec(kind="trade_date", refetch_recent=1))
    fetcher(lake, client, spec).run("r1", DAYS[0], DAYS[-1])
    client.calls.clear()
    fetcher(lake, client, spec).run("r2", DAYS[0], DAYS[-1])
    assert [c[1]["trade_date"] for c in client.calls] == [DAYS[-1]]


# TC-BF-005
def test_tc_bf_005_empty_marked_done_without_file(
    lake: MiniLake, client: FakeTushareClient
) -> None:
    fetcher(lake, client).run("r1", DAYS[2], DAYS[2])
    assert lake.fetch_log.is_done("bars", DAYS[2])
    assert not (lake.lake_root / "raw" / "bars").exists()


# TC-BF-006
def test_tc_bf_006_failure_keeps_progress(lake: MiniLake, client: FakeTushareClient) -> None:
    client.fail("daily", DAYS[1], DataSourceError("boom"))
    with pytest.raises(DataSourceError):
        fetcher(lake, client).run("r1", DAYS[0], DAYS[-1])
    assert lake.fetch_log.read_done_keys("bars") == {DAYS[0]}
    assert lake.fetch_log.mirror_path.exists()
    failed = lake.query.sql("SELECT key FROM meta.run_log WHERE status = 'failed'")
    assert failed["key"].tolist() == [DAYS[1]]
