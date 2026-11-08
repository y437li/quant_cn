from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.dataset_spec import SweepSpec, ValuesFromDataset
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError
from quant_cn.data_loading.fetcher_factory import FetcherFactory
from quant_cn.data_loading.fetchers import (
    DateSweepFetcher,
    DateWindowFetcher,
    EnumFetcher,
    PeriodSweepFetcher,
    SingleCallFetcher,
)
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.trading_calendar import TradingCalendar
from tests.support import FakeTushareClient, MiniLake, Sample


def build_factory(config: Config, lake: MiniLake) -> FetcherFactory:
    return FetcherFactory(
        config,
        FakeTushareClient(),
        lake.writer,
        lake.fetch_log,
        lake.run_log,
        lake.clock,
        TradingCalendar(lake.query),
        DateCodec(),
    )


# TC-FF-001
@pytest.mark.parametrize(
    ("name", "cls"),
    [
        ("trade_cal", SingleCallFetcher),
        ("stock_basic", EnumFetcher),
        ("index_daily", EnumFetcher),
        ("opt_basic", EnumFetcher),
        ("index_weight", DateWindowFetcher),
        ("index_member_all", EnumFetcher),
        ("index_classify", SingleCallFetcher),
        ("sw_daily", DateSweepFetcher),
        ("fund_nav", DateSweepFetcher),
        ("fund_basic", SingleCallFetcher),
        ("daily", DateSweepFetcher),
        ("income_vip", PeriodSweepFetcher),
    ],
)
def test_tc_ff_001_kind_mapping(config: Config, lake: MiniLake, name: str, cls: type) -> None:
    assert type(build_factory(config, lake).build(config.get_dataset(name))) is cls


# TC-FF-002
def test_tc_ff_002_enum_values(config: Config, lake: MiniLake) -> None:
    built = build_factory(config, lake).build(config.get_dataset("index_daily"))
    assert built.list_keys("a", "b") == config.enum_values["indices"]
    broken = config.model_copy(update={"enum_values": {}})
    with pytest.raises(ConfigError):
        build_factory(broken, lake).build(config.get_dataset("index_daily"))


# TC-FF-003
def test_tc_ff_003_values_from_dataset(config: Config, lake: MiniLake) -> None:
    basic = {f: None for f in config.get_dataset("stock_basic").fields}
    rows = pd.DataFrame(
        [
            {**basic, "ts_code": c, "market": m, "list_status": "L"}
            for c, m in [("510300.SH", "E"), ("159919.SZ", "E"), ("600000.SH", "主板")]
        ]
    )
    lake.writer.write_raw(config.get_dataset("stock_basic"), "L", rows)
    Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(
        config.get_dataset("stock_basic")
    )
    spec = config.get_dataset("index_daily").model_copy(
        update={
            "sweep": SweepSpec(
                kind="ts_code",
                range_params=True,
                values_from_dataset=ValuesFromDataset(
                    dataset="stock_basic", column="ts_code", where="market = 'E'"
                ),
            )
        }
    )
    factory = FetcherFactory(
        config,
        FakeTushareClient(),
        lake.writer,
        lake.fetch_log,
        lake.run_log,
        lake.clock,
        TradingCalendar(lake.query),
        DateCodec(),
        query=lake.query,
    )
    assert factory.build(spec).list_keys("a", "b") == ["159919.SZ", "510300.SH"]


# TC-FF-004
def test_tc_ff_004_source(config: Config, lake: MiniLake) -> None:
    fred_spec = Sample.build_spec(source="fred", sweep=SweepSpec(kind="date_window", window="year"))
    with pytest.raises(ConfigError):
        build_factory(config, lake).build(fred_spec)
    fred = FakeTushareClient()
    factory = FetcherFactory(
        config,
        FakeTushareClient(),
        lake.writer,
        lake.fetch_log,
        lake.run_log,
        lake.clock,
        TradingCalendar(lake.query),
        DateCodec(),
        extra_clients={"fred": fred},
    )
    built = factory.build(fred_spec)
    assert type(built) is DateWindowFetcher and built._client is fred


# TC-FF-005
def test_tc_ff_005_missing_key_source(config: Config, lake: MiniLake) -> None:
    factory = FetcherFactory(
        config,
        FakeTushareClient(),
        lake.writer,
        lake.fetch_log,
        lake.run_log,
        lake.clock,
        TradingCalendar(lake.query),
        DateCodec(),
        query=lake.query,
    )
    fetcher = factory.build(config.get_dataset("ths_member"))
    assert fetcher.list_keys("20260101", "20261107") == []
