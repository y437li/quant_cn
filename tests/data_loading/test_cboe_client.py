"""Contract tests for data_loading.CboeClient (plan 03 ph6, D-152)."""

from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.cboe_client import COLUMNS, CboeClient
from quant_cn.data_loading.http_transport import HttpTransport
from tests.support import FakeClock

CSV = (
    b"DATE,OPEN,HIGH,LOW,CLOSE\n"
    b"11/12/2026,18.36,19.34,17.38,18.70\n"
    b"01/02/1990,17.24,17.24,17.24,17.24\n"
)


class FakeCsvTransport(HttpTransport):
    """Scripted bodies (bytes or exception) in order; records every URL."""

    def __init__(self, replies: list[bytes | Exception]) -> None:
        self.replies = list(replies)
        self.urls: list[str] = []

    def fetch_bytes(self, url: str, timeout: float) -> bytes:
        self.urls.append(url)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def _build_client(transport: HttpTransport, clock: FakeClock) -> CboeClient:
    return CboeClient(clock, transport, min_interval_s=0, retries=0, retry_sleep_s=0)


# TC-CBC-001
def test_tc_cbc_001_parsed(clock: FakeClock) -> None:
    transport = FakeCsvTransport([CSV])
    out = _build_client(transport, clock).query("daily_prices", {"index": "VIX"}, [])
    assert list(out.columns) == COLUMNS
    assert out["trade_date"].tolist() == ["19900102", "20261112"]
    assert out["close"].iloc[1] == pytest.approx(18.70) and out["index_code"].iloc[0] == "VIX"
    assert pd.api.types.is_string_dtype(out["trade_date"]) and out["close"].dtype == "float64"
    assert transport.urls[0].endswith("/VIX_History.csv")


# TC-CBC-002
def test_tc_cbc_002_bad_rows_and_failures(clock: FakeClock) -> None:
    body = CSV + b"not a date,1,1,1,1\n"
    assert len(_build_client(FakeCsvTransport([body]), clock).query("x", {}, [])) == 2
    with pytest.raises(DataSourceError):
        _build_client(FakeCsvTransport([]), clock).query("x", {"index": "../VIX"}, [])
    with pytest.raises(DataSourceError):
        _build_client(FakeCsvTransport([b"a,b\n1,2\n"]), clock).query("x", {}, [])
    with pytest.raises(DataSourceError):
        _build_client(FakeCsvTransport([OSError("down")]), clock).query("x", {}, [])
