"""Cross-sectional neutralisation against industry and size (plan 04 phase 2)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


class Neutralizer:
    """
    Purpose:
        Remove what industry membership and numeric exposures (e.g. log market cap) explain in a
        factor, date by date: the residual of OLS
        x_i = a + sum_g d_{ig} b_g + sum_k z_{ik} c_k + e_i, so the factor's IC is not an
        industry or size bet in disguise.

    Contract:
        Input:
            min_names: int >= 2  -- dates with fewer complete rows get NaN
        Output:
            instance; `compute`
        Raises:
            (none)

    Used by:
        factor.FactorPreprocessor  -- injected type or call

    Test cases:
        TC-NEU-001  residuals are orthogonal to each industry dummy and to the numeric exposure
        TC-NEU-002  rows with a missing regressor get NaN; a pure industry effect is removed
    """

    def __init__(self, min_names: int = 10) -> None:
        self._min_names = min_names

    def compute(
        self,
        frame: pd.DataFrame,
        column: str = "value",
        categorical: Sequence[str] = (),
        numeric: Sequence[str] = (),
        by: str = "trade_date",
    ) -> pd.DataFrame:
        """
        Purpose:
            Replace `column` by its per-date OLS residual.

        Contract:
            Input:
                frame: DataFrame; column: str
                categorical: Sequence[str]  -- dummy-coded (one level dropped; intercept kept)
                numeric:     Sequence[str]  -- continuous exposures
                by: str
            Output:
                DataFrame  -- copy; column = x - X beta_hat, beta_hat = argmin ||x - X beta||^2
                              (numpy lstsq) per date; NaN where any input is missing
            Raises:
                KeyError  -- missing column
        """
        cols = [column, *categorical, *numeric]
        out = frame[column].astype(float) * np.nan
        for _, part in frame[[by, *cols]].dropna().groupby(by):
            if len(part) < self._min_names:
                continue
            design = [np.ones(len(part))]
            for name in categorical:
                dummies = pd.get_dummies(part[name], drop_first=True, dtype=float)
                design += [dummies[c].to_numpy() for c in dummies.columns]
            design += [part[name].to_numpy(float) for name in numeric]
            x = np.column_stack(design)
            y = part[column].to_numpy(float)
            beta, *_ = np.linalg.lstsq(x, y, rcond=None)
            out.loc[part.index] = y - x @ beta
        return frame.assign(**{column: out})
