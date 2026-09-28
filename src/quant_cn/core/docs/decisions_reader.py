"""Read the append-only decision log (plans/decisions/DECISIONS.md) into records."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader

_DETAIL = re.compile(r"^### (D-\d{3})\b", re.MULTILINE)
_BULLET = re.compile(r"^- (Context|Decision)(?: \(proposed\))?:\s*(.*)$", re.MULTILINE)


@dataclass(frozen=True)
class DecisionRecord:
    """
    Purpose:
        One decision: its log-table row joined with the Context and Decision bullets of its block.

    Contract:
        Input:
            id, date, title, status, applies_to: str  -- log-table cells
            context, decision: str                   -- detail bullets ("" if the block is missing)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.DecisionsReader  -- return items

    Test cases:
        TC-DR-001  table rows joined with detail bullets
    """

    id: str
    date: str
    title: str
    status: str
    applies_to: str
    context: str = ""
    decision: str = ""


class DecisionsReader:
    """
    Purpose:
        Parse DECISIONS.md: the ID/Date/Title/Status/Where table plus `### D-NNN` detail blocks.

    Contract:
        Input:
            tables: MarkdownTableReader
        Output:
            instance; `read(path) -> list[DecisionRecord]`
        Raises:
            (none at construction)

    Used by:
        core.docs.DocTableBuilder  -- decisions table
        cli.QuantCnCli             -- injected type or call

    Test cases:
        TC-DR-001  table rows joined with detail bullets
        TC-DR-002  a decision without a detail block keeps empty context and decision
    """

    def __init__(self, tables: MarkdownTableReader) -> None:
        self._tables = tables

    def read(self, path: Path) -> list[DecisionRecord]:
        """
        Purpose:
            All decisions in table order.

        Contract:
            Input:
                path: Path  -- DECISIONS.md
            Output:
                list[DecisionRecord]
            Raises:
                OSError  -- unreadable file
        """
        text = path.read_text(encoding="utf-8")
        details = self._read_details(text)
        out: list[DecisionRecord] = []
        for table in self._tables.read(text):
            if table.header[:1] != ("ID",):
                continue
            for row in table.rows:
                context, decision = details.get(row[0], ("", ""))
                cells = (list(row) + [""] * 5)[:5]
                record = DecisionRecord(
                    id=cells[0],
                    date=cells[1],
                    title=cells[2],
                    status=cells[3],
                    applies_to=cells[4],
                    context=context,
                    decision=decision,
                )
                out.append(record)
        return out

    def _read_details(self, text: str) -> dict[str, tuple[str, str]]:
        starts = list(_DETAIL.finditer(text))
        out: dict[str, tuple[str, str]] = {}
        for i, match in enumerate(starts):
            end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
            bullets = dict(_BULLET.findall(text[match.end() : end]))
            out[match.group(1)] = (bullets.get("Context", ""), bullets.get("Decision", ""))
        return out
