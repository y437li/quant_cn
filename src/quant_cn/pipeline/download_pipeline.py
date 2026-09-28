"""Download datasets from Tushare into the lake in dependency order (DATA_LOADING_DESIGN §2.1)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from quant_cn.core.base_fetch_log import BaseFetchLog
from quant_cn.core.base_fetcher import BaseFetcher
from quant_cn.core.base_step import BaseStep, ProgressHook
from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError, LakeError
from quant_cn.core.step_report import StepReport
from quant_cn.data_loading.fetcher_factory import FetcherFactory
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.pipeline.runner import BaseRunner, PipelineReport


class FetchStep(BaseStep):
    """
    Purpose:
        Adapt one dataset's fetcher to a pipeline step: keys computed in list_units (so the
        calendar fetched earlier in the run is visible), catalog view refreshed after the run.

    Contract:
        Input:
            fetcher: BaseFetcher; catalog: LakeCatalog; start: str; end: str; force: bool
        Output:
            instance; BaseStep API
        Raises:
            (none at construction)

    Used by:
        pipeline.DownloadPipeline.run  -- one step per dataset

    Test cases:
        TC-DP-002  crash on a key, rerun fetches only the remaining keys
    """

    def __init__(
        self, fetcher: BaseFetcher, catalog: LakeCatalog, start: str, end: str, force: bool
    ) -> None:
        self._fetcher = fetcher
        self._catalog = catalog
        self._start = start
        self._end = end
        self._force = force
        self._keys: list[str] = []

    @property
    def name(self) -> str:
        """
        Purpose:
            The dataset name.

        Contract:
            Input:
                (none)
            Output:
                str
            Raises:
                (none)
        """
        return self._fetcher.spec.name

    def list_units(self) -> list[str]:
        """
        Purpose:
            Compute the dataset's keys for the range.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- the keys
            Raises:
                LakeError  -- calendar missing for trade_date sweeps
        """
        self._keys = self._fetcher.list_keys(self._start, self._end)
        return list(self._keys)

    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        """
        Purpose:
            Fetch the prepared keys, then refresh the dataset's catalog views.

        Contract:
            Input:
                run_id: str; progress: ProgressHook | None
            Output:
                StepReport
            Raises:
                DataSourceError, PermissionDeniedError, SchemaError, LakeError
        """
        try:
            return self._fetcher.run(
                run_id, self._start, self._end, self._keys, self._force, progress
            )
        finally:
            self._catalog.refresh_view(self._fetcher.spec)


class DownloadPipeline:
    """
    Purpose:
        Resolve which datasets and date ranges to download, run one FetchStep per dataset through
        the runner, and regenerate the lake indexes; `dry_run` lists pending keys without calling
        the API.

    Contract:
        Input:
            config:    Config
            factory:   FetcherFactory
            runner:    BaseRunner
            catalog:   LakeCatalog
            fetch_log: BaseFetchLog
            clock:     Clock         -- default end date (today)
            codec:     DateCodec     -- validates overrides
        Output:
            instance; `run`
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- `download` command

    Test cases:
        TC-DP-001  dry run lists keys and pending counts without API calls
        TC-DP-002  crash on a key, rerun fetches only the remaining keys
        TC-DP-003  permission-blocked dataset does not stop later datasets
        TC-DP-004  long-history datasets start at long_history_start; others at default_start
        TC-DP-005  unknown dataset raises ConfigError; end before start raises ValueError
        TC-DP-006  start after the configured one on an overwrite range dataset raises ConfigError
        TC-DP-007  extend_days pushes a dataset's end past the run end (future calendar)
    """

    def __init__(
        self,
        config: Config,
        factory: FetcherFactory,
        runner: BaseRunner,
        catalog: LakeCatalog,
        fetch_log: BaseFetchLog,
        clock: Clock,
        codec: DateCodec,
    ) -> None:
        self._config = config
        self._factory = factory
        self._runner = runner
        self._catalog = catalog
        self._fetch_log = fetch_log
        self._clock = clock
        self._codec = codec

    def run(
        self,
        datasets: Sequence[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        dry_run: bool = False,
        force: bool = False,
    ) -> PipelineReport:
        """
        Purpose:
            Download the requested datasets (default: config.download.order).

        Contract:
            Input:
                datasets: Sequence[str] | None  -- subset, run in config order
                start:    str | None            -- override every dataset's start (YYYYMMDD)
                end:      str | None            -- default config.download.end or today
                dry_run:  bool                  -- report keys/pending only
                force:    bool                  -- refetch done keys
            Output:
                PipelineReport  -- status "dry_run" for dry runs
            Raises:
                ConfigError      -- unknown dataset, or a start that would shrink an overwrite
                                    range dataset's stored history (D-049)
                ValueError       -- malformed dates or end before start
                DataSourceError  -- non-permission fetch failure (progress kept)
        """
        names = self._list_datasets(datasets)
        stop = self._codec.validate(end or self._config.download.end or self._clock.get_today())
        ranges = {n: self._parse_range(n, start, stop) for n in names}
        if dry_run:
            return self._build_dry_run(ranges)
        steps = [
            FetchStep(
                self._factory.build(self._config.get_dataset(n)), self._catalog, *ranges[n], force
            )
            for n in names
        ]
        report = self._runner.run("download", steps)
        self._catalog.write_indexes()
        return report

    def _list_datasets(self, datasets: Sequence[str] | None) -> list[str]:
        if not datasets:
            return list(self._config.download.order)
        unknown = [d for d in datasets if d not in self._config.datasets]
        if unknown:
            raise ConfigError(f"unknown datasets: {unknown}")
        ordered = [n for n in self._config.download.order if n in datasets]
        return ordered + [d for d in datasets if d not in ordered]

    def _parse_range(self, name: str, start: str | None, end: str) -> tuple[str, str]:
        configured = self._config.get_start(name)
        begin = self._codec.validate(start or configured)
        spec = self._config.get_dataset(name)
        if spec.extend_days:
            end = self._codec.to_str(self._codec.to_date(end) + dt.timedelta(days=spec.extend_days))
        if begin > end:
            raise ValueError(f"{name}: start {begin} is after end {end}")
        if spec.refresh == "overwrite" and spec.sweep.range_params and begin > configured:
            raise ConfigError(
                f"{name} is refreshed by overwrite over its date range; start {begin} after the "
                f"configured {configured} would replace its stored history (D-049). Omit --start "
                "or change the dataset start in config."
            )
        return begin, end

    def _build_dry_run(self, ranges: dict[str, tuple[str, str]]) -> PipelineReport:
        report = PipelineReport(run_id="dry-run", status="dry_run")
        for name, (begin, stop) in ranges.items():
            fetcher = self._factory.build(self._config.get_dataset(name))
            try:
                keys = fetcher.list_keys(begin, stop)
            except LakeError as exc:
                report.steps.append(StepReport(name, status="dry_run", message=str(exc)))
                continue
            todo = fetcher.list_due_keys(keys)
            report.steps.append(
                StepReport(
                    name,
                    status="dry_run",
                    keys_total=len(keys),
                    skipped=len(keys) - len(todo),
                    message=f"{begin}..{stop}: {len(todo)} to fetch",
                )
            )
        return report
