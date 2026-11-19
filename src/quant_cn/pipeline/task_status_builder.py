"""`task_status.json`: the latest update-all run and each step's recent history (plan 38 ph3)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.task_log import STATUSES, TaskLog

FILE_NAME = "task_status.json"


class TaskStatusBuilder:
    """
    Purpose:
        From the task ledger, the document the app's 更新状态 panel and the e-mail line read:
        the latest run (id, trigger, start, end, counts, every step) and per step of the config
        its last status, last success time, last `as_of` and its last `history` runs.

    Contract:
        Input:
            task_log: TaskLog
            history:  int > 0  -- runs kept per step
        Output:
            instance; `build(task_names) -> dict`, `write(out_dir, task_names) -> Path`
        Raises:
            (none at construction)

    Used by:
        cli.UpdateCommands  -- after a run

    Test cases:
        TC-TSB-001  latest run counts and steps; per step last ok time and as_of from the last
                    ok row, history newest first capped at `history`; a step never run has
                    status None
        TC-TSB-002  empty ledger -> last_run None and steps with status None; write is atomic
                    and returns the path
    """

    def __init__(self, task_log: TaskLog, history: int = 10) -> None:
        self._log = task_log
        self._history = history

    def build(self, task_names: list[str]) -> dict[str, Any]:
        """
        Purpose:
            Build the status document.

        Contract:
            Input:
                task_names: list[str]  -- steps in config order (rows of other steps are kept
                                          in last_run but get no per-step entry)
            Output:
                dict  -- {last_run: {...} | None, steps: [...]}
            Raises:
                LakeError  -- the ledger cannot be read
        """
        rows = self._log.read_rows()
        last = None
        if not rows.empty:
            run = rows[rows.run_id == rows.run_id.max()].sort_values("seq")
            last = {"run_id": run.run_id.iloc[0], "trigger": run.trigger.iloc[0],
                    "started_at": self._to_text(run.started_at.min()),
                    "finished_at": self._to_text(run.finished_at.max()),
                    "counts": {s: int((run.status == s).sum()) for s in STATUSES},
                    "steps": [self._build_row(r) for r in run.to_dict("records")]}  # fmt: skip
        return {"last_run": last, "steps": [self._build_step(rows, n) for n in task_names]}

    def write(self, out_dir: Path, task_names: list[str]) -> Path:
        """
        Purpose:
            Write `task_status.json` into the app data directory (tmp + rename).

        Contract:
            Input:
                out_dir: Path; task_names: list[str]
            Output:
                Path
            Raises:
                LakeError  -- the ledger cannot be read or the file cannot be written
        """
        path = out_dir / FILE_NAME
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(FILE_NAME + ".tmp")
            tmp.write_text(json.dumps(self.build(task_names), ensure_ascii=False, indent=1),
                           encoding="utf-8")  # fmt: skip
            os.replace(tmp, path)
        except OSError as exc:
            raise LakeError(f"cannot write {path}: {exc}") from exc
        return path

    def _build_step(self, rows: pd.DataFrame, name: str) -> dict[str, Any]:
        own = rows[rows.task == name].sort_values(["run_id", "seq"], ascending=False)
        if own.empty:
            return {"task": name, "status": None, "last_ok_at": None, "as_of": None,
                    "history": []}  # fmt: skip
        ok = own[own.status == "ok"]
        return {"task": name, "status": own.status.iloc[0],
                "last_ok_at": self._to_text(ok.finished_at.iloc[0]) if not ok.empty else None,
                "as_of": next((a for a in ok.as_of if isinstance(a, str) and a), None),
                "history": [{"run_id": r["run_id"], "status": r["status"],
                             "duration_s": float(r["duration_s"])}
                            for r in own.head(self._history).to_dict("records")]}  # fmt: skip

    def _build_row(self, r: dict[str, Any]) -> dict[str, Any]:
        code = r["exit_code"]
        return {"task": r["task"], "status": r["status"], "duration_s": float(r["duration_s"]),
                "exit_code": None if pd.isna(code) else int(code),
                "as_of": r["as_of"] if isinstance(r["as_of"], str) else None,
                "note": (r["message"] or "").splitlines()[-1] if r["message"] else ""}  # fmt: skip

    @staticmethod
    def _to_text(value: Any) -> str:
        return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M:%S")
