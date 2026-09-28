from __future__ import annotations

import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.trading_calendar import TradingCalendar
from tests.support import Build, MiniLake

OPEN = ["20260827", "20260828", "20260831"]
CLOSED = ["20260829", "20260830"]


@pytest.fixture
def calendar(lake: MiniLake, config: Config) -> TradingCalendar:
    lake.writer.write_raw(config.get_dataset("trade_cal"), "all", Build.trade_cal(OPEN, CLOSED))
    lake.catalog.refresh_views()
    return TradingCalendar(lake.query)


# TC-TCA-001
def test_tc_tca_001_sessions(calendar: TradingCalendar) -> None:
    assert calendar.list_sessions("20260828", "20260831") == ["20260828", "20260831"]
    assert calendar.list_sessions("20260829", "20260830") == []


# TC-TCA-002
def test_tc_tca_002_weekend(calendar: TradingCalendar) -> None:
    assert not calendar.is_open("20260829")
    assert calendar.get_next("20260828") == "20260831"
    assert calendar.get_prev("20260831") == "20260828"


# TC-TCA-003
def test_tc_tca_003_missing(lake: MiniLake) -> None:
    with pytest.raises(LakeError):
        TradingCalendar(lake.query).list_sessions("20260101", "20260131")


# TC-TCA-004
def test_tc_tca_004_edges(calendar: TradingCalendar) -> None:
    with pytest.raises(LakeError):
        calendar.get_next("20260831")
    with pytest.raises(LakeError):
        calendar.get_prev("20260827")
