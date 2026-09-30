"""Momentum 12-1: past-year return skipping the last month (FACTOR_LIBRARY §8)."""

from __future__ import annotations

import pandas as pd

from quant_cn.factor.base_factor import BaseFactor, FactorInputs


class MomentumFactor(BaseFactor):
    """
    Purpose:
        MOM_{12-1} = P_adj(t - skip) / P_adj(t - window) - 1 on the backward-adjusted close (ratios
        are PIT-safe, FACTOR_TESTING_DESIGN §11), skipping the most recent month to avoid the
        short-term reversal (Jegadeesh & Titman 1993). Suspended sessions carry the last close.

    Contract:
        Input:
            name: str; window: int > skip (default 252); skip: int >= 0 (default 21)
        Output:
            instance; BaseFactor API
        Raises:
            ValueError  -- window <= skip

    Used by:
        (none yet)

    Test cases:
        TC-MOM-001  known answer on a synthetic path; changing prices after t leaves the value at
                    t unchanged; the first `window` sessions of a stock have no value
    """

    inputs = ("prices",)

    def __init__(self, name: str, window: int = 252, skip: int = 21) -> None:
        super().__init__(name)
        if window <= skip or skip < 0:
            raise ValueError("need window > skip >= 0")
        self._window, self._skip = window, skip

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
            12-1 momentum per stock and session.

        Contract:
            Input:
                inputs: FactorInputs  -- dense prices
            Output:
                DataFrame  -- trade_date, ts_code, value_raw = c(t - skip) / c(t - window) - 1,
                              c = close_adj carried forward within the stock
            Raises:
                (none)
        """
        prices = inputs.prices.sort_values(["ts_code", "trade_date"])
        close = prices.groupby("ts_code")["close_adj"].ffill()
        grouped = close.groupby(prices["ts_code"])
        value = grouped.shift(self._skip) / grouped.shift(self._window) - 1
        return prices[["trade_date", "ts_code"]].assign(value_raw=value)
