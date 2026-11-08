"""Profit growth: year-on-year change of TTM net profit (FACTOR_LIBRARY §8)."""

from __future__ import annotations

import pandas as pd

from quant_cn.factor.base_factor import BaseFactor, FactorInputs


class ProfitGrowthFactor(BaseFactor):
    """
    Purpose:
        Growth = (NI_TTM(P) - NI_TTM(P - 1 year)) / |NI_TTM(P - 1 year)| for the latest PIT-visible
        period P, both TTMs from the versions known at the announcement (the lake's
        `n_income_attr_p_ttm_yoy`, D-092). Growth / earnings-momentum factor (Jegadeesh & Livnat
        2006). Needs eight quarters of history, so it starts about two years after the statements.

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
        TC-PGF-001  value = TTM yoy from the lake; nothing before the effective session
    """

    inputs = ("fundamentals",)
    fields = ("n_income_attr_p_ttm_yoy",)

    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        """
        Purpose:
            TTM profit growth per stock and session.

        Contract:
            Input:
                inputs: FactorInputs
            Output:
                DataFrame  -- trade_date, ts_code, value_raw = n_income_attr_p_ttm_yoy
            Raises:
                (none)
        """
        field_frame = inputs.compute_field("n_income_attr_p_ttm_yoy")
        return field_frame.rename(columns={"n_income_attr_p_ttm_yoy": "value_raw"})
