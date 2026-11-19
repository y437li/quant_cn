"""The update task ledger: `meta/task_log/part-*.parquet`, one row per step (plan 38, D-181)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from quant_cn.core.exceptions import LakeError

TASK_LOG_DIR = Path("meta") / "task_log"
VIEW = "meta.task_log"
TASK_COLUMNS = [
    "run_id", "seq", "trigger", "task", "target", "started_at", "finished_at", "duration_s",
    "status", "exit_code", "attempts", "as_of", "output", "message",
]  # fmt: skip
STATUSES = ("ok", "failed", "skipped")


class TaskLog:
    """
    Purpose:
        Record each `update-all` step as one zstd parquet part under `<lake_root>/meta/task_log/`
        (tmp + rename), without the DuckDB catalog, so the steps keep the single writer lock.
        Rows are never rewritten. `refresh_view` exposes all parts as `meta.task_log`.

    Contract:
        Input:
            lake_root: Path
        Output:
            instance; `write_row(row) -> Path`, `read_rows() -> DataFrame`,
            `refresh_view(connection)`, `get_glob() -> str`
        Raises:
            (none at construction)

    Used by:
        pipeline.UpdateAllRunner  -- one row per step
        lake.LakeCatalog          -- view refresh with the other views
        pipeline.TaskStatusBuilder  -- reads the ledger
        cli.UpdateCommands        -- view refresh after a run, status file

    Test cases:
        TC-TKL-001  a row is written with TASK_COLUMNS; a bad status or missing key raises
                   LakeError; no .tmp file is left
        TC-TKL-002  read_rows returns every part in (run_id, seq) order; empty ledger -> empty
                   frame with TASK_COLUMNS; parts of an interrupted run stay readable
        TC-TKL-003  refresh_view creates meta.task_log over the parts; no parts -> view dropped
    """

    def __init__(self, lake_root: Path) -> None:
        self._folder = lake_root / TASK_LOG_DIR

    def get_glob(self) -> str:
        """
        Purpose:
            The glob of every part file, for read_parquet.

        Contract:
            Input:
                (none)
            Output:
                str  -- "<lake_root>/meta/task_log/part-*.parquet"
            Raises:
                (none)
        """
        return str(self._folder / "part-*.parquet")

    def write_row(self, row: Mapping[str, Any]) -> Path:
        """
        Purpose:
            Persist one step as `part-<run_id>-<seq>.parquet`.

        Contract:
            Input:
                row: Mapping[str, Any]  -- every TASK_COLUMNS key; status in STATUSES
            Output:
                Path  -- the part file
            Raises:
                LakeError  -- a missing key, an unknown status, or the file cannot be written
        """
        missing = [c for c in TASK_COLUMNS if c not in row]
        if missing or row.get("status") not in STATUSES:
            raise LakeError(f"bad task row: missing {missing}, status {row.get('status')!r}")
        path = self._folder / f"part-{row['run_id']}-{int(row['seq']):03d}.parquet"
        frame = pd.DataFrame([{c: row[c] for c in TASK_COLUMNS}], columns=TASK_COLUMNS)
        frame = frame.astype({"seq": "int64", "duration_s": "float64"})
        frame["exit_code"] = frame["exit_code"].astype("Int64")
        frame["attempts"] = frame["attempts"].astype("int64")
        for col in ("started_at", "finished_at"):
            frame[col] = pd.to_datetime(frame[col])
        for col in ("run_id", "trigger", "task", "target", "status", "as_of", "output", "message"):
            frame[col] = frame[col].astype("string")  # typed even when null (DuckDB views)
        try:
            self._folder.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            frame.to_parquet(tmp, index=False, compression="zstd")
            os.replace(tmp, path)
        except OSError as exc:
            raise LakeError(f"cannot write task row {path}: {exc}") from exc
        return path

    def read_rows(self) -> pd.DataFrame:
        """
        Purpose:
            Every recorded step, oldest run first.

        Contract:
            Input:
                (none)
            Output:
                DataFrame  -- TASK_COLUMNS, sorted by (run_id, seq); empty when no parts
            Raises:
                LakeError  -- a part cannot be read
        """
        parts = sorted(self._folder.glob("part-*.parquet"))
        if not parts:
            return pd.DataFrame(columns=TASK_COLUMNS)
        try:
            frame = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
        except (OSError, ValueError) as exc:
            raise LakeError(f"cannot read the task log: {exc}") from exc
        return frame.sort_values(["run_id", "seq"]).reset_index(drop=True)[TASK_COLUMNS]

    def refresh_view(self, connection: duckdb.DuckDBPyConnection) -> None:
        """
        Purpose:
            (Re)create `meta.task_log`, or drop it when there are no parts.

        Contract:
            Input:
                connection: duckdb.DuckDBPyConnection  -- catalog connection (schema meta exists)
            Output:
                None
            Raises:
                LakeError  -- DuckDB rejects the view
        """
        try:
            if not any(self._folder.glob("part-*.parquet")):
                connection.execute(f"DROP VIEW IF EXISTS {VIEW}")
                return
            path = self.get_glob().replace("'", "''")
            connection.execute(
                f"CREATE OR REPLACE VIEW {VIEW} AS SELECT * FROM "
                f"read_parquet('{path}', union_by_name=true)"
            )
        except duckdb.Error as exc:
            raise LakeError(f"cannot create view {VIEW}: {exc}") from exc
