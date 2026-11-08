"""Read the method verb table from NAMING_CONVENTION §2.1 so the linter never drifts from it."""

from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader


class ConventionReader:
    """
    Purpose:
        Extract the allowed method-name verb prefixes from the naming convention's §2.1 table.

    Contract:
        Input:
            tables: MarkdownTableReader
        Output:
            instance; `read_verbs(path) -> list[str]`
        Raises:
            (none at construction)

    Used by:
        core.docs.ContractLinter  -- injected type or call

    Test cases:
        TC-CR-001  verbs split on "/" with trailing "_" kept for prefixes and bare verbs kept whole
        TC-CR-002  a document without the verb table raises ValueError
    """

    def __init__(self, tables: MarkdownTableReader) -> None:
        self._tables = tables

    def read_verbs(self, path: Path) -> list[str]:
        """
        Purpose:
            Verb prefixes (e.g. "get_") and bare verbs (e.g. "run") in table order.

        Contract:
            Input:
                path: Path  -- NAMING_CONVENTION.md
            Output:
                list[str]  -- non-empty
            Raises:
                ValueError  -- no table with a "Verb prefix" column
                OSError     -- unreadable file
        """
        for table in self._tables.read(path.read_text(encoding="utf-8")):
            if table.header[:1] == ("Verb prefix",):
                return [
                    v
                    for cell in table.get_column("Verb prefix")
                    for v in self._tables.list_ticked(cell)
                ]
        raise ValueError(f"no verb table in {path}")
