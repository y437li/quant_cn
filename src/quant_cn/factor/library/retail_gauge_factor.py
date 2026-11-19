"""散户温度计 RetailGauge as a factor: minus the latest gauge reading (plan 21 ph6)."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from quant_cn.factor.base_factor import BaseFactor, FactorInputs


class RetailGaugeFactor(BaseFactor):
    """
    Purpose:
        value_raw = -pct of the latest RetailGauge reading (derived.retail_gauge, plan 21) with
        as_of on or before t and at most `max_age_days` calendar days old (a quarter's first 14
        sessions have no new reading). A low reading means retail is leaving, which the research
        found to be followed by better returns (D-155: the top decile trails by ~3.8%/qtr), so the
        sign is flipped to the library's higher-is-better convention. The reading at as_of uses
        data known by its close, so the value at t is point in time.

    Contract:
        Input:
            name: str; max_age_days: int >= 1 (default 45)
        Output:
            instance; BaseFactor API (inputs prices and retail_gauge)
        Raises:
            ValueError  -- max_age_days < 1

    Used by:
        (none yet)

    Test cases:
        TC-RGFA-001  each session takes the latest reading on or before it (a later reading
                     does not change earlier sessions); value_raw = -pct
        TC-RGFA-002  a reading older than max_age_days gives no value; exactly max_age_days
                     does; max_age_days < 1 raises ValueError
    """

    inputs = ("prices", "retail_gauge")

    def __init__(self, name: str, max_age_days: int = 45) -> None:
        super().__init__(name)
        if max_age_days < 1:
            raise ValueError("max_age_days must be >= 1")
        self._max_age = max_age_days

    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        """
        Purpose:
            Minus the latest fresh gauge reading per stock and session.

        Contract:
            Input:
                inputs: FactorInputs  -- dense prices (session grid) and retail_gauge
            Output:
                DataFrame  -- trade_date, ts_code, value_raw (NaN without a fresh reading)
            Raises:
                (none)
        """
        grid = inputs.prices[["trade_date", "ts_code"]].copy()
        gauge = inputs.retail_gauge
        if gauge.empty:
            return grid.assign(value_raw=float("nan"))
        readings = gauge[["as_of", "ts_code", "pct"]].copy()
        for frame, col in ((grid, "trade_date"), (readings, "as_of")):
            frame["k"] = self._to_ordinal(frame[col])
            frame["ts_code"] = frame["ts_code"].astype(str)  # string NA dtypes differ
        joined = pd.merge_asof(
            grid.sort_values("k"),
            readings.sort_values("k")
            .rename(columns={"k": "k_read"})
            .assign(k=lambda f: f["k_read"])[["k", "k_read", "ts_code", "pct"]],
            on="k",
            by="ts_code",
            direction="backward",
        )
        fresh = (joined["k"] - joined["k_read"]) <= self._max_age
        value = (-joined["pct"].astype(float)).where(fresh)
        return joined[["trade_date", "ts_code"]].assign(value_raw=value)

    @staticmethod
    def _to_ordinal(dates: pd.Series) -> pd.Series:
        days = {d: dt.date(int(d[:4]), int(d[4:6]), int(d[6:])).toordinal() for d in dates.unique()}
        return dates.map(days).astype("int64")
