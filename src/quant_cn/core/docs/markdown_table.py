"""Read pipe tables out of governance markdown (INDEX.md, CLASS_REGISTRY.md, conventions)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_TICKS = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class MarkdownTable:
    """
    Purpose:
        One pipe table with the heading it sits under.

    Contract:
        Input:
            heading: str                  -- nearest preceding markdown heading text ("" if none)
            header:  tuple[str, ...]      -- column names
            rows:    tuple[tuple[str, ...], ...]  -- cell text, stripped, padded to header width
        Output:
            frozen dataclass; `get_column`
        Raises:
            (none)

    Used by:
        core.docs.MarkdownTableReader.read  -- return items

    Test cases:
        TC-MTR-001  tables are read with their headings and cells
    """

    heading: str
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def get_column(self, name: str) -> list[str]:
        """
        Purpose:
            All cells of one column.

        Contract:
            Input:
                name: str  -- a header name
            Output:
                list[str]  -- one cell per row
            Raises:
                KeyError  -- no such column
        """
        if name not in self.header:
            raise KeyError(name)
        i = self.header.index(name)
        return [row[i] for row in self.rows]


class MarkdownTableReader:
    """
    Purpose:
        Extract every pipe table from markdown text, and backticked names from a cell.

    Contract:
        Input:
            (none)
        Output:
            instance; `read`, `list_ticked`
        Raises:
            (none)

    Used by:
        core.docs.IndexReader       -- parses INDEX.md
        core.docs.RegistryReader    -- parses CLASS_REGISTRY.md
        core.docs.ConventionReader  -- parses NAMING_CONVENTION.md
        core.docs.ContractLinter    -- injected type or call

    Test cases:
        TC-MTR-001  tables are read with their headings and cells
        TC-MTR-002  escaped pipes stay inside a cell; separator rows are skipped
        TC-MTR-003  list_ticked returns backticked names in order
    """

    def read(self, text: str) -> list[MarkdownTable]:
        """
        Purpose:
            All tables in document order.

        Contract:
            Input:
                text: str  -- markdown
            Output:
                list[MarkdownTable]
            Raises:
                (none)
        """
        tables: list[MarkdownTable] = []
        heading = ""
        block: list[list[str]] = []
        for line in [*text.splitlines(), ""]:
            stripped = line.strip()
            if stripped.startswith("|"):
                block.append(self._parse_row(stripped))
                continue
            if block:
                tables.append(self._build_table(heading, block))
                block = []
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
        return [t for t in tables if t.header]

    def list_ticked(self, cell: str) -> list[str]:
        """
        Purpose:
            Names written in backticks inside a cell.

        Contract:
            Input:
                cell: str
            Output:
                list[str]  -- in order of appearance
            Raises:
                (none)
        """
        return _TICKS.findall(cell)

    def _parse_row(self, line: str) -> list[str]:
        cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))
        return [c.strip().replace("\\|", "|") for c in cells]

    def _build_table(self, heading: str, block: list[list[str]]) -> MarkdownTable:
        header = tuple(block[0])
        body = [r for r in block[1:] if not all(set(c) <= set("-: ") for c in r)]
        width = len(header)
        rows = tuple(tuple((r + [""] * width)[:width]) for r in body)
        return MarkdownTable(heading, header, rows)
