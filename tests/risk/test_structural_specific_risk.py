"""Tests of structural_specific_risk (plan 05)."""

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


# TC-SSR-001
def test_tc_ssr_001_recovers_log_linear_sigma() -> None:
    rng = np.random.default_rng(8)
    x = np.hstack([np.ones((200, 1)), rng.standard_normal((200, 2))])
    sigma = np.exp(x @ np.array([np.log(0.02), 0.2, -0.1]))
    fit = np.arange(200) < 150
    out = StructuralSpecificRisk(min_fit=50).compute(
        np.where(fit, sigma, np.nan), x, np.ones(200), fit
    )
    np.testing.assert_allclose(out, sigma, rtol=1e-8)


# TC-SSR-002
def test_tc_ssr_002_e0_and_small_fit_set() -> None:
    rng = np.random.default_rng(9)
    x = np.hstack([np.ones((100, 1)), rng.standard_normal((100, 1))])
    sigma = np.exp(-4 + 0.3 * x[:, 1] + rng.normal(0, 0.3, 100))
    w, fit = rng.uniform(1, 2, 100), np.ones(100, dtype=bool)
    out = StructuralSpecificRisk(min_fit=50).compute(sigma, x, w, fit)
    assert (w * out).sum() == pytest.approx((w * sigma).sum())
    assert np.isnan(StructuralSpecificRisk(min_fit=500).compute(sigma, x, w, fit)).all()
