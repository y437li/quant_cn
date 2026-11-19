"""Track record of an ETF CTA paper run: NAV, return, vol, Sharpe, drawdown (plan 27)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from quant_cn.core.date_codec import DateCodec

YEAR = 252


class EtfCtaRecord:
    """
    Purpose:
        Summarise a daily NAV of a paper run (EtfCtaPaperBook) for the document: last NAV,
        annualised return, vol and Sharpe over cash (only after a year of sessions), max
        drawdown, calendar-year returns and weekly NAV / drawdown points.

    Contract:
        Input:
            codec: DateCodec
        Output:
            instance; `build(nav, cash)` -> dict
        Raises:
            (none at construction)

    Used by:
        portfolio.EtfCtaBook  -- back-test, paper and 含观点 records

    Test cases:
        TC-ECR-001  a year of NAV gives ann, vol, Sharpe, max dd, years and weekly points;
                    under a year ann and Sharpe are None
    """

    def __init__(self, codec: DateCodec) -> None:
        self._codec = codec

    def build(self, nav: pd.Series, cash: pd.Series) -> dict[str, Any]:
        """
        Purpose:
            The record of one NAV series.

        Contract:
            Input:
                nav:  Series  -- daily NAV by session (DatetimeIndex), starts near 1
                cash: Series  -- daily cash return by session
            Output:
                dict  -- {start, nav, ann, vol, sharpe, max_dd, years: [{year, ret}],
                         points: [{d, nav, dd}]}; fractions rounded to 4 places
            Raises:
                (none)
        """
        idx = pd.DatetimeIndex(nav.index)
        daily = nav.pct_change().fillna(nav.iloc[0] - 1.0)
        excess = daily - cash.reindex(daily.index).fillna(0.0)
        n = len(daily)
        sd = float(excess.std()) if n > 1 else float("nan")
        dd = nav / nav.cummax() - 1.0
        weekly = nav.groupby(idx.to_period("W")).tail(1)
        years = (1.0 + daily).groupby(idx.year).prod() - 1.0
        return {
            "start": self._codec.to_str(idx[0].date()),
            "nav": self._to_number(nav.iloc[-1]),
            "ann": self._to_number(nav.iloc[-1] ** (YEAR / n) - 1.0) if n >= YEAR else None,
            "vol": self._to_number(daily.std() * math.sqrt(YEAR)) if n > 1 else None,
            "sharpe": self._to_number(excess.mean() / sd * math.sqrt(YEAR))
            if n >= YEAR and sd > 0
            else None,
            "max_dd": self._to_number(dd.min()),
            "years": [
                {"year": int(y), "ret": self._to_number(float(v))}
                for y, v in zip(years.index, years.to_numpy(), strict=True)
            ],
            "points": [
                {
                    "d": self._codec.to_str(d.date()),
                    "nav": self._to_number(float(v)),
                    "dd": self._to_number(float(x)),
                }
                for d, v, x in zip(
                    pd.DatetimeIndex(weekly.index),
                    weekly.to_numpy(),
                    dd.loc[weekly.index],
                    strict=True,
                )
            ],
        }

    @staticmethod
    def _to_number(value: float) -> float | None:
        return (
            None
            if value is None or (isinstance(value, float) and np.isnan(value))
            else round(float(value), 4)
        )
