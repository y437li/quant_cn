"""Bayesian shrinkage of specific risk toward size-group means (USE4 / CNE5, plan 05 phase 4)."""

from __future__ import annotations

import numpy as np


class BayesianShrinker:
    """
    Purpose:
        Pull each stock's specific vol toward the cap-weighted mean of its size group, more so
        the further it is from it: sigma_sh = v sigma_bar + (1 - v) sigma with
        v = q |sigma - sigma_bar| / (delta + q |sigma - sigma_bar|), delta the root mean square
        deviation inside the group. Corrects the over-prediction of extreme historical vols
        (mean reversion of specific risk).

    Contract:
        Input:
            q:      float >= 0  -- shrinkage intensity (USE4: 0.1); 0 = no shrinkage
            groups: int >= 1    -- size groups (deciles of cap)
        Output:
            instance; `compute(sigma, cap) -> np.ndarray`
        Raises:
            ValueError  -- q < 0 or groups < 1

    Used by:
        risk.SpecificRiskEstimator  -- shrinkage step
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-BS-001  q = 0 returns sigma unchanged; outliers move toward the group mean, more for
                   larger deviations
        TC-BS-002  sigma equal within a group is unchanged; NaN sigma stays NaN
    """

    def __init__(self, q: float = 0.1, groups: int = 10) -> None:
        if q < 0 or groups < 1:
            raise ValueError("q >= 0 and groups >= 1 required")
        self._q, self._groups = q, groups

    def compute(self, sigma: np.ndarray, cap: np.ndarray) -> np.ndarray:
        """
        Purpose:
            Shrunk specific vol for one session.

        Contract:
            Input:
                sigma: np.ndarray  -- (N,) specific vol, NaN allowed
                cap:   np.ndarray  -- (N,) market cap (group key and mean weight), > 0
            Output:
                np.ndarray  -- (N,) shrunk vol; NaN where sigma or cap is not usable
            Raises:
                (none)
        """
        out = np.full(len(sigma), np.nan)
        ok = np.isfinite(sigma) & np.isfinite(cap) & (cap > 0)
        if not ok.any() or self._q == 0:
            return np.where(ok, sigma, np.nan)
        ranks = np.argsort(np.argsort(cap[ok]))
        group = (ranks * self._groups) // ok.sum()
        s, c = sigma[ok], cap[ok]
        shrunk = s.copy()
        for g in np.unique(group):
            m = group == g
            mean = float((c[m] * s[m]).sum() / c[m].sum())
            dev = np.abs(s[m] - mean)
            delta = float(np.sqrt(((s[m] - mean) ** 2).mean()))
            if delta <= 0:
                continue
            v = self._q * dev / (delta + self._q * dev)
            shrunk[m] = v * mean + (1 - v) * s[m]
        out[ok] = shrunk
        return out
