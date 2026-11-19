"""Contract tests for core.SmallCapWatchSettings (plan 30)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.small_cap_watch_settings import SmallCapWatchSettings, WatchEtf, WatchIndex

REPO = Path(__file__).resolve().parents[2]
IDX: dict[str, Any] = {
    "small_index": WatchIndex(code="000852.SH", name="中证1000"),
    "large_index": WatchIndex(code="000300.SH", name="沪深300"),
    "star_index": WatchIndex(code="000688.SH", name="科创50"),
}
IDX_YAML = (
    'small_index: {code: "000852.SH", name: 中证1000}\n'
    'large_index: {code: "000300.SH", name: 沪深300}\n'
    'star_index: {code: "000688.SH", name: 科创50}\n'
)


def _write(root: Path, name: str, text: str) -> None:
    (root / "config").mkdir(exist_ok=True)
    (root / "config" / name).write_text(text, encoding="utf-8")


# TC-SCS-001
def test_tc_scs_001_repo_file_loads(tmp_path: Path) -> None:
    _write(tmp_path, "smallcap_watch.yaml", (REPO / "config" / "smallcap_watch.yaml").read_text())
    s = SmallCapWatchSettings.load(tmp_path)
    assert s.small_index.code == "000852.SH" and s.star_index.code == "000688.SH"
    assert len(s.etfs) == 11 and {e.code for e in s.etfs if e.own_row} == {
        "512100.SH",
        "588000.SH",
    }


# TC-SCS-002
def test_tc_scs_002_local_overrides_levels(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        SmallCapWatchSettings.load(tmp_path)
    _write(tmp_path, "smallcap_watch.yaml", IDX_YAML + "levels: []\npanic_limit_downs: 400\n")
    _write(tmp_path, "local.smallcap_watch.yaml", "levels: [6075, 5500]\n")
    s = SmallCapWatchSettings.load(tmp_path)
    assert s.levels == [6075.0, 5500.0] and s.panic_limit_downs == 400


# TC-SCS-003
def test_tc_scs_003_refused(tmp_path: Path) -> None:
    etf = WatchEtf(code="512100.SH", name="x")
    with pytest.raises(ValidationError):
        SmallCapWatchSettings(**IDX, etfs=[etf, etf])
    with pytest.raises(ValidationError):
        SmallCapWatchSettings(**IDX, gap_entry_pct=0.7, gap_exit_pct=0.7)
    with pytest.raises(ValidationError):
        SmallCapWatchSettings(**IDX, near_share=1.5)
    with pytest.raises(ValidationError):
        SmallCapWatchSettings(**IDX, levels=[0.0])
    _write(tmp_path, "smallcap_watch.yaml", IDX_YAML + "levels: [1, \n")
    with pytest.raises(ConfigError):
        SmallCapWatchSettings.load(tmp_path)


# TC-SCS-004
def test_tc_scs_004_entry_fields() -> None:
    with pytest.raises(ValidationError):
        SmallCapWatchSettings(**IDX, selloff_drop=-0.03, selloff_near_drop=-0.04)
    with pytest.raises(ValidationError):
        SmallCapWatchSettings(**IDX, entry_since="2026-11-19")
    with pytest.raises(ValidationError):
        SmallCapWatchSettings(**IDX, entry_bought=4)
    s = SmallCapWatchSettings(**IDX)
    assert s.entry_since is None and s.selloff_drop == -0.03 and s.selloff_turnover == 1.3
