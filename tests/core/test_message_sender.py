"""Contract tests for core.NotifySettings and core.IMessageSender (plan 22, D-153)."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.exceptions import ConfigError, DataSourceError
from quant_cn.core.message_sender import IMessageSender, NotifyRecipient, NotifySettings

REPO = Path(__file__).resolve().parents[2]


class FakeRunner:
    """Records commands; answers with a fixed exit code or raises."""

    def __init__(self, code: int = 0, error: Exception | None = None) -> None:
        self.code, self.error, self.calls = code, error, []

    def __call__(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(args))
        if self.error:
            raise self.error
        return subprocess.CompletedProcess(list(args), self.code, "", "not allowed")


# TC-NS-001
def test_tc_ns_001_load_and_refuse(tmp_path: Path) -> None:
    example = NotifySettings.load(REPO, Path("config") / "notify.example.yaml")
    assert example.recipients[0].handle.startswith("+86") and "volatility" in example.triggers
    assert NotifySettings.load(tmp_path).recipients == []
    with pytest.raises(ValidationError):
        NotifyRecipient(name="a", handle="")
    with pytest.raises(ValidationError):
        NotifySettings(triggers=["holdings"])
    with pytest.raises(ValidationError):
        NotifySettings(recipients=[NotifyRecipient(name="A", handle="1"),
                                   NotifyRecipient(name="a", handle="2")])  # fmt: skip
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "local.notify.yaml").write_text("max_items: 0\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        NotifySettings.load(tmp_path)


# TC-NS-002
def test_tc_ns_002_find_recipient() -> None:
    s = NotifySettings(recipients=[NotifyRecipient(name="Ella", handle="+1")])
    assert s.find_recipient("ella").handle == "+1"
    with pytest.raises(ConfigError):
        s.find_recipient("bob")


# TC-IMS-001
def test_tc_ims_001_arguments() -> None:
    runner = FakeRunner()
    IMessageSender(runner).run("+8613800000000", '测试 "quote" ; end tell')
    args = runner.calls[0]
    assert args[0] == "osascript" and args[-2:] == ["+8613800000000", '测试 "quote" ; end tell']
    assert all("+86" not in a for a in args[:-2])  # handle never inside the script


# TC-IMS-002
def test_tc_ims_002_failures() -> None:
    with pytest.raises(DataSourceError):
        IMessageSender(FakeRunner()).run(" ", "x")
    with pytest.raises(DataSourceError):
        IMessageSender(FakeRunner()).run("+1", "")
    with pytest.raises(DataSourceError):
        IMessageSender(FakeRunner(code=1)).run("+1", "x")
    with pytest.raises(DataSourceError):
        IMessageSender(FakeRunner(error=subprocess.TimeoutExpired("osascript", 30))).run("+1", "x")


# TC-IMS-003
def test_tc_ims_003_images(tmp_path: Path) -> None:
    img = tmp_path / "a.png"
    img.write_bytes(b"png")
    runner = FakeRunner()
    IMessageSender(runner).run("+1", "看图", [img])
    assert len(runner.calls) == 2 and runner.calls[1][-1] == str(img.resolve())
    assert any("as alias" in a for a in runner.calls[1]) and runner.calls[0][-1] == "看图"
    empty = FakeRunner()
    with pytest.raises(DataSourceError):
        IMessageSender(empty).run("+1", "x", [tmp_path / "missing.png"])
    assert empty.calls == []
