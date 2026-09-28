"""Template for downloading a dataset key by key: skip done, fetch, write, log.

DATA_LOADING_DESIGN §2.1.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence

import pandas as pd

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.base_fetch_log import BaseFetchLog
from quant_cn.core.base_run_log import BaseRunLog
from quant_cn.core.base_step import ProgressHook
from quant_cn.core.base_store import BaseStore
from quant_cn.core.clock import Clock
from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.exceptions import DataSourceError
from quant_cn.core.step_report import StepReport

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """
    Purpose:
        Download one dataset as a sequence of keys; subclasses define the keys and the per-key
        parameters of one sweep pattern, never one endpoint.

    Contract:
        Input:
            spec:      DatasetSpec   -- endpoint, fields, refresh policy
            client:    BaseApiClient
            store:     BaseStore     -- raw writer
            fetch_log: BaseFetchLog  -- done keys
            run_log:   BaseRunLog    -- per-key events
            clock:     Clock         -- durations
        Output:
            instance; `run` returns StepReport
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        data_loading.SingleCallFetcher   -- subclass
        data_loading.EnumFetcher         -- subclass
        data_loading.DateSweepFetcher    -- subclass
        data_loading.PeriodSweepFetcher  -- subclass
        data_loading.FetcherFactory.build  -- return type
        pipeline.FetchStep               -- runs one fetcher per dataset
        pipeline.DownloadPipeline.run    -- dry-run keys

    Test cases:
        TC-BF-001  fetch run counts fetched/skipped/empty correctly
        TC-BF-002  done keys are skipped for append datasets; force refetches them
        TC-BF-003  overwrite datasets refetch every key
        TC-BF-004  refetch_recent always refetches the newest N keys
        TC-BF-005  empty result is marked done with 0 rows and writes no file
        TC-BF-006  failure on a key re-raises; earlier keys stay done and the log is saved
    """

    def __init__(
        self,
        spec: DatasetSpec,
        client: BaseApiClient,
        store: BaseStore,
        fetch_log: BaseFetchLog,
        run_log: BaseRunLog,
        clock: Clock,
    ) -> None:
        self.spec = spec
        self._client = client
        self._store = store
        self._fetch_log = fetch_log
        self._run_log = run_log
        self._clock = clock

    @abstractmethod
    def list_keys(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            All fetch keys for [start, end], ascending.

        Contract:
            Input:
                start: str  -- YYYYMMDD
                end:   str  -- YYYYMMDD, >= start
            Output:
                list[str]
            Raises:
                LakeError   -- a prerequisite (e.g. trading calendar) is missing
                ValueError  -- malformed dates
        """

    @abstractmethod
    def build_params(self, key: str, start: str, end: str) -> dict[str, str]:
        """
        Purpose:
            API parameters for one key.

        Contract:
            Input:
                key: str; start: str; end: str  -- the run's range, for range-parameter endpoints
            Output:
                dict[str, str]
            Raises:
                (none)
        """

    def list_due_keys(self, keys: Sequence[str], force: bool = False) -> list[str]:
        """
        Purpose:
            Keys that must be fetched: all if forced or overwrite, else pending plus the newest
            `refetch_recent` keys.

        Contract:
            Input:
                keys:  Sequence[str]  -- ascending
                force: bool
            Output:
                list[str]  -- subset of keys, input order
            Raises:
                LakeError  -- fetch log unreadable
        """
        if force or self.spec.refresh == "overwrite":
            return list(keys)
        recent = set(keys[len(keys) - self.spec.sweep.refetch_recent :])
        pending = set(self._fetch_log.list_pending(self.spec.name, keys))
        return [k for k in keys if k in pending or k in recent]

    def fetch_one(self, key: str, start: str, end: str) -> pd.DataFrame:
        """
        Purpose:
            Query the endpoint for one key.

        Contract:
            Input:
                key: str; start: str; end: str
            Output:
                DataFrame  -- vendor columns; may be empty
            Raises:
                DataSourceError, PermissionDeniedError
        """
        return self._client.query(
            self.spec.endpoint, self.build_params(key, start, end), self.spec.fields
        )

    def run(
        self,
        run_id: str,
        start: str,
        end: str,
        keys: Sequence[str] | None = None,
        force: bool = False,
        progress: ProgressHook | None = None,
    ) -> StepReport:
        """
        Purpose:
            Fetch every key that needs fetching, writing and logging each before the next.

        Contract:
            Input:
                run_id:   str
                start:    str  -- YYYYMMDD
                end:      str  -- YYYYMMDD
                keys:     Sequence[str] | None  -- precomputed; None = self.list_keys(start, end)
                force:    bool                  -- refetch done keys
                progress: ProgressHook | None   -- called (key, status) per key
            Output:
                StepReport  -- status "ok"
            Raises:
                DataSourceError, PermissionDeniedError  -- after logging the key as failed;
                                                          finished keys remain done
                SchemaError, LakeError                  -- write failed
        """
        all_keys = list(keys) if keys is not None else self.list_keys(start, end)
        todo = self.list_due_keys(all_keys, force)
        report = StepReport(self.spec.name, keys_total=len(all_keys))
        report.skipped = len(all_keys) - len(todo)
        for key in all_keys:
            if key not in todo and progress:
                progress(key, "skipped")
        try:
            for key in todo:
                status = self._fetch_key(run_id, key, start, end, report)
                if progress:
                    progress(key, status)
        finally:
            self._fetch_log.save()
        return report

    def _fetch_key(self, run_id: str, key: str, start: str, end: str, report: StepReport) -> str:
        began = self._clock.get_monotonic()
        try:
            df = self.fetch_one(key, start, end)
        except DataSourceError as exc:
            self._run_log.record_event(run_id, self.spec.name, key, "failed", message=str(exc))
            raise
        path = self._store.write_raw(self.spec, key, df)
        self._fetch_log.mark_done(self.spec.name, key, len(df), path)
        status = "fetched" if len(df) else "empty"
        elapsed = int((self._clock.get_monotonic() - began) * 1000)
        self._run_log.record_event(run_id, self.spec.name, key, status, len(df), elapsed)
        if len(df):
            report.fetched += 1
            report.rows += len(df)
        else:
            report.empty += 1
        logger.debug("%s %s: %s rows", self.spec.name, key, len(df))
        return status
