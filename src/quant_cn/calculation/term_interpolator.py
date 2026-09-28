"""Blend two term variances to the constant-maturity index (CBOE white paper step 4)."""

from __future__ import annotations

import math


class TermInterpolator:
    """
    Purpose:
        VIX = 100 * sqrt([T1 s1^2 (N2 - Nt)/(N2 - N1) + T2 s2^2 (Nt - N1)/(N2 - N1)] * Ny / Nt),
        with N in the clock's unit (minutes or sessions) and Ny one year in that unit.

    Contract:
        Input:
            (none)
        Output:
            instance; `compute`
        Raises:
            (none at construction)

    Used by:
        calculation.VixCalculator  -- the index value per day

    Test cases:
        TC-TI-001  equal variances return 100*sqrt(variance) whatever the weights
        TC-TI-002  target at N1 returns the near term; N1 == N2 or negative total raises ValueError
    """

    def compute(
        self, var1: float, n1: float, var2: float, n2: float, target: float, year: float
    ) -> float:
        """
        Purpose:
            The interpolated (or extrapolated) index level.

        Contract:
            Input:
                var1, var2: float  -- annualised variances of near and next term
                n1, n2:     float  -- times to expiry in clock units, n1 < n2
                target:     float  -- constant maturity in clock units (N30 / 21 sessions)
                year:       float  -- one year in clock units
            Output:
                float  -- index in volatility points
            Raises:
                ValueError  -- n1 == n2, or the blended total variance is not positive
        """
        if n1 == n2:
            raise ValueError("near and next term have the same time to expiry")
        t1, t2 = n1 / year, n2 / year
        w1, w2 = (n2 - target) / (n2 - n1), (target - n1) / (n2 - n1)
        total = t1 * var1 * w1 + t2 * var2 * w2
        if total <= 0:
            raise ValueError(f"non-positive blended variance {total}")
        return 100 * math.sqrt(total * year / target)
