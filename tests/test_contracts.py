from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.docs.contract_linter import ContractLinter
from tests.support import SampleRepo

REPO = Path(__file__).resolve().parents[1]


# TC-CTL-001
def test_tc_ctl_001_repository_passes() -> None:
    findings = ContractLinter(REPO).run()
    assert [f.to_text() for f in findings] == []


# TC-CTL-002
def test_tc_ctl_002_group_selection(tmp_path: Path) -> None:
    root = SampleRepo.build_repo(tmp_path / "r", {"src/big.py": "x = 1\n" * 601})
    with pytest.raises(ValueError):
        ContractLinter(root).run(["nope"])
    assert {f.rule for f in ContractLinter(root).run(["size"])} == {"size"}
