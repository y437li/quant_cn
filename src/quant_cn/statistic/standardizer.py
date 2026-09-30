"""Cross-sectional z-scores of factor values (plan 04 phase 2)."""

from __future__ import annotations

import numpy as np
import pandas as pd


class Standardizer:
    """
    Purpose:
        Put factor values on a common scale within each date: z = (x - m) / s with m the
        equal-weighted mean (or a weighted mean, e.g. cap weights as in Barra-style exposures) and
        s the equal-weighted standard deviation, so the cross-section has unit dispersion.

    Contract:
        Input:
            (none)
        Output:
            instance; `compute`
        Raises:
            (none)

    Used by:
        (none yet)

    Test cases:
        TC-STD-001  per date: mean 0, standard deviation 1; NaN rows stay NaN
        TC-STD-002  weighted mean centres on the weights; a constant date gives NaN, not inf
    """

    def compute(
        self,
        frame: pd.DataFrame,
        column: str = "value",
        by: str = "trade_date",
        weight_column: str | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            z-score one column within each group.

        Contract:
            Input:
                frame: DataFrame; column: str; by: str
                weight_column: str | None  -- weights for the mean (None = equal)
            Output:
                DataFrame  -- copy with column = (x - m) / s, m = sum(w x) / sum(w) over non-NaN,
                              s = sample sd (ddof 1); s = 0 -> NaN
            Raises:
                KeyError  -- missing column
        """
        x = frame[column]
        if weight_column is None:
            mean = x.groupby(frame[by]).transform("mean")
        else:
            w = frame[weight_column].where(x.notna())
            mean = (x * w).groupby(frame[by]).transform("sum") / w.groupby(frame[by]).transform(
                "sum"
            )
        sd = x.groupby(frame[by]).transform("std").replace(0, np.nan)
        return frame.assign(**{column: (x - mean) / sd})
