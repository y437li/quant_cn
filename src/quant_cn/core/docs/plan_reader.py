"""Read an execution plan (plans/execution/NN_<slug>.md) into a plan record with its phases."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader

_TITLE = re.compile(r"^#\s+(\d{2})\s+[—-]+\s+(.+)$", re.MULTILINE)
_DECISION = re.compile(r"D-\d{3}")
_PHASE_COLUMNS = ("#", "Phase", "Deliverable", "Done criterion", "Depends on", "Status")


@dataclass(frozen=True)
class PhaseRecord:
    """
    Purpose:
        One row of a plan's Phases table.

    Contract:
        Input:
            plan: str; n: str; phase, deliverable, done_criterion, depends_on, status: str
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.PlanRecord       -- `phases`
        core.docs.PlanReader.read  -- builds records

    Test cases:
        TC-PR-001  header, decisions and phases are read from a plan file
    """

    plan: str
    n: str
    phase: str
    deliverable: str
    done_criterion: str
    depends_on: str
    status: str


@dataclass(frozen=True)
class PlanRecord:
    """
    Purpose:
        One execution plan: number, title, header fields and phases.

    Contract:
        Input:
            nn: str; title: str; status: str; decisions: tuple[str, ...]; depends_on: str
            phases: tuple[PhaseRecord, ...]
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.PlanReader.read  -- return type

    Test cases:
        TC-PR-001  header, decisions and phases are read from a plan file
    """

    nn: str
    title: str
    status: str
    decisions: tuple[str, ...]
    depends_on: str
    phases: tuple[PhaseRecord, ...]


class PlanReader:
    """
    Purpose:
        Parse a plan file: `# NN — Title`, the two-column header table (Status, Decisions,
        Depends on plans) and the Phases table.

    Contract:
        Input:
            tables: MarkdownTableReader
        Output:
            instance; `read(path) -> PlanRecord | None`
        Raises:
            (none at construction)

    Used by:
        core.docs.DocTableBuilder  -- plans and phases tables
        cli.QuantCnCli             -- injected type or call

    Test cases:
        TC-PR-001  header, decisions and phases are read from a plan file
        TC-PR-002  a markdown file without a plan title returns None
    """

    def __init__(self, tables: MarkdownTableReader) -> None:
        self._tables = tables

    def read(self, path: Path) -> PlanRecord | None:
        """
        Purpose:
            Parse one plan file.

        Contract:
            Input:
                path: Path
            Output:
                PlanRecord | None  -- None when the file has no `# NN — Title` heading
            Raises:
                OSError  -- unreadable file
        """
        text = path.read_text(encoding="utf-8")
        title = _TITLE.search(text)
        if not title:
            return None
        nn = title.group(1)
        header: dict[str, str] = {}
        phases: list[PhaseRecord] = []
        for table in self._tables.read(text):
            if table.header == ("", "") or table.header[:1] == ("",):
                header.update({row[0]: row[1] for row in table.rows if len(row) > 1})
            elif table.header[: len(_PHASE_COLUMNS)] == _PHASE_COLUMNS:
                phases += [PhaseRecord(nn, *row[:6]) for row in table.rows]
        return PlanRecord(
            nn=nn,
            title=title.group(2).strip(),
            status=header.get("Status", ""),
            decisions=tuple(_DECISION.findall(header.get("Decisions", ""))),
            depends_on=header.get("Depends on plans", ""),
            phases=tuple(phases),
        )
