"""One fetcher per sweep pattern (DATA_LOADING_DESIGN §2.2); the endpoint comes from DatasetSpec."""

from __future__ import annotations

import calendar
from collections.abc import Sequence

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.base_fetch_log import BaseFetchLog
from quant_cn.core.base_fetcher import BaseFetcher
from quant_cn.core.base_run_log import BaseRunLog
from quant_cn.core.base_store import BaseStore
from quant_cn.core.clock import Clock
from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.date_codec import DateCodec
from quant_cn.lake.trading_calendar import TradingCalendar


class SingleCallFetcher(BaseFetcher):
    """
    Purpose:
        Datasets fetched in one (paged) call, key "all": trade_cal, namechange.

    Contract:
        Input:
            BaseFetcher dependencies
        Output:
            instance; keys -> ["all"]; params -> extra_params (+ start/end if range_params)
        Raises:
            (none)

    Used by:
        data_loading.FetcherFactory.build  -- sweep kind "none"

    Test cases:
        TC-SCF-001  single key "all"; range params passed when configured
    """

    def list_keys(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            The single key.

        Contract:
            Input:
                start: str; end: str  -- unused
            Output:
                list[str]  -- ["all"]
            Raises:
                (none)
        """
        return ["all"]

    def build_params(self, key: str, start: str, end: str) -> dict[str, str]:
        """
        Purpose:
            Constant parameters, plus the run's date range when configured.

        Contract:
            Input:
                key: str; start: str; end: str
            Output:
                dict[str, str]
            Raises:
                (none)
        """
        out = dict(self.spec.sweep.extra_params)
        if self.spec.sweep.range_params:
            out.update(start_date=start, end_date=end)
        return out


class EnumFetcher(BaseFetcher):
    """
    Purpose:
        Datasets swept over an enumerated list: stock_basic by list_status (L, D, P),
        index_daily / fund_daily by ts_code, opt_basic by exchange.

    Contract:
        Input:
            BaseFetcher dependencies
            values: Sequence[str]  -- resolved enum keys, non-empty
        Output:
            instance; keys -> values; params -> {param: key} + extra (+ range)
        Raises:
            (none)

    Used by:
        data_loading.FetcherFactory.build  -- sweep kinds "list_status", "ts_code", "exchange"

    Test cases:
        TC-EF-001  keys are the configured values; params carry the key and range
    """

    def __init__(
        self,
        spec: DatasetSpec,
        client: BaseApiClient,
        store: BaseStore,
        fetch_log: BaseFetchLog,
        run_log: BaseRunLog,
        clock: Clock,
        values: Sequence[str],
    ) -> None:
        super().__init__(spec, client, store, fetch_log, run_log, clock)
        self._values = list(values)

    def list_keys(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            The enumerated values.

        Contract:
            Input:
                start: str; end: str  -- unused
            Output:
                list[str]
            Raises:
                (none)
        """
        return list(self._values)

    def build_params(self, key: str, start: str, end: str) -> dict[str, str]:
        """
        Purpose:
            Key parameter plus constants and optional date range.

        Contract:
            Input:
                key: str; start: str; end: str
            Output:
                dict[str, str]
            Raises:
                (none)
        """
        out = dict(self.spec.sweep.extra_params)
        out[str(self.spec.sweep.param)] = key
        if self.spec.sweep.range_params:
            out.update(start_date=start, end_date=end)
        return out


class DateSweepFetcher(BaseFetcher):
    """
    Purpose:
        Whole-market daily sweeps: trade_date keys are trading days (daily, adj_factor,
        daily_basic, moneyflow, stk_limit); ann_date keys are weekdays (event datasets).

    Contract:
        Input:
            BaseFetcher dependencies
            calendar: TradingCalendar
            codec:    DateCodec
        Output:
            instance; one key per day
        Raises:
            (none)

    Used by:
        data_loading.FetcherFactory.build  -- sweep kinds "trade_date", "ann_date"

    Test cases:
        TC-DSF-001  trade_date keys are calendar sessions in range
        TC-DSF-002  ann_date keys are weekdays in range
    """

    def __init__(
        self,
        spec: DatasetSpec,
        client: BaseApiClient,
        store: BaseStore,
        fetch_log: BaseFetchLog,
        run_log: BaseRunLog,
        clock: Clock,
        calendar: TradingCalendar,
        codec: DateCodec,
    ) -> None:
        super().__init__(spec, client, store, fetch_log, run_log, clock)
        self._calendar = calendar
        self._codec = codec

    def list_keys(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            Trading days (trade_date) or weekdays (ann_date) in [start, end].

        Contract:
            Input:
                start: str; end: str  -- YYYYMMDD
            Output:
                list[str]  -- ascending
            Raises:
                LakeError   -- trade_cal missing (trade_date sweeps)
                ValueError  -- malformed dates
        """
        if self.spec.sweep.kind == "trade_date":
            return self._calendar.list_sessions(start, end)
        return self._codec.list_weekdays(start, end)

    def build_params(self, key: str, start: str, end: str) -> dict[str, str]:
        """
        Purpose:
            {param: key} plus constants.

        Contract:
            Input:
                key: str; start: str; end: str
            Output:
                dict[str, str]
            Raises:
                (none)
        """
        return {**self.spec.sweep.extra_params, str(self.spec.sweep.param): key}


class PeriodSweepFetcher(BaseFetcher):
    """
    Purpose:
        Whole-market report-period sweeps (the *_vip fundamentals): one key per quarter end.

    Contract:
        Input:
            BaseFetcher dependencies
            codec: DateCodec
        Output:
            instance; keys -> quarter ends; params -> {"period": key}
        Raises:
            (none)

    Used by:
        data_loading.FetcherFactory.build  -- sweep kind "period"

    Test cases:
        TC-PSF-001  keys are quarter ends in range; params carry period
    """

    def __init__(
        self,
        spec: DatasetSpec,
        client: BaseApiClient,
        store: BaseStore,
        fetch_log: BaseFetchLog,
        run_log: BaseRunLog,
        clock: Clock,
        codec: DateCodec,
    ) -> None:
        super().__init__(spec, client, store, fetch_log, run_log, clock)
        self._codec = codec

    def list_keys(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            Quarter ends in [start, end].

        Contract:
            Input:
                start: str; end: str  -- YYYYMMDD
            Output:
                list[str]
            Raises:
                ValueError  -- malformed dates
        """
        return self._codec.list_quarter_ends(start, end)

    def build_params(self, key: str, start: str, end: str) -> dict[str, str]:
        """
        Purpose:
            {"period": key} plus constants.

        Contract:
            Input:
                key: str; start: str; end: str
            Output:
                dict[str, str]
            Raises:
                (none)
        """
        return {**self.spec.sweep.extra_params, "period": key}


class DateWindowFetcher(BaseFetcher):
    """
    Purpose:
        Range-only endpoints swept by calendar window (D-063): one call per month ("YYYYMM" keys)
        or year ("YYYY" keys) with start_date / end_date clipped to the run range. Used where offset
        paging is broken or capped (share_float; index_weight past 100k rows) or the API takes
        ranges only (FRED series, fund_nav ranges). With `sweep.value_param` and values, each
        window is fetched once per value: keys "<window>_<value>", window-major so the newest
        `refetch_recent` keys are the latest window of every value (D-069).

    Contract:
        Input:
            BaseFetcher dependencies
            codec:  DateCodec
            values: list[str] | None  -- required exactly when sweep.value_param is set
        Output:
            instance; keys -> windows in [start, end] (x values); params -> start_date, end_date,
            value_param + extra
        Raises:
            (none)

    Used by:
        data_loading.FetcherFactory.build  -- sweep kind "date_window"

    Test cases:
        TC-DWF-001  monthly windows cover the range and clip the first and last month
        TC-DWF-002  yearly windows use YYYY keys and full-year bounds inside the range
        TC-DWF-003  with value_param: window-major "<window>_<value>" keys, value passed as param
    """

    def __init__(
        self,
        spec: DatasetSpec,
        client: BaseApiClient,
        store: BaseStore,
        fetch_log: BaseFetchLog,
        run_log: BaseRunLog,
        clock: Clock,
        codec: DateCodec,
        values: list[str] | None = None,
    ) -> None:
        super().__init__(spec, client, store, fetch_log, run_log, clock)
        self._codec = codec
        self._values = values or []

    def list_keys(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            Window keys covering [start, end].

        Contract:
            Input:
                start: str; end: str  -- YYYYMMDD
            Output:
                list[str]  -- "YYYYMM" (month) or "YYYY" (year), ascending; with values,
                              "<window>_<value>" for every value inside each window
            Raises:
                ValueError  -- malformed dates or start > end
        """
        windows = self._list_windows(start, end)
        if not self.spec.sweep.value_param:
            return windows
        return [f"{w}_{v}" for w in windows for v in self._values]

    def build_params(self, key: str, start: str, end: str) -> dict[str, str]:
        """
        Purpose:
            start_date / end_date of the window, clipped to the run range (+ the swept value).

        Contract:
            Input:
                key: str  -- window key or "<window>_<value>"; start, end: str  -- run range
            Output:
                dict[str, str]
            Raises:
                (none)
        """
        window, _, value = key.partition("_")
        extra = dict(self.spec.sweep.extra_params)
        if self.spec.sweep.value_param:
            extra[self.spec.sweep.value_param] = value
        first, last = self._get_bounds(window)
        return {**extra, "start_date": max(first, start), "end_date": min(last, end)}

    def _list_windows(self, start: str, end: str) -> list[str]:
        lo, hi = self._codec.to_date(start), self._codec.to_date(end)
        if lo > hi:
            raise ValueError(f"start {start} is after end {end}")
        if self.spec.sweep.window == "year":
            return [str(y) for y in range(lo.year, hi.year + 1)]
        keys, year, month = [], lo.year, lo.month
        while (year, month) <= (hi.year, hi.month):
            keys.append(f"{year}{month:02d}")
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)  # noqa: PLR2004 -- December
        return keys

    @staticmethod
    def _get_bounds(window: str) -> tuple[str, str]:
        if len(window) == 4:  # noqa: PLR2004 -- YYYY
            return f"{window}0101", f"{window}1231"
        year, month = int(window[:4]), int(window[4:])
        return f"{window}01", f"{window}{calendar.monthrange(year, month)[1]:02d}"
