"""EP TTM: trailing net profit over market value (FACTOR_LIBRARY §8)."""

from __future__ import annotations

import pandas as pd

from quant_cn.factor.base_factor import BaseFactor, FactorInputs

WAN = 1e4  # daily_basic.total_mv is in 10k CNY; statements are in CNY


class EarningsYieldFactor(BaseFactor):
    """
    Purpose:
        Earnings yield EP_TTM = net profit attributable to parent over the trailing twelve months
        (PIT, D-092) / total market value at the close of t. Value factor (Basu 1977; Fama &
        French 1992), EP rather than PE so loss-makers rank low instead of flipping sign.

    Contract:
        Input:
            name: str
        Output:
            instance; BaseFactor API
        Raises:
            (none)

    Used by:
        (none yet)

    Test cases:
        TC-EYF-001  EP = n_income_attr_p_ttm / (total_mv * 1e4); nothing before the statement's
                    effective session; a restatement changes the value from its effective session
    """

    inputs = ("fundamentals", "daily_basic")
    fields = ("n_income_attr_p_ttm",)
    basic_columns = ("total_mv",)

    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        """
        Purpose:
            EP per stock and session.

        Contract:
            Input:
                inputs: FactorInputs
            Output:
                DataFrame  -- trade_date, ts_code, value_raw = n_income_attr_p_ttm /
                              (total_mv * 1e4); NaN when market value <= 0
            Raises:
                (none)
        """
        basic = inputs.daily_basic[["trade_date", "ts_code", "total_mv"]]
        joined = self._build_joined([inputs.compute_field("n_income_attr_p_ttm"), basic])
        mv = joined["total_mv"].where(joined["total_mv"] > 0) * WAN
        return joined.assign(value_raw=joined["n_income_attr_p_ttm"] / mv)[
            ["trade_date", "ts_code", "value_raw"]
        ]
