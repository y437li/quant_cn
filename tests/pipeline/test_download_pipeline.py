from __future__ import annotations

import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError, DataSourceError, PermissionDeniedError
from quant_cn.data_loading.fetcher_factory import FetcherFactory
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.pipeline.download_pipeline import DownloadPipeline
from quant_cn.pipeline.runner import LocalRunner
from tests.support import Build, FakeTushareClient, MiniLake

OPEN = ["20260826", "20260827", "20260828"]


@pytest.fixture
def client() -> FakeTushareClient:
    fake = FakeTushareClient()
    fake.add("trade_cal", "all", Build.trade_cal(OPEN, ["20260829", "20260830"]))
    for day in OPEN:
        fake.add("daily", day, Build.bars(day).assign(open=1.0))
    return fake


def pipeline(config: Config, lake: MiniLake, client: FakeTushareClient) -> DownloadPipeline:
    factory = FetcherFactory(
        config,
        client,
        lake.writer,
        lake.fetch_log,
        lake.run_log,
        lake.clock,
        TradingCalendar(lake.query),
        DateCodec(),
    )
    runner = LocalRunner(lake.run_log, show_progress=False)
    return DownloadPipeline(
        config, factory, runner, lake.catalog, lake.fetch_log, lake.clock, DateCodec()
    )


def daily_calls(client: FakeTushareClient) -> list[str]:
    return [p["trade_date"] for api, p in client.calls if api == "daily"]


# TC-DP-001
def test_tc_dp_001_dry_run(config: Config, lake: MiniLake, client: FakeTushareClient) -> None:
    report = pipeline(config, lake, client).run(
        ["trade_cal", "income_vip"], end="20260828", dry_run=True
    )
    assert report.status == "dry_run" and client.calls == []
    income = next(s for s in report.steps if s.name == "income_vip")
    assert income.keys_total == len(
        DateCodec().quarter_ends(config.start_for("income_vip"), "20260828")
    )


# TC-DP-002
def test_tc_dp_002_crash_resume(config: Config, lake: MiniLake, client: FakeTushareClient) -> None:
    client.fail("daily", OPEN[2], DataSourceError("network"))
    with pytest.raises(DataSourceError):
        pipeline(config, lake, client).run(["trade_cal", "daily"], start="20260826", end="20260828")
    assert daily_calls(client) == OPEN
    client.calls.clear()
    report = pipeline(config, lake, client).run(
        ["trade_cal", "daily"], start="20260826", end="20260828"
    )
    assert daily_calls(client) == [OPEN[2]]
    daily = next(s for s in report.steps if s.name == "daily")
    assert (daily.skipped, daily.fetched) == (2, 1)
    assert lake.query.sql("SELECT count(*) n FROM raw.daily")["n"].iloc[0] == 6


# TC-DP-003
def test_tc_dp_003_blocked_continues(
    config: Config, lake: MiniLake, client: FakeTushareClient
) -> None:
    client.fail("income_vip", "20260630", PermissionDeniedError("no points"))
    report = pipeline(config, lake, client).run(
        ["income_vip", "trade_cal"], start="20260601", end="20260828"
    )
    assert report.blocked() == ["income_vip"]
    assert [s.name for s in report.steps] == ["trade_cal", "income_vip"]
    assert lake.query.has_view("raw.trade_cal")


# TC-DP-004
def test_tc_dp_004_start_dates(config: Config, lake: MiniLake, client: FakeTushareClient) -> None:
    report = pipeline(config, lake, client).run(
        ["index_daily", "daily_basic"], end="20260828", dry_run=True
    )
    messages = {s.name: s.message for s in report.steps}
    assert messages["index_daily"].startswith(config.download.long_history_start)
    assert "trade_cal is not downloaded" in messages["daily_basic"]
    idx = pipeline(config, lake, client).run(["index_daily"], end="20260828")
    first = next(p for api, p in client.calls if api == "index_daily")
    assert first["start_date"] == config.download.long_history_start and idx.status == "ok"


# TC-DP-005
def test_tc_dp_005_bad_input(config: Config, lake: MiniLake, client: FakeTushareClient) -> None:
    with pytest.raises(ConfigError):
        pipeline(config, lake, client).run(["nope"])
    with pytest.raises(ValueError):
        pipeline(config, lake, client).run(["daily"], start="20260901", end="20260828")
