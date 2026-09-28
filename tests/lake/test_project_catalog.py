from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.config import Config
from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.code_table_builder import CodeTableBuilder
from quant_cn.core.docs.contract_linter import ContractLinter
from quant_cn.core.docs.decisions_reader import DecisionsReader
from quant_cn.core.docs.doc_table_builder import DocTableBuilder
from quant_cn.core.docs.docstring_parser import DocstringParser
from quant_cn.core.docs.index_reader import IndexReader
from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.plan_reader import PlanReader
from quant_cn.core.docs.registry_reader import RegistryReader
from quant_cn.core.docs.repo_files import RepoFiles
from quant_cn.lake.project_catalog import SCHEMA, VIEWS, ProjectCatalog
from tests.support import MiniLake, SampleRepo

CLASS = 'class Thing:\n    """\n    Purpose:\n        Do it.\n    """\n'
REGISTRY = (
    "## A.\n| Class | Tests |\n|---|---|\n| `Thing` | — |\n\n## B.\n## C.\n## D.\n## E.\n## F.\n"
)
PLAN = """\
# 01 — X

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | a | b | c | — | done |
| 2 | d | e | f | 1 | todo |
"""
FOLDERS = "## Folders\n| Folder | Purpose |\n|---|---|\n"
FILES_TABLE = "## Files\n| File | Purpose | Contains |\n|---|---|---|\n"
FILES = {
    "INDEX.md": "# repo/\n\n" + FOLDERS + "| [`.claude/`](.claude/INDEX.md) | tools |\n"
    "| [`plans/`](plans/INDEX.md) | plans |\n| [`src/`](src/INDEX.md) | code |\n",
    ".claude/INDEX.md": "# .claude/\n\n" + FILES_TABLE + "| `CLASS_REGISTRY.md` | r | |\n",
    ".claude/CLASS_REGISTRY.md": REGISTRY,
    "plans/INDEX.md": "# plans/\n\n" + FOLDERS + "| [`execution/`](execution/INDEX.md) | plans |\n",
    "plans/execution/INDEX.md": "# plans/execution/\n\n" + FILES_TABLE + "| `01_x.md` | x | |\n",
    "plans/execution/01_x.md": PLAN,
    "src/INDEX.md": "# src/\n\n" + FOLDERS + "| [`quant_cn/`](quant_cn/INDEX.md) | pkg |\n",
    "src/quant_cn/INDEX.md": "# src/quant_cn/\n\n"
    + FILES_TABLE
    + "| `__init__.py` | marker | |\n| `thing.py` | a thing | `Thing` |\n",
    "src/quant_cn/__init__.py": "",
    "src/quant_cn/thing.py": CLASS,
}


def build_project(lake: MiniLake, config: Config, root: Path) -> ProjectCatalog:
    tables, scanner = MarkdownTableReader(), CodeScanner()
    code = CodeTableBuilder(root, scanner, DocstringParser(), RegistryReader(tables))
    docs = DocTableBuilder(
        root, RepoFiles(root), IndexReader(tables), DecisionsReader(tables), PlanReader(tables)
    )
    linter = ContractLinter(root)
    return ProjectCatalog(lake.catalog, code, docs, config.datasets, linter, lake.clock)


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    return SampleRepo.build_repo(tmp_path / "repo_sample", FILES)


# TC-PJC-001
def test_tc_pjc_001_tables_and_views(lake: MiniLake, config: Config, repo_root: Path) -> None:
    counts = build_project(lake, config, repo_root).rebuild(run_lint=False)
    for name in [*counts, *VIEWS]:
        assert (
            lake.query.has_view(f"{SCHEMA}.{name}")
            or not lake.query.sql(f"SELECT count(*) AS n FROM {SCHEMA}.{name}").empty
        )
    assert counts["classes"] == 1 and counts["datasets"] == len(config.datasets)


# TC-PJC-002
def test_tc_pjc_002_idempotent(lake: MiniLake, config: Config, repo_root: Path) -> None:
    project = build_project(lake, config, repo_root)
    first = project.rebuild(run_lint=False)
    tree = lake.query.sql(f"SELECT * FROM {SCHEMA}.tree")
    assert project.rebuild(run_lint=False) == first
    assert lake.query.sql(f"SELECT * FROM {SCHEMA}.tree").equals(tree)
    assert tree["entry"].tolist()[:2] == ["./", "  .claude/"]


# TC-PJC-003
def test_tc_pjc_003_stale(lake: MiniLake, config: Config, repo_root: Path) -> None:
    project = build_project(lake, config, repo_root)
    project.rebuild(run_lint=False)
    assert lake.query.sql(f"SELECT * FROM {SCHEMA}.stale").empty
    (repo_root / "src" / "quant_cn" / "extra.py").write_text("class Extra:\n    pass\n")
    project.rebuild(run_lint=False)
    stale = lake.query.sql(f"SELECT kind, item FROM {SCHEMA}.stale ORDER BY kind")
    assert stale.values.tolist() == [["class", "Extra"], ["file", "src/quant_cn/extra.py"]]


# TC-PJC-004
def test_tc_pjc_004_todo(lake: MiniLake, config: Config, repo_root: Path) -> None:
    build_project(lake, config, repo_root).rebuild(run_lint=False)
    todo = lake.query.sql(f"SELECT plan, n, status FROM {SCHEMA}.todo")
    assert todo.values.tolist() == [["01", "2", "todo"]]
