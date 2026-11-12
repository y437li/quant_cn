"""Tests of FactorCovarianceEstimator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.core.frames import FACTOR_COV
from quant_cn.core.risk_model_settings import RiskModelSettings
from quant_cn.risk.eigenfactor_adjuster import EigenfactorAdjuster
from quant_cn.risk.factor_covariance_estimator import FactorCovarianceEstimator
from quant_cn.risk.volatility_regime_adjuster import VolatilityRegimeAdjuster

DAYS = pd.bdate_range("2024-01-02", periods=150).strftime("%Y%m%d").tolist()


def build(lags: int = 0, sims: int = 0, **kw: int) -> FactorCovarianceEstimator:
    s = RiskModelSettings(
        vol_half_life=10_000,
        corr_half_life=10_000,
        cov_window=150,
        cov_nw_lags=lags,
        min_factor_obs=30,
        eigen_sims=sims,
        eigen_refit_days=50,
        vra_half_life=0,
        **kw,
    )
    return FactorCovarianceEstimator(s, EigenfactorAdjuster(sims), VolatilityRegimeAdjuster(0))


def build_returns(rng: np.random.Generator, k: int = 4) -> pd.DataFrame:
    values = rng.standard_normal((len(DAYS), k)) * 0.01
    rows = [
        {
            "trade_date": d,
            "factor": f"f{j}",
            "ret": values[t, j],
            "t_stat": 0.0,
            "r2": 0.3,
            "n_obs": 100.0,
        }
        for t, d in enumerate(DAYS)
        for j in range(k)
    ]
    return pd.DataFrame(rows)


# TC-FCE-001
def test_tc_fce_001_raw_matches_sample_and_nw_adds_autocorrelation() -> None:
    rng = np.random.default_rng(5)
    x = rng.standard_normal((150, 3)) * 0.01
    raw = build().compute_raw(x)
    np.testing.assert_allclose(raw, x.T @ x / 150, rtol=0.02, atol=1e-7)
    ar = np.zeros((150, 1))
    shocks = rng.standard_normal(150) * 0.01
    for t in range(1, 150):
        ar[t] = 0.5 * ar[t - 1] + shocks[t]
    assert build(lags=2).compute_raw(ar)[0, 0] > build(lags=0).compute_raw(ar)[0, 0]


# TC-FCE-002
def test_tc_fce_002_symmetric_psd_and_eigen_raises_small_direction() -> None:
    frame = build_returns(np.random.default_rng(6))
    out = build(sims=100).compute(frame)
    last = out[out["trade_date"] == DAYS[-1]]
    cov = last.pivot(index="factor_i", columns="factor_j", values="cov").to_numpy()
    raw = last.pivot(index="factor_i", columns="factor_j", values="cov_raw").to_numpy()
    np.testing.assert_allclose(cov, cov.T)
    assert np.linalg.eigvalsh(cov).min() > 0
    assert np.linalg.eigvalsh(cov)[0] >= np.linalg.eigvalsh(raw)[0]


# TC-FCE-003
def test_tc_fce_003_too_few_observations_and_schema() -> None:
    frame = build_returns(np.random.default_rng(7))
    late = (frame["factor"] == "f3") & (frame["trade_date"] < DAYS[130])
    frame = frame[~late]
    out = build().compute(frame, start=DAYS[100])
    assert out["trade_date"].min() == DAYS[100]
    assert "f3" not in set(out["factor_i"])  # only 20 observations
    assert set(out[out["trade_date"] == DAYS[100]]["factor_i"]) == {"f0", "f1", "f2"}
    FACTOR_COV.validate(out)
