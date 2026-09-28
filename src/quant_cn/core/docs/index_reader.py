"""Read a folder `INDEX.md` (CODING_STANDARD §5.1) into folder and file entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader

_CONTAINS = 2


@dataclass(frozen=True)
class IndexEntry:
    """
    Purpose:
        One row of an INDEX.md table: a subfolder or a file with its purpose and named contents.

    Contract:
        Input:
            name:     str         -- folder name without "/" or file name
            purpose:  str
            contains: tuple[str]  -- backticked names in the Contains cell (files only)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.IndexInfo         -- folder and file maps
        core.docs.IndexReader.read  -- builds entries

    Test cases:
        TC-IR-001  folder and file rows parsed with contains names
    """

    name: str
    purpose: str
    contains: tuple[str, ...] = ()


@dataclass(frozen=True)
class IndexInfo:
    """
    Purpose:
        Parsed INDEX.md: title line, subfolder entries, file entries.

    Contract:
        Input:
            title:   str                     -- first heading, e.g. "src/quant_cn/lake/"
            folders: dict[str, IndexEntry]   -- by folder name
            files:   dict[str, IndexEntry]   -- by file name
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.IndexReader.read  -- return type
        core.docs.IndexChecker      -- compares with disk and code

    Test cases:
        TC-IR-001  folder and file rows parsed with contains names
    """

    title: str
    folders: dict[str, IndexEntry] = field(default_factory=dict)
    files: dict[str, IndexEntry] = field(default_factory=dict)


class IndexReader:
    """
    Purpose:
        Parse the fixed INDEX.md format: `## Folders` (Folder, Purpose) and `## Files`
        (File, Purpose, Contains) tables.

    Contract:
        Input:
            tables: MarkdownTableReader
        Output:
            instance; `read(path) -> IndexInfo`
        Raises:
            (none at construction)

    Used by:
        core.docs.IndexChecker    -- one read per folder
        core.docs.ContractLinter  -- injected type or call

    Test cases:
        TC-IR-001  folder and file rows parsed with contains names
        TC-IR-002  a missing table yields an empty map; title taken from the first heading
    """

    def __init__(self, tables: MarkdownTableReader) -> None:
        self._tables = tables

    def read(self, path: Path) -> IndexInfo:
        """
        Purpose:
            Parse one INDEX.md.

        Contract:
            Input:
                path: Path  -- an existing INDEX.md
            Output:
                IndexInfo
            Raises:
                OSError  -- unreadable file
        """
        text = path.read_text(encoding="utf-8")
        title = next((ln.lstrip("#").strip() for ln in text.splitlines() if ln.startswith("#")), "")
        folders: dict[str, IndexEntry] = {}
        files: dict[str, IndexEntry] = {}
        for table in self._tables.read(text):
            if table.header[:1] == ("Folder",):
                for row in table.rows:
                    name = self._get_first_ticked(row[0]).rstrip("/")
                    folders[name] = IndexEntry(name, row[1] if len(row) > 1 else "")
            elif table.header[:1] == ("File",):
                for row in table.rows:
                    name = self._get_first_ticked(row[0])
                    contains = (
                        tuple(self._tables.list_ticked(row[_CONTAINS]))
                        if len(row) > _CONTAINS
                        else ()
                    )
                    files[name] = IndexEntry(name, row[1] if len(row) > 1 else "", contains)
        return IndexInfo(title, folders, files)

    def _get_first_ticked(self, cell: str) -> str:
        names = self._tables.list_ticked(cell)
        return names[0] if names else cell.strip()
