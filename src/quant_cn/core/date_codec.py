"""The only place that converts between `YYYYMMDD` strings and dates (D-005)."""

from __future__ import annotations

import datetime as dt

_FMT = "%Y%m%d"
_LEN = 8
_SATURDAY = 5


class DateCodec:
    """
    Purpose:
        Validate and convert Tushare `YYYYMMDD` date strings and generate date keys for sweeps.

    Contract:
        Input:
            date strings: str  -- exactly 8 digits forming a valid calendar date
        Output:
            str / datetime.date / list[str] sorted ascending, see each method
        Raises:
            ValueError  -- malformed date string or start > end

    Used by:
        core.Config.load                 -- validates configured start dates
        data_loading.DateSweepFetcher.keys    -- weekdays for ann_date sweeps
        data_loading.PeriodSweepFetcher.keys  -- quarter ends for period sweeps
        pipeline.DownloadPipeline.run    -- validates start/end overrides

    Test cases:
        TC-DC-001  to_date/to_str round trip
        TC-DC-002  malformed or impossible date raises ValueError
        TC-DC-003  quarter_ends inclusive of boundaries, sorted
        TC-DC-004  weekdays skips Saturday and Sunday
        TC-DC-005  start > end raises ValueError
    """

    def validate(self, value: str) -> str:
        """
        Purpose:
            Return `value` unchanged if it is a valid `YYYYMMDD` date string.

        Contract:
            Input:
                value: str  -- candidate date string
            Output:
                str  -- the same string
            Raises:
                ValueError  -- not 8 digits or not a real date
        """
        self.to_date(value)
        return value

    def to_date(self, value: str) -> dt.date:
        """
        Purpose:
            Parse a `YYYYMMDD` string.

        Contract:
            Input:
                value: str  -- 8 digits
            Output:
                datetime.date
            Raises:
                ValueError  -- malformed or impossible date
        """
        if len(value) != _LEN or not value.isdigit():
            raise ValueError(f"expected YYYYMMDD, got {value!r}")
        return dt.datetime.strptime(value, _FMT).date()

    def to_str(self, value: dt.date) -> str:
        """
        Purpose:
            Format a date as `YYYYMMDD`.

        Contract:
            Input:
                value: datetime.date
            Output:
                str  -- 8 digits
            Raises:
                (none)
        """
        return value.strftime(_FMT)

    def quarter_ends(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            Report periods (Mar 31, Jun 30, Sep 30, Dec 31) within [start, end].

        Contract:
            Input:
                start: str  -- YYYYMMDD, inclusive
                end:   str  -- YYYYMMDD, inclusive, >= start
            Output:
                list[str]  -- YYYYMMDD quarter ends, ascending; empty if none fall inside
            Raises:
                ValueError  -- malformed dates or start > end
        """
        lo, hi = self._range(start, end)
        out = []
        for year in range(lo.year, hi.year + 1):
            for month, day in ((3, 31), (6, 30), (9, 30), (12, 31)):
                q = dt.date(year, month, day)
                if lo <= q <= hi:
                    out.append(self.to_str(q))
        return out

    def weekdays(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            Monday-to-Friday dates within [start, end], for announcement-date sweeps.

        Contract:
            Input:
                start: str  -- YYYYMMDD, inclusive
                end:   str  -- YYYYMMDD, inclusive, >= start
            Output:
                list[str]  -- YYYYMMDD, ascending
            Raises:
                ValueError  -- malformed dates or start > end
        """
        lo, hi = self._range(start, end)
        days = (hi - lo).days + 1
        dates = (lo + dt.timedelta(days=i) for i in range(days))
        return [self.to_str(d) for d in dates if d.weekday() < _SATURDAY]

    def _range(self, start: str, end: str) -> tuple[dt.date, dt.date]:
        lo, hi = self.to_date(start), self.to_date(end)
        if lo > hi:
            raise ValueError(f"start {start} is after end {end}")
        return lo, hi
