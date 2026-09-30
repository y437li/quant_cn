from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.lake.effective_date_resolver import EffectiveDateResolver
from quant_cn.lake.trading_calendar import TradingCalendar
from tests.support import MiniLake, Sample

# 2026-09-25 Mid-Autumn, 09-26/27 weekend, 10-01..07 National Day
OPEN = ["20260924", "20260928", "20260929", "20260930", "20261008", "20261009", "20261012"]


@pytest.fixture
def resolver(lake: MiniLake, config: Config) -> EffectiveDateResolver:
    lake.writer.write_raw(config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(OPEN))
    lake.catalog.refresh_views()
    return EffectiveDateResolver(TradingCalendar(lake.query), DateCodec())


# TC-EDR-001
def test_tc_edr_001_as_is(resolver: EffectiveDateResolver) -> None:
    spec = Sample.build_spec()
    assert resolver.get_effective_date("20260924", spec) == "20260924"
    assert resolver.get_effective_date("20260926", spec) == "20260928"


# TC-EDR-002
def test_tc_edr_002_next_session(resolver: EffectiveDateResolver) -> None:
    spec = Sample.build_spec(source="fred", known_on_rule="next_session")
    assert resolver.get_effective_date("20260925", spec) == "20260928"  # US Friday -> China Monday
    assert resolver.get_effective_date("20260930", spec) == "20261008"  # over National Day


# TC-EDR-003
def test_tc_edr_003_period_end_lag(resolver: EffectiveDateResolver) -> None:
    spec = Sample.build_spec(known_on_rule="period_end_lag", release_lag_days=8)
    assert resolver.get_effective_date("202609", spec) == "20261008"  # 09-30 + 8 = 10-08
    assert resolver.get_effective_date("20260920", spec) == "20260928"


# TC-EDR-004
def test_tc_edr_004_resolve(resolver: EffectiveDateResolver) -> None:
    spec = Sample.build_spec(known_on_rule="next_session")
    frame = pd.DataFrame(
        {"trade_date": ["20260924", None], "ts_code": ["A", "B"], "close": [1.0, 2.0]}
    )
    out = resolver.compute(frame, spec)
    assert out["effective_date"].iloc[0] == "20260928" and pd.isna(out["effective_date"].iloc[1])


# TC-EDR-005
def test_tc_edr_005_period_start_lag(resolver: EffectiveDateResolver) -> None:
    spec = Sample.build_spec(known_on_rule="period_start_lag")
    assert resolver.get_effective_date("202610", spec) == "20261008"  # 10-01..07 National Day
    lagged = Sample.build_spec(known_on_rule="period_start_lag", release_lag_days=1)
    assert resolver.get_effective_date("202609", lagged) == "20260924"  # 09-02 -> first open


# TC-EDR-006
def test_tc_edr_006_two_sessions(resolver: EffectiveDateResolver) -> None:
    spec = Sample.build_spec(known_on_rule="next_session", lag_sessions=2)
    assert resolver.get_effective_date("20260924", spec) == "20260929"  # 09-28, then 09-29
    assert resolver.get_effective_date("20260929", spec) == "20261008"  # 09-30, then 10-08
