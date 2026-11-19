"""Contract tests for calculation.SpreadReversion (plan 15 ph7i, D-156)."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from quant_cn.calculation.spread_reversion import SpreadReversion
from quant_cn.core.futures_monitor_settings import FuturesMonitorSettings


def _build_spread(z: float | None, reversion: bool = True) -> dict[str, Any]:
    return {"key": "mto", "name": "甲醇制烯烃利润", "unit": "元/吨", "value": -700.0, "z_1y": z,
            "reversion": reversion, "half_life_d": 94}  # fmt: skip


# TC-SRV-001
def test_tc_srv_001_z() -> None:
    values = pd.Series([float(i % 2) for i in range(119)] + [3.0])
    window = values.iloc[-250:]
    expected = round(float((3.0 - window.mean()) / window.std()), 2)
    assert SpreadReversion.compute_z(values) == pytest.approx(expected)
    assert SpreadReversion.compute_z(values.iloc[1:]) is None  # 119 values < MIN_OBS
    assert SpreadReversion.compute_z(pd.Series([5.0] * 130)) is None  # zero spread


# TC-SRV-002
def test_tc_srv_002_flags() -> None:
    sr = SpreadReversion(FuturesMonitorSettings(reversion_z=2.0))
    flags = sr.list_flags([_build_spread(-2.0)])
    assert [f["key"] for f in flags] == ["reversion:mto"] and flags[0]["kind"] == "reversion"
    assert (
        "低于一年均值 2.0 个标准差" in flags[0]["message"] and "94 个交易日" in flags[0]["message"]
    )
    assert (
        sr.list_flags(
            [_build_spread(1.99), _build_spread(-3.0, reversion=False), _build_spread(None)]
        )
        == []
    )
