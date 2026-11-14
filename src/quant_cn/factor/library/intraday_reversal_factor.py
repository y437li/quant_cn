"""Intraday high-turnover reversal: minus intraday returns on the busiest sessions (plan 25)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from quant_cn.factor.base_factor import FactorInputs
from quant_cn.factor.library.reversal_factor import ReversalFactor


class IntradayReversalFactor(ReversalFactor):
    """
    Purpose:
        IRV = -sum(ln(close / open)) over the `top_k` sessions with the highest free-float
        turnover among the last `window` grid sessions. The 1-month reversal lives in the
        intraday leg of busy sessions; the overnight leg is momentum (research run
        20261114_reversal_variants: 20-day rank IC 0.076 vs 0.046 for ReversalFactor). Sign
        flipped so higher values are expected to earn more. Open and close of one session share
        the adjustment factor, so unadjusted prices are used.

    Contract:
        Input:
            name: str; window: int >= 1 (default 21); top_k: int >= 1 (default 10);
            min_obs: int (default 15), top_k <= min_obs <= window
        Output:
            instance; BaseFactor API
        Raises:
            ValueError  -- window < 1, or not 1 <= top_k <= min_obs <= window

    Used by:
        (none yet)

    Test cases:
        TC-IRV-001  known answer: the top_k busiest sessions' intraday returns, summed, sign
                    flipped; the first value needs a full window
        TC-IRV-002  equal turnover: the later session is taken first
        TC-IRV-003  a session without open, close or turnover is skipped; fewer than min_obs
                    traded sessions give no value, exactly min_obs gives one
        TC-IRV-004  changing prices or turnover after t leaves the value at t unchanged
        TC-IRV-005  invalid window / top_k / min_obs raise ValueError
    """

    inputs = ("prices", "daily_basic")
    basic_columns = ("turnover_rate_f",)

    def __init__(self, name: str, window: int = 21, top_k: int = 10, min_obs: int = 15) -> None:
        super().__init__(name, window)
        if not 1 <= top_k <= min_obs <= window:
            raise ValueError("need 1 <= top_k <= min_obs <= window")
        self._top_k, self._min_obs = top_k, min_obs

    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        """
        Purpose:
            Intraday high-turnover reversal per stock and session on the dense session grid.

        Contract:
            Input:
                inputs: FactorInputs  -- dense prices (open, close) and daily_basic
                                         turnover_rate_f
            Output:
                DataFrame  -- trade_date, ts_code, value_raw = -sum of ln(close/open) on the
                              top_k highest-turnover traded sessions of the last `window`;
                              NaN with fewer than min_obs traded sessions or a partial window
            Raises:
                (none)
        """
        grid = inputs.prices[["trade_date", "ts_code", "open", "close"]]
        basic = inputs.daily_basic[["trade_date", "ts_code", "turnover_rate_f"]]
        panel = grid.merge(basic, on=["trade_date", "ts_code"], how="left")
        panel = panel.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
        ret = np.log(panel["close"].to_numpy(dtype=float) / panel["open"].to_numpy(dtype=float))
        turnover = panel["turnover_rate_f"].to_numpy(dtype=float)
        value = np.full(len(panel), np.nan)
        for rows in panel.groupby("ts_code", sort=False).indices.values():
            value[rows] = self._compute_window(ret[rows], turnover[rows])
        return panel[["trade_date", "ts_code"]].assign(value_raw=value)

    def _compute_window(self, ret: np.ndarray, turnover: np.ndarray) -> np.ndarray:
        out = np.full(len(ret), np.nan)
        if len(ret) < self._window:
            return out
        traded = np.isfinite(ret) & np.isfinite(turnover)
        rets = sliding_window_view(np.where(traded, ret, 0.0), self._window)
        key = sliding_window_view(np.where(traded, turnover, -np.inf), self._window)
        order = np.argsort(key, axis=1, kind="stable")  # ties: the later session sorts last
        top = order[:, -self._top_k :]
        picked = np.take_along_axis(rets, top, axis=1).sum(axis=1)
        enough = sliding_window_view(traded, self._window).sum(axis=1) >= self._min_obs
        out[self._window - 1 :] = np.where(enough, -picked, np.nan)
        return out
