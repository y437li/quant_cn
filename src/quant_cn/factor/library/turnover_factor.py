"""Turnover: minus the mean free-float turnover over 60 sessions (FACTOR_LIBRARY §8)."""

from __future__ import annotations

import pandas as pd

from quant_cn.factor.base_factor import BaseFactor, FactorInputs


class TurnoverFactor(BaseFactor):
    """
    Purpose:
        TURN = -mean(turnover_rate_f over the last `window` sessions, at least `min_obs` traded):
        heavily traded stocks underperform, a liquidity / attention effect that is strong in China
        (Datar, Naik & Radcliffe 1998; Liu, Stambaugh & Yuan 2019). Suspended sessions are missing,
        not zero.

    Contract:
        Input:
            name: str; window: int >= 1 (default 60); min_obs: int in [1, window] (default 40)
        Output:
            instance; BaseFactor API
        Raises:
            ValueError  -- bad window / min_obs

    Used by:
        (none yet)

    Test cases:
        TC-TRN-001  known answer (sign flipped); fewer than min_obs traded sessions give no value;
                    changing turnover after t leaves the value at t unchanged
    """

    inputs = ("prices", "daily_basic")
    basic_columns = ("turnover_rate_f",)

    def __init__(self, name: str, window: int = 60, min_obs: int = 40) -> None:
        super().__init__(name)
        if window < 1 or not 1 <= min_obs <= window:
            raise ValueError("need window >= 1 and 1 <= min_obs <= window")
        self._window, self._min_obs = window, min_obs

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
            Turnover per stock and session on the dense session grid.

        Contract:
            Input:
                inputs: FactorInputs  -- dense prices (grid) and daily_basic turnover_rate_f
            Output:
                DataFrame  -- trade_date, ts_code, value_raw = -rolling mean over `window` grid
                              sessions with at least `min_obs` observations
            Raises:
                (none)
        """
        grid = inputs.prices[["trade_date", "ts_code"]]
        basic = inputs.daily_basic[["trade_date", "ts_code", "turnover_rate_f"]]
        panel = grid.merge(basic, on=["trade_date", "ts_code"], how="left")
        panel = panel.sort_values(["ts_code", "trade_date"])
        mean = panel.groupby("ts_code")["turnover_rate_f"].transform(
            lambda s: s.rolling(self._window, min_periods=self._min_obs).mean()
        )
        return panel[["trade_date", "ts_code"]].assign(value_raw=-mean)
