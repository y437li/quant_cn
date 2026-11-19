"""Contract tests for core.VolatilityMonitorSettings (plan 03 ph6, D-152)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.volatility_monitor_settings import VolatilityLine, VolatilityMonitorSettings

REPO = Path(__file__).resolve().parents[2]
LINE = {"key": "a", "name": "A", "group": "美国", "kind": "cboe", "code": "VIX"}


# TC-VMS-001
def test_tc_vms_001_load_and_refuse(tmp_path: Path) -> None:
    settings = VolatilityMonitorSettings.load(REPO)
    assert any(x.kind == "cboe" for x in settings.lines) and settings.window > 0
    with pytest.raises(ValidationError):
        VolatilityLine(**(LINE | {"kind": "fx"}))
    with pytest.raises(ValidationError):
        VolatilityLine(**(LINE | {"alert_pct": 1.5}))
    with pytest.raises(ValidationError):
        VolatilityMonitorSettings(lines=[VolatilityLine(**LINE), VolatilityLine(**LINE)])
    assert VolatilityMonitorSettings.load(tmp_path / "empty").lines == []
    bad = tmp_path / "bad"
    (bad / "config").mkdir(parents=True)
    (bad / "config" / "volatility_monitor.yaml").write_text("window: -1\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        VolatilityMonitorSettings.load(bad)
