from __future__ import annotations

from pathlib import Path

import pandas as pd

from quant_cn.core.docs.decisions_reader import DecisionsReader
from quant_cn.core.docs.doc_table_builder import COLUMNS, DocTableBuilder
from quant_cn.core.docs.index_reader import IndexReader
from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.plan_reader import PlanReader
from quant_cn.core.docs.repo_files import RepoFiles
from tests.support import SampleRepo

ROOT_INDEX = """\
# repo/

## Folders
| Folder | Purpose |
|---|---|
| [`plans/`](plans/INDEX.md) | governance |
"""
DECISIONS = """\
| ID | Date | Title | Status | Where |
|---|---|---|---|---|
| D-001 | d | t | accepted | w |
"""
PLAN = """\
# 01 — X

| | |
|---|---|
| Status | doing |

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | a | b | c | — | todo |
"""
FILES = {
    "INDEX.md": ROOT_INDEX,
    "plans/INDEX.md": "# plans/\n\n## Files\n| File | Purpose | Contains |\n|---|---|---|\n",
    "plans/stray.md": "not indexed\n",
    "plans/decisions/DECISIONS.md": DECISIONS,
    "plans/execution/01_x.md": PLAN,
}


def build_tables(root: Path) -> dict[str, pd.DataFrame]:
    tables = MarkdownTableReader()
    builder = DocTableBuilder(
        root, RepoFiles(root), IndexReader(tables), DecisionsReader(tables), PlanReader(tables)
    )
    return builder.build_tables()


# TC-DTB-001
def test_tc_dtb_001_tree(tmp_path: Path) -> None:
    tables = build_tables(SampleRepo.build_repo(tmp_path / "r", FILES))
    folders = tables["folders"].set_index("path")
    assert folders.loc["plans", "purpose"] == "governance" and bool(
        folders.loc["plans", "has_index"]
    )
    assert not bool(folders.loc["plans/decisions", "has_index"])
    files = tables["files"].set_index("path")
    assert (
        not bool(files.loc["plans/stray.md", "in_index"])
        and int(files.loc["plans/stray.md", "lines"]) == 1
    )


# TC-DTB-002
def test_tc_dtb_002_governance(tmp_path: Path) -> None:
    tables = build_tables(SampleRepo.build_repo(tmp_path / "r", FILES))
    assert all(list(tables[k].columns) == COLUMNS[k] for k in COLUMNS)
    assert tables["decisions"]["id"].tolist() == ["D-001"]
    assert tables["plans"][["nn", "status"]].values.tolist() == [["01", "doing"]]
    assert tables["phases"][["plan", "n", "status"]].values.tolist() == [["01", "1", "todo"]]
