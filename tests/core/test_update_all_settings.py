"""Contract tests for core.UpdateAllSettings (plan 38)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.update_all_settings import UpdateAllSettings, UpdateStep

REPO = Path(__file__).resolve().parents[2]


def _build(*steps: tuple[str, list[str]]) -> UpdateAllSettings:
    return UpdateAllSettings(steps=[UpdateStep(name=n, target=n, needs=d) for n, d in steps])


# TC-UAS-001
def test_tc_uas_001_repo_file_loads() -> None:
    s = UpdateAllSettings.load(REPO)
    assert s.steps[0].name == "market-data" and len(s.steps) >= 15
    assert s.find_missing_targets(REPO / "Makefile") == []
    assert _build(("nope-target", [])).find_missing_targets(REPO / "Makefile") == ["nope-target"]


# TC-UAS-002
def test_tc_uas_002_validation(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        _build(("a", []), ("a", []))
    with pytest.raises(ValidationError):
        _build(("a", ["x"]))
    with pytest.raises(ValidationError):
        _build(("a", ["b"]), ("b", []))
    with pytest.raises(ConfigError):
        UpdateAllSettings.load(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "update_all.yaml").write_text("steps: [{name: a}]", encoding="utf-8")
    with pytest.raises(ConfigError):
        UpdateAllSettings.load(tmp_path)


# TC-UAS-003
def test_tc_uas_003_select_and_timeout() -> None:
    s = _build(("a", []), ("b", ["a"]), ("c", []))
    assert [x.name for x in s.list_steps()] == ["a", "b", "c"]
    assert [x.name for x in s.list_steps(only=["c", "a"])] == ["a", "c"]
    assert [x.name for x in s.list_steps(start="b")] == ["b", "c"]
    with pytest.raises(ConfigError):
        s.list_steps(only=["z"])
    assert s.get_timeout_s(s.steps[0]) == 1800
    assert s.get_timeout_s(UpdateStep(name="x", target="x", timeout_min=2)) == 120
