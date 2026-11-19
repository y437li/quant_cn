"""Contract tests for core.RetailGaugeSettings (plan 21, D-142, D-155, D-167)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings

ROOT = Path(__file__).resolve().parents[2]


# TC-RGS-001
def test_tc_rgs_001_load_and_refuse(tmp_path: Path) -> None:
    s = RetailGaugeSettings.load(ROOT)
    assert (s.windows, s.halflives, s.avoid_pct, s.leaving_pct) == (
        [5, 20, 60, 120],
        [5, 20, 60],
        0.9,
        0.3,
    )
    assert (s.persist_n, s.persist_step, s.model_version) == (3, 3, "retail_gauge_v5")
    assert s.model["num_leaves"] == 63 and len(s.lagged) == 9
    assert RetailGaugeSettings.load(tmp_path) == RetailGaugeSettings()
    with pytest.raises(ValidationError):
        RetailGaugeSettings(avoid_pct=1.5)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "retail_gauge.yaml").write_text("unknown: 1\n")
    with pytest.raises(ConfigError):
        RetailGaugeSettings.load(tmp_path)
