from __future__ import annotations

import datetime as dt
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from quant_cn.core.config import LlmConfig
from quant_cn.core.exceptions import ConfigError, DataSourceError
from quant_cn.data_loading.deep_seek_client import DeepSeekClient
from quant_cn.data_loading.http_transport import HttpTransport
from tests.support import FakeClock


def build_reply(content: str, finish: str = "stop") -> dict[str, Any]:
    return {
        "choices": [{"finish_reason": finish, "message": {"content": content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


class FakeLlmTransport(HttpTransport):
    """Scripted replies in order; records payloads and headers."""

    def __init__(self, replies: list[dict[str, Any]]) -> None:
        self.replies = list(replies)
        self.calls: list[tuple[dict[str, Any], dict[str, str]]] = []

    def fetch_json(
        self,
        url: str,
        payload: Mapping[str, Any],
        timeout: float,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        self.calls.append((dict(payload), dict(headers or {})))
        return self.replies.pop(0)


def build_config(**overrides: Any) -> LlmConfig:
    return LlmConfig(**{"api_key": "sk-test", "retries": 1, "min_interval_s": 0.0, **overrides})


# TC-DSC-001
def test_tc_dsc_001_request_and_parse(clock: FakeClock) -> None:
    transport = FakeLlmTransport([build_reply('{"answer": "动力电池"}')])
    reply = DeepSeekClient(build_config(), clock, None, transport).fetch_json("sys", "user")
    payload, headers = transport.calls[0]
    assert payload["model"] == "deepseek-flash" and payload["temperature"] == 0
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["thinking"] == {"type": "disabled"}
    assert [m["role"] for m in payload["messages"]] == ["system", "user"]
    assert headers["Authorization"] == "Bearer sk-test"
    assert reply.content == {"answer": "动力电池"}
    assert (reply.prompt_tokens, reply.completion_tokens, reply.cached) == (10, 5, False)


# TC-DSC-002
def test_tc_dsc_002_cache(clock: FakeClock, tmp_path: Path) -> None:
    transport = FakeLlmTransport([build_reply('{"a": 1}')])
    client = DeepSeekClient(build_config(), clock, tmp_path / "cache", transport)
    first = client.fetch_json("sys", "user")
    second = client.fetch_json("sys", "user")
    assert second.cached and second.content == first.content and len(transport.calls) == 1
    usage = client.get_usage()
    assert (usage["calls"], usage["cached"], usage["prompt_tokens"]) == (1, 1, 10)
    stored = next((tmp_path / "cache").rglob("*.json"))
    assert json.loads(stored.read_text())["content"] == {"a": 1}


# TC-DSC-003
def test_tc_dsc_003_bad_reply_and_missing_key(clock: FakeClock) -> None:
    transport = FakeLlmTransport([build_reply("not json"), build_reply("", finish="length")])
    with pytest.raises(DataSourceError, match="truncated"):
        DeepSeekClient(build_config(), clock, None, transport).fetch_json("sys", "user")
    with pytest.raises(ConfigError, match="DEEPSEEK_API_KEY"):
        DeepSeekClient(build_config(api_key=""), clock, None, FakeLlmTransport([])).fetch_json(
            "s", "u"
        )


class BeijingClock(FakeClock):
    """Fixed aware time in Beijing."""

    def __init__(self, when: dt.datetime) -> None:
        super().__init__()
        self.when = when

    def get_now(self) -> dt.datetime:
        return self.when


# TC-DSC-004
def test_tc_dsc_004_cost() -> None:
    prices = {"deepseek-flash": {"input_hit": 0.04, "input_miss": 2.0, "output": 8.0}}
    bj = dt.timezone(dt.timedelta(hours=8))
    peak = DeepSeekClient(
        build_config(prices=prices), BeijingClock(dt.datetime(2026, 11, 9, 10, tzinfo=bj))
    )
    off = DeepSeekClient(
        build_config(prices=prices), BeijingClock(dt.datetime(2026, 11, 7, 10, tzinfo=bj))
    )
    assert peak.compute_cost("deepseek-flash", 1_000_000, 1_000_000, 1_000_000) == pytest.approx(
        10.04
    )
    assert off.compute_cost("deepseek-flash", 1_000_000, 1_000_000, 1_000_000) == pytest.approx(
        5.02
    )
    assert peak.compute_cost("unknown-model", 10, 0, 10) == 0.0
    transport = FakeLlmTransport([build_reply('{"a": 1}')])
    client = DeepSeekClient(
        build_config(prices=prices),
        BeijingClock(dt.datetime(2026, 11, 7, tzinfo=bj)),
        None,
        transport,
    )
    client.fetch_json("s", "u")
    assert client.get_usage()["cost_cny"] == pytest.approx((10 * 2.0 + 5 * 8.0) / 1e6 / 2)


# TC-DSC-005
def test_tc_dsc_005_ledger(clock: FakeClock, tmp_path: Path) -> None:
    client = DeepSeekClient(
        build_config(), clock, None, FakeLlmTransport([build_reply('{"a": 1}')])
    )
    client.fetch_json("s", "u")
    ledger = tmp_path / "meta" / "llm_usage.jsonl"
    client.record_usage(ledger, "pilot")
    client.record_usage(ledger, "pilot again")
    lines = [json.loads(x) for x in ledger.read_text().splitlines()]
    assert [x["label"] for x in lines] == ["pilot", "pilot again"]
    assert (
        lines[0]["calls"] == 1 and lines[0]["model"] == "deepseek-flash" and "cost_cny" in lines[0]
    )
