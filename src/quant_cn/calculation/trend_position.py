"""Short-trend blend with volatility sizing (plan 24 rule, D-157; first used by plan 27)."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

YEAR = 252  # sessions per year for annualising volatility
MIN_VOL_WINDOW = 2


class TrendPosition:
    """
    Purpose:
        The trend rule of plan 24 on any price series: for each window n the signal is up when
        the price is above its level n sessions ago; the blend is the share of windows up
        (0..1); the size is min(1, vol_target / annualised vol of daily returns over vol_window);
        the position is blend x size. With vol_target None the position is the blend alone
        (the bond switch of plan 27).

    Contract:
        Input:
            windows:    list[int]     -- sessions, each > 0, at least one
            vol_target: float | None  -- annual vol target > 0, or None for no sizing
            vol_window: int           -- sessions of the vol estimate (> 1)
        Output:
            instance; `compute_blend(prices)`, `compute_position(prices)` -> DataFrame aligned
            with prices (NaN until the longest window, and for sizing the vol window, is filled);
            `build_summary(prices)` -> dict for the last row
        Raises:
            ValueError  -- empty or non-positive windows, vol_target <= 0, vol_window < 2

    Used by:
        portfolio.EtfCtaWeights  -- A股 position and bond switch

    Test cases:
        TC-TP-001  blend counts windows up; NaN until the longest window has a past price
        TC-TP-002  size caps at 1 for a calm series and halves when vol is twice the target
        TC-TP-003  vol_target None gives the blend; build_summary lists each window and the position
        TC-TP-004  bad windows, target or vol window raise ValueError
    """

    def __init__(self, windows: list[int], vol_target: float | None, vol_window: int) -> None:
        if not windows or min(windows) <= 0:
            raise ValueError(f"windows must be positive: {windows}")
        if vol_target is not None and vol_target <= 0:
            raise ValueError(f"vol_target must be > 0: {vol_target}")
        if vol_window < MIN_VOL_WINDOW:
            raise ValueError(f"vol_window must be >= 2: {vol_window}")
        self._windows = list(windows)
        self._target = vol_target
        self._vol_window = vol_window

    def compute_blend(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Share of windows whose signal is up, per column and date.

        Contract:
            Input:
                prices: DataFrame  -- dates x series, NaN before a series starts
            Output:
                DataFrame  -- same shape, values in {0, 1/k, .., 1} or NaN
            Raises:
                (none)
        """
        parts = [self._compute_signal(prices, n) for n in self._windows]
        total = parts[0]
        for p in parts[1:]:
            total = total + p
        return total / len(parts)

    def compute_position(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Blend x size per column and date.

        Contract:
            Input:
                prices: DataFrame  -- dates x series
            Output:
                DataFrame  -- same shape, values in [0, 1] or NaN
            Raises:
                (none)
        """
        blend = self.compute_blend(prices)
        if self._target is None:
            return blend
        return blend * self._compute_size(prices)

    def build_summary(self, prices: pd.Series) -> dict[str, Any]:
        """
        Purpose:
            The last row of one series: each window's signal, blend, vol, size and position.

        Contract:
            Input:
                prices: Series  -- one price series by date
            Output:
                dict  -- {windows: [{n, up}], blend, vol, size, position}; None where unknown
            Raises:
                (none)
        """
        frame = prices.to_frame("p")
        signals = [
            {"n": n, "up": self._to_flag(self._compute_signal(frame, n)["p"].iloc[-1])}
            for n in self._windows
        ]
        vol = self._compute_vol(frame)["p"].iloc[-1]
        size = self._compute_size(frame)["p"].iloc[-1] if self._target is not None else 1.0
        blend = self.compute_blend(frame)["p"].iloc[-1]
        return {
            "windows": signals,
            "blend": self._to_number(blend),
            "vol": self._to_number(vol),
            "size": self._to_number(size),
            "position": self._to_number(blend * size),
        }

    def _compute_signal(self, prices: pd.DataFrame, n: int) -> pd.DataFrame:
        past = prices.shift(n)
        return (prices > past).astype(float).where(past.notna() & prices.notna())

    def _compute_vol(self, prices: pd.DataFrame) -> pd.DataFrame:
        returns = prices.pct_change(fill_method=None)
        return returns.rolling(self._vol_window).std() * math.sqrt(YEAR)

    def _compute_size(self, prices: pd.DataFrame) -> pd.DataFrame:
        target = self._target if self._target is not None else 1.0
        return (target / self._compute_vol(prices)).clip(upper=1.0)

    @staticmethod
    def _to_flag(value: float) -> bool | None:
        return None if pd.isna(value) else bool(value > 0)

    @staticmethod
    def _to_number(value: float) -> float | None:
        return None if pd.isna(value) else round(float(value), 4)
