from __future__ import annotations

import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.data_loading.fetchers import (
    DateSweepFetcher,
    EnumFetcher,
    PeriodSweepFetcher,
    SingleCallFetcher,
)
from quant_cn.lake.trading_calendar import TradingCalendar
from tests.support import FakeTushareClient, MiniLake, Sample


@pytest.fixture
def deps(lake: MiniLake) -> tuple[object, ...]:
    return (FakeTushareClient(), lake.writer, lake.fetch_log, lake.run_log, lake.clock)


# TC-SCF-001
def test_tc_scf_001_single_call(config: Config, deps: tuple[object, ...]) -> None:
    f = SingleCallFetcher(config.get_dataset("trade_cal"), *deps)  # type: ignore[arg-type]
    assert f.list_keys("19901219", "20260830") == ["all"]
    assert f.build_params("all", "19901219", "20260830") == {
        "exchange": "SSE",
        "start_date": "19901219",
        "end_date": "20260830",
    }
    assert (
        SingleCallFetcher(config.get_dataset("namechange"), *deps).build_params("all", "a", "b")
        == {}
    )  # type: ignore[arg-type]


# TC-EF-001
def test_tc_ef_001_enum(config: Config, deps: tuple[object, ...]) -> None:
    f = EnumFetcher(config.get_dataset("index_daily"), *deps, values=["000300.SH"])  # type: ignore[arg-type]
    assert f.list_keys("a", "b") == ["000300.SH"]
    assert f.build_params("000300.SH", "20100101", "20260830") == {
        "ts_code": "000300.SH",
        "start_date": "20100101",
        "end_date": "20260830",
    }


# TC-DSF-001
def test_tc_dsf_001_trade_date_keys(
    lake: MiniLake, config: Config, deps: tuple[object, ...]
) -> None:
    lake.writer.write_raw(
        config.get_dataset("trade_cal"),
        "all",
        Sample.build_trade_cal(["20260827", "20260828"], ["20260829"]),
    )
    lake.catalog.refresh_views()
    f = DateSweepFetcher(
        config.get_dataset("daily"), *deps, calendar=TradingCalendar(lake.query), codec=DateCodec()
    )  # type: ignore[arg-type]
    assert f.list_keys("20260828", "20260830") == ["20260828"]
    assert f.build_params("20260828", "", "") == {"trade_date": "20260828"}


# TC-DSF-002
def test_tc_dsf_002_ann_date_keys(lake: MiniLake, deps: tuple[object, ...]) -> None:
    spec = Sample.build_spec(
        sweep={"kind": "ann_date"},
        fields=["ts_code", "ann_date"],
        text_fields=["ts_code", "ann_date"],
        primary_key=["ts_code", "ann_date"],
        known_on="ann_date",
        curated={"path": "ev"},
    )
    f = DateSweepFetcher(spec, *deps, calendar=TradingCalendar(lake.query), codec=DateCodec())  # type: ignore[arg-type]
    assert f.list_keys("20260828", "20260831") == ["20260828", "20260831"]


# TC-PSF-001
def test_tc_psf_001_period(config: Config, deps: tuple[object, ...]) -> None:
    f = PeriodSweepFetcher(config.get_dataset("income_vip"), *deps, codec=DateCodec())  # type: ignore[arg-type]
    assert f.list_keys("20250101", "20250930") == ["20250331", "20250630", "20250930"]
    assert f.build_params("20250630", "", "") == {"period": "20250630"}
