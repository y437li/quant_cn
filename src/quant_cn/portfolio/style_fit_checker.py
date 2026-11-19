"""Does a candidate stock worsen the book's largest style bets? (plan 21 ph4)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.core.opportunity_settings import OpportunitySettings
from quant_cn.risk.risk_snapshot import RiskSnapshot

COLUMNS = ["fit", "fit_styles", "fit_delta"]
_NON_STYLE = ("country", "ind_")


class StyleFitChecker:
    """
    Purpose:
        The factor-fit rule of the opportunity list: the book's style exposures are
        b = X^T h (RiskSnapshot.compute_exposure_vector, industries and country left out);
        adding candidate c at weight a, funded pro rata from the book, gives
        b' = (1 - a) b + a x_c. The candidate fits when |b'_k| <= |b_k| for each of the
        `fit_styles` styles with the largest |b_k|. An empty book (no covered weight) fits
        every candidate.

    Contract:
        Input:
            settings: OpportunitySettings  -- fit_weight, fit_styles
        Output:
            instance; `compute(snap, weights, codes) -> DataFrame` indexed by codes with
            COLUMNS: fit (1.0 / 0.0; NaN when the candidate has no exposures), fit_styles
            (comma-joined style names checked), fit_delta (sum over those styles of
            |b'_k| - |b_k|; <= 0 when it fits)
        Raises:
            (none)

    Used by:
        portfolio.OpportunityScreen  -- fit rule
        cli.GaugeCommands            -- wires it

    Test cases:
        TC-SFC-001  hand 2-stock book: a candidate leaning against the largest style fits, one
                    adding to it does not; fit_delta equals the hand value
        TC-SFC-002  empty book: every covered candidate fits; uncovered candidate -> NaN
    """

    def __init__(self, settings: OpportunitySettings) -> None:
        self._weight = settings.fit_weight
        self._count = settings.fit_styles

    def compute(self, snap: RiskSnapshot, weights: pd.Series, codes: list[str]) -> pd.DataFrame:
        """
        Purpose:
            Fit of each candidate against the book `weights` (see the class contract).

        Contract:
            Input:
                snap: RiskSnapshot; weights: Series (index ts_code, book weights);
                codes: list[str]  -- candidates
            Output:
                DataFrame  -- index codes (order kept), COLUMNS
            Raises:
                (none)
        """
        styles = [c for c in snap.exposures.columns if not str(c).startswith(_NON_STYLE)]
        out = pd.DataFrame(index=pd.Index(codes, name="ts_code"), columns=COLUMNS)
        book = snap.compute_exposure_vector(weights)[styles]
        covered = [c for c in codes if c in snap.exposures.index]
        if book.abs().sum() == 0:
            out.loc[covered, ["fit", "fit_delta"]] = [1.0, 0.0]
            out["fit_styles"] = ""
            return out.astype({"fit": float, "fit_delta": float})
        top = book.abs().sort_values(ascending=False).index[: self._count]
        b = book[top].to_numpy(float)
        x = snap.exposures.loc[covered, top].to_numpy(float)
        after = (1 - self._weight) * b + self._weight * x
        delta = np.abs(after) - np.abs(b)
        out.loc[covered, "fit"] = (delta <= 0).all(axis=1).astype(float)
        out.loc[covered, "fit_delta"] = delta.sum(axis=1)
        out["fit_styles"] = ",".join(str(s) for s in top)
        return out.astype({"fit": float, "fit_delta": float})
