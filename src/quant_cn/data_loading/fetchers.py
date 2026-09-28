"""One fetcher per sweep pattern (DATA_LOADING_DESIGN §2.2); the endpoint comes from DatasetSpec."""

from __future__ import annotations

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
        index_daily by index ts_code.

    Contract:
        Input:
            BaseFetcher dependencies
            values: Sequence[str]  -- resolved enum keys, non-empty
        Output:
            instance; keys -> values; params -> {param: key} + extra (+ range)
        Raises:
            (none)

    Used by:
        data_loading.FetcherFactory.build  -- sweep kinds "list_status", "ts_code"

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
