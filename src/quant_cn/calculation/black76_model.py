"""Black-76 option prices on a forward and implied volatility by bisection."""

from __future__ import annotations

import math
from typing import Literal

Side = Literal["C", "P"]


class Black76Model:
    """
    Purpose:
        Price European options on a forward (Black-76, discounted at the continuous rate) and
        invert a price to implied volatility; used for ATM-IV checks and known-answer chains.

    Contract:
        Input:
            (none)
        Output:
            instance; `compute_price`, `compute_implied_vol`
        Raises:
            (none at construction)

    Used by:
        research_space/notebooks/20260927_vix_calculation.ipynb  -- ATM IV check, synthetic chain

    Test cases:
        TC-BM-001  put-call parity holds: C - P = e^{-rT}(F - K)
        TC-BM-002  implied vol recovers the pricing vol for calls and puts
        TC-BM-003  a price outside the no-arbitrage bounds raises ValueError
    """

    def compute_price(
        self, f: float, k: float, t: float, r: float, sigma: float, side: Side
    ) -> float:
        """
        Purpose:
            Black-76 price.

        Contract:
            Input:
                f, k > 0; t > 0 years; r continuous; sigma > 0; side "C" | "P"
            Output:
                float
            Raises:
                (none)
        """
        d1 = (math.log(f / k) + sigma**2 * t / 2) / (sigma * math.sqrt(t))
        d2 = d1 - sigma * math.sqrt(t)
        call = math.exp(-r * t) * (f * self._get_cdf(d1) - k * self._get_cdf(d2))
        return call if side == "C" else call - math.exp(-r * t) * (f - k)

    def compute_implied_vol(
        self, price: float, f: float, k: float, t: float, r: float, side: Side
    ) -> float:
        """
        Purpose:
            Volatility that reproduces `price` (bisection on [1e-4, 5]).

        Contract:
            Input:
                price: float; f, k, t, r, side as in compute_price
            Output:
                float  -- annualised volatility
            Raises:
                ValueError  -- price below intrinsic value or above the forward bound
        """
        lo, hi = 1e-4, 5.0
        if (
            not self.compute_price(f, k, t, r, lo, side)
            <= price
            <= self.compute_price(f, k, t, r, hi, side)
        ):
            raise ValueError(f"price {price} outside the Black-76 range for K={k}")
        for _ in range(100):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if self.compute_price(f, k, t, r, mid, side) < price else (lo, mid)
        return (lo + hi) / 2

    @staticmethod
    def _get_cdf(x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
