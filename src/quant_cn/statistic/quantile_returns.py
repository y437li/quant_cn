"""Forward returns by factor quantile (plan 04 phase 2)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.core.frames import FACTOR_PANEL, FORWARD_RETURN, QUANTILE_RETURNS


class QuantileReturns:
    """
    Purpose:
        Sort names into n quantiles of the factor within each date and horizon, and report each
        quantile's equal-weighted mean forward return plus the long-short spread (top minus
        bottom, stored as quantile 0): the monotone "ladder" that complements the IC.

    Contract:
        Input:
            n_quantiles: int >= 2  -- default 5
        Output:
            instance; `compute`
        Raises:
            ValueError  -- n_quantiles < 2

    Used by:
        (none yet)

    Test cases:
        TC-QR-001  a monotone factor gives an increasing ladder and a positive long-short
        TC-QR-002  quantile n counts sum to the matched names; 0 is top minus bottom
    """

    def __init__(self, n_quantiles: int = 5) -> None:
        if n_quantiles < 2:  # noqa: PLR2004 -- a spread needs two buckets
            raise ValueError("n_quantiles must be >= 2")
        self._n = n_quantiles

    def compute(self, factors: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Mean forward return per quantile, date, factor and horizon.

        Contract:
            Input:
                factors: DataFrame  -- FACTOR_PANEL; returns: DataFrame -- FORWARD_RETURN
            Output:
                DataFrame  -- QUANTILE_RETURNS; quantile q = ceil(rank_pct(value) * n) in 1..n
                              (ties by average rank); ret = mean fwd_return; quantile 0: ret =
                              ret_n - ret_1, n = names in the two extremes
            Raises:
                SchemaError  -- inputs are not FACTOR_PANEL / FORWARD_RETURN
        """
        f = FACTOR_PANEL.validate(factors)[["trade_date", "ts_code", "factor", "value"]]
        joined = f.merge(FORWARD_RETURN.validate(returns), on=["trade_date", "ts_code"])
        joined = joined.dropna(subset=["value", "fwd_return"])
        keys = ["trade_date", "factor", "horizon"]
        pct = joined.groupby(keys)["value"].rank(pct=True)
        joined = joined.assign(quantile=np.ceil(pct * self._n).clip(1, self._n).astype(float))
        ladder = (
            joined.groupby([*keys, "quantile"])["fwd_return"]
            .agg(ret="mean", n="size")
            .reset_index()
        )
        wide = ladder.pivot_table(index=keys, columns="quantile", values=["ret", "n"])
        spread = pd.DataFrame(
            {
                "ret": wide[("ret", float(self._n))] - wide[("ret", 1.0)],
                "n": wide[("n", float(self._n))] + wide[("n", 1.0)],
                "quantile": 0.0,
            }
        ).reset_index()
        out = pd.concat([ladder.assign(n=ladder["n"].astype(float)), spread], ignore_index=True)
        out = out.sort_values([*keys, "quantile"]).reset_index(drop=True)
        return QUANTILE_RETURNS.validate(QUANTILE_RETURNS.normalize(out, strict=True))
