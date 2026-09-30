"""Combine processed factors into one score (SRC_DESIGN §2.5)."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from quant_cn.core.frames import FACTOR_PANEL
from quant_cn.statistic.standardizer import Standardizer

SCORE = "score"


class SignalCombiner:
    """
    Purpose:
        score_{i,t} = sum_f w_f z_{f,i,t} / sum_{f available} |w_f| over the processed factors a
        stock has at t (at least `min_factors`), then standardised per date: an equal-risk blend
        of z-scores that tolerates a missing factor instead of dropping the stock.

    Contract:
        Input:
            weights:      Mapping[str, float]  -- factor -> weight (factors absent from the map
                                                  are ignored)
            standardizer: Standardizer
            min_factors:  int >= 1
        Output:
            instance; `compute`
        Raises:
            ValueError  -- empty weights or min_factors < 1

    Used by:
        (none yet)

    Test cases:
        TC-SGC-001  known answer: weighted mean renormalised over available factors; value_raw is
                   the blend, value its per-date z-score; factor = "score"
        TC-SGC-002  stocks with fewer than min_factors factors get no score
    """

    def __init__(
        self, weights: Mapping[str, float], standardizer: Standardizer, min_factors: int = 3
    ) -> None:
        if not weights or min_factors < 1:
            raise ValueError("need weights and min_factors >= 1")
        self._weights = dict(weights)
        self._standardizer = standardizer
        self._min_factors = min_factors

    def compute(self, factors: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Score rows from processed factor rows.

        Contract:
            Input:
                factors: DataFrame  -- FACTOR_PANEL with processed `value`
            Output:
                DataFrame  -- FACTOR_PANEL rows with factor "score"
            Raises:
                SchemaError  -- not FACTOR_PANEL
        """
        frame = FACTOR_PANEL.validate(factors)
        frame = frame[frame["factor"].isin(list(self._weights))]
        w = frame["factor"].map(self._weights)
        parts = frame.assign(wv=w * frame["value"], aw=w.abs(), one=1)
        agg = parts.groupby(["trade_date", "ts_code"]).agg(
            wv=("wv", "sum"), aw=("aw", "sum"), n=("one", "sum")
        )
        agg = agg[(agg["n"] >= self._min_factors) & (agg["aw"] > 0)].reset_index()
        score = agg.assign(
            factor=SCORE, value_raw=agg["wv"] / agg["aw"], value=agg["wv"] / agg["aw"]
        )
        score = self._standardizer.compute(score, "value", by="trade_date")
        out = score.dropna(subset=["value"])[FACTOR_PANEL.columns].sort_values(
            ["trade_date", "ts_code"]
        )
        return FACTOR_PANEL.validate(
            FACTOR_PANEL.normalize(out.reset_index(drop=True), strict=True)
        )
