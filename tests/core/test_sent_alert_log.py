"""Contract tests for core.SentAlertLog (plan 22, D-153)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.sent_alert_log import SentAlertLog


# TC-SAL-001
def test_tc_sal_001_episodes(tmp_path: Path) -> None:
    log = SentAlertLog(tmp_path / "sent.json")
    assert log.read_keys() == set() and log.list_new(["b", "a"]) == ["b", "a"]
    log.write(["a", "b"], ["a"])
    assert log.read_keys() == {"a"} and log.list_new(["a", "b"]) == ["b"]
    log.write(["b"], ["b"])  # a cleared
    assert log.read_keys() == {"b"} and log.list_new(["a", "b"]) == ["a"]


# TC-SAL-002
def test_tc_sal_002_malformed(tmp_path: Path) -> None:
    path = tmp_path / "sent.json"
    for body in ("{bad", '{"a": 1}'):
        path.write_text(body, encoding="utf-8")
        with pytest.raises(ConfigError):
            SentAlertLog(path).read_keys()
