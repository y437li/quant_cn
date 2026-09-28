"""Read `.claude/CLASS_REGISTRY.md` (CODING_STANDARD §5, D-013) into typed sections."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader

_BLOCK = re.compile(r"^### `(\w+)` — `([\w.]+)` \(L(\d)\)", re.MULTILINE)


@dataclass(frozen=True)
class RegistryInfo:
    """
    Purpose:
        The registry's content as sets and maps the linter can compare with code.

    Contract:
        Input:
            index:      dict[str, dict[str, str]]  -- section A rows by class (column -> cell)
            methods:    dict[str, list[str]]       -- section B method names per class block
            abstract:   set[str]                   -- section C classes
            exceptions: set[str]                   -- section D classes
            schemas:    set[str]                   -- section E schema names
            method_rows: dict[str, list[dict[str, str]]]  -- section B method rows (column -> cell)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.RegistryReader.read  -- return type
        core.docs.ContractChecker      -- registry parity
        core.docs.CodeTableBuilder     -- injected type or call

    Test cases:
        TC-RR-001  sections A-E parsed; template block ignored
    """

    index: dict[str, dict[str, str]] = field(default_factory=dict)
    methods: dict[str, list[str]] = field(default_factory=dict)
    abstract: set[str] = field(default_factory=set)
    exceptions: set[str] = field(default_factory=set)
    schemas: set[str] = field(default_factory=set)
    method_rows: dict[str, list[dict[str, str]]] = field(default_factory=dict)


class RegistryReader:
    """
    Purpose:
        Parse CLASS_REGISTRY.md: section A index, section B detail blocks and their method
        tables, and the class/schema names of sections C, D, E.

    Contract:
        Input:
            tables: MarkdownTableReader
        Output:
            instance; `read(path) -> RegistryInfo`
        Raises:
            (none at construction)

    Used by:
        core.docs.ContractChecker   -- registry row, block and method parity
        core.docs.ContractLinter    -- injected type or call
        core.docs.CodeTableBuilder  -- injected type or call
        cli.QuantCnCli              -- injected type or call

    Test cases:
        TC-RR-001  sections A-E parsed; template block ignored
        TC-RR-002  method names strip "(private)" markers and argument lists
        TC-RR-003  full method rows are kept per class
    """

    def __init__(self, tables: MarkdownTableReader) -> None:
        self._tables = tables

    def read(self, path: Path) -> RegistryInfo:
        """
        Purpose:
            Parse the registry file.

        Contract:
            Input:
                path: Path  -- CLASS_REGISTRY.md
            Output:
                RegistryInfo
            Raises:
                OSError  -- unreadable file
        """
        text = path.read_text(encoding="utf-8")
        info = RegistryInfo()
        for table in self._tables.read(self._get_section(text, "## A.", "## B.")):
            for row in table.rows:
                name = self._parse_name(row[0])
                if name:
                    info.index[name] = dict(zip(table.header, row, strict=True))
        rows = self._read_blocks(self._get_section(text, "## B.", "## C."))
        info.method_rows.update(rows)
        info.methods.update(
            {cls: [self._parse_name(r["Method"]) for r in items] for cls, items in rows.items()}
        )
        info.abstract.update(self._list_names(self._get_section(text, "## C.", "## D.")))
        info.exceptions.update(self._list_names(self._get_section(text, "## D.", "## E.")))
        info.schemas.update(self._list_names(self._get_section(text, "## E.", "## F.")))
        return info

    def _read_blocks(self, text: str) -> dict[str, list[dict[str, str]]]:
        blocks: dict[str, list[dict[str, str]]] = {}
        starts = list(_BLOCK.finditer(text))
        for i, match in enumerate(starts):
            end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
            rows: list[dict[str, str]] = []
            for table in self._tables.read(text[match.end() : end]):
                if table.header[:1] == ("Method",):
                    rows += [dict(zip(table.header, r, strict=True)) for r in table.rows]
            blocks[match.group(1)] = [r for r in rows if self._parse_name(r["Method"])]
        return blocks

    def _list_names(self, text: str) -> set[str]:
        return {self._parse_name(row[0]) for t in self._tables.read(text) for row in t.rows} - {""}

    def _parse_name(self, cell: str) -> str:
        ticked = self._tables.list_ticked(cell)
        return ticked[0].split("(")[0].strip() if ticked else ""

    @staticmethod
    def _get_section(text: str, start: str, end: str) -> str:
        i = text.find(start)
        if i < 0:
            return ""
        j = text.find(end, i + len(start))
        return text[i : j if j >= 0 else len(text)]
