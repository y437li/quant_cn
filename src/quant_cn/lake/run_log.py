"""Run history for monitoring: `meta.run_log` in DuckDB, mirrored to logging (D-022)."""

from __future__ import annotations

import logging
import uuid

import duckdb

from quant_cn.core.base_run_log import BaseRunLog
from quant_cn.core.clock import Clock
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_catalog import LakeCatalog

logger = logging.getLogger(__name__)
_TABLE = "meta.run_log"


class RunLog(BaseRunLog):
    """
    Purpose:
        Append run and per-key events to `meta.run_log` (run_id, started_at, finished_at, kind,
        dataset, key, status, n_rows, duration_ms, message) and echo them to logging.

    Contract:
        Input:
            catalog: LakeCatalog  -- connection
            clock:   Clock        -- timestamps
        Output:
            instance; BaseRunLog API
        Raises:
            LakeError  -- table cannot be created

    Used by:
        core.BaseFetcher.run             -- via BaseRunLog
        pipeline.LocalRunner             -- run start/finish, blocked events
        cli.QuantCnCli                   -- composition root

    Test cases:
        TC-RL-001  start/event/finish rows are queryable
        TC-RL-002  run ids are unique; finish_run sets status and finished_at on the run row
    """

    def __init__(self, catalog: LakeCatalog, clock: Clock) -> None:
        self._catalog = catalog
        self._clock = clock
        self._query(
            f"CREATE TABLE IF NOT EXISTS {_TABLE} (run_id VARCHAR, started_at TIMESTAMP, "
            "finished_at TIMESTAMP, kind VARCHAR, dataset VARCHAR, key VARCHAR, status VARCHAR, "
            "n_rows BIGINT, duration_ms BIGINT, message VARCHAR)"
        )

    def open_run(self, kind: str) -> str:
        """
        Purpose:
            Insert the run row (dataset and key NULL, status "running").

        Contract:
            Input:
                kind: str
            Output:
                str  -- 12-hex-digit run id
            Raises:
                LakeError
        """
        run_id = uuid.uuid4().hex[:12]
        self._query(
            f"INSERT INTO {_TABLE} VALUES (?, ?, NULL, ?, NULL, NULL, 'running', 0, 0, '')",
            [run_id, self._clock.get_now(), kind],
        )
        logger.info("run %s started (%s)", run_id, kind)
        return run_id

    def record_event(
        self,
        run_id: str,
        dataset: str,
        key: str,
        status: str,
        n_rows: int = 0,
        duration_ms: int = 0,
        message: str = "",
    ) -> None:
        """
        Purpose:
            Append one key event.

        Contract:
            Input:
                see BaseRunLog.record_event
            Output:
                None
            Raises:
                LakeError
        """
        now = self._clock.get_now()
        self._query(
            f"INSERT INTO {_TABLE} VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)",
            [run_id, now, now, dataset, key, status, n_rows, duration_ms, message],
        )
        level = logging.WARNING if status in ("failed", "blocked") else logging.DEBUG
        logger.log(level, "%s %s %s rows=%s %s", dataset, key, status, n_rows, message)

    def close_run(self, run_id: str, status: str, message: str = "") -> None:
        """
        Purpose:
            Set status, message and finished_at on the run row.

        Contract:
            Input:
                run_id: str; status: str; message: str
            Output:
                None
            Raises:
                LakeError
        """
        self._query(
            f"UPDATE {_TABLE} SET finished_at = ?, status = ?, message = ? "
            "WHERE run_id = ? AND dataset IS NULL",
            [self._clock.get_now(), status, message, run_id],
        )
        logger.info("run %s finished: %s %s", run_id, status, message)

    def _query(self, sql: str, params: list[object] | None = None) -> None:
        try:
            self._catalog.connection.execute(sql, params or [])
        except duckdb.Error as exc:
            raise LakeError(f"run_log: {exc}") from exc
