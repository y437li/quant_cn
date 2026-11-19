"""Linear-pricing gap: market value against a consensus value with fading growth (plan 36)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.factor.base_factor import BaseFactor, FactorInputs

FY_END_FLOOR = 0.1  # years to the FY1 end, floored (FY1 may have just ended before May)
DAYS_PER_YEAR = 365.25


class PricingGapFactor(BaseFactor):
    """
    Purpose:
        Linear-pricing gap (plan 36, D-173). Value on session t from the latest consensus known
        on or before t (month-end readings, ConsensusPanelBuilder): FY1-FY3 median net profit
        discounted at `discount` from each fiscal year end (FY1 end floored at FY_END_FLOOR
        years), then growth starting at FY2 -> FY3 (clipped to [growth_floor, growth_cap])
        multiplied by `fade` each year for `fade_years` years, and an exit at `exit_pe` times the
        last profit. A missing FY3 = FY2 x FY2 / FY1. value_raw = -log(total_mv / value): higher
        = cheaper than the linear consensus price (the library's higher-is-better sign; the
        research gap is its negative). FY1 or FY2 <= 0 or no consensus -> NaN.

    Contract:
        Input:
            name: str; fade: float in (0, 1]; fade_years: int >= 0; exit_pe: float > 0;
            discount: float > 0; growth_floor < growth_cap; window_days: int > 0 (consensus
            note window)
        Output:
            instance; BaseFactor API; `consensus_days` = window_days; `compute_value` (pure)
        Raises:
            ValueError  -- parameters out of range

    Used by:
        (none yet)

    Test cases:
        TC-LPG-001  compute_value: known answer on a 3-year consensus; FY3 fill; growth clip;
                    FY1 or FY2 <= 0 -> NaN
        TC-LPG-002  compute_raw: each session takes the last consensus on or before it (PIT: a
                    later reading does not change earlier sessions); value_raw = -log(mv / value)
        TC-LPG-003  bad parameters raise ValueError; consensus_days = window_days
    """

    inputs = ("daily_basic", "consensus")
    basic_columns = ("total_mv",)

    def __init__(
        self,
        name: str,
        fade: float = 0.7,
        fade_years: int = 7,
        exit_pe: float = 15.0,
        discount: float = 0.09,
        growth_floor: float = -0.3,
        growth_cap: float = 1.0,
        window_days: int = 90,
    ) -> None:
        super().__init__(name)
        if not (0 < fade <= 1 and fade_years >= 0 and exit_pe > 0 and discount > 0):
            raise ValueError("fade in (0, 1], fade_years >= 0, exit_pe > 0, discount > 0")
        if growth_floor >= growth_cap or window_days <= 0:
            raise ValueError("growth_floor < growth_cap and window_days > 0")
        self._fade, self._years, self._exit = fade, fade_years, exit_pe
        self._r, self._clip, self._window = discount, (growth_floor, growth_cap), window_days

    @property
    def consensus_days(self) -> int:
        """
        Purpose:
            The consensus note window this factor needs.

        Contract:
            Input:
                (none)
            Output:
                int  -- window_days
            Raises:
                (none)
        """
        return self._window

    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        """
        Purpose:
            -log(market value / linear consensus value) per stock and session.

        Contract:
            Input:
                inputs: FactorInputs  -- daily_basic total_mv (10k CNY), consensus (10k CNY)
            Output:
                DataFrame  -- trade_date, ts_code, value_raw (NaN without a usable consensus)
            Raises:
                (none)
        """
        cols = ["trade_date", "ts_code", "value_raw"]
        if inputs.consensus.empty or inputs.daily_basic.empty:
            return pd.DataFrame(columns=cols)
        basic = inputs.daily_basic[["trade_date", "ts_code", "total_mv"]].copy()
        basic["k"] = basic["trade_date"].astype(str).astype(int)
        cons = inputs.consensus.rename(columns={"trade_date": "cons_date"}).copy()
        cons["k"] = cons["cons_date"].astype(str).astype(int)
        for frame in (basic, cons):  # the lake's string dtypes differ in their NA value
            frame["ts_code"] = frame["ts_code"].astype(str)
        joined = pd.merge_asof(
            basic.sort_values("k"),
            cons.sort_values("k"),
            on="k",
            by="ts_code",
            direction="backward",
        )
        session = joined["k"].astype(float)
        fy_end = joined["fy1"].astype(float) * 10000 + 1231
        years = (self._to_ordinal(fy_end) - self._to_ordinal(session)) / DAYS_PER_YEAR
        value = self.compute_value(
            joined["np1"].to_numpy(float), joined["np2"].to_numpy(float),
            joined["np3"].to_numpy(float), years.to_numpy(float),
        )  # fmt: skip
        mv = joined["total_mv"].where(joined["total_mv"] > 0).to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            joined["value_raw"] = -np.log(mv / value)
        return joined[cols]

    def compute_value(
        self, np1: np.ndarray, np2: np.ndarray, np3: np.ndarray, years: np.ndarray
    ) -> np.ndarray:
        """
        Purpose:
            The linear consensus value of each stock (same unit as the forecasts).

        Contract:
            Input:
                np1, np2, np3: arrays of FY1-FY3 forecasts (NaN np3 filled as FY2 x FY2 / FY1);
                years: array, years from the session to the FY1 end
            Output:
                ndarray  -- value; NaN where FY1 or FY2 <= 0 or missing
            Raises:
                (none)
        """
        ok = (np1 > 0) & (np2 > 0)
        np1, np2 = np.where(ok, np1, np.nan), np.where(ok, np2, np.nan)
        np3 = np.where(np.isnan(np3), np2 * np2 / np1, np3)
        ok &= np3 > 0
        t = np.maximum(years, FY_END_FLOOR)
        r = 1 + self._r
        value = np1 / r**t + np2 / r ** (t + 1) + np3 / r ** (t + 2)
        growth = np.clip(np3 / np2 - 1, *self._clip)
        profit = np3.copy()
        for k in range(1, self._years + 1):
            growth = growth * self._fade
            profit = profit * (1 + growth)
            value = value + profit / r ** (t + 2 + k)
        value = value + self._exit * profit / r ** (t + 2 + self._years)
        return np.where(ok, value, np.nan)

    @staticmethod
    def _to_ordinal(yyyymmdd: pd.Series) -> pd.Series:
        """Days since year 0 of YYYYMMDD integers (vectorised, no datetime parsing)."""
        y = (yyyymmdd // 10000).astype(float)
        m = (yyyymmdd // 100 % 100).astype(float)
        d = (yyyymmdd % 100).astype(float)
        a = (14 - m) // 12
        yy, mm = y + 4800 - a, m + 12 * a - 3
        return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400
