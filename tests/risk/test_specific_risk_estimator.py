"""Tests of specific_risk_estimator (plan 05)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.frames import SPECIFIC_RISK
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


# TC-SRE-001
def test_tc_sre_001_time_series_sigma_and_counts() -> None:
    rng = np.random.default_rng(10)
    u = rng.normal(0, 0.02, (150, 3))
    u[:140, 2] = np.nan  # thin history
    days = pd.bdate_range("2024-01-02", periods=150).strftime("%Y%m%d")
    sigma, h = build_estimator().compute_time_series(pd.DataFrame(u, index=days))
    assert sigma.iloc[-1, 0] == pytest.approx(np.sqrt((u[-100:, 0] ** 2).mean()), rel=1e-3)
    assert h.iloc[-1, 0] == 100 and h.iloc[-1, 2] == 10
    assert np.isnan(sigma.iloc[-1, 2])


# TC-SRE-002
def test_tc_sre_002_thin_history_uses_structural() -> None:
    rng = np.random.default_rng(11)
    n = 60
    x = np.hstack([np.ones((n, 1)), rng.standard_normal((n, 1))])
    sigma_ts = np.full(n, 0.02)
    obs = np.full(n, 100.0)
    sigma_ts[0], obs[0] = np.nan, 5.0
    obs[1] = 40.0  # half way between min_obs 20 and full_obs 60
    out, g = build_estimator().compute_session(sigma_ts, obs, x, np.ones(n))
    assert g[0] == 0.0 and g[1] == pytest.approx(0.5) and g[2] == 1.0
    assert out[0] == pytest.approx(0.02)  # structural on a flat cross-section
    assert out[2] == pytest.approx(0.02)


# TC-SRE-003
def test_tc_sre_003_final_applies_lambda() -> None:
    days = pd.bdate_range("2024-01-02", periods=300).strftime("%Y%m%d").tolist()
    rng = np.random.default_rng(12)
    resid = pd.DataFrame(rng.normal(0, 0.02, (300, 40)), index=days)
    pre = pd.DataFrame(
        [
            {"trade_date": d, "ts_code": c, "sigma": 0.01, "sigma_raw": 0.01, "g": 1.0, "cap": 1.0}
            for d in days
            for c in resid.columns
        ]
    )
    resid.columns = resid.columns.astype(str)
    pre["ts_code"] = pre["ts_code"].astype(str)
    out = build_estimator(vra=42).compute_final(pre, resid, start=days[-1])
    assert out["sigma"].mean() == pytest.approx(0.02, rel=0.08)
    assert set(out["method"]) == {"ewma"}
    SPECIFIC_RISK.validate(out)
