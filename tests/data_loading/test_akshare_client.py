from __future__ import annotations

import datetime as dt
from types import SimpleNamespace
from typing import Any

import pandas as pd
import pytest

from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.akshare_client import AkshareClient
from tests.support import FakeClock


def build_module(**functions: Any) -> Any:
    return SimpleNamespace(**functions)


# TC-AKC-001
def test_tc_akc_001_call_and_dates(clock: FakeClock) -> None:
    seen: dict[str, str] = {}

    def bond_china_yield(start_date: str, end_date: str) -> pd.DataFrame:
        seen.update(start_date=start_date, end_date=end_date)
        return pd.DataFrame(
            {
                "日期": [dt.date(2025, 1, 2), dt.date(2025, 1, 3)],
                "iso": ["2025-01-02", None],
                "stamp": pd.to_datetime(["2025-01-02", "2025-01-03"]),
                "10年": [1.6, 1.7],
            }
        )

    client = AkshareClient(clock, module=build_module(bond_china_yield=bond_china_yield))
    out = client.query("bond_china_yield", {"start_date": "20250101", "end_date": "20251231"}, [])
    assert seen == {"start_date": "20250101", "end_date": "20251231"}
    assert out["日期"].tolist() == ["20250102", "20250103"]
    assert out["iso"].tolist()[0] == "20250102" and pd.isna(out["iso"].iloc[1])
    assert out["stamp"].tolist() == ["20250102", "20250103"]
    assert out["10年"].tolist() == [1.6, 1.7]


# TC-AKC-002
def test_tc_akc_002_retry_then_fail(clock: FakeClock) -> None:
    calls = {"n": 0}

    def flaky() -> pd.DataFrame:
        calls["n"] += 1
        raise ConnectionError("reset by peer")

    client = AkshareClient(clock, retries=2, retry_sleep_s=6.0, module=build_module(flaky=flaky))
    with pytest.raises(DataSourceError, match="failed after 3 attempts"):
        client.query("flaky", {}, [])
    assert calls["n"] == 3
    with pytest.raises(DataSourceError, match="no function"):
        client.query("missing", {}, [])
