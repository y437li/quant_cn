"""Map a dataset's sweep kind to its fetcher class; new datasets of a known kind need no code."""

from __future__ import annotations

from collections.abc import Mapping

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
    DateWindowFetcher,
    EnumFetcher,
    PeriodSweepFetcher,
    SingleCallFetcher,
)
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.trading_calendar import TradingCalendar


class FetcherFactory:
    """
    Purpose:
        Build the right fetcher for a DatasetSpec and inject the shared dependencies.

    Contract:
        Input:
            config, client, store, fetch_log, run_log, clock, calendar, codec  -- shared services
            extra_clients: Mapping[str, BaseApiClient] | None  -- clients for non-tushare sources
            query:         LakeQuery | None  -- needed for sweep.values_from_dataset
        Output:
            instance; `build`
        Raises:
            (none at construction)

    Used by:
        pipeline.DownloadPipeline  -- one fetcher per requested dataset
        cli.ServiceBuilder         -- injected type or call

    Test cases:
        TC-FF-001  each sweep kind maps to its fetcher class
        TC-FF-002  enum values resolved from values or values_from; missing list raises ConfigError
        TC-FF-003  values_from_dataset keys resolved from a curated dataset with a filter
        TC-FF-004  source selects the client; an unconfigured source raises ConfigError
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
        extra_clients: Mapping[str, BaseApiClient] | None = None,
        query: LakeQuery | None = None,
    ) -> None:
        self._config = config
        self._clients: dict[str, BaseApiClient] = {"tushare": client, **(extra_clients or {})}
        self._store, self._fetch_log, self._run_log, self._clock = store, fetch_log, run_log, clock
        self._query = query
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
                ConfigError  -- enum sweep without resolvable values, or no client for the source
        """
        client = self._clients.get(spec.source)
        if client is None:
            raise ConfigError(f"{spec.name}: no client configured for source {spec.source!r}")
        deps = (client, self._store, self._fetch_log, self._run_log, self._clock)
        kind = spec.sweep.kind
        if kind == "none":
            return SingleCallFetcher(spec, *deps)
        if kind == "date_window":
            return DateWindowFetcher(spec, *deps, codec=self._codec)
        if kind in ("list_status", "ts_code", "exchange"):
            return EnumFetcher(spec, *deps, values=self._list_values(spec))
        if kind in ("trade_date", "ann_date"):
            return DateSweepFetcher(spec, *deps, calendar=self._calendar, codec=self._codec)
        return PeriodSweepFetcher(spec, *deps, codec=self._codec)

    def _list_values(self, spec: DatasetSpec) -> list[str]:
        source = spec.sweep.values_from_dataset
        if source is not None:
            if self._query is None:
                raise ConfigError(f"{spec.name}: values_from_dataset needs a LakeQuery")
            where = f" WHERE {source.where}" if source.where else ""
            table = f"curated.{source.dataset}{where}"
            sql = f"SELECT DISTINCT {source.column} AS k FROM {table} ORDER BY 1"
            return [str(k) for k in self._query.sql(sql)["k"]]
        if spec.sweep.values:
            return list(spec.sweep.values)
        name = spec.sweep.values_from
        if name and self._config.enum_values.get(name):
            return list(self._config.enum_values[name])
        raise ConfigError(f"{spec.name}: enum sweep needs sweep.values or a valid values_from")
