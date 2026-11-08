from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.repo_files import RepoFiles
from quant_cn.core.docs.size_checker import SizeChecker
from tests.support import SampleRepo


def run_sizes(root: Path) -> list[str]:
    return [f.message for f in SizeChecker(root, CodeScanner(), RepoFiles(root).list_files()).run()]


# TC-SC-001
def test_tc_sc_001_code_limits(tmp_path: Path) -> None:
    method = "    def run_long(self) -> None:\n" + "        x = 1\n" * 55
    klass = (
        "class Big:\n"
        + method
        + "".join(f"    def run_{i}(self) -> None:\n        pass\n" for i in range(130))
    )
    root = SampleRepo.build_repo(tmp_path / "r", {"src/big.py": klass + "\n" * 300})
    messages = run_sizes(root)
    assert len(messages) == 3
    assert any(m.startswith("file ") for m in messages) and any(
        m.startswith("class Big") for m in messages
    )
    assert any(m.startswith("run_long") for m in messages)


# TC-SC-002
def test_tc_sc_002_docs(tmp_path: Path) -> None:
    long = "line\n" * 301
    files = {
        "x/INDEX.md": long,
        "plans/execution/01_x.md": long,
        "plans/execution/ROADMAP.md": long,
        "notes.md": long,
    }
    root = SampleRepo.build_repo(tmp_path / "r", files)
    found = SizeChecker(root, CodeScanner(), RepoFiles(root).list_files()).run()
    assert sorted(f.path for f in found) == ["plans/execution/01_x.md", "x/INDEX.md"]
