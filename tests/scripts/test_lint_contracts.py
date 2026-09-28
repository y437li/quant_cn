from __future__ import annotations

from pathlib import Path

import pytest
from scripts.lint_contracts import LintContractsCli

from tests.support import SampleRepo


# TC-LCC-001
def test_tc_lcc_001_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    clean = SampleRepo.build_repo(tmp_path / "clean", {"src/ok.py": "x = 1\n"})
    assert LintContractsCli(clean).run(["--size"]) == 0
    dirty = SampleRepo.build_repo(tmp_path / "dirty", {"src/big.py": "x = 1\n" * 601})
    assert LintContractsCli(dirty).run(["--size"]) == 1
    out = capsys.readouterr().out
    assert "src/big.py:0 [size] file 601 lines > 600" in out and "(size): 1 finding(s)" in out
