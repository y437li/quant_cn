from __future__ import annotations

import pytest

from quant_cn.core.ticker_normalizer import TickerNormalizer


@pytest.fixture
def tn() -> TickerNormalizer:
    return TickerNormalizer()


# TC-TN-001
def test_tc_tn_001_ts_code_passthrough(tn: TickerNormalizer) -> None:
    assert tn.normalize("600519.SH") == "600519.SH"
    assert tn.is_valid("830799.BJ")


# TC-TN-002
@pytest.mark.parametrize(("raw", "out"), [("sh600519", "600519.SH"), ("SZ000001", "000001.SZ")])
def test_tc_tn_002_prefixed(tn: TickerNormalizer, raw: str, out: str) -> None:
    assert tn.normalize(raw) == out


# TC-TN-003
@pytest.mark.parametrize(
    ("raw", "out"),
    [
        ("600519", "600519.SH"),
        ("000001", "000001.SZ"),
        ("300750", "300750.SZ"),
        ("830799", "830799.BJ"),
    ],
)
def test_tc_tn_003_bare_codes(tn: TickerNormalizer, raw: str, out: str) -> None:
    assert tn.normalize(raw) == out


# TC-TN-004
@pytest.mark.parametrize("bad", ["", "AAPL", "12345", "700001"])
def test_tc_tn_004_garbage(tn: TickerNormalizer, bad: str) -> None:
    with pytest.raises(ValueError):
        tn.normalize(bad)
    assert not tn.is_valid(bad)
