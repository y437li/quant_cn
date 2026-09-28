"""Build the document-side project tables (folders, files, decisions, plans, phases) as frames."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from quant_cn.core.docs.decisions_reader import DecisionsReader
from quant_cn.core.docs.index_reader import IndexInfo, IndexReader
from quant_cn.core.docs.plan_reader import PlanReader
from quant_cn.core.docs.repo_files import RepoFiles

DECISIONS = Path("plans/decisions/DECISIONS.md")
PLANS = Path("plans/execution")
COLUMNS = {
    "folders": ["path", "parent", "name", "purpose", "depth", "has_index"],
    "files": [
        "path",
        "folder",
        "name",
        "purpose",
        "contains",
        "kind",
        "lines",
        "mtime",
        "in_index",
    ],
    "decisions": ["id", "date", "title", "status", "applies_to", "context", "decision"],
    "plans": ["nn", "title", "status", "decisions", "depends_on", "path"],
    "phases": ["plan", "n", "phase", "deliverable", "done_criterion", "depends_on", "status"],
}


class DocTableBuilder:
    """
    Purpose:
        Turn the INDEX.md tree, the files on disk, the decision log and the execution plans into
        the document-side tables of the `project` schema.

    Contract:
        Input:
            repo_root: Path
            files:     RepoFiles
            index:     IndexReader
            decisions: DecisionsReader
            plans:     PlanReader
        Output:
            instance; `build_tables() -> dict[str, DataFrame]` keyed by table name (COLUMNS)
        Raises:
            (none at construction)

    Used by:
        lake.ProjectCatalog  -- document tables
        cli.QuantCnCli       -- injected type or call

    Test cases:
        TC-DTB-001  folders and files carry purposes from their indexes; unindexed files flagged
        TC-DTB-002  decisions, plans and phases built from the governance files
    """

    def __init__(
        self,
        repo_root: Path,
        files: RepoFiles,
        index: IndexReader,
        decisions: DecisionsReader,
        plans: PlanReader,
    ) -> None:
        self._root = repo_root
        self._files = files
        self._index = index
        self._decisions = decisions
        self._plans = plans

    def build_tables(self) -> dict[str, pd.DataFrame]:
        """
        Purpose:
            Build all five document tables.

        Contract:
            Input:
                (none)
            Output:
                dict[str, DataFrame]  -- keys = COLUMNS keys; every frame has exactly its columns
            Raises:
                RuntimeError  -- git listing failed
                OSError       -- unreadable file
        """
        tables = self._build_tree()
        tables["decisions"] = self._build_decisions()
        tables.update(self._build_plans())
        return tables

    def _build_tree(self) -> dict[str, pd.DataFrame]:
        files, folders = self._files.list_files(), self._files.list_folders()
        indexes = {f: self._read_index(f, files) for f in folders}
        folder_rows = []
        for folder in folders:
            parent = indexes.get(folder.parent) if folder != Path(".") else None
            entry = parent.folders.get(folder.name) if parent else None
            folder_rows.append(
                [
                    str(folder),
                    str(folder.parent) if folder != Path(".") else None,
                    folder.name or ".",
                    entry.purpose if entry else None,
                    len(folder.parts),
                    indexes[folder] is not None,
                ]
            )
        file_rows = []
        for rel in files:
            info = indexes.get(rel.parent)
            entry = info.files.get(rel.name) if info else None
            stat = (self._root / rel).stat()
            lines = self._get_line_count(rel)
            file_rows.append(
                [
                    str(rel),
                    str(rel.parent),
                    rel.name,
                    entry.purpose if entry else None,
                    ", ".join(entry.contains) if entry else None,
                    rel.suffix.lstrip(".") or rel.name,
                    lines,
                    pd.Timestamp(stat.st_mtime, unit="s"),
                    entry is not None or rel.name == "INDEX.md",
                ]
            )
        return {
            "folders": pd.DataFrame(folder_rows, columns=COLUMNS["folders"]),
            "files": pd.DataFrame(file_rows, columns=COLUMNS["files"]),
        }

    def _read_index(self, folder: Path, files: list[Path]) -> IndexInfo | None:
        path = folder / "INDEX.md"
        return self._index.read(self._root / path) if path in files else None

    def _get_line_count(self, rel: Path) -> int | None:
        try:
            return len((self._root / rel).read_text(encoding="utf-8").splitlines())
        except (UnicodeDecodeError, OSError):
            return None

    def _build_decisions(self) -> pd.DataFrame:
        path = self._root / DECISIONS
        records = self._decisions.read(path) if path.exists() else []
        rows = [
            [r.id, r.date, r.title, r.status, r.applies_to, r.context, r.decision] for r in records
        ]
        return pd.DataFrame(rows, columns=COLUMNS["decisions"])

    def _build_plans(self) -> dict[str, pd.DataFrame]:
        plan_rows, phase_rows = [], []
        folder = self._root / PLANS
        for path in sorted(folder.glob("[0-9][0-9]_*.md")) if folder.exists() else []:
            plan = self._plans.read(path)
            if plan is None:
                continue
            plan_rows.append(
                [
                    plan.nn,
                    plan.title,
                    plan.status,
                    ", ".join(plan.decisions),
                    plan.depends_on,
                    str(path.relative_to(self._root)),
                ]
            )
            phase_rows += [
                [p.plan, p.n, p.phase, p.deliverable, p.done_criterion, p.depends_on, p.status]
                for p in plan.phases
            ]
        return {
            "plans": pd.DataFrame(plan_rows, columns=COLUMNS["plans"]),
            "phases": pd.DataFrame(phase_rows, columns=COLUMNS["phases"]),
        }
