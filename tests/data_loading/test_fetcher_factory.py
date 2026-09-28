from __future__ import annotations

import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError
from quant_cn.data_loading.fetcher_factory import FetcherFactory
from quant_cn.data_loading.fetchers import (
    DateSweepFetcher,
    EnumFetcher,
    PeriodSweepFetcher,
    SingleCallFetcher,
)
from quant_cn.lake.trading_calendar import TradingCalendar
from tests.support import FakeTushareClient, MiniLake


def factory(config: Config, lake: MiniLake) -> FetcherFactory:
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
        ("daily", DateSweepFetcher),
        ("income_vip", PeriodSweepFetcher),
    ],
)
def test_tc_ff_001_kind_mapping(config: Config, lake: MiniLake, name: str, cls: type) -> None:
    assert type(factory(config, lake).build(config.get_dataset(name))) is cls


# TC-FF-002
def test_tc_ff_002_enum_values(config: Config, lake: MiniLake) -> None:
    built = factory(config, lake).build(config.get_dataset("index_daily"))
    assert built.list_keys("a", "b") == config.enum_values["indices"]
    broken = config.model_copy(update={"enum_values": {}})
    with pytest.raises(ConfigError):
        factory(broken, lake).build(config.get_dataset("index_daily"))
