"""Extension point for repository checkers and their Finding records."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Finding:
    """
    Purpose:
        One rule violation at a location, printable as `path:line [rule] message`.

    Contract:
        Input:
            path:    str  -- repo-relative path
            line:    int  -- 1-based line, 0 when the whole file is meant
            rule:    str  -- short rule id, e.g. "contract", "index", "size", "names"
            message: str
        Output:
            frozen, ordered dataclass; `to_text`
        Raises:
            (none)

    Used by:
        core.docs.BaseChecker.run  -- return items
        core.docs.ContractChecker  -- produces findings
        core.docs.IndexChecker     -- produces findings
        core.docs.SizeChecker      -- produces findings
        core.docs.NameChecker      -- produces findings
        core.docs.ContractLinter   -- injected type or call

    Test cases:
        TC-BCH-001  findings sort by path and line and print as path:line [rule] message
    """

    path: str
    line: int
    rule: str
    message: str

    def to_text(self) -> str:
        """
        Purpose:
            One-line human form.

        Contract:
            Input:
                (none)
            Output:
                str  -- "path:line [rule] message"
            Raises:
                (none)
        """
        return f"{self.path}:{self.line} [{self.rule}] {self.message}"


class BaseChecker(ABC):
    """
    Purpose:
        Abstract repository check: inspect the tree, return findings (empty = pass).

    Contract:
        Input:
            (subclass-specific constructor)
        Output:
            instance; `rule`, `run`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        core.docs.ContractChecker  -- subclass
        core.docs.IndexChecker     -- subclass
        core.docs.SizeChecker      -- subclass
        core.docs.NameChecker      -- subclass
        core.docs.ContractLinter   -- injected type or call

    Test cases:
        TC-BCH-001  findings sort by path and line and print as path:line [rule] message
    """

    rule: str = "check"

    @abstractmethod
    def run(self) -> list[Finding]:
        """
        Purpose:
            Run the check over the repository.

        Contract:
            Input:
                (none)
            Output:
                list[Finding]  -- sorted; empty when the tree passes
            Raises:
                OSError, SyntaxError  -- unreadable or unparsable files
        """
