"""Tests of volatility_regime_adjuster (plan 05)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.risk.volatility_regime_adjuster import VolatilityRegimeAdjuster


def build_cov(k: int = 8, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((200, k)) * np.linspace(0.002, 0.02, k)
    return np.asarray(np.cov(a.T))


# TC-VRA-001
def test_tc_vra_001_lambda_tracks_underforecast() -> None:
    rng = np.random.default_rng(4)
    returns = rng.normal(0, 0.02, (400, 30))
    sigma = np.full_like(returns, 0.01)  # forecasts twice too low
    vra = VolatilityRegimeAdjuster(42)
    lam = vra.compute_lambda(pd.Series(vra.compute_bias(returns, sigma)))
    assert lam.iloc[-1] == pytest.approx(2.0, rel=0.05)


# TC-VRA-002
def test_tc_vra_002_disabled_and_missing() -> None:
    bias = pd.Series([np.nan, 4.0, np.nan, 4.0])
    np.testing.assert_array_equal(VolatilityRegimeAdjuster(0).compute_lambda(bias), 1.0)
    lam = VolatilityRegimeAdjuster(2).compute_lambda(bias)
    assert lam.iloc[0] == 1.0 and lam.iloc[3] == pytest.approx(2.0)
    out = VolatilityRegimeAdjuster.compute_bias(np.ones((2, 2)), np.full((2, 2), np.nan))
    assert np.isnan(out).all()


# TC-VRA-003
def test_tc_vra_003_weighted_bias() -> None:
    returns = np.array([[1.0, 3.0]])
    sigma = np.ones((1, 2))
    out = VolatilityRegimeAdjuster.compute_bias(returns, sigma, np.array([[3.0, 1.0]]))
    assert out[0] == pytest.approx((3 * 1 + 1 * 9) / 4)
