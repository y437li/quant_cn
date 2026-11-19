"""Read research_space/RESEARCH_LOG.md: one row per ad-hoc analysis (plan 02 ph6, D-144)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader

LOG_COLUMNS = ("Date", "Slug", "Question", "Scripts", "Outputs", "Conclusion", "Follow-up")


@dataclass(frozen=True)
class ResearchRun:
    """
    Purpose:
        One ad-hoc analysis as logged: when, what was asked, where its scripts and outputs live,
        what it concluded and what followed from it.

    Contract:
        Input:
            date:       str  -- YYYY-MM-DD
            slug:       str  -- `YYYYMMDD_<topic>`, unique in the log
            question:   str  -- the user's question, in their words
            scripts:    str  -- repo-relative folder (backticks removed)
            outputs:    str  -- lake-relative folder (backticks removed)
            conclusion: str  -- one line
            follow_up:  str  -- plan / decision IDs, or "none"
            line:       int  -- 1-based line of the row in the log
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.ResearchLogReader.read  -- return items

    Test cases:
        TC-RLR-001  rows of the log table become records with backticks stripped and line numbers
    """

    date: str
    slug: str
    question: str
    scripts: str
    outputs: str
    conclusion: str
    follow_up: str
    line: int


class ResearchLogReader:
    """
    Purpose:
        Parse the research log: the first markdown table whose header is LOG_COLUMNS. Other
        tables and prose are ignored.

    Contract:
        Input:
            tables: MarkdownTableReader
        Output:
            instance; `read(path) -> list[ResearchRun]`
        Raises:
            (none at construction)

    Used by:
        core.docs.DocTableBuilder     -- research_runs table
        core.docs.ResearchLogChecker  -- log rules
        core.docs.ContractLinter      -- builds the research checker
        cli.ServiceBuilder            -- injected type or call

    Test cases:
        TC-RLR-001  rows of the log table become records with backticks stripped and line numbers
        TC-RLR-002  a missing file or a file without the log table gives an empty list
    """

    def __init__(self, tables: MarkdownTableReader) -> None:
        self._tables = tables

    def read(self, path: Path) -> list[ResearchRun]:
        """
        Purpose:
            Parse one log file.

        Contract:
            Input:
                path: Path
            Output:
                list[ResearchRun]  -- file order; empty when the file or the table is missing
            Raises:
                OSError  -- unreadable file
        """
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        table = next((t for t in self._tables.read(text) if t.header == LOG_COLUMNS), None)
        if table is None:
            return []
        lines = self._find_row_lines(text, [row[1] for row in table.rows])
        return [
            ResearchRun(
                date=row[0],
                slug=row[1].strip("`"),
                question=row[2],
                scripts=row[3].strip("`"),
                outputs=row[4].strip("`"),
                conclusion=row[5],
                follow_up=row[6],
                line=line,
            )
            for row, line in zip(table.rows, lines, strict=True)
        ]

    @staticmethod
    def _find_row_lines(text: str, slugs: list[str]) -> list[int]:
        rows = text.splitlines()
        out, start = [], 0
        for slug in slugs:
            hit = next((i for i in range(start, len(rows)) if f"| {slug} |" in rows[i]), start)
            out.append(hit + 1)
            start = hit + 1
        return out
