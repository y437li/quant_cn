"""Dividend yield: trailing 12-month cash dividends / market cap (FACTOR_LIBRARY §1 DP)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.factor.base_factor import BaseFactor, FactorInputs

PERCENT = 100.0


class DividendYieldFactor(BaseFactor):
    """
    Purpose:
        DP = trailing 12-month dividend yield (daily_basic dv_ttm, percent -> fraction). A stock
        with a market cap and no dividend in the last 12 months gets 0 (dv_ttm is empty then),
        a session without daily_basic gets no value. The 红利 effect: high payers outperform in
        China, partly a value and quality proxy (user 2026-11-12: "测一下股息率的选股能力"; the
        same descriptor is the risk style dividend_yield, D-148).

    Contract:
        Input:
            name: str
        Output:
            instance; BaseFactor API
        Raises:
            (none at construction)

    Used by:
        (none yet)

    Test cases:
        TC-DYF-001  value = dv_ttm / 100; missing dv_ttm with a market cap = 0; no daily_basic row
                    = no value; a later dv_ttm leaves the value at t unchanged
    """

    inputs = ("prices", "daily_basic")
    basic_columns = ("dv_ttm", "total_mv")

    @property
    def lookback(self) -> int:
        """
        Purpose:
            Sessions of history needed.

        Contract:
            Input:
                (none)
            Output:
                int  -- 1 (same-session value)
            Raises:
                (none)
        """
        return 1

    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        """
        Purpose:
            Dividend yield per stock and session on the dense session grid.

        Contract:
            Input:
                inputs: FactorInputs  -- dense prices (grid) and daily_basic dv_ttm, total_mv
            Output:
                DataFrame  -- trade_date, ts_code, value_raw (fraction; NaN without a market cap)
            Raises:
                (none)
        """
        grid = inputs.prices[["trade_date", "ts_code"]]
        basic = inputs.daily_basic[["trade_date", "ts_code", "dv_ttm", "total_mv"]]
        panel = grid.merge(basic, on=["trade_date", "ts_code"], how="left")
        value = np.where(panel["total_mv"].notna(), panel["dv_ttm"].fillna(0.0) / PERCENT, np.nan)
        return panel[["trade_date", "ts_code"]].assign(value_raw=value)
