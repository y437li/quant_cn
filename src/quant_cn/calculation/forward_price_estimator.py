"""Forward price and K0 from put-call parity (CBOE white paper step 1)."""

from __future__ import annotations

import math

import pandas as pd


class ForwardPriceEstimator:
    """
    Purpose:
        Per term: F = K* + e^{RT}(C - P) at the strike K* with the smallest |C - P|, and K0 the
        largest strike at or below F.

    Contract:
        Input:
            (none)
        Output:
            instance; `compute`
        Raises:
            (none at construction)

    Used by:
        calculation.VixCalculator  -- F and K0 per term

    Test cases:
        TC-FPE-001  parity-consistent quotes return the true forward; K0 is the strike just below F
        TC-FPE-002  no strike with both call and put raises ValueError; F below all strikes too
    """

    def compute(self, quotes: pd.DataFrame, rate: float, t: float) -> tuple[float, float]:
        """
        Purpose:
            (F, K0) for one term.

        Contract:
            Input:
                quotes: DataFrame  -- OptionChainBuilder.build_quotes table
                rate:   float      -- continuous annual rate
                t:      float > 0  -- years to expiry
            Output:
                tuple[float, float]  -- forward, K0
            Raises:
                ValueError  -- no strike quotes both sides, or F below the lowest strike
        """
        diff = (quotes[("price", "C")] - quotes[("price", "P")]).dropna()
        if diff.empty:
            raise ValueError("no strike with both call and put prices")
        values = diff.to_numpy(dtype=float)
        best = int(abs(values).argmin())
        k_star = float(diff.index[best])
        forward = k_star + math.exp(rate * t) * float(values[best])
        below = [float(k) for k in quotes.index if k <= forward]
        if not below:
            raise ValueError(f"forward {forward} is below every strike")
        return forward, max(below)
