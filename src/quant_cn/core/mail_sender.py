"""Send the morning report e-mails over SMTP with STARTTLS (plan 15 ph7e, D-136)."""

from __future__ import annotations

import smtplib
import ssl
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "local.mail.yaml"  # git-ignored by the config/local.*.yaml rule


class MailSettings(BaseModel):
    """
    Purpose:
        Where the morning report goes: SMTP host and port, sender, recipients and the name of
        the environment variable that holds the app password (never the password itself).

    Contract:
        Input:
            host:         str        -- default smtp.gmail.com
            port:         int        -- default 587 (STARTTLS)
            sender:       str        -- From address, also the SMTP login
            recipients:   list[str]  -- at least one to send
            password_env: str        -- default GMAIL_APP_PASSWORD (read from .env)
        Output:
            frozen pydantic model; `load(repo_root)` -> MailSettings (empty when no file)
        Raises:
            ConfigError  -- unreadable YAML or invalid content

    Used by:
        core.MailSender      -- connection and addresses
        cli.ReportCommands   -- loads it for `morning-report`

    Test cases:
        TC-MS-001  the file loads; missing file gives empty recipients; extra keys refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str = "smtp.gmail.com"
    port: int = Field(default=587, gt=0)
    sender: str = ""
    recipients: list[str] = Field(default_factory=list)
    password_env: str = "GMAIL_APP_PASSWORD"

    @classmethod
    def load(cls, repo_root: Path) -> MailSettings:
        """
        Purpose:
            Read `<repo_root>/config/local.mail.yaml`.

        Contract:
            Input:
                repo_root: Path
            Output:
                MailSettings  -- defaults with no recipients when the file does not exist
            Raises:
                ConfigError  -- unreadable YAML or invalid content
        """
        path = repo_root / FILE
        if not path.exists():
            return cls()
        try:
            return cls(**(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid mail settings {path}: {exc}") from exc


@dataclass(frozen=True)
class MailContent:
    """
    Purpose:
        One rendered e-mail: subject, HTML body and the plain-text alternative.

    Contract:
        Input:
            subject: str; html: str; text: str
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.MailSender.run                   -- what to send
        visualization.MonitorReportRenderer   -- render output
        visualization.OpportunityReportRenderer  -- render output
        visualization.MorningReportBuilder    -- build output

    Test cases:
        TC-MSN-001  a multipart message carries the subject, plain text and HTML
    """

    subject: str
    html: str
    text: str


class MailSender:
    """
    Purpose:
        Build a multipart (plain + HTML) message and send it through SMTP with STARTTLS and
        login. The password comes from the environment variable named in the settings; it is
        checked before connecting and never logged or echoed.

    Contract:
        Input:
            settings:     MailSettings
            env:          Mapping[str, str]   -- environment (os.environ in production)
            smtp_factory: Callable[[str, int], smtplib.SMTP]  -- injectable for tests
        Output:
            instance; `build_message(content)` -> EmailMessage, `run(content)` -> None (send)
        Raises:
            (none at construction)

    Used by:
        visualization.MorningReportBuilder  -- sends the two daily e-mails
        cli.ReportCommands                  -- injected type or call

    Test cases:
        TC-MSN-001  a multipart message carries the subject, plain text and HTML
        TC-MSN-002  run: STARTTLS, login with the env password (spaces removed), one sendmail
        TC-MSN-003  no password or no recipients -> ConfigError before any connection
    """

    def __init__(
        self,
        settings: MailSettings,
        env: Mapping[str, str],
        smtp_factory: Callable[[str, int], smtplib.SMTP] = smtplib.SMTP,
    ) -> None:
        self._settings = settings
        self._env = env
        self._smtp_factory = smtp_factory

    def build_message(self, content: MailContent) -> EmailMessage:
        """
        Purpose:
            The message as it will be sent.

        Contract:
            Input:
                content: MailContent
            Output:
                EmailMessage  -- From, To, Subject; text/plain then text/html alternative
            Raises:
                (none)
        """
        msg = EmailMessage()
        msg["Subject"] = content.subject
        msg["From"] = self._settings.sender
        msg["To"] = ", ".join(self._settings.recipients)
        msg.set_content(content.text)
        msg.add_alternative(content.html, subtype="html")
        return msg

    def run(self, content: MailContent) -> None:
        """
        Purpose:
            Send one e-mail to every recipient.

        Contract:
            Input:
                content: MailContent
            Output:
                None
            Raises:
                ConfigError         -- no sender / recipients, or the password variable is empty
                smtplib.SMTPException, OSError  -- delivery failure
        """
        password = self._env.get(self._settings.password_env, "").replace(" ", "")
        if not self._settings.sender or not self._settings.recipients:
            raise ConfigError("mail: sender and recipients must be set in config/local.mail.yaml")
        if not password:
            raise ConfigError(f"mail: {self._settings.password_env} is not set (see .env)")
        message = self.build_message(content)
        with self._smtp_factory(self._settings.host, self._settings.port) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(self._settings.sender, password)
            smtp.send_message(message)
