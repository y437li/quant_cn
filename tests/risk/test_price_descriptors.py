"""Tests of PriceDescriptors."""

from __future__ import annotations

import numpy as np
import pytest

from quant_cn.risk.ewm_window import EwmWindow
from quant_cn.risk.price_descriptors import PriceDescriptors


# TC-PD-001
def test_tc_pd_001_beta_and_hsigma_recovered() -> None:
    rng = np.random.default_rng(1)
    market = rng.normal(0, 0.02, 600)
    betas = np.array([0.5, 1.0, 1.5])
    resid = rng.normal(0, 0.01, (600, 3))
    returns = market[:, None] * betas + resid
    beta, hsigma = PriceDescriptors(beta_half_life=10_000).compute_beta(returns, market)
    np.testing.assert_allclose(beta[-1], betas, atol=0.1)
    np.testing.assert_allclose(hsigma[-1], 0.01, rtol=0.15)
    assert np.isnan(beta[30]).all()  # fewer than min_obs


# TC-PD-002
def test_tc_pd_002_rstr_skips_lag_and_needs_history() -> None:
    returns = np.full((60, 1), 0.01)
    returns[-5:] = 0.5  # inside the lag: must not count
    d = PriceDescriptors(rstr_window=20, rstr_half_life=10_000, rstr_lag=5)
    out = d.compute_rstr(returns)
    assert out[-1, 0] == pytest.approx(np.log1p(0.01))  # weights sum to 1 over the window
    assert np.isnan(out[10, 0])


# TC-PD-003
def test_tc_pd_003_dastd_and_cmra() -> None:
    rng = np.random.default_rng(2)
    returns = rng.normal(0, 0.02, (300, 2))
    d = PriceDescriptors(vol_window=100, vol_half_life=10_000, min_obs=50)
    dastd = d.compute_dastd(returns)
    assert dastd[-1, 0] == pytest.approx(returns[-100:, 0].std(), rel=1e-3)
    cmra = d.compute_cmra(returns, months=3)
    logs = np.log1p(returns[-63:, 1])
    z = [logs[-21 * k :].sum() for k in (1, 2, 3)]
    assert cmra[-1, 1] == pytest.approx(max(z) - min(z))
    assert np.isnan(cmra[50, 0])


# TC-PD-004
def test_tc_pd_004_liquidity() -> None:
    turnover = np.full((300, 2), 0.01)
    turnover[:, 1] = 0.0
    out = PriceDescriptors().compute_liquidity(turnover)
    assert out["stom"][-1, 0] == pytest.approx(np.log(0.21))
    assert out["stoq"][-1, 0] == pytest.approx(np.log(0.21))
    assert out["stoa"][-1, 0] == pytest.approx(np.log(0.21))
    assert np.isnan(out["stom"][-1, 1])
    assert np.isnan(out["stoa"][100, 0])
    assert EwmWindow(21, np.inf).compute_count(np.isfinite(turnover))[-1, 0] == 21


# TC-PD-005
def test_tc_pd_005_partial_beta() -> None:
    rng = np.random.default_rng(3)
    market = rng.normal(0, 0.015, 600)
    us = 0.5 * market + rng.normal(0, 0.01, 600)  # correlated with the home market
    returns = (
        market[:, None] * 1.0 + us[:, None] * np.array([0.0, 0.4]) + rng.normal(0, 0.005, (600, 2))
    )
    d = PriceDescriptors(beta_half_life=10_000)
    out = d.compute_partial_beta(returns, market, us)
    np.testing.assert_allclose(out[-1], [0.0, 0.4], atol=0.06)
    assert np.isnan(d.compute_partial_beta(returns, market, market)[-1]).all()
