"""Realised volatility of price series and its trailing percentile (plans 30 and 31)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

PERIODS_PER_YEAR = 252


class RealizedVolCalculator:
    """
    Purpose:
        Annualised realised volatility of close-price columns and the trailing percentile of
        any series. Vol = rolling sample std of daily log returns over `window` sessions x
        sqrt(PERIODS_PER_YEAR) x 100 (percent). The percentile of a value is the share of the
        trailing `pct_window` non-missing values at or below it, from `pct_min_obs` values on.

    Contract:
        Input:
            pct_window: int >= 1; pct_min_obs: int >= 1
        Output:
            instance; `compute_vol(closes, window) -> DataFrame` (same index and columns, %);
            `compute_rank_pct(series) -> Series` (fractions 0..1, NaN before pct_min_obs)
        Raises:
            (none)

    Used by:
        portfolio.SectorMonitorBuilder  -- company and index vols (plan 31)
        portfolio.MarketSignalReader  -- valuation percentile (5-year window)
        cli.AppServiceBuilder  -- `build_sector_monitor`
        portfolio.SmallCapWatchBuilder  -- index vols and the 1000-300 gap
        cli.ReportCommands  -- builds it for `smallcap-watch`

    Test cases:
        TC-RVC-001  compute_vol equals log-return std x sqrt(252) x 100; first window NaN
        TC-RVC-002  compute_rank_pct: share at or below the latest of the trailing window,
                    NaN before min_obs, missing values skipped and kept missing
    """

    def __init__(self, pct_window: int, pct_min_obs: int) -> None:
        self._pct_window = pct_window
        self._pct_min_obs = pct_min_obs

    def compute_vol(self, closes: pd.DataFrame, window: int) -> pd.DataFrame:
        """
        Purpose:
            Rolling annualised realised vol of every column.

        Contract:
            Input:
                closes: DataFrame  -- index sessions ascending, one column per series
                window: int >= 2   -- sessions per estimate
            Output:
                DataFrame  -- same shape, percent, NaN until `window` returns exist
            Raises:
                (none)
        """
        ratio = closes / closes.shift(1)
        logret = pd.DataFrame(
            np.log(ratio.to_numpy(dtype=float)), index=ratio.index, columns=ratio.columns
        )
        return logret.rolling(window).std() * math.sqrt(PERIODS_PER_YEAR) * 100

    def compute_rank_pct(self, series: pd.Series) -> pd.Series:
        """
        Purpose:
            Trailing percentile of each value (NaN-aware).

        Contract:
            Input:
                series: Series
            Output:
                Series  -- same index; fractions 0..1
            Raises:
                (none)
        """
        clean = series.dropna()
        pct = clean.rolling(self._pct_window, min_periods=self._pct_min_obs).apply(
            lambda x: float((x <= x[-1]).mean()), raw=True
        )
        return pct.reindex(series.index)
