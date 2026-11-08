"""Short-term reversal: minus the last month's return (FACTOR_LIBRARY §8)."""

from __future__ import annotations

import pandas as pd

from quant_cn.factor.base_factor import BaseFactor, FactorInputs


class ReversalFactor(BaseFactor):
    """
    Purpose:
        REV = -(P_adj(t) / P_adj(t - window) - 1): last month's losers tend to rebound, strongly so
        in China's retail-driven market (Jegadeesh 1990; Lehmann 1990). Sign flipped so higher
        values are expected to earn more. Suspended sessions carry the last close.

    Contract:
        Input:
            name: str; window: int >= 1 (default 21)
        Output:
            instance; BaseFactor API
        Raises:
            ValueError  -- window < 1

    Used by:
        (none yet)

    Test cases:
        TC-REV-001  known answer with the sign flipped; changing prices after t leaves the value
                    at t unchanged
    """

    inputs = ("prices",)

    def __init__(self, name: str, window: int = 21) -> None:
        super().__init__(name)
        if window < 1:
            raise ValueError("window must be >= 1")
        self._window = window

    @property
    def lookback(self) -> int:
        """
        Purpose:
            Sessions of history needed.

        Contract:
            Input:
                (none)
            Output:
                int  -- window
            Raises:
                (none)
        """
        return self._window

    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        """
        Purpose:
            Reversal per stock and session.

        Contract:
            Input:
                inputs: FactorInputs  -- dense prices
            Output:
                DataFrame  -- trade_date, ts_code, value_raw = -(c(t) / c(t - window) - 1)
            Raises:
                (none)
        """
        prices = inputs.prices.sort_values(["ts_code", "trade_date"])
        close = prices.groupby("ts_code")["close_adj"].ffill()
        value = -(close / close.groupby(prices["ts_code"]).shift(self._window) - 1)
        return prices[["trade_date", "ts_code"]].assign(value_raw=value)
