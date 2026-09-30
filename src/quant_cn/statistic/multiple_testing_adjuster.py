"""Multiple-testing corrections across a campaign's factors (FACTOR_TESTING_DESIGN §3, §10)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from quant_cn.core.frames import IC_TEST

HLZ_HURDLE = 3.0
Values = Sequence[float] | np.ndarray


class MultipleTestingAdjuster:
    """
    Purpose:
        Adjust the p-values of many factor tests run in one campaign: Holm step-down FWER
        (Holm 1979), Benjamini-Hochberg FDR (1995), Benjamini-Hochberg-Yekutieli FDR under
        arbitrary dependence (2001), Romano-Wolf bootstrap step-down FWER (Romano & Wolf 2005,
        2016), and the Harvey-Liu-Zhu (2016) |t| >= 3.0 hurdle. Pure arithmetic on arrays.

    Contract:
        Input:
            hurdle: float > 0  -- HLZ t hurdle (default 3.0)
        Output:
            instance; `compute_holm`, `compute_bh`, `compute_bhy`, `compute_romano_wolf`,
            `build_adjusted`
        Raises:
            (none at construction)

    Used by:
        factor.FactorEvaluator  -- injected type or call

    Test cases:
        TC-MTA-001  known answer: Holm/BH/BHY on a hand-worked 4-value example
        TC-MTA-002  known answer: BH 1995 15-value example rejects 4 at 5%, Holm rejects 3
        TC-MTA-003  null family of 200 tests: BHY and Holm reject at most 5% of families
        TC-MTA-004  Romano-Wolf: monotone in |t|, never below the unadjusted bootstrap p, a
                    strong signal survives
        TC-MTA-005  build_adjusted fills p_adj_* and hlz_pass on the chosen metric rows only
    """

    def __init__(self, hurdle: float = HLZ_HURDLE) -> None:
        self._hurdle = hurdle

    def compute_holm(self, p_values: Values) -> np.ndarray:
        """
        Purpose:
            Holm step-down adjusted p-values (family-wise error).

        Contract:
            Input:
                p_values: Values  -- p_1..p_m
            Output:
                ndarray  -- in input order; with p_(1) <= ... <= p_(m):
                            p_adj_(i) = max_{j <= i} min(1, (m - j + 1) p_(j))  (Holm 1979)
            Raises:
                (none)
        """
        p = np.asarray(p_values, dtype=float)
        m = len(p)
        order = np.argsort(p, kind="stable")
        scaled = np.minimum(1.0, (m - np.arange(m)) * p[order])
        return self._to_input_order(np.maximum.accumulate(scaled), order)

    def compute_bh(self, p_values: Values, factor: float = 1.0) -> np.ndarray:
        """
        Purpose:
            Benjamini-Hochberg adjusted p-values (false discovery rate).

        Contract:
            Input:
                p_values: Values
                factor:   float >= 1  -- m is replaced by m * factor (BHY passes c(m))
            Output:
                ndarray  -- in input order; p_adj_(i) = min_{j >= i} min(1, m p_(j) / j)
                            (Benjamini & Hochberg 1995)
            Raises:
                (none)
        """
        p = np.asarray(p_values, dtype=float)
        m = len(p)
        order = np.argsort(p, kind="stable")
        scaled = np.minimum(1.0, m * factor * p[order] / np.arange(1, m + 1))
        return self._to_input_order(np.minimum.accumulate(scaled[::-1])[::-1], order)

    def compute_bhy(self, p_values: Values) -> np.ndarray:
        """
        Purpose:
            Benjamini-Hochberg-Yekutieli adjusted p-values (FDR under arbitrary dependence).

        Contract:
            Input:
                p_values: Values
            Output:
                ndarray  -- BH with m replaced by m c(m), c(m) = sum_{k=1}^{m} 1/k
                            (Benjamini & Yekutieli 2001)
            Raises:
                (none)
        """
        m = len(np.asarray(p_values))
        return self.compute_bh(p_values, factor=float(np.sum(1.0 / np.arange(1, m + 1))))

    def compute_romano_wolf(self, t_stats: Values, t_boot: np.ndarray) -> np.ndarray:
        """
        Purpose:
            Romano-Wolf step-down adjusted p-values from bootstrap null statistics.

        Contract:
            Input:
                t_stats: Values             -- studentised statistics t_1..t_m
                t_boot:  ndarray (B, m)     -- bootstrap statistics recentred under the null
            Output:
                ndarray  -- in input order; with |t|_(1) >= ... >= |t|_(m):
                            p_(s) = max(p_(s-1), P*(max_{j >= s} |t*_(j)| >= |t|_(s)))
                            (Romano & Wolf 2005, 2016; two-sided, monotone)
            Raises:
                ValueError  -- t_boot does not have m columns
        """
        t = np.abs(np.asarray(t_stats, dtype=float))
        boot = np.abs(np.asarray(t_boot, dtype=float))
        if boot.ndim != 2 or boot.shape[1] != len(t):  # noqa: PLR2004 -- a (B, m) matrix
            raise ValueError("t_boot must have shape (B, m)")
        order = np.argsort(-t, kind="stable")
        tail_max = np.maximum.accumulate(boot[:, order][:, ::-1], axis=1)[:, ::-1]
        raw = (tail_max >= t[order]).mean(axis=0)
        return self._to_input_order(np.maximum.accumulate(raw), order)

    def build_adjusted(
        self,
        ic_test: pd.DataFrame,
        metric: str = "ic_mean",
        window: str | None = None,
        t_boot: np.ndarray | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            Fill adjusted p-values and the HLZ flag on one metric (and window) across factors.

        Contract:
            Input:
                ic_test: DataFrame           -- IC_TEST rows of one campaign
                metric:  str                 -- rows to adjust (default the NW mean-IC test)
                window:  str | None          -- restrict to one window (None = all windows)
                t_boot:  ndarray | None      -- (B, m) bootstrap t for Romano-Wolf, rows in the
                                                order of the selected IC_TEST rows
            Output:
                DataFrame  -- IC_TEST; selected rows get p_adj_holm, p_adj_bhy, p_adj_romano_wolf
                              (NaN without t_boot) and hlz_pass (1.0 if |t| >= hurdle)
            Raises:
                SchemaError -- ic_test is not IC_TEST
                ValueError  -- t_boot shape does not match the selected rows
        """
        frame = IC_TEST.validate(IC_TEST.normalize(ic_test, strict=True)).copy()
        mask = frame["metric"] == metric
        if window is not None:
            mask &= frame["window"] == window
        if not mask.any():
            return frame
        chosen = frame.loc[mask]
        frame.loc[mask, "p_adj_holm"] = self.compute_holm(chosen["p"].to_numpy())
        frame.loc[mask, "p_adj_bhy"] = self.compute_bhy(chosen["p"].to_numpy())
        if t_boot is not None:
            frame.loc[mask, "p_adj_romano_wolf"] = self.compute_romano_wolf(
                chosen["t"].to_numpy(), t_boot
            )
        frame.loc[mask, "hlz_pass"] = (chosen["t"].abs() >= self._hurdle).astype(float)
        return IC_TEST.validate(frame)

    @staticmethod
    def _to_input_order(sorted_values: np.ndarray, order: np.ndarray) -> np.ndarray:
        out = np.empty_like(sorted_values)
        out[order] = sorted_values
        return out
