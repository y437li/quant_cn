"""Cross-sectional winsorisation of factor values (plan 04 phase 2)."""

from __future__ import annotations

from typing import Literal

import pandas as pd

Method = Literal["mad", "quantile"]
MAD_SCALE = 1.4826  # MAD -> standard deviation under normality


class Winsorizer:
    """
    Purpose:
        Clip extreme factor values within each date so a few outliers do not dominate ranks,
        z-scores or regressions: median +- k * 1.4826 * MAD (robust default) or the q / 1 - q
        cross-sectional quantiles.

    Contract:
        Input:
            method: "mad" | "quantile"
            k:      float > 0        -- MAD multiple (default 5)
            q:      float in (0, .5) -- quantile tail (default 0.01)
        Output:
            instance; `compute`
        Raises:
            ValueError  -- k <= 0 or q outside (0, 0.5)

    Used by:
        factor.FactorPreprocessor  -- injected type or call
        cli.ServiceBuilder         -- injected type or call

    Test cases:
        TC-WZ-001  MAD method clips to median +- k * 1.4826 * MAD per date; NaN stays NaN
        TC-WZ-002  quantile method clips to the per-date q and 1 - q quantiles
    """

    def __init__(self, method: Method = "mad", k: float = 5.0, q: float = 0.01) -> None:
        if k <= 0 or not 0 < q < 0.5:  # noqa: PLR2004 -- a two-sided tail
            raise ValueError("k must be > 0 and q in (0, 0.5)")
        self._method, self._k, self._q = method, k, q

    def compute(
        self, frame: pd.DataFrame, column: str = "value", by: str = "trade_date"
    ) -> pd.DataFrame:
        """
        Purpose:
            Winsorise one column within each group.

        Contract:
            Input:
                frame: DataFrame; column: str; by: str  -- group column (date)
            Output:
                DataFrame  -- copy with `column` clipped: mad: [med - k s, med + k s],
                              s = 1.4826 median(|x - med|); quantile: [Q_q, Q_{1-q}]
            Raises:
                KeyError  -- missing column
        """
        grouped = frame.groupby(by)[column]
        if self._method == "mad":
            med = grouped.transform("median")
            mad = (frame[column] - med).abs().groupby(frame[by]).transform("median") * MAD_SCALE
            lo, hi = med - self._k * mad, med + self._k * mad
        else:
            lo, hi = (
                grouped.transform(lambda s: s.quantile(self._q)),
                grouped.transform(lambda s: s.quantile(1 - self._q)),
            )
        return frame.assign(**{column: frame[column].clip(lo, hi)})
