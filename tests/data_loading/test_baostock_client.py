from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pandas as pd
import pytest

from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.baostock_client import BaostockClient
from tests.support import FakeClock


class FakeResult:
    def __init__(self, rows: list[dict[str, str]], error_code: str = "0") -> None:
        self.rows, self.error_code, self.error_msg = rows, error_code, "boom"

    def get_data(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


def build_module(results: list[FakeResult], calls: list[dict[str, Any]]) -> Any:
    state = {"logins": 0}

    def login() -> Any:
        state["logins"] += 1
        return SimpleNamespace(error_code="0", error_msg="")

    def query_history_k_data_plus(**kwargs: Any) -> FakeResult:
        calls.append(kwargs)
        return results.pop(0)

    return SimpleNamespace(
        login=login, query_history_k_data_plus=query_history_k_data_plus, state=state
    )


# TC-BSC-001
def test_tc_bsc_001_conversions(clock: FakeClock) -> None:
    calls: list[dict[str, Any]] = []
    rows = [{"date": "2026-09-28", "code": "sh.600000", "close": "9.1600", "tradestatus": "1"}]
    module = build_module([FakeResult(rows)], calls)
    client = BaostockClient(clock, module=module)
    params = {
        "ts_code": "600000.SH",
        "start_date": "20260920",
        "end_date": "20260928",
        "adjustflag": "3",
    }
    out = client.query(
        "query_history_k_data_plus", params, ["date", "code", "close", "tradestatus"]
    )
    assert calls == [
        {
            "code": "sh.600000",
            "start_date": "2026-09-20",
            "end_date": "2026-09-28",
            "adjustflag": "3",
            "fields": "date,code,close,tradestatus",
        }
    ]
    assert out.to_dict("records") == [
        {"ts_code": "600000.SH", "date": "20260928", "close": 9.16, "tradestatus": 1.0}
    ]


# TC-BSC-002
def test_tc_bsc_002_retry_and_login(clock: FakeClock) -> None:
    calls: list[dict[str, Any]] = []
    module = build_module([FakeResult([], "10002007")] * 3, calls)
    client = BaostockClient(clock, retries=2, module=module)
    with pytest.raises(DataSourceError, match="10002007"):
        client.query("query_history_k_data_plus", {"ts_code": "600000.SH"}, ["close"])
    assert (
        len(calls) == 3 and module.state["logins"] == 3
    )  # login once, re-login after each failure


# TC-BSC-003
def test_tc_bsc_003_beijing_skipped(clock: FakeClock) -> None:
    calls: list[dict[str, Any]] = []
    client = BaostockClient(clock, module=build_module([], calls))
    assert client.query("query_history_k_data_plus", {"ts_code": "920001.BJ"}, ["close"]).empty
    assert client.query("query_adjust_factor", {"ts_code": "T600018.SH"}, []).empty
    assert calls == []


# TC-BSC-004
def test_tc_bsc_004_login_retry(clock: FakeClock) -> None:
    calls: list[dict[str, Any]] = []
    module = build_module(
        [FakeResult([{"date": "2026-09-28", "code": "sh.600000", "close": "9.16"}])], calls
    )
    replies = iter(
        [
            SimpleNamespace(error_code="10001", error_msg="网络接收错误"),
            SimpleNamespace(error_code="0", error_msg=""),
        ]
    )
    module.login = lambda: next(replies)
    out = BaostockClient(clock, retries=2, module=module).query(
        "query_history_k_data_plus", {"ts_code": "600000.SH"}, ["date", "code", "close"]
    )
    assert out["close"].tolist() == [9.16]
