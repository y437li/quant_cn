"""Which phone alerts are already sent, so each goes out once per episode (plan 22, D-153)."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from quant_cn.core.exceptions import ConfigError


class SentAlertLog:
    """
    Purpose:
        A JSON list of alert keys already sent and still active. `list_new` gives the active
        keys not yet sent; `write` stores the keys active now that were sent (before or now),
        so a condition that clears drops out and is sent again when it comes back.

    Contract:
        Input:
            path: Path  -- the JSON file (in the app data folder); missing = nothing sent
        Output:
            instance; `read_keys`, `list_new(active)`, `write(active, sent)`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `notify` command

    Test cases:
        TC-SAL-001  missing file reads empty; list_new keeps order; write keeps only active
                    keys; a cleared key comes back as new
        TC-SAL-002  a malformed file raises ConfigError
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def read_keys(self) -> set[str]:
        """
        Purpose:
            Keys recorded as sent.

        Contract:
            Input:
                (none)
            Output:
                set[str]  -- empty when the file is missing
            Raises:
                ConfigError  -- the file is not a JSON list of strings
        """
        if not self._path.exists():
            return set()
        try:
            keys = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"sent alert log {self._path} is not JSON: {exc}") from exc
        if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
            raise ConfigError(f"sent alert log {self._path} must be a list of keys")
        return set(keys)

    def list_new(self, active: Iterable[str]) -> list[str]:
        """
        Purpose:
            Active keys not yet sent, in the given order.

        Contract:
            Input:
                active: Iterable[str]
            Output:
                list[str]
            Raises:
                ConfigError  -- as read_keys
        """
        sent = self.read_keys()
        return [k for k in active if k not in sent]

    def write(self, active: Iterable[str], sent: Iterable[str]) -> Path:
        """
        Purpose:
            Store the active keys that have been sent (earlier or in this run).

        Contract:
            Input:
                active: Iterable[str]; sent: Iterable[str]  -- keys sent in this run
            Output:
                Path  -- the file written
            Raises:
                ConfigError  -- as read_keys
        """
        done = self.read_keys() | set(sent)
        keep = sorted(k for k in set(active) if k in done)
        self._path.write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")
        return self._path
