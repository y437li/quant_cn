"""Contract tests for lake.TaskLog (plan 38)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import duckdb
import pytest

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.task_log import TASK_COLUMNS, TaskLog

T0 = dt.datetime(2026, 11, 18, 6, 0)


def build_row(run_id: str, seq: int, task: str, status: str = "ok", **kw: Any) -> dict[str, Any]:
    return {"run_id": run_id, "seq": seq, "trigger": "manual", "task": task, "target": task,
            "started_at": T0, "finished_at": T0 + dt.timedelta(seconds=5), "duration_s": 5.0,
            "status": status, "exit_code": 0 if status == "ok" else None, "attempts": 1,
            "as_of": "20261118", "output": None, "message": ""} | kw  # fmt: skip


# TC-TKL-001
def test_tc_tkl_001_write_row(tmp_path: Path) -> None:
    log = TaskLog(tmp_path)
    path = log.write_row(build_row("r1", 1, "market-data"))
    assert path.name == "part-r1-001.parquet" and path.exists()
    assert not list(path.parent.glob("*.tmp"))
    with pytest.raises(LakeError):
        log.write_row(build_row("r1", 2, "x", status="running"))
    bad = build_row("r1", 3, "x")
    del bad["message"]
    with pytest.raises(LakeError):
        log.write_row(bad)


# TC-TKL-002
def test_tc_tkl_002_read_rows(tmp_path: Path) -> None:
    log = TaskLog(tmp_path)
    empty = log.read_rows()
    assert empty.empty and list(empty.columns) == TASK_COLUMNS
    log.write_row(build_row("r2", 2, "b", status="failed", exit_code=2, message="boom"))
    log.write_row(build_row("r1", 1, "a"))
    log.write_row(build_row("r2", 1, "a"))  # r2 interrupted after two steps: both rows kept
    rows = log.read_rows()
    assert list(rows.columns) == TASK_COLUMNS
    assert list(zip(rows.run_id, rows.seq, strict=True)) == [("r1", 1), ("r2", 1), ("r2", 2)]
    assert rows.iloc[2].exit_code == 2 and rows.iloc[2].message == "boom"


# TC-TKL-003
def test_tc_tkl_003_view(tmp_path: Path) -> None:
    con = duckdb.connect()
    con.execute("CREATE SCHEMA meta")
    log = TaskLog(tmp_path)
    log.refresh_view(con)
    views = con.execute("SELECT count(*) FROM duckdb_views() WHERE view_name='task_log'")
    assert views.fetchall() == [(0,)]
    log.write_row(build_row("r1", 1, "a"))
    log.refresh_view(con)
    assert con.execute("SELECT task, status FROM meta.task_log").fetchall() == [("a", "ok")]
    log.write_row(build_row("r1", 2, "b", as_of=None, output=None))
    log.refresh_view(con)
    types = dict(
        con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'task_log'"
        ).fetchall()
    )
    assert types["as_of"] == "VARCHAR" and types["output"] == "VARCHAR"
    assert con.execute("SELECT as_of FROM meta.task_log WHERE task = 'b'").fetchall() == [(None,)]
