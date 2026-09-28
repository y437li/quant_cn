from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.name_checker import NameChecker
from quant_cn.core.docs.repo_files import RepoFiles
from tests.support import SampleRepo

VERBS = ["get_", "list_", "run", "is_"]


def run_names(root: Path) -> list[str]:
    return [
        f.message
        for f in NameChecker(root, CodeScanner(), RepoFiles(root).list_files(), VERBS).run()
    ]


# TC-NC-001
def test_tc_nc_001_paths(tmp_path: Path) -> None:
    files = {"Docs/a.txt": "", "b/Bad.txt": "", "b/GOOD_DOC.md": "", "Makefile": ""}
    root = SampleRepo.build_repo(tmp_path / "r", files)
    assert sorted(run_names(root)) == [
        "file name not allowed: Bad.txt",
        "folder not lowercase: Docs",
    ]


# TC-NC-002
def test_tc_nc_002_verbs(tmp_path: Path) -> None:
    src = (
        "import pytest\n\nclass Thing:\n"
        "    @property\n    def size(self) -> int: ...\n"
        "    def __len__(self) -> int: ...\n"
        "    def get_x(self) -> None: ...\n"
        "    def _run_step(self) -> None: ...\n"
        "    def compute(self) -> None: ...\n"
    )
    test = "import pytest\n\n@pytest.fixture\ndef config() -> None: ...\n"
    root = SampleRepo.build_repo(tmp_path / "r", {"src/thing.py": src, "tests/test_thing.py": test})
    assert run_names(root) == ["Thing.compute: no verb prefix"]


# TC-NC-003
def test_tc_nc_003_banned_and_tests(tmp_path: Path) -> None:
    src = "class Thing:\n    def handle_it(self) -> None: ...\n"
    test = "def test_something() -> None: ...\n\ndef test_tc_ab_001_ok() -> None: ...\n"
    root = SampleRepo.build_repo(tmp_path / "r", {"src/thing.py": src, "tests/test_x.py": test})
    assert sorted(run_names(root)) == [
        "Thing.handle_it: no verb prefix",
        "test name test_something",
    ]


# TC-NC-004
def test_tc_nc_004_module_class(tmp_path: Path) -> None:
    files = {
        "src/thing.py": "class Other: ...\n",
        "src/runners.py": "class LocalRunner: ...\n",
        "src/repo_files.py": "class RepoFiles: ...\n",
    }
    root = SampleRepo.build_repo(tmp_path / "r", files)
    assert run_names(root) == ["module thing.py holds no class named Thing or *Thing"]
