from __future__ import annotations

import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.data_loading.fetchers import (
    DateSweepFetcher,
    DateWindowFetcher,
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


# TC-DWF-001
def test_tc_dwf_001_monthly(deps: tuple[object, ...]) -> None:
    spec = Sample.build_spec(sweep={"kind": "date_window", "window": "month"})
    f = DateWindowFetcher(spec, *deps, codec=DateCodec())  # type: ignore[arg-type]
    assert f.list_keys("20260115", "20260310") == ["202601", "202602", "202603"]
    assert f.build_params("202601", "20260115", "20260310") == {
        "start_date": "20260115",
        "end_date": "20260131",
    }
    assert f.build_params("202602", "20260115", "20260310")["end_date"] == "20260228"
    assert f.build_params("202603", "20260115", "20260310")["end_date"] == "20260310"


# TC-DWF-002
def test_tc_dwf_002_yearly(deps: tuple[object, ...]) -> None:
    spec = Sample.build_spec(sweep={"kind": "date_window", "window": "year"})
    f = DateWindowFetcher(spec, *deps, codec=DateCodec())  # type: ignore[arg-type]
    assert f.list_keys("20240601", "20260930") == ["2024", "2025", "2026"]
    assert f.build_params("2025", "20240601", "20260930") == {
        "start_date": "20250101",
        "end_date": "20251231",
    }


# TC-DWF-003
def test_tc_dwf_003_value_param(deps: tuple[object, ...]) -> None:
    sweep = {
        "kind": "date_window",
        "window": "year",
        "value_param": "index_code",
        "values": ["000300.SH", "000852.SH"],
        "range_params": True,
    }
    spec = Sample.build_spec(sweep=sweep)
    f = DateWindowFetcher(spec, *deps, codec=DateCodec(), values=["000300.SH", "000852.SH"])  # type: ignore[arg-type]
    keys = f.list_keys("20250301", "20260930")
    assert keys == ["2025_000300.SH", "2025_000852.SH", "2026_000300.SH", "2026_000852.SH"]
    assert f.build_params("2025_000852.SH", "20250301", "20260930") == {
        "index_code": "000852.SH",
        "start_date": "20250301",
        "end_date": "20251231",
    }
