from __future__ import annotations

import math

import pytest

from quant_cn.calculation.risk_free_curve import RiskFreeCurve
from tests.support import SampleOptions


# TC-RFC-001
def test_tc_rfc_001_exact_tenor() -> None:
    rate = RiskFreeCurve(SampleOptions.SHIBOR).get_rate("20260828", 30)
    assert rate == pytest.approx(math.log(1 + 0.014 * 30 / 360) / (30 / 365))


# TC-RFC-002
def test_tc_rfc_002_interpolate_and_clamp() -> None:
    curve = RiskFreeCurve(SampleOptions.SHIBOR)
    mid = curve.get_rate("20260828", 60)
    assert curve.get_rate("20260828", 30) < mid < curve.get_rate("20260828", 90)
    long = curve.get_rate("20260828", 720)
    assert long == pytest.approx(math.log(1 + 0.015 * 720 / 360) / (720 / 365))


# TC-RFC-003
def test_tc_rfc_003_latest_fixing() -> None:
    curve = RiskFreeCurve(SampleOptions.SHIBOR)
    assert curve.get_rate("20261231", 7) == curve.get_rate("20260801", 7)
    with pytest.raises(ValueError):
        curve.get_rate("20260731", 7)
    with pytest.raises(ValueError):
        RiskFreeCurve(SampleOptions.SHIBOR.drop(columns="1y"))
