"""Contract tests for core.SectorEarningsSignalSettings (plan 35, D-172)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.sector_earnings_signal_settings import SectorEarningsSignalSettings

ROOT = Path(__file__).resolve().parents[2]


# TC-SES-001
def test_tc_ses_001_load_and_refuse(tmp_path: Path) -> None:
    s = SectorEarningsSignalSettings.load(ROOT)
    assert (s.pre_min, s.react_max, s.rally_min, s.report_share) == (15.0, 1.0, 20.0, 0.8)
    assert (s.top_decile, s.min_events, s.fwd_windows) == (8, 5, [60, 120])
    assert SectorEarningsSignalSettings.load(tmp_path) == SectorEarningsSignalSettings()
    with pytest.raises(ValidationError):
        SectorEarningsSignalSettings(report_share=0)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "sector_earnings_signal.yaml").write_text("unknown: 1\n")
    with pytest.raises(ConfigError):
        SectorEarningsSignalSettings.load(tmp_path)
