from __future__ import annotations

import pytest

from quant_cn.calculation.expiry_clock import ExpiryClock

SESSIONS = ["20260924", "20260928", "20260929", "20260930", "20261008", "20261009"]


# TC-EC-001
def test_tc_ec_001_calendar() -> None:
    clock = ExpiryClock()
    assert clock.get_units("20260924", "20261009", 15) == 15 * 1440
    assert clock.get_target() / clock.get_year() == pytest.approx(30 / 365)


# TC-EC-002
def test_tc_ec_002_trading() -> None:
    clock = ExpiryClock("trading", SESSIONS)
    assert clock.get_units("20260924", "20261009", 15) == 5
    assert (clock.get_target(), clock.get_year()) == (21, 244)


# TC-EC-003
def test_tc_ec_003_errors() -> None:
    with pytest.raises(ValueError):
        ExpiryClock("trading")
    with pytest.raises(ValueError):
        ExpiryClock("trading", SESSIONS).get_units("20260924", "20261231", 98)
