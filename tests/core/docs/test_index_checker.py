from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.index_checker import IndexChecker
from quant_cn.core.docs.index_reader import IndexReader
from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.repo_files import RepoFiles
from tests.support import SampleRepo

ROOT_INDEX = (
    "# repo/\n\n## Folders\n| Folder | Purpose |\n|---|---|\n| [`pkg/`](pkg/INDEX.md) | code |\n"
)
PKG_INDEX = (
    "# pkg/\n\n## Files\n| File | Purpose | Contains |\n|---|---|---|\n"
    "| `mod.py` | thing | `Thing` |\n"
)


def run_index(root: Path) -> list[str]:
    checker = IndexChecker(root, RepoFiles(root), IndexReader(MarkdownTableReader()), CodeScanner())
    return [f.message for f in checker.run()]


# TC-IC-001
def test_tc_ic_001_missing_index(tmp_path: Path) -> None:
    root = SampleRepo.build_repo(
        tmp_path / "r", {"INDEX.md": ROOT_INDEX, "pkg/mod.py": "class Thing: ...\n"}
    )
    assert run_index(root) == ["missing INDEX.md"]


# TC-IC-002
def test_tc_ic_002_rows_vs_disk(tmp_path: Path) -> None:
    files = {
        "INDEX.md": ROOT_INDEX
        + "\n## Files\n| File | Purpose | Contains |\n|---|---|---|\n| `gone.txt` | x | |\n",
        "pkg/INDEX.md": PKG_INDEX,
        "pkg/mod.py": "class Thing: ...\n",
        "extra.txt": "",
    }
    root = SampleRepo.build_repo(tmp_path / "r", files)
    assert sorted(run_index(root)) == [
        "file not listed: extra.txt",
        "listed file missing: gone.txt",
    ]


# TC-IC-003
def test_tc_ic_003_contains(tmp_path: Path) -> None:
    files = {"INDEX.md": ROOT_INDEX, "pkg/INDEX.md": PKG_INDEX, "pkg/mod.py": "class Other: ...\n"}
    root = SampleRepo.build_repo(tmp_path / "r", files)
    assert run_index(root) == ["mod.py Contains ['Thing'] != code ['Other']"]


# TC-IC-004
def test_tc_ic_004_consistent(tmp_path: Path) -> None:
    files = {"INDEX.md": ROOT_INDEX, "pkg/INDEX.md": PKG_INDEX, "pkg/mod.py": "class Thing: ...\n"}
    assert run_index(SampleRepo.build_repo(tmp_path / "r", files)) == []
