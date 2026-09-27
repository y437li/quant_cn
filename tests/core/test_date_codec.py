from __future__ import annotations

import datetime as dt

import pytest

from quant_cn.core.date_codec import DateCodec


@pytest.fixture
def codec() -> DateCodec:
    return DateCodec()


# TC-DC-001
def test_tc_dc_001_round_trip(codec: DateCodec) -> None:
    assert codec.to_date("20260828") == dt.date(2026, 8, 28)
    assert codec.to_str(dt.date(2026, 8, 28)) == "20260828"
    assert codec.validate("20240229") == "20240229"


# TC-DC-002
@pytest.mark.parametrize("bad", ["2026-08-28", "2026082", "20260230", "abcdefgh"])
def test_tc_dc_002_malformed_raises(codec: DateCodec, bad: str) -> None:
    with pytest.raises(ValueError):
        codec.validate(bad)


# TC-DC-003
def test_tc_dc_003_quarter_ends(codec: DateCodec) -> None:
    assert codec.quarter_ends("20250331", "20251231") == [
        "20250331",
        "20250630",
        "20250930",
        "20251231",
    ]
    assert codec.quarter_ends("20250401", "20250629") == []


# TC-DC-004
def test_tc_dc_004_weekdays(codec: DateCodec) -> None:
    # 2026-08-28 is a Friday
    assert codec.weekdays("20260828", "20260831") == ["20260828", "20260831"]


# TC-DC-005
def test_tc_dc_005_start_after_end(codec: DateCodec) -> None:
    with pytest.raises(ValueError):
        codec.quarter_ends("20260101", "20250101")
    with pytest.raises(ValueError):
        codec.weekdays("20260101", "20250101")
