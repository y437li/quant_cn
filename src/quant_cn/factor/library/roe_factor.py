"""ROE TTM: trailing net profit over latest equity (FACTOR_LIBRARY §8)."""

from __future__ import annotations

import pandas as pd

from quant_cn.factor.base_factor import BaseFactor, FactorInputs


class RoeFactor(BaseFactor):
    """
    Purpose:
        Return on equity ROE_TTM = net profit attributable to parent over the trailing twelve months
        / equity attributable to parent in the latest PIT-visible balance sheet (both D-092 PIT).
        Profitability / quality factor (Novy-Marx 2013; Fama & French 2015 RMW).

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
        TC-ROE-001  ROE = TTM profit / equity; non-positive equity gives no value; nothing before
                    the effective session of either statement
    """

    inputs = ("fundamentals",)
    fields = ("n_income_attr_p_ttm", "total_hldr_eqy_exc_min_int")

    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        """
        Purpose:
            ROE per stock and session.

        Contract:
            Input:
                inputs: FactorInputs
            Output:
                DataFrame  -- trade_date, ts_code, value_raw = n_income_attr_p_ttm /
                              total_hldr_eqy_exc_min_int; NaN when equity <= 0
            Raises:
                (none)
        """
        joined = self._build_joined(
            [
                inputs.compute_field("n_income_attr_p_ttm"),
                inputs.compute_field("total_hldr_eqy_exc_min_int"),
            ]
        )
        equity = joined["total_hldr_eqy_exc_min_int"].where(
            joined["total_hldr_eqy_exc_min_int"] > 0
        )
        return joined.assign(value_raw=joined["n_income_attr_p_ttm"] / equity)[
            ["trade_date", "ts_code", "value_raw"]
        ]
