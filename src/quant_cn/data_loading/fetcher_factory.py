"""Map a dataset's sweep kind to its fetcher class; new datasets of a known kind need no code."""

from __future__ import annotations

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.base_fetch_log import BaseFetchLog
from quant_cn.core.base_fetcher import BaseFetcher
from quant_cn.core.base_run_log import BaseRunLog
from quant_cn.core.base_store import BaseStore
from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError
from quant_cn.data_loading.fetchers import (
    DateSweepFetcher,
    EnumFetcher,
    PeriodSweepFetcher,
    SingleCallFetcher,
)
from quant_cn.lake.trading_calendar import TradingCalendar


class FetcherFactory:
    """
    Purpose:
        Build the right fetcher for a DatasetSpec and inject the shared dependencies.

    Contract:
        Input:
            config, client, store, fetch_log, run_log, clock, calendar, codec  -- shared services
        Output:
            instance; `build`
        Raises:
            (none at construction)

    Used by:
        pipeline.DownloadPipeline        -- one fetcher per requested dataset
        cli.QuantCnCli                   -- composition root

    Test cases:
        TC-FF-001  each sweep kind maps to its fetcher class
        TC-FF-002  enum values resolved from values or values_from; missing list raises ConfigError
    """

    def __init__(
        self,
        config: Config,
        client: BaseApiClient,
        store: BaseStore,
        fetch_log: BaseFetchLog,
        run_log: BaseRunLog,
        clock: Clock,
        calendar: TradingCalendar,
        codec: DateCodec,
    ) -> None:
        self._config = config
        self._deps = (client, store, fetch_log, run_log, clock)
        self._calendar = calendar
        self._codec = codec

    def build(self, spec: DatasetSpec) -> BaseFetcher:
        """
        Purpose:
            Instantiate the fetcher for `spec.sweep.kind`.

        Contract:
            Input:
                spec: DatasetSpec
            Output:
                BaseFetcher  -- SingleCall / Enum / DateSweep / PeriodSweep
            Raises:
                ConfigError  -- enum sweep without resolvable values
        """
        kind = spec.sweep.kind
        if kind == "none":
            return SingleCallFetcher(spec, *self._deps)
        if kind in ("list_status", "ts_code"):
            return EnumFetcher(spec, *self._deps, values=self._values(spec))
        if kind in ("trade_date", "ann_date"):
            return DateSweepFetcher(spec, *self._deps, calendar=self._calendar, codec=self._codec)
        return PeriodSweepFetcher(spec, *self._deps, codec=self._codec)

    def _values(self, spec: DatasetSpec) -> list[str]:
        if spec.sweep.values:
            return list(spec.sweep.values)
        name = spec.sweep.values_from
        if name and self._config.enum_values.get(name):
            return list(self._config.enum_values[name])
        raise ConfigError(f"{spec.name}: enum sweep needs sweep.values or a valid values_from")
