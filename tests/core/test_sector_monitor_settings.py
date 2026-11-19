"""Contract tests for core.SectorMonitorSettings (plan 31 ph4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.sector_monitor_settings import SectorMonitorSettings

REPO = Path(__file__).resolve().parents[2]


# TC-SMS-001
def test_tc_sms_001_repo_config_loads() -> None:
    settings = SectorMonitorSettings.load(REPO)
    assert [s.key for s in settings.sectors] == ["real_estate", "games"]
    assert all(len(s.companies) == 6 for s in settings.sectors)
    assert len(settings.tiers["一线"]) == 4 and len(settings.tiers["二线"]) == 31


# TC-SMS-002
def test_tc_sms_002_invalid(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        SectorMonitorSettings.load(tmp_path)  # no file
    (tmp_path / "config").mkdir()
    text = (REPO / "config" / "sector_monitors.yaml").read_text(encoding="utf-8")
    (tmp_path / "config" / "sector_monitors.yaml").write_text(
        text.replace("realized_vol]", "bogus_metric]", 1), encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="bogus_metric"):
        SectorMonitorSettings.load(tmp_path)
