"""First trading session a row may be used, from its known-on column and rule (D-063, §11)."""

from __future__ import annotations

import calendar
import datetime as dt

import pandas as pd

from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.date_codec import DateCodec
from quant_cn.lake.trading_calendar import TradingCalendar

MONTH_KEY = 6


class EffectiveDateResolver:
    """
    Purpose:
        Turn a dataset's `known_on` value into `effective_date`, the first China trading session
        the row may be used (FACTOR_TESTING_DESIGN §11):
        as_is          -> that session, or the next one if the day is closed (same-day data);
        next_session   -> the first session strictly after (FRED US observations, analyst reports);
        period_end_lag -> period end (a YYYYMM month or YYYYMMDD date) + release_lag_days, then the
                          first session on or after (monthly macro without an announce date).

    Contract:
        Input:
            calendar: TradingCalendar  -- must cover every effective date asked for
            codec:    DateCodec
        Output:
            instance; `compute`, `get_effective_date`
        Raises:
            (none at construction)

    Used by:
        (none yet)  -- macro / FRED alignment in plan 11 phases 5-6, factors in plan 04

    Test cases:
        TC-EDR-001  as_is keeps a session and rolls a weekend or holiday to the next session
        TC-EDR-002  next_session: a US Friday observation becomes the following China session
        TC-EDR-003  period_end_lag: a monthly print is effective from month end + lag, on or after
        TC-EDR-004  compute adds effective_date per row; missing known_on stays empty
    """

    def __init__(self, calendar: TradingCalendar, codec: DateCodec) -> None:
        self._calendar = calendar
        self._codec = codec

    def get_effective_date(self, known_on: str, spec: DatasetSpec) -> str:
        """
        Purpose:
            Effective session for one known-on value under the dataset's rule.

        Contract:
            Input:
                known_on: str  -- YYYYMMDD, or YYYYMM for period_end_lag months
                spec:     DatasetSpec  -- known_on_rule, release_lag_days
            Output:
                str  -- YYYYMMDD trading session
            Raises:
                ValueError  -- malformed known_on
                LakeError   -- trade_cal missing or not far enough ahead
        """
        if spec.known_on_rule == "next_session":
            return self._calendar.get_next(self._codec.validate(known_on))
        if spec.known_on_rule == "period_end_lag":
            end = self._get_period_end(known_on)
            released = self._codec.to_str(end + dt.timedelta(days=spec.release_lag_days))
            return self._get_on_or_after(released)
        return self._get_on_or_after(self._codec.validate(known_on))

    def compute(self, frame: pd.DataFrame, spec: DatasetSpec) -> pd.DataFrame:
        """
        Purpose:
            Copy of `frame` with an `effective_date` column.

        Contract:
            Input:
                frame: DataFrame  -- rows of `spec`, with its known_on column
                spec:  DatasetSpec -- must declare known_on
            Output:
                DataFrame  -- same rows plus effective_date (string; NA where known_on is missing)
            Raises:
                ValueError  -- spec has no known_on column
                LakeError   -- calendar too short
        """
        if not spec.known_on:
            raise ValueError(f"{spec.name} has no known_on column")
        cache: dict[str, str] = {}
        values: list[object] = []
        for raw in frame[spec.known_on]:
            if pd.isna(raw) or not str(raw):
                values.append(pd.NA)
                continue
            key = str(raw)
            if key not in cache:
                cache[key] = self.get_effective_date(key, spec)
            values.append(cache[key])
        return frame.assign(effective_date=pd.Series(values, index=frame.index, dtype="string"))

    def _get_on_or_after(self, date: str) -> str:
        return date if self._calendar.is_open(date) else self._calendar.get_next(date)

    def _get_period_end(self, period: str) -> dt.date:
        if len(period) == MONTH_KEY and period.isdigit():
            year, month = int(period[:4]), int(period[4:])
            return dt.date(year, month, calendar.monthrange(year, month)[1])
        return self._codec.to_date(period)
