"""Phone alerts by iMessage through this Mac's Messages app (plan 22, D-153)."""

from __future__ import annotations

import logging
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.exceptions import ConfigError, DataSourceError

logger = logging.getLogger(__name__)
FILE = Path("config") / "local.notify.yaml"  # git-ignored by the config/local.*.yaml rule
TRIGGERS = ("volatility", "watchlist", "futures", "macro")
# argv keeps the handle and the text out of the script source (no quoting or injection)
SCRIPT = (
    "on run argv",
    'tell application "Messages"',
    "set acct to 1st account whose service type = iMessage",
    "send (item 2 of argv) to participant (item 1 of argv) of acct",
    "end tell",
    "end run",
)
# a file: item 2 is a POSIX path, coerced to an alias before `send` (a bare `POSIX file` is
# accepted but never delivered, tested 2026-11-13); keep files under ~/Pictures
FILE_SCRIPT = (
    "on run argv",
    "set f to (POSIX file (item 2 of argv)) as alias",
    'tell application "Messages"',
    "set acct to 1st account whose service type = iMessage",
    "send f to participant (item 1 of argv) of acct",
    "end tell",
    "end run",
)
Runner = Callable[[Sequence[str]], "subprocess.CompletedProcess[str]"]


class NotifyRecipient(BaseModel):
    """
    Purpose:
        One person who gets the alerts: a display name and an iMessage handle (phone number
        with country code, or Apple ID e-mail).

    Contract:
        Input:
            name: str (non-empty); handle: str (non-empty)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- empty name or handle, extra keys

    Used by:
        cli.ReportCommands    -- recipients of `notify`
        core.NotifySettings  -- field `recipients`

    Test cases:
        TC-NS-001  example and local files load; empty handle, unknown trigger and duplicate
                   names are refused; a missing file gives no recipients
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    name: str = Field(min_length=1)
    handle: str = Field(min_length=1)


class NotifySettings(BaseModel):
    """
    Purpose:
        Who gets phone alerts and which: recipients, triggers switched on (TRIGGERS) and the
        most alert lines and pictures in one message, from git-ignored
        `config/local.notify.yaml` (phone numbers never enter git; `config/notify.example.yaml`
        is the template).

    Contract:
        Input:
            recipients: list[NotifyRecipient] (unique names); triggers: list[str] in TRIGGERS;
            max_items: int > 0; max_images: int >= 0 (card pictures per message);
            volatility_groups: list[str] -- volatility_monitor groups that may alert (default
            A股 only)
        Output:
            frozen pydantic model; `load(repo_root)`, `find_recipient(name)`
        Raises:
            pydantic.ValidationError  -- unknown trigger, duplicate names, bad values

    Used by:
        cli.ReportCommands  -- `notify` command

    Test cases:
        TC-NS-001  example and local files load; empty handle, unknown trigger and duplicate
                   names are refused; a missing file gives no recipients
        TC-NS-002  find_recipient matches the name case-insensitively; unknown raises
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    recipients: list[NotifyRecipient] = []
    triggers: list[str] = list(TRIGGERS)
    max_items: int = Field(default=8, gt=0)
    max_images: int = Field(default=3, ge=0)
    volatility_groups: list[str] = ["A股"]  # user: China only, not the US VIX (2026-11-13)

    @model_validator(mode="after")
    def _check(self) -> NotifySettings:
        unknown = [t for t in self.triggers if t not in TRIGGERS]
        if unknown:
            raise ValueError(f"unknown triggers {unknown}, expected {TRIGGERS}")
        names = [r.name.lower() for r in self.recipients]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate recipient names: {names}")
        return self

    @classmethod
    def load(cls, repo_root: Path, file: Path = FILE) -> NotifySettings:
        """
        Purpose:
            Read `<repo_root>/<file>` (default config/local.notify.yaml).

        Contract:
            Input:
                repo_root: Path; file: Path relative to repo_root
            Output:
                NotifySettings  -- no recipients when the file is missing
            Raises:
                ConfigError  -- unreadable YAML or invalid content
        """
        path = repo_root / file
        if not path.exists():
            return cls()
        try:
            return cls(**(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid notify settings {path}: {exc}") from exc

    def find_recipient(self, name: str) -> NotifyRecipient:
        """
        Purpose:
            The recipient with this name (case-insensitive).

        Contract:
            Input:
                name: str
            Output:
                NotifyRecipient
            Raises:
                ConfigError  -- no recipient by that name
        """
        for r in self.recipients:
            if r.name.lower() == name.lower():
                return r
        raise ConfigError(f"notify: no recipient named {name!r} in {FILE}")


class MessageSender(ABC):
    """
    Purpose:
        Base of a channel that delivers one short text to one handle.

    Contract:
        Input:
            (none)
        Output:
            instance; `run(handle, text)`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        core.IMessageSender  -- subclass
        cli.ReportCommands   -- `notify` command (typed as the base)

    Test cases:
        TC-IMS-001  (via IMessageSender) the script gets the handle and text as arguments
    """

    @abstractmethod
    def run(self, handle: str, text: str, images: Sequence[Path] = ()) -> None:
        """
        Purpose:
            Deliver `text`, then each image, to `handle`.

        Contract:
            Input:
                handle: str (non-empty); text: str (non-empty);
                images: Sequence[Path] -- existing image files, sent in order after the text
            Output:
                None
            Raises:
                DataSourceError  -- delivery failed
        """


class IMessageSender(MessageSender):
    """
    Purpose:
        Send an iMessage from this Mac's Messages app: `osascript` runs SCRIPT with the handle
        and the text as argv, through the iMessage account, then FILE_SCRIPT once per image.
        Needs Messages signed in and the macOS Automation permission for the calling process;
        Messages may refuse files outside folders it can read (keep images under ~/Pictures).

    Contract:
        Input:
            runner:    Runner | None  -- runs the command; default subprocess.run (capture,
                                         text, timeout_s)
            timeout_s: float > 0
        Output:
            instance; `run`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `notify` command

    Test cases:
        TC-IMS-001  the script gets the handle and text as arguments
        TC-IMS-002  empty handle or text, a non-zero exit and a runner error raise
                    DataSourceError
        TC-IMS-003  images follow the text as file sends; a missing image raises
                    DataSourceError before anything is sent
    """

    def __init__(self, runner: Runner | None = None, timeout_s: float = 30.0) -> None:
        self._runner = runner or self._run
        self._timeout_s = timeout_s

    def run(self, handle: str, text: str, images: Sequence[Path] = ()) -> None:
        """
        Purpose:
            Deliver `text`, then each image, to `handle` by iMessage.

        Contract:
            Input:
                handle: str (non-empty); text: str (non-empty); images: Sequence[Path]
            Output:
                None
            Raises:
                DataSourceError  -- empty input, a missing image, osascript failure or a
                                    non-zero exit
        """
        if not handle.strip() or not text.strip():
            raise DataSourceError("imessage: empty handle or text")
        missing = [str(p) for p in images if not p.is_file()]
        if missing:
            raise DataSourceError(f"imessage: image files missing: {missing}")
        self._execute(SCRIPT, handle, text)
        for image in images:
            self._execute(FILE_SCRIPT, handle, str(image.resolve()))
        logger.info("imessage: sent %d characters and %d images", len(text), len(images))

    def _execute(self, script: Sequence[str], handle: str, item: str) -> None:
        args = ["osascript"] + [a for line in script for a in ("-e", line)] + [handle, item]
        try:
            done = self._runner(args)
        except (OSError, subprocess.SubprocessError) as exc:
            raise DataSourceError(f"imessage: osascript failed: {exc}") from exc
        if done.returncode != 0:
            raise DataSourceError(f"imessage: exit {done.returncode}: {done.stderr.strip()[:200]}")

    def _run(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args), capture_output=True, text=True, timeout=self._timeout_s, check=False
        )
