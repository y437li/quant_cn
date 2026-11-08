"""Per-term variance from the out-of-the-money option strip (CBOE white paper steps 2-3)."""

from __future__ import annotations

import math
from typing import Literal

import pandas as pd

STOP_AFTER_ZEROS = 2
ZeroRule = Literal["price", "price_or_volume"]


class VarianceStripCalculator:
    """
    Purpose:
        sigma^2 = (2/T) sum(dK/K^2 e^{RT} Q(K)) - (1/T)(F/K0 - 1)^2 over puts below K0, calls above
        K0 and the call/put average at K0; walking away from K0 stops after two consecutive
        "zero" strikes (zero price, or with price_or_volume also zero volume: no bid/ask, D-048).

    Contract:
        Input:
            zero_rule: "price" | "price_or_volume"  -- what counts as a zero strike (design default
                                                       price_or_volume)
        Output:
            instance; `compute`
        Raises:
            (none at construction)

    Used by:
        calculation.VixCalculator  -- variance per term

    Test cases:
        TC-VSC-001  flat-volatility Black-76 strip recovers sigma^2 within 1% on a wide grid
        TC-VSC-002  walking stops after two consecutive zero strikes; single zeros are skipped
        TC-VSC-003  dK is half the neighbour gap inside and the one-sided gap at the edges
    """

    def __init__(self, zero_rule: ZeroRule = "price_or_volume") -> None:
        self.zero_rule = zero_rule

    def compute(
        self, quotes: pd.DataFrame, forward: float, k0: float, rate: float, t: float
    ) -> tuple[float, int]:
        """
        Purpose:
            Variance and number of strikes used for one term.

        Contract:
            Input:
                quotes: DataFrame  -- OptionChainBuilder.build_quotes table; must contain K0
                forward, k0: float; rate: float (continuous); t: float > 0 (years)
            Output:
                tuple[float, int]  -- sigma^2 (annualised), strikes used
            Raises:
                KeyError  -- K0 not in quotes
        """
        prices = self._read_side(quotes, "price")
        volumes = self._read_side(quotes, "vol")
        strikes_all = [float(k) for k in quotes.index]
        selected = {k0: (prices["C"][k0] + prices["P"][k0]) / 2}
        below = sorted((k for k in strikes_all if k < k0), reverse=True)
        above = sorted(k for k in strikes_all if k > k0)
        selected |= self._list_prices(prices["P"], volumes["P"], below)
        selected |= self._list_prices(prices["C"], volumes["C"], above)
        strikes = sorted(selected)
        total = 0.0
        for i, k in enumerate(strikes):
            lo, hi = strikes[max(i - 1, 0)], strikes[min(i + 1, len(strikes) - 1)]
            dk = (hi - lo) / (2 if 0 < i < len(strikes) - 1 else 1)
            total += dk / k**2 * math.exp(rate * t) * selected[k]
        return 2 / t * total - (forward / k0 - 1) ** 2 / t, len(strikes)

    @staticmethod
    def _read_side(quotes: pd.DataFrame, field: str) -> dict[str, dict[float, float]]:
        out: dict[str, dict[float, float]] = {}
        for side in ("C", "P"):
            if (field, side) in quotes.columns:
                col = quotes[(field, side)]
                out[side] = {
                    float(k): float(v) for k, v in zip(col.index, col.to_numpy(), strict=True)
                }
            else:
                out[side] = {}
        return out

    def _list_prices(
        self, prices: dict[float, float], volumes: dict[float, float], strikes: list[float]
    ) -> dict[float, float]:
        out: dict[float, float] = {}
        zeros = 0
        for k in strikes:
            if self._is_zero(prices.get(k, math.nan), volumes.get(k, math.nan)):
                zeros += 1
                if zeros == STOP_AFTER_ZEROS:
                    break
                continue
            zeros = 0
            out[k] = prices[k]
        return out

    def _is_zero(self, price: float, volume: float) -> bool:
        if math.isnan(price) or price <= 0:
            return True
        if self.zero_rule == "price":
            return False
        return math.isnan(volume) or volume <= 0
