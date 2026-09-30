"""Tradeable forward returns and cross-sectional information coefficients (§10, §11)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
import pandas as pd

from quant_cn.core.frames import FACTOR_PANEL, FORWARD_RETURN, IC_SERIES, PRICE_PANEL

Method = Literal["spearman", "pearson"]
Entry = Literal["open", "close"]
MIN_NAMES = 30


class IcCalculator:
    """
    Purpose:
        Per-date information coefficient between factor values and forward returns across the
        universe: IC_t = corr_rank(f_{i,t}, r_{i,t->t+h}) (Spearman; Pearson on the values as a
        variant). Forward returns are tradeable (FACTOR_TESTING_DESIGN §10, §11): the factor known
        at the close of t is traded at the next open, r = P_adj close(t+h) / P_adj open(t+1) - 1;
        close-to-close is available for comparison only.

    Contract:
        Input:
            method:    "spearman" | "pearson"
            min_names: int >= 3  -- dates with fewer matched names get no IC
        Output:
            instance; `build_forward_returns`, `compute`
        Raises:
            ValueError  -- min_names < 3

    Used by:
        factor.FactorEvaluator  -- injected type or call
        cli.ServiceBuilder      -- injected type or call

    Test cases:
        TC-ICC-001  open entry: r = close_adj(t+h) / open_adj(t+1) - 1; the last h dates are NaN
        TC-ICC-002  a suspended session (NaN row in dense prices) makes the return NaN
        TC-ICC-003  Spearman IC of a perfectly monotone factor is 1; reversed is -1; n counted
        TC-ICC-004  dates with fewer than min_names matched names are dropped
    """

    def __init__(self, method: Method = "spearman", min_names: int = MIN_NAMES) -> None:
        if min_names < 3:  # noqa: PLR2004 -- a correlation needs three points
            raise ValueError("min_names must be >= 3")
        self._method = method
        self._min_names = min_names

    def build_forward_returns(
        self, prices: pd.DataFrame, horizons: Sequence[int], entry: Entry = "open"
    ) -> pd.DataFrame:
        """
        Purpose:
            Forward returns per stock, session and horizon from dense adjusted prices.

        Contract:
            Input:
                prices:   DataFrame      -- PRICE_PANEL from LakeReader.read_prices(dense=True):
                                            one row per session inside each stock's span
                horizons: Sequence[int]  -- h >= 1 in sessions
                entry:    "open" | "close"
            Output:
                DataFrame  -- FORWARD_RETURN; open: r_{t->t+h} = close_adj(t+h) / (open(t+1) *
                              adj_factor(t+1)) - 1; close: close_adj(t+h) / close_adj(t) - 1
                              (§10); NaN where an endpoint is missing (suspended, end of data)
            Raises:
                SchemaError  -- prices is not PRICE_PANEL
                ValueError   -- a horizon < 1
        """
        if any(h < 1 for h in horizons):
            raise ValueError("horizons must be >= 1")
        panel = PRICE_PANEL.validate(prices).sort_values(["ts_code", "trade_date"])
        grouped = panel.groupby("ts_code", sort=False)
        open_adj = panel["open"] * panel["adj_factor"]
        start = (
            grouped["close_adj"].shift(0)
            if entry == "close"
            else open_adj.groupby(panel["ts_code"]).shift(-1)
        )
        frames = []
        for h in horizons:
            end = grouped["close_adj"].shift(-h)
            frames.append(
                pd.DataFrame(
                    {
                        "trade_date": panel["trade_date"],
                        "ts_code": panel["ts_code"],
                        "horizon": float(h),
                        "fwd_return": end / start - 1,
                    }
                )
            )
        out = pd.concat(frames, ignore_index=True).sort_values(["trade_date", "ts_code", "horizon"])
        return FORWARD_RETURN.validate(
            FORWARD_RETURN.normalize(out.reset_index(drop=True), strict=True)
        )

    def compute(self, factors: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            IC_t per date, factor and horizon.

        Contract:
            Input:
                factors: DataFrame  -- FACTOR_PANEL (value used; universe already applied)
                returns: DataFrame  -- FORWARD_RETURN
            Output:
                DataFrame  -- IC_SERIES: ic = Spearman (ranks within date) or Pearson correlation
                              of value and fwd_return over names with both present; n = names;
                              dates with n < min_names or zero variance dropped
            Raises:
                SchemaError  -- inputs are not FACTOR_PANEL / FORWARD_RETURN
        """
        f = FACTOR_PANEL.validate(factors)[["trade_date", "ts_code", "factor", "value"]]
        r = FORWARD_RETURN.validate(returns)
        joined = f.merge(r, on=["trade_date", "ts_code"]).dropna(subset=["value", "fwd_return"])
        keys = ["trade_date", "factor", "horizon"]
        if self._method == "spearman":
            joined = joined.assign(
                value=joined.groupby(keys)["value"].rank(),
                fwd_return=joined.groupby(keys)["fwd_return"].rank(),
            )
        x, y = joined["value"], joined["fwd_return"]
        sums = (
            joined.assign(xy=x * y, xx=x * x, yy=y * y)
            .groupby(keys)
            .agg(
                n=("value", "size"),
                sx=("value", "sum"),
                sy=("fwd_return", "sum"),
                sxy=("xy", "sum"),
                sxx=("xx", "sum"),
                syy=("yy", "sum"),
            )
        )
        cov = sums["sxy"] - sums["sx"] * sums["sy"] / sums["n"]
        var_x = sums["sxx"] - sums["sx"] ** 2 / sums["n"]
        var_y = sums["syy"] - sums["sy"] ** 2 / sums["n"]
        ic: pd.Series = cov / np.sqrt(var_x * var_y)
        out = pd.DataFrame({"ic": ic, "n": sums["n"].astype(float)}).reset_index()
        tiny = 1e-15
        out = out[
            (out["n"] >= self._min_names) & (var_x.to_numpy() > tiny) & (var_y.to_numpy() > tiny)
        ]
        return IC_SERIES.validate(IC_SERIES.normalize(out.reset_index(drop=True), strict=True))
