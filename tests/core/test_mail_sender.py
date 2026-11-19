"""Contract tests for core.MailSettings and core.MailSender (plan 15 ph7e)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.mail_sender import MailContent, MailSender, MailSettings

CONTENT = MailContent("持仓监测 2026-11-13", "<p>表</p>", "纯文本")
SETTINGS = MailSettings(sender="me@example.com", recipients=["me@example.com", "you@example.com"])


def test_tc_ms_001_settings(tmp_path: Path) -> None:
    """TC-MS-001"""
    assert MailSettings.load(tmp_path).recipients == []
    (tmp_path / "config").mkdir()
    path = tmp_path / "config" / "local.mail.yaml"
    path.write_text("sender: a@example.com\nrecipients: [a@example.com]\n", encoding="utf-8")
    loaded = MailSettings.load(tmp_path)
    assert (loaded.host, loaded.port, loaded.password_env) == (
        "smtp.gmail.com",
        587,
        "GMAIL_APP_PASSWORD",
    )
    path.write_text("sender: a\npassword: nope\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        MailSettings.load(tmp_path)


def test_tc_msn_001_message() -> None:
    """TC-MSN-001"""
    msg = MailSender(SETTINGS, {}).build_message(CONTENT)
    assert msg["Subject"] == CONTENT.subject and msg["To"] == "me@example.com, you@example.com"
    parts = [p.get_content_type() for p in msg.iter_parts()]
    assert parts == ["text/plain", "text/html"]
    assert "表" in msg.get_body(("html",)).get_content()  # type: ignore[union-attr]


def test_tc_msn_002_send() -> None:
    """TC-MSN-002"""
    factory = MagicMock()
    smtp = factory.return_value.__enter__.return_value
    sender = MailSender(SETTINGS, {"GMAIL_APP_PASSWORD": "abcd efgh ijkl mnop"}, cast(Any, factory))
    sender.run(CONTENT)
    factory.assert_called_once_with("smtp.gmail.com", 587)
    assert smtp.starttls.call_count == 1
    smtp.login.assert_called_once_with("me@example.com", "abcdefghijklmnop")
    assert smtp.send_message.call_args.args[0]["Subject"] == CONTENT.subject


def test_tc_msn_003_refuses_before_connecting() -> None:
    """TC-MSN-003"""
    factory = MagicMock()
    with pytest.raises(ConfigError, match="GMAIL_APP_PASSWORD"):
        MailSender(SETTINGS, {}, cast(Any, factory)).run(CONTENT)
    with pytest.raises(ConfigError, match="recipients"):
        MailSender(MailSettings(), {"GMAIL_APP_PASSWORD": "x"}, cast(Any, factory)).run(CONTENT)
    factory.assert_not_called()
