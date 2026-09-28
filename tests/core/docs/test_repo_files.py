from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quant_cn.core.docs.repo_files import RepoFiles
from tests.support import SampleRepo

FILES = {".gitignore": "*.tmp\n", "a/b.py": "x = 1\n", "a/c.tmp": "", "d.md": "# d\n"}


# TC-RF-001
def test_tc_rf_001_visible_files(tmp_path: Path) -> None:
    root = SampleRepo.build_repo(tmp_path / "r", FILES)
    subprocess.run(["git", "add", "d.md"], cwd=root, check=True)
    (root / "d.md").unlink()
    assert RepoFiles(root).list_files() == [Path(".gitignore"), Path("a/b.py")]


# TC-RF-002
def test_tc_rf_002_folders(tmp_path: Path) -> None:
    root = SampleRepo.build_repo(tmp_path / "r", {"x/y/z.py": ""})
    assert RepoFiles(root).list_folders() == [Path("."), Path("x"), Path("x/y")]


# TC-RF-003
def test_tc_rf_003_not_a_repo(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        RepoFiles(tmp_path).list_files()
