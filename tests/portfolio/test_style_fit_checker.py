"""Contract tests for portfolio.StyleFitChecker (plan 21 ph4)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.core.opportunity_settings import OpportunitySettings
from quant_cn.portfolio.style_fit_checker import StyleFitChecker
from quant_cn.risk.risk_snapshot import RiskSnapshot

A, B, UP, DOWN, NONE = "A", "B", "UP", "DOWN", "NONE"
FACTORS = ["country", "ind_x", "momentum", "usd_sensitivity", "size"]
X = pd.DataFrame(
    [
        [1, 1, 1.0, 0.5, 0.0],  # A
        [1, 0, 1.0, -0.1, 0.1],  # B
        [1, 1, 2.0, 0.0, 0.0],  # UP: adds momentum
        [1, 0, -1.0, 0.0, 3.0],  # DOWN: leans against momentum, size is not a top style
    ],
    index=[A, B, UP, DOWN],
    columns=FACTORS,
    dtype=float,
)
COV = pd.DataFrame(0.0, index=FACTORS, columns=FACTORS)
SPEC = pd.Series(0.02, index=X.index)
SNAP = RiskSnapshot("20261113", X, COV, SPEC)
SETTINGS = OpportunitySettings(fit_weight=0.1, fit_styles=2)


# TC-SFC-001
def test_tc_sfc_001_hand_book() -> None:
    weights = pd.Series({A: 0.5, B: 0.5})
    out = StyleFitChecker(SETTINGS).compute(SNAP, weights, [UP, DOWN])
    # book: momentum 1.0, usd 0.2, size 0.05 -> top 2 = momentum, usd_sensitivity
    assert out.loc[UP, "fit_styles"] == "momentum,usd_sensitivity"
    assert out.loc[UP, "fit"] == 0.0 and out.loc[DOWN, "fit"] == 1.0
    # UP: momentum 0.9 + 0.2 = 1.1 (+0.1); usd 0.18 (-0.02) -> +0.08
    assert out.loc[UP, "fit_delta"] == pytest.approx(0.08)
    # DOWN: momentum 0.9 - 0.1 = 0.8 (-0.2); usd 0.18 (-0.02) -> -0.22
    assert out.loc[DOWN, "fit_delta"] == pytest.approx(-0.22)


# TC-SFC-002
def test_tc_sfc_002_empty_book_and_uncovered() -> None:
    out = StyleFitChecker(SETTINGS).compute(SNAP, pd.Series(dtype=float), [UP, NONE])
    assert out.loc[UP, "fit"] == 1.0 and out.loc[UP, "fit_styles"] == ""
    assert math.isnan(out.loc[NONE, "fit"])
    held = StyleFitChecker(SETTINGS).compute(SNAP, pd.Series({A: 1.0}), [NONE])
    assert math.isnan(held.loc[NONE, "fit"])
