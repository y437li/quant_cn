"""Contract tests for pipeline.TaskStatusBuilder (plan 38 ph3)."""

from __future__ import annotations

import json
from pathlib import Path

from quant_cn.lake.task_log import TaskLog
from quant_cn.pipeline.task_status_builder import TaskStatusBuilder
from tests.lake.test_task_log import build_row


# TC-TSB-001
def test_tc_tsb_001_status(tmp_path: Path) -> None:
    log = TaskLog(tmp_path)
    log.write_row(build_row("r1", 1, "a", as_of="20261117"))
    log.write_row(build_row("r1", 2, "b"))
    log.write_row(build_row("r2", 1, "a", status="failed", exit_code=2, message="x\nboom",
                            as_of=None))  # fmt: skip
    log.write_row(build_row("r2", 2, "b", status="skipped", message="needs not ok: a"))
    doc = TaskStatusBuilder(log, history=1).build(["a", "b", "c"])
    last = doc["last_run"]
    assert last["run_id"] == "r2" and last["counts"] == {"ok": 0, "failed": 1, "skipped": 1}
    assert last["steps"][0] == {"task": "a", "status": "failed", "duration_s": 5.0,
                                "exit_code": 2, "as_of": None, "note": "boom"}  # fmt: skip
    a, b, c = doc["steps"]
    assert a["status"] == "failed" and a["as_of"] == "20261117"
    assert a["last_ok_at"] == "2026-11-18 06:00:05"
    assert a["history"] == [{"run_id": "r2", "status": "failed", "duration_s": 5.0}]
    assert b["status"] == "skipped" and c == {"task": "c", "status": None, "last_ok_at": None,
                                              "as_of": None, "history": []}  # fmt: skip


# TC-TSB-002
def test_tc_tsb_002_empty_and_write(tmp_path: Path) -> None:
    builder = TaskStatusBuilder(TaskLog(tmp_path))
    never: dict[str, object] = {
        "task": "a",
        "status": None,
        "last_ok_at": None,
        "as_of": None,
        "history": [],
    }
    assert builder.build(["a"]) == {"last_run": None, "steps": [never]}
    path = builder.write(tmp_path / "app", ["a"])
    assert json.loads(path.read_text(encoding="utf-8"))["last_run"] is None
    assert not list(path.parent.glob("*.tmp"))
