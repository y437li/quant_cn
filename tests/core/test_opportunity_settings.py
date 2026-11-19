"""Contract tests for core.OpportunitySettings (plan 21 ph4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.core.opportunity_settings import OpportunitySettings

REPO = Path(__file__).resolve().parents[2]


# TC-OPS-001
def test_tc_ops_001_load(tmp_path: Path) -> None:
    real = OpportunitySettings.load(REPO)
    assert real.min_circ_mv == 50 and real.required == ["retail_leaving"]
    assert real.valuation_field == "pb" and real.top_n == 10 and real.near_n == 5
    assert OpportunitySettings.load(tmp_path) == OpportunitySettings()
    (tmp_path / "config").mkdir()
    path = tmp_path / "config" / "discovery_rules.yaml"
    path.write_text("other: {a: 1}\n", encoding="utf-8")
    assert OpportunitySettings.load(tmp_path) == OpportunitySettings()
    for bad in ("opportunity: {nope: 1}\n", "opportunity: {required: [magic]}\n"):
        path.write_text(bad, encoding="utf-8")
        with pytest.raises(ConfigError):
            OpportunitySettings.load(tmp_path)
