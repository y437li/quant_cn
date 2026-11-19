"""Contract tests for core.RatesFxMonitorSettings (plan 34, D-171)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.rates_fx_monitor_settings import RatesFxLine, RatesFxMonitorSettings

ROOT = Path(__file__).resolve().parents[2]


# TC-RFS-001
def test_tc_rfs_001_load_and_refuse(tmp_path: Path) -> None:
    s = RatesFxMonitorSettings.load(ROOT)
    keys = [line.key for line in s.lines]
    assert "cn_10y" in keys and "usdcnh" in keys and len(keys) == len(set(keys))
    assert RatesFxMonitorSettings.load(tmp_path).lines == []
    base = {"key": "x", "name": "x", "group": "债市"}
    with pytest.raises(ValidationError):
        RatesFxLine(**base, kind="combo", unit="bp", op="diff", a="a")
    with pytest.raises(ValidationError):
        RatesFxLine(**base, kind="curve", unit="yield", curve="c")
    with pytest.raises(ValidationError):
        RatesFxLine(**base, kind="us", unit="pct", field="us_10y")
    one = RatesFxLine(**base, kind="us", unit="yield", field="us_10y")
    with pytest.raises(ValidationError):
        RatesFxMonitorSettings(lines=[one, one])
    later = RatesFxLine(key="y", name="y", group="债市", kind="combo", unit="bp", op="diff",
                        a="x", b="z")  # fmt: skip
    with pytest.raises(ValidationError):
        RatesFxMonitorSettings(lines=[one, later])
