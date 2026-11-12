"""Exponentially weighted sums over a fixed trailing window of a date x stock matrix (plan 05)."""

from __future__ import annotations

import numpy as np
from scipy.signal import lfilter


class EwmWindow:
    """
    Purpose:
        The trailing-window kernel of every Barra descriptor and covariance estimate: weight
        w_k = 0.5^(k / half_life) on the observation k sessions before the current one
        (k = lag .. lag + window - 1), normalised to sum 1. Sums are exact finite-window
        convolutions along axis 0 (scipy.signal.lfilter with an FIR kernel), so a value at row t
        uses rows t - lag - window + 1 .. t - lag only.

    Contract:
        Input:
            window:    int >= 1    -- sessions in the window
            half_life: float > 0   -- sessions; inf = equal weights
            lag:       int >= 0    -- most recent sessions skipped (RSTR: 21)
        Output:
            instance; `weights`, `compute_sum`, `compute_count`
        Raises:
            ValueError  -- window < 1, half_life <= 0 or lag < 0

    Used by:
        risk.PriceDescriptors           -- beta, momentum, volatility, liquidity windows
        risk.FactorCovarianceEstimator  -- injected type or call
        risk.SpecificRiskEstimator      -- injected type or call
        risk.VolatilityRegimeAdjuster  -- injected type or call

    Test cases:
        TC-EW-001  weights sum to 1, halve every half_life sessions, lag shifts the kernel
        TC-EW-002  compute_sum equals the explicit weighted sum of the trailing window; NaN = 0
        TC-EW-003  compute_count counts valid rows in the window; bad parameters raise
    """

    def __init__(self, window: int, half_life: float, lag: int = 0) -> None:
        if window < 1 or half_life <= 0 or lag < 0:
            raise ValueError("window >= 1, half_life > 0 and lag >= 0 required")
        decay = 0.5 ** (np.arange(window) / half_life)
        self._weights = decay / decay.sum()
        self._kernel = np.concatenate([np.zeros(lag), self._weights])
        self._ones = np.concatenate([np.zeros(lag), np.ones(window)])

    @property
    def weights(self) -> np.ndarray:
        """
        Purpose:
            The normalised weights, most recent first (without the lag zeros).

        Contract:
            Input:
                (none)
            Output:
                np.ndarray  -- shape (window,), sums to 1, non-increasing
            Raises:
                (none)
        """
        return self._weights.copy()

    def compute_sum(self, values: np.ndarray) -> np.ndarray:
        """
        Purpose:
            Weighted trailing sum per row and column; NaN counts as 0.

        Contract:
            Input:
                values: np.ndarray  -- shape (T,) or (T, N), rows in date order
            Output:
                np.ndarray  -- same shape; row t = sum_k w_k values[t - lag - k]
                               (rows before the start contribute 0)
            Raises:
                (none)
        """
        clean = np.nan_to_num(np.asarray(values, dtype=float), nan=0.0)
        return np.asarray(lfilter(self._kernel, [1.0], clean, axis=0))

    def compute_count(self, valid: np.ndarray) -> np.ndarray:
        """
        Purpose:
            Number of valid observations inside each trailing window.

        Contract:
            Input:
                valid: np.ndarray  -- bool or 0/1, shape (T,) or (T, N)
            Output:
                np.ndarray  -- same shape, float counts (exact integers)
            Raises:
                (none)
        """
        counts = lfilter(self._ones, [1.0], np.asarray(valid, dtype=float), axis=0)
        return np.rint(np.asarray(counts))
