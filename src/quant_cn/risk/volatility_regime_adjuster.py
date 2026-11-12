"""Volatility regime adjustment of risk forecasts (USE4/CNE5 VRA, plan 05 phase 4)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.risk.ewm_window import EwmWindow

WINDOW_HALF_LIVES = 6


class VolatilityRegimeAdjuster:
    """
    Purpose:
        Scale risk forecasts by lambda_t so they track the current volatility regime: the
        cross-sectional bias statistic B_t^2 = weighted mean of (x_t / sigma_{t-1})^2 (factor
        returns over their forecast vol, equal weights; or specific returns over specific
        risk, cap weights) is averaged with an exponential kernel (half-life h, window 6 h) and
        lambda_t = sqrt(of that average). Multiplying variances by lambda_t^2 (vols by lambda_t)
        removes the bias a slow EWMA has right after a regime change. lambda at t uses B up to t.

    Contract:
        Input:
            half_life: int >= 0  -- sessions (CNE5: 42); 0 disables (lambda = 1)
        Output:
            instance; `compute_bias`, `compute_lambda`
        Raises:
            (none)

    Used by:
        risk.FactorCovarianceEstimator  -- factor VRA
        risk.SpecificRiskEstimator      -- specific VRA
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-VRA-001  forecasts that are too low by a factor k give lambda ~ k after the window
        TC-VRA-002  half_life 0 gives lambda 1; sessions without forecasts give NaN B (skipped)
        TC-VRA-003  compute_bias weights the squared standardised returns per session
    """

    def __init__(self, half_life: int = 42) -> None:
        self._half_life = half_life

    @staticmethod
    def compute_bias(
        returns: np.ndarray, sigma_prev: np.ndarray, weights: np.ndarray | None = None
    ) -> np.ndarray:
        """
        Purpose:
            B_t^2 per session.

        Contract:
            Input:
                returns:    np.ndarray  -- (T, N) realised returns
                sigma_prev: np.ndarray  -- (T, N) forecast vol made at t-1 (NaN = none)
                weights:    np.ndarray | None  -- (T, N) cross-sectional weights; None = equal
            Output:
                np.ndarray  -- (T,) weighted mean of (returns / sigma_prev)^2 over finite pairs;
                               NaN when a session has none
            Raises:
                (none)
        """
        with np.errstate(divide="ignore", invalid="ignore"):
            z2 = (returns / sigma_prev) ** 2
        w = np.ones_like(z2) if weights is None else np.nan_to_num(weights)
        ok = np.isfinite(z2) & (w > 0)
        total = np.where(ok, w, 0.0).sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            bias = np.where(ok, w * z2, 0.0).sum(axis=1) / total
        return np.where(total > 0, bias, np.nan)

    def compute_lambda(self, bias_sq: pd.Series) -> pd.Series:
        """
        Purpose:
            lambda_t from the B_t^2 series.

        Contract:
            Input:
                bias_sq: Series  -- B_t^2 indexed by session (NaN allowed)
            Output:
                Series  -- same index; sqrt(EWMA of B^2 over finite values up to t); 1.0 before
                           the first finite value or when disabled
            Raises:
                (none)
        """
        if self._half_life == 0:
            return pd.Series(1.0, index=bias_sq.index)
        window = EwmWindow(WINDOW_HALF_LIVES * self._half_life, self._half_life)
        values = bias_sq.to_numpy(float)
        valid = np.isfinite(values)
        with np.errstate(divide="ignore", invalid="ignore"):
            mean = window.compute_sum(values) / window.compute_sum(valid)
        out = np.sqrt(np.where(np.isfinite(mean) & (mean > 0), mean, 1.0))
        return pd.Series(out, index=bias_sq.index)
