"""Trading-day arithmetic from the downloaded `trade_cal` (SRC_DESIGN §2.2)."""

from __future__ import annotations

import bisect

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery

_VIEW = "raw.trade_cal"


class TradingCalendar:
    """
    Purpose:
        Answer trading-day questions (sessions in a range, is_open, next, prev) from the SSE
        calendar in the lake; loads lazily so it works after trade_cal is fetched in the same run.

    Contract:
        Input:
            query: LakeQuery  -- reads raw.trade_cal (cal_date, is_open)
        Output:
            instance; `sessions`, `is_open`, `next`, `prev`, `reload`
        Raises:
            (none at construction)

    Used by:
        data_loading.DateSweepFetcher.list_keys  -- trading days for trade_date sweeps
        data_loading.FetcherFactory      -- injected into DateSweepFetcher
        cli.QuantCnCli                   -- composition root

    Test cases:
        TC-TCA-001  sessions returns open days in range, inclusive, ascending
        TC-TCA-002  is_open / next / prev around a weekend
        TC-TCA-003  missing trade_cal raises LakeError
        TC-TCA-004  next past the last known session raises LakeError
    """

    def __init__(self, query: LakeQuery) -> None:
        self._query = query
        self._days: list[str] | None = None

    def refresh(self) -> None:
        """
        Purpose:
            Drop the cached calendar so the next call re-reads trade_cal.

        Contract:
            Input:
                (none)
            Output:
                None
            Raises:
                (none)
        """
        self._days = None

    def list_sessions(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            Trading days within [start, end].

        Contract:
            Input:
                start: str; end: str  -- YYYYMMDD
            Output:
                list[str]  -- ascending; empty when none
            Raises:
                LakeError  -- trade_cal not downloaded
        """
        days = self._load()
        return days[bisect.bisect_left(days, start) : bisect.bisect_right(days, end)]

    def is_open(self, date: str) -> bool:
        """
        Purpose:
            True if `date` is a trading day.

        Contract:
            Input:
                date: str  -- YYYYMMDD
            Output:
                bool
            Raises:
                LakeError  -- trade_cal not downloaded
        """
        days = self._load()
        i = bisect.bisect_left(days, date)
        return i < len(days) and days[i] == date

    def get_next(self, date: str) -> str:
        """
        Purpose:
            First trading day strictly after `date`.

        Contract:
            Input:
                date: str  -- YYYYMMDD
            Output:
                str
            Raises:
                LakeError  -- trade_cal missing or `date` at/after the last known session
        """
        days = self._load()
        i = bisect.bisect_right(days, date)
        if i >= len(days):
            raise LakeError(f"no trading day after {date} in trade_cal")
        return days[i]

    def get_prev(self, date: str) -> str:
        """
        Purpose:
            Last trading day strictly before `date`.

        Contract:
            Input:
                date: str  -- YYYYMMDD
            Output:
                str
            Raises:
                LakeError  -- trade_cal missing or `date` at/before the first known session
        """
        days = self._load()
        i = bisect.bisect_left(days, date)
        if i == 0:
            raise LakeError(f"no trading day before {date} in trade_cal")
        return days[i - 1]

    def _load(self) -> list[str]:
        if self._days is None:
            if not self._query.has_view(_VIEW):
                raise LakeError("trade_cal is not downloaded; run the trade_cal step first")
            df = self._query.sql(f"SELECT DISTINCT cal_date FROM {_VIEW} WHERE is_open = 1")
            self._days = sorted(str(d) for d in df["cal_date"])
        return self._days
