"""Pick the near and next expiries around the 30-day target (CBOE rule, CALCULATION_DESIGN §2)."""

from __future__ import annotations

import pandas as pd

N_TERMS = 2


class TermSelector:
    """
    Purpose:
        Choose the two nearest expiries with at least `min_days` calendar days to expiry.

    Contract:
        Input:
            min_days: int >= 0  -- near term must have at least this many days (7 per design)
        Output:
            instance; `list_terms`
        Raises:
            (none at construction)

    Used by:
        calculation.VixCalculator  -- near and next term per day

    Test cases:
        TC-TS-001  skips expiries under min_days and returns the next two, ascending
        TC-TS-002  fewer than two eligible expiries raises ValueError
    """

    def __init__(self, min_days: int = 7) -> None:
        self.min_days = min_days

    def list_terms(self, day_chain: pd.DataFrame) -> tuple[str, str]:
        """
        Purpose:
            (near, next) maturity dates for one day's chain.

        Contract:
            Input:
                day_chain: DataFrame  -- chain rows of one trade_date (maturity_date, days)
            Output:
                tuple[str, str]  -- YYYYMMDD, near < next
            Raises:
                ValueError  -- fewer than two expiries with days >= min_days
        """
        eligible = day_chain.loc[day_chain["days"] >= self.min_days, "maturity_date"]
        expiries = sorted(eligible.unique())
        if len(expiries) < N_TERMS:
            raise ValueError(f"need two expiries with >= {self.min_days} days, got {expiries}")
        return str(expiries[0]), str(expiries[1])
