"""Stationary and circular block bootstrap of time series (FACTOR_TESTING_DESIGN §10)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

import numpy as np

Method = Literal["stationary", "circular"]
Values = Sequence[float] | np.ndarray
MIN_BLOCK = 20


class BlockBootstrap:
    """
    Purpose:
        Resample a time series (or several aligned series with the same draws) in blocks so
        serial correlation survives: stationary bootstrap with geometric block lengths (Politis &
        Romano 1994) or circular block bootstrap with fixed blocks (Politis & Romano 1992); both
        wrap around. Seeded, so reports reproduce byte for byte.

    Contract:
        Input:
            resamples: int > 0  -- B (default 2,000)
            seed:      int      -- numpy Generator seed
            method:    "stationary" | "circular"
        Output:
            instance; `compute_block`, `build_indices`, `compute_distribution`, `compute_interval`
        Raises:
            ValueError  -- resamples <= 0

    Used by:
        statistic.IcSignificance  -- CI of mean IC and ICIR, bootstrap p
        factor.FactorEvaluator    -- injected type or call
        cli.ServiceBuilder        -- injected type or call

    Test cases:
        TC-BB-001  indices have shape (B, T), values in [0, T); same seed -> same draws
        TC-BB-002  circular blocks are consecutive runs of length b (wrapping); stationary mean
                   block length is close to b
        TC-BB-003  known answer: 95% percentile CI of an AR(1) mean covers the true mean at
                   95% +- 4 pp over repeated samples
        TC-BB-004  block rule b = max(h, 20)
    """

    def __init__(self, resamples: int = 2000, seed: int = 0, method: Method = "stationary") -> None:
        if resamples <= 0:
            raise ValueError("resamples must be positive")
        self._resamples = resamples
        self._seed = seed
        self._method = method

    @staticmethod
    def compute_block(horizon: int) -> int:
        """
        Purpose:
            Expected block length for a horizon.

        Contract:
            Input:
                horizon: int >= 1  -- h in sessions
            Output:
                int  -- b = max(h, 20)
            Raises:
                (none)
        """
        return max(horizon, MIN_BLOCK)

    def build_indices(self, n_obs: int, block: int) -> np.ndarray:
        """
        Purpose:
            B resampled index vectors of length T.

        Contract:
            Input:
                n_obs: int >= 1  -- T
                block: int >= 1  -- b (mean length for stationary, fixed for circular)
            Output:
                ndarray[int] of shape (B, T)  -- stationary: block starts uniform, lengths
                                                 ~ Geometric(1/b); circular: fixed length b;
                                                 positions wrap modulo T
            Raises:
                (none)
        """
        rng = np.random.default_rng(self._seed)
        out = np.empty((self._resamples, n_obs), dtype=np.int64)
        for row in range(self._resamples):
            filled = 0
            while filled < n_obs:
                start = int(rng.integers(n_obs))
                length = int(rng.geometric(1 / block)) if self._method == "stationary" else block
                length = min(length, n_obs - filled)
                out[row, filled : filled + length] = (start + np.arange(length)) % n_obs
                filled += length
        return out

    def compute_distribution(
        self, values: Values, statistic: Callable[[np.ndarray], float], block: int
    ) -> np.ndarray:
        """
        Purpose:
            The statistic recomputed on every resample.

        Contract:
            Input:
                values:    Values                          -- x_1..x_T (NaN dropped)
                statistic: Callable[[ndarray], float]      -- e.g. mean, ICIR
                block:     int >= 1
            Output:
                ndarray of shape (B,)
            Raises:
                ValueError  -- fewer than 2 observations
        """
        x = np.asarray(values, dtype=float)
        x = x[~np.isnan(x)]
        if len(x) < 2:  # noqa: PLR2004 -- a mean needs two points to vary
            raise ValueError("need at least 2 observations")
        indices = self.build_indices(len(x), block)
        return np.array([statistic(x[row]) for row in indices])

    def compute_interval(
        self,
        values: Values,
        statistic: Callable[[np.ndarray], float],
        block: int,
        level: float = 0.95,
    ) -> dict[str, float]:
        """
        Purpose:
            Percentile confidence interval and bootstrap p-value of H0: statistic = 0.

        Contract:
            Input:
                values, statistic, block  -- as compute_distribution
                level: float in (0, 1)    -- 0.95 -> [2.5%, 97.5%]
            Output:
                dict  -- estimate, ci_lo, ci_hi (percentiles of theta*), p = share of
                         |theta* - theta_hat| >= |theta_hat| (Politis & Romano 1994)
            Raises:
                ValueError  -- fewer than 2 observations
        """
        x = np.asarray(values, dtype=float)
        x = x[~np.isnan(x)]
        estimate = float(statistic(x))
        dist = self.compute_distribution(x, statistic, block)
        tail = (1 - level) / 2 * 100
        lo, hi = np.percentile(dist, [tail, 100 - tail])
        p = float(np.mean(np.abs(dist - estimate) >= abs(estimate)))
        return {"estimate": estimate, "ci_lo": float(lo), "ci_hi": float(hi), "p": p}
