"""Risk-free rate for any tenor from SHIBOR fixings (CALCULATION_DESIGN §2 step 2)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

TENOR_DAYS = {"on": 1, "1w": 7, "2w": 14, "1m": 30, "3m": 90, "6m": 180, "9m": 270, "1y": 360}


class RiskFreeCurve:
    """
    Purpose:
        Continuously compounded risk-free rate for a tenor in calendar days, from the latest SHIBOR
        fixing on or before the date, linearly interpolated between tenors and clamped outside them.

    Contract:
        Input:
            shibor: DataFrame  -- curated.shibor: `date` (YYYYMMDD) + tenors on..1y in percent
                                  (ACT/360 simple); at least one row
        Output:
            instance; `get_rate`
        Raises:
            ValueError  -- empty frame or missing tenor columns

    Used by:
        calculation.VixCalculator  -- rate per term

    Test cases:
        TC-RFC-001  exact tenor hit converts percent ACT/360 simple to continuous
        TC-RFC-002  interpolation between tenors; clamps beyond 1y and below overnight
        TC-RFC-003  uses the latest fixing on or before the date; earlier date raises ValueError
    """

    def __init__(self, shibor: pd.DataFrame) -> None:
        missing = [c for c in ["date", *TENOR_DAYS] if c not in shibor.columns]
        if shibor.empty or missing:
            raise ValueError(f"shibor frame empty or missing columns {missing}")
        self._fixings = shibor.set_index("date").sort_index()

    def get_rate(self, trade_date: str, days: int) -> float:
        """
        Purpose:
            Continuous annual rate for `days` calendar days as of `trade_date`.

        Contract:
            Input:
                trade_date: str  -- YYYYMMDD
                days:       int > 0
            Output:
                float  -- continuously compounded, ACT/365
            Raises:
                ValueError  -- no fixing on or before trade_date, or days <= 0
        """
        if days <= 0:
            raise ValueError(f"days must be positive, got {days}")
        known = self._fixings.loc[:trade_date]
        if known.empty:
            raise ValueError(f"no SHIBOR fixing on or before {trade_date}")
        row = known.iloc[-1]
        xs = list(TENOR_DAYS.values())
        ys = [float(row[k]) / 100 for k in TENOR_DAYS]
        simple = float(np.interp(days, xs, ys))
        return math.log(1 + simple * days / 360) / (days / 365)
