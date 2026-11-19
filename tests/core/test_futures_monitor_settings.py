"""Contract tests for core.FuturesMonitorSettings (plan 15 ph7i, D-145)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.futures_monitor_settings import FuturesMonitorSettings

REPO = Path(__file__).resolve().parents[2]


def test_tc_fms_001_load(tmp_path: Path) -> None:
    """TC-FMS-001"""
    s = FuturesMonitorSettings.load(REPO)
    assert len(s.families) >= 20 and any(x.kind == "ratio" for x in s.spreads)
    assert FuturesMonitorSettings.load(tmp_path).families == []
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "futures_monitor.yaml").write_text(
        "families: [{family: cu, name: 铜, group: 有色}]\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError):
        FuturesMonitorSettings.load(tmp_path)


def test_tc_fms_002_legs() -> None:
    """TC-FMS-002"""
    fam = [{"family": "CU.SHF", "name": "铜", "group": "有色"}]
    leg = [{"family": "CU.SHF", "coef": 1.0}, {"family": "AL.SHF", "coef": -1.0}]
    with pytest.raises(ValidationError):
        FuturesMonitorSettings(families=fam, spreads=[{"key": "x", "name": "x", "legs": leg}])
    three = [*leg, {"family": "CU.SHF", "coef": 1.0}]
    fam2 = [*fam, {"family": "AL.SHF", "name": "铝", "group": "有色"}]
    with pytest.raises(ValidationError):
        FuturesMonitorSettings(
            families=fam2, spreads=[{"key": "x", "name": "x", "kind": "ratio", "legs": three}]
        )


def test_tc_fms_003_reversion() -> None:
    """TC-FMS-003"""
    s = FuturesMonitorSettings.load(REPO)
    rev = {x.key: x.half_life_d for x in s.spreads if x.reversion}
    assert rev == {"pta_margin": 12, "mto_margin": 94, "rebar_margin": 152, "hrc_margin": 149}
    assert s.reversion_z > 0
    fam = [{"family": "CU.SHF", "name": "铜", "group": "有色"}]
    leg = [{"family": "CU.SHF", "coef": 1.0}, {"family": "CU.SHF", "coef": -1.0}]
    with pytest.raises(ValidationError):
        FuturesMonitorSettings(
            families=fam, spreads=[{"key": "x", "name": "x", "legs": leg, "half_life_d": 0}]
        )
