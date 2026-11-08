"""Shared fixture: a mini lake with statements, daily_basic and a calendar (factor PIT tests)."""

from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.panel_cache import PanelCache
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar
from tests.support import MiniLake, SampleFactorLake


@pytest.fixture
def reader(lake: MiniLake, config: Config) -> LakeReader:
    SampleFactorLake.write_market(
        lake, config, pd.bdate_range("2024-01-02", "2026-06-30").strftime("%Y%m%d").tolist()
    )
    SampleFactorLake.write_statements(lake, config)
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    aligner = PitAligner(lake.catalog, lake.query, DateCodec())
    aligner.refresh()
    return LakeReader(
        lake.catalog,
        lake.query,
        config.datasets,
        aligner,
        TickerAliasMap(lake.catalog, lake.query),
        TradingCalendar(lake.query),
        PanelCache(),
    )
