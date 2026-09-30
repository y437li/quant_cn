"""Descriptive statistics of a return series (plan 04 phase 2)."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from scipy import stats

TRADING_DAYS = 244
ZERO_SD = 1e-12
Values = Sequence[float] | np.ndarray


class ReturnStats:
    """
    Purpose:
        Summarise a series of period returns: annualised mean and volatility, Sharpe (per period
        and annualised with sqrt(244 / h)), maximum drawdown of the compounded path, hit rate,
        skewness and non-excess kurtosis (the PSR / DSR inputs of Bailey & López de Prado 2012).

    Contract:
        Input:
            periods_per_year: int > 0  -- sessions per year (244 for A-shares)
        Output:
            instance; `compute`
        Raises:
            (none)

    Used by:
        (none yet)

    Test cases:
        TC-RS-001  known answer: constant returns give zero volatility, no drawdown, Sharpe inf
        TC-RS-002  drawdown of a path 1 -> 1.2 -> 0.9 is -25%; skew/kurtosis match scipy
    """

    def __init__(self, periods_per_year: int = TRADING_DAYS) -> None:
        self._ppy = periods_per_year

    def compute(self, returns: Values, horizon: int = 1) -> dict[str, float]:
        """
        Purpose:
            Statistics of non-overlapping returns of length h sessions.

        Contract:
            Input:
                returns: Values  -- r_1..r_T (NaN dropped); horizon: int >= 1
            Output:
                dict  -- n, mean, sd (ddof 1), sharpe_period = mean / sd, ann_return = mean * A,
                         ann_vol = sd * sqrt(A), sharpe = sharpe_period * sqrt(A) with
                         A = periods_per_year / h; max_drawdown = min_t (V_t / max_{s<=t} V_s - 1),
                         V = prod(1 + r); hit_rate = share r > 0; skew;
                         kurtosis (non-excess, 3 for a normal)
            Raises:
                ValueError  -- fewer than 2 returns
        """
        r = np.asarray(returns, float)
        r = r[~np.isnan(r)]
        if len(r) < 2:  # noqa: PLR2004 -- a volatility needs two points
            raise ValueError("need at least 2 returns")
        scale = self._ppy / horizon
        mean, sd = float(r.mean()), float(r.std(ddof=1))
        sd = 0.0 if sd <= ZERO_SD * max(1.0, abs(mean)) else sd  # float noise of a constant series
        per = mean / sd if sd > 0 else math.copysign(math.inf, mean) if mean else 0.0
        path = np.cumprod(1 + r)
        drawdown = float((path / np.maximum.accumulate(np.r_[1.0, path])[1:] - 1).min())
        return {
            "n": float(len(r)),
            "mean": mean,
            "sd": sd,
            "sharpe_period": per,
            "ann_return": mean * scale,
            "ann_vol": sd * math.sqrt(scale),
            "sharpe": per * math.sqrt(scale),
            "max_drawdown": min(drawdown, 0.0),
            "hit_rate": float((r > 0).mean()),
            "skew": float(stats.skew(r)) if sd > 0 else 0.0,
            "kurtosis": float(stats.kurtosis(r, fisher=False)) if sd > 0 else 3.0,
        }
