"""Injectable time source so sleeps and "today" are controllable in tests (SRC_DESIGN §2.1)."""

from __future__ import annotations

import datetime as dt
import time


class Clock:
    """
    Purpose:
        The single source of wall time, monotonic time and sleeping; tests inject a fake subclass.

    Contract:
        Input:
            (none)
        Output:
            instance; methods below
        Raises:
            (none)

    Used by:
        data_loading.TushareClient       -- retry and rate-limit sleeps
        core.BaseFetcher.run             -- per-key duration
        lake.RunLog                      -- event timestamps
        lake.Compactor.rebuild           -- manifest timestamp
        pipeline.DownloadPipeline        -- default end date (today)
        cli.QuantCnCli                   -- composition root
        data_loading.DateSweepFetcher    -- injected type or call
        data_loading.EnumFetcher         -- injected type or call
        data_loading.FetcherFactory      -- injected type or call
        data_loading.PeriodSweepFetcher  -- injected type or call

    Test cases:
        TC-CL-001  today_str is YYYYMMDD and equals get_now().date()
        TC-CL-002  sleep(0) returns immediately; monotonic is non-decreasing
    """

    def get_now(self) -> dt.datetime:
        """
        Purpose:
            Current local wall time.

        Contract:
            Input:
                (none)
            Output:
                datetime.datetime  -- naive local time
            Raises:
                (none)
        """
        return dt.datetime.now()

    def get_today(self) -> str:
        """
        Purpose:
            Today's date as a Tushare `YYYYMMDD` string.

        Contract:
            Input:
                (none)
            Output:
                str  -- 8 digits
            Raises:
                (none)
        """
        return self.get_now().strftime("%Y%m%d")

    def get_monotonic(self) -> float:
        """
        Purpose:
            Monotonic seconds for measuring durations.

        Contract:
            Input:
                (none)
            Output:
                float  -- seconds, non-decreasing
            Raises:
                (none)
        """
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        """
        Purpose:
            Block for `seconds`; fakes record the call instead.

        Contract:
            Input:
                seconds: float  -- >= 0
            Output:
                None
            Raises:
                (none)
        """
        time.sleep(seconds)
