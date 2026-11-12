"""Tests of bayesian_shrinker (plan 05)."""

from __future__ import annotations

import numpy as np
import pytest

from quant_cn.core.risk_model_settings import RiskModelSettings
from quant_cn.risk.bayesian_shrinker import BayesianShrinker
from quant_cn.risk.specific_risk_estimator import SpecificRiskEstimator
from quant_cn.risk.structural_specific_risk import StructuralSpecificRisk
from quant_cn.risk.volatility_regime_adjuster import VolatilityRegimeAdjuster


def build_estimator(vra: int = 0, q: float = 0.0) -> SpecificRiskEstimator:
    s = RiskModelSettings(
        specific_half_life=10_000,
        specific_window=100,
        specific_nw_lags=0,
        specific_min_obs=20,
        specific_full_obs=60,
        vra_half_life=vra,
    )
    return SpecificRiskEstimator(
        s, StructuralSpecificRisk(min_fit=10), BayesianShrinker(q), VolatilityRegimeAdjuster(vra)
    )


# TC-BS-001
def test_tc_bs_001_shrinks_outliers_more() -> None:
    sigma = np.array([0.02, 0.02, 0.02, 0.05, 0.10])
    cap = np.ones(5)
    np.testing.assert_array_equal(BayesianShrinker(0.0, 1).compute(sigma, cap), sigma)
    out = BayesianShrinker(0.5, 1).compute(sigma, cap)
    assert out[4] < 0.10 and out[3] < 0.05
    assert (0.10 - out[4]) / (0.10 - 0.042) > (0.05 - out[3]) / (0.05 - 0.042)
    with pytest.raises(ValueError):
        BayesianShrinker(-1.0)


# TC-BS-002
def test_tc_bs_002_flat_group_and_nan() -> None:
    sigma = np.array([0.02, 0.02, np.nan])
    out = BayesianShrinker(0.1, 1).compute(sigma, np.array([1.0, 2.0, 3.0]))
    np.testing.assert_allclose(out[:2], 0.02)
    assert np.isnan(out[2])
