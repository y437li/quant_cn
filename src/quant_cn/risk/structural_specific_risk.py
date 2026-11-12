"""Structural model of specific risk for stocks with thin residual histories (plan 05 phase 4)."""

from __future__ import annotations

import numpy as np


class StructuralSpecificRisk:
    """
    Purpose:
        Predict specific volatility from exposures (USE4 / CNE5 structural model): regress
        ln(sigma_ts) on the factor exposures (industry dummies and styles) over stocks with a
        full residual history, weighted by cap, then sigma_str = E0 exp(X b) with
        E0 = sum w sigma_ts / sum w exp(X b) over the fit set (removes the log-retransformation
        bias). Used for stocks whose residual history is shorter than `specific_full_obs`.

    Contract:
        Input:
            min_fit: int  -- fewer fit stocks -> no structural forecast (default 100)
        Output:
            instance; `compute(sigma_ts, exposures, weights, fit) -> np.ndarray`
        Raises:
            (none)

    Used by:
        risk.SpecificRiskEstimator  -- thin-history fallback
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-SSR-001  recovers sigma when log sigma is exactly linear in the exposures
        TC-SSR-002  E0 makes the weighted mean prediction equal the weighted mean sigma on
                    the fit set; too few fit stocks -> all NaN
    """

    def __init__(self, min_fit: int = 100) -> None:
        self._min_fit = min_fit

    def compute(
        self, sigma_ts: np.ndarray, exposures: np.ndarray, weights: np.ndarray, fit: np.ndarray
    ) -> np.ndarray:
        """
        Purpose:
            Structural specific vol for every stock of one session.

        Contract:
            Input:
                sigma_ts:  np.ndarray  -- (N,) time-series specific vol (NaN outside the fit set)
                exposures: np.ndarray  -- (N, K) exposures, finite for every stock to predict
                weights:   np.ndarray  -- (N,) regression weights > 0
                fit:       np.ndarray  -- (N,) bool, stocks used to fit
            Output:
                np.ndarray  -- (N,) sigma_str > 0; NaN where exposures are not finite or the fit
                               set is smaller than min_fit
            Raises:
                (none)
        """
        n = len(sigma_ts)
        usable = np.isfinite(exposures).all(axis=1)
        ok = fit & usable & np.isfinite(sigma_ts) & (sigma_ts > 0) & (weights > 0)
        if ok.sum() < self._min_fit:
            return np.full(n, np.nan)
        x, w = exposures[ok], weights[ok]
        sw = np.sqrt(w)
        coef, *_ = np.linalg.lstsq(x * sw[:, None], np.log(sigma_ts[ok]) * sw, rcond=None)
        fitted = np.full(n, np.nan)
        fitted[usable] = np.exp(exposures[usable] @ coef)
        e0 = float((w * sigma_ts[ok]).sum() / (w * fitted[ok]).sum())
        return e0 * fitted
