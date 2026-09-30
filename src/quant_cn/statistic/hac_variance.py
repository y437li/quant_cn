"""Newey-West / Bartlett HAC variance of a mean (FACTOR_TESTING_DESIGN §10)."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from scipy import stats

MIN_OBS = 3
Values = Sequence[float] | np.ndarray
MAX_RHO = 0.97  # prewhitening AR(1) coefficient cap (Andrews & Monahan 1992)


class HacVariance:
    """
    Purpose:
        Heteroskedasticity- and autocorrelation-consistent variance of a sample mean with the
        Bartlett kernel (Newey & West 1987; lag rule of Newey & West 1994), for series whose
        observations overlap (IC_t at horizon h is serially correlated by construction). By
        default the series is AR(1)-prewhitened before the kernel and recoloured after
        (Andrews & Monahan 1992): with the plain rule-of-thumb lag, 95% intervals covered only
        89.8% on AR(1) phi = 0.6 and 88.4% on an overlapping 20-session MA(19), against 95.1% and
        99.0% prewhitened (D-090). Used for the NW t on mean IC and by every HAC test.

    Contract:
        Input:
            fixed_lag: int | None  -- None = automatic lag max(h - 1, floor(4 (T/100)^(2/9)))
            prewhiten: bool        -- AR(1) prewhitening (default True, D-090)
        Output:
            instance; `compute_lag`, `compute_long_run_variance`, `compute_t`
        Raises:
            ValueError  -- negative fixed_lag

    Used by:
        statistic.IcSignificance  -- NW t on mean IC, sub-periods, break test

    Test cases:
        TC-HAC-001  lag rule: max(h - 1, floor(4 (T/100)^(2/9)))
        TC-HAC-002  white noise: long-run variance equals the sample variance (lag 0)
        TC-HAC-003  known answer: prewhitened 95% NW intervals on simulated AR(1) means (phi 0.3,
                    0.6) cover 95% +- 2 pp; the naive t under-covers
        TC-HAC-005  overlapping MA(h-1) series: prewhitened coverage >= 93% (conservative allowed)
        TC-HAC-004  fewer than 3 observations raises ValueError
    """

    def __init__(self, fixed_lag: int | None = None, prewhiten: bool = True) -> None:
        if fixed_lag is not None and fixed_lag < 0:
            raise ValueError("fixed_lag must be >= 0")
        self._fixed_lag = fixed_lag
        self._prewhiten = prewhiten

    def compute_lag(self, n_obs: int, horizon: int = 1) -> int:
        """
        Purpose:
            Bartlett truncation lag.

        Contract:
            Input:
                n_obs: int >= 1   -- T
                horizon: int >= 1 -- h in sessions
            Output:
                int  -- fixed_lag if set, else L = max(h - 1, floor(4 (T/100)^(2/9)))
                        (Newey & West 1994 rule of thumb; h - 1 for overlapping horizons)
            Raises:
                (none)
        """
        if self._fixed_lag is not None:
            return self._fixed_lag
        return int(max(horizon - 1, math.floor(4 * (n_obs / 100) ** (2 / 9))))

    def compute_long_run_variance(self, values: Values, lag: int) -> float:
        """
        Purpose:
            Bartlett-kernel long-run variance of a series.

        Contract:
            Input:
                values: Values  -- x_1..x_T, NaN dropped
                lag:    int >= 0         -- L
            Output:
                float  -- Omega = gamma_0 + 2 sum_{l=1}^{L} (1 - l/(L+1)) gamma_l, where
                          gamma_l = (1/T) sum_{t=l+1}^{T} (x_t - mean)(x_{t-l} - mean)
                          (Newey & West 1987)
            Raises:
                ValueError  -- fewer than 3 observations
        """
        x = self._to_array(values)
        centred = x - x.mean()
        n = len(x)
        omega = float(centred @ centred) / n
        for lag_l in range(1, min(lag, n - 1) + 1):
            gamma = float(centred[lag_l:] @ centred[:-lag_l]) / n
            omega += 2 * (1 - lag_l / (lag + 1)) * gamma
        return max(omega, 0.0)

    def compute_hac_variance(self, values: Values, horizon: int = 1) -> float:
        """
        Purpose:
            Long-run variance used for inference: prewhitened (default) or plain Bartlett.

        Contract:
            Input:
                values:  Sequence[float]; horizon: int >= 1
            Output:
                float  -- plain: Omega(x, L); prewhitened: rho = OLS AR(1) of the centred series
                          (capped at 0.97), e_t = x_t - rho x_{t-1},
                          Omega = Omega(e, L) / (1 - rho)^2
                          (Andrews & Monahan 1992), L from compute_lag
            Raises:
                ValueError  -- fewer than 3 observations
        """
        x = self._to_array(values)
        if not self._prewhiten:
            return self.compute_long_run_variance(x, self.compute_lag(len(x), horizon))
        centred = x - x.mean()
        denom = float(centred[:-1] @ centred[:-1])
        rho = min(float(centred[1:] @ centred[:-1]) / denom, MAX_RHO) if denom > 0 else 0.0
        resid = centred[1:] - rho * centred[:-1]
        lag = self.compute_lag(len(resid), horizon)
        return self.compute_long_run_variance(resid, lag) / (1 - rho) ** 2

    def compute_t(self, values: Values, horizon: int = 1) -> dict[str, float]:
        """
        Purpose:
            Newey-West t statistic of the mean.

        Contract:
            Input:
                values:  Sequence[float]  -- e.g. IC_t, NaN dropped
                horizon: int >= 1         -- h, for the lag rule
            Output:
                dict  -- mean, se = sqrt(Omega / T) with Omega from compute_hac_variance,
                         t = mean / se, p two-sided from Student-t with T - 1 df, lag L, n T
                         (Newey & West 1987, 1994; Andrews & Monahan 1992)
            Raises:
                ValueError  -- fewer than 3 observations
        """
        x = self._to_array(values)
        n = len(x)
        lag = self.compute_lag(n, horizon)
        se = math.sqrt(self.compute_hac_variance(x, horizon) / n)
        mean = float(x.mean())
        t_stat = mean / se if se > 0 else math.inf * np.sign(mean) if mean else 0.0
        p = float(2 * stats.t.sf(abs(t_stat), df=n - 1)) if math.isfinite(t_stat) else 0.0
        return {
            "mean": mean,
            "se": se,
            "t": float(t_stat),
            "p": p,
            "lag": float(lag),
            "n": float(n),
        }

    @staticmethod
    def _to_array(values: Values) -> np.ndarray:
        x = np.asarray(values, dtype=float)
        x = x[~np.isnan(x)]
        if len(x) < MIN_OBS:
            raise ValueError(f"need at least {MIN_OBS} observations, got {len(x)}")
        return x
