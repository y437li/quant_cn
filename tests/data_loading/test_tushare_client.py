from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from quant_cn.core.config import Config, TushareConfig
from quant_cn.core.exceptions import ConfigError, DataSourceError, PermissionDeniedError
from quant_cn.data_loading.http_transport import HttpTransport
from quant_cn.data_loading.tushare_client import TushareClient
from tests.support import FakeClock


class ScriptedTransport(HttpTransport):
    """Returns queued responses (dicts) or raises queued exceptions; records payloads."""

    def __init__(self, script: list[dict[str, Any] | Exception]) -> None:
        self.script = list(script)
        self.payloads: list[Mapping[str, Any]] = []

    def fetch_json(self, url: str, payload: Mapping[str, Any], timeout: float) -> dict[str, Any]:
        self.payloads.append(payload)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ok(items: list[list[object]]) -> dict[str, Any]:
    return {"code": 0, "msg": "", "data": {"fields": ["ts_code", "close"], "items": items}}


def err(msg: str) -> dict[str, Any]:
    return {"code": -2001, "msg": msg, "data": None}


@pytest.fixture
def settings(config: Config) -> TushareConfig:
    return config.tushare.model_copy(update={"page_size": 2, "retries": 2})


def client(
    settings: TushareConfig, script: list[dict[str, Any] | Exception], clock: FakeClock
) -> tuple[TushareClient, ScriptedTransport]:
    transport = ScriptedTransport(script)
    return TushareClient(settings, clock, transport), transport


# TC-TC-001
def test_tc_tc_001_paging(settings: TushareConfig, clock: FakeClock) -> None:
    c, t = client(settings, [ok([["A", 1], ["B", 2]]), ok([["C", 3]])], clock)
    df = c.query("daily", {"trade_date": "20260828"}, ["ts_code", "close"])
    assert df["ts_code"].tolist() == ["A", "B", "C"]
    assert [p["params"]["offset"] for p in t.payloads] == [0, 2]
    assert t.payloads[0]["fields"] == "ts_code,close" and t.payloads[0]["token"] == "test-token"


# TC-TC-002
def test_tc_tc_002_rate_limit(settings: TushareConfig, clock: FakeClock) -> None:
    script: list[dict[str, Any] | Exception] = [err("抱歉,您每分钟最多访问该接口500次")] * 3 + [
        ok([["A", 1]])
    ]
    c, _ = client(settings, script, clock)
    assert len(c.query("daily", {}, [])) == 1
    assert clock.sleeps == [settings.rate_limit_sleep_s] * 3


# TC-TC-003
def test_tc_tc_003_retries_exhausted(settings: TushareConfig, clock: FakeClock) -> None:
    c, t = client(settings, [err("server error")] * 3, clock)
    with pytest.raises(DataSourceError):
        c.query("daily", {}, [])
    assert len(t.payloads) == 3 and clock.sleeps == [settings.retry_sleep_s] * 2


# TC-TC-004
def test_tc_tc_004_permission(settings: TushareConfig, clock: FakeClock) -> None:
    c, t = client(settings, [err("抱歉,您没有访问该接口的权限")], clock)
    with pytest.raises(PermissionDeniedError):
        c.query("income_vip", {}, [])
    assert len(t.payloads) == 1 and clock.sleeps == []


# TC-TC-005
def test_tc_tc_005_network_retry(settings: TushareConfig, clock: FakeClock) -> None:
    c, _ = client(settings, [TimeoutError("timed out"), ok([["A", 1]])], clock)
    assert len(c.query("daily", {}, [])) == 1
    assert clock.sleeps == [settings.retry_sleep_s]


# TC-TC-006
def test_tc_tc_006_empty(settings: TushareConfig, clock: FakeClock) -> None:
    empty = {"code": 0, "msg": "", "data": {"fields": [], "items": []}}
    c, _ = client(settings, [empty], clock)
    df = c.query("daily", {}, ["ts_code", "close"])
    assert df.empty and list(df.columns) == ["ts_code", "close"]


# TC-TC-007
def test_tc_tc_007_empty_token(settings: TushareConfig, clock: FakeClock) -> None:
    c, _ = client(settings.model_copy(update={"token": ""}), [], clock)
    with pytest.raises(ConfigError):
        c.query("daily", {}, [])
