"""Run the update steps in order and record each one in the task ledger (plan 38, D-181)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from quant_cn.core.clock import Clock
from quant_cn.core.update_all_settings import UpdateAllSettings, UpdateStep
from quant_cn.lake.task_log import TaskLog


class TargetRunner(Protocol):
    """
    Purpose:
        What UpdateAllRunner needs from a process runner (MakeTargetRunner or a test fake).

    Contract:
        Input:
            (structural type)
        Output:
            `run_target(target, timeout_s, tail_lines) -> (exit_code | None, tail)`
        Raises:
            (none)

    Used by:
        pipeline.UpdateAllRunner  -- injected process runner type

    Test cases:
        TC-UAR-001  (through UpdateAllRunner with a fake)
    """

    def run_target(
        self, target: str, timeout_s: int, tail_lines: int
    ) -> tuple[int | None, list[str]]:
        """
        Purpose:
            Run one make target.

        Contract:
            Input:
                target: str; timeout_s: int; tail_lines: int
            Output:
                tuple  -- (exit code or None at the time limit, last output lines)
            Raises:
                (none)
        """
        ...


class UpdateAllRunner:
    """
    Purpose:
        Run the selected update steps in config order. A failed step does not stop the run; a
        step whose `needs` failed or was skipped in this run is skipped (a need outside the
        selection counts as met). A failed step is retried `retry` times. After each step one
        row goes to the task ledger, with the `as_of` of the step's output JSON when it ran ok.

    Contract:
        Input:
            settings: UpdateAllSettings
            task_log: TaskLog
            process:  TargetRunner     -- runs make targets
            clock:    Clock
            app_data: Path             -- where step outputs are read for `as_of`
        Output:
            instance; `run(steps, trigger) -> list[dict]` (the ledger rows, in order)
        Raises:
            (none at construction)

    Used by:
        cli.UpdateCommands  -- `update-all`

    Test cases:
        TC-UAR-001  a failed step is recorded failed with its exit code and tail; its dependents
                    are skipped (also transitively); independent steps still run; rows are
                    written one per step with seq 1..n under one run_id
        TC-UAR-002  retry: a step failing once then passing is ok with attempts 2; a timeout
                    (exit None) is failed with "timeout" in the message
        TC-UAR-003  as_of is read from the output JSON of an ok step; missing file or key -> None
    """

    def __init__(
        self,
        settings: UpdateAllSettings,
        task_log: TaskLog,
        process: TargetRunner,
        clock: Clock,
        app_data: Path,
    ) -> None:
        self._settings = settings
        self._log = task_log
        self._process = process
        self._clock = clock
        self._app_data = app_data

    def run(self, steps: list[UpdateStep], trigger: str) -> list[dict[str, Any]]:
        """
        Purpose:
            Run `steps` and record them.

        Contract:
            Input:
                steps:   list[UpdateStep]  -- from settings.list_steps
                trigger: str               -- "manual" or "launchd"
            Output:
                list[dict]  -- one ledger row per step (TASK_COLUMNS keys)
            Raises:
                LakeError  -- a ledger row cannot be written
        """
        run_id = self._clock.get_now().strftime("%Y%m%dT%H%M%S")
        status: dict[str, str] = {}
        rows = []
        for seq, step in enumerate(steps, start=1):
            blocked = [n for n in step.needs if status.get(n, "ok") != "ok"]
            row = self._build_skip(step, blocked) if blocked else self._run_step(step)
            row |= {"run_id": run_id, "seq": seq, "trigger": trigger}
            status[step.name] = row["status"]
            self._log.write_row(row)
            rows.append(row)
        return rows

    def _build_skip(self, step: UpdateStep, blocked: list[str]) -> dict[str, Any]:
        now = self._clock.get_now()
        return {"task": step.name, "target": step.target, "started_at": now,
                "finished_at": now, "duration_s": 0.0, "status": "skipped", "exit_code": None,
                "attempts": 0, "as_of": None, "output": step.output,
                "message": "needs not ok: " + ", ".join(blocked)}  # fmt: skip

    def _run_step(self, step: UpdateStep) -> dict[str, Any]:
        started = self._clock.get_now()
        t0 = self._clock.get_monotonic()
        timeout = self._settings.get_timeout_s(step)
        code: int | None = None
        tail: list[str] = []
        attempts = 0
        while attempts <= step.retry:
            attempts += 1
            code, tail = self._process.run_target(step.target, timeout, self._settings.tail_lines)
            if code == 0:
                break
        ok = code == 0
        message = "" if ok else ("timeout; " if code is None else "") + "\n".join(tail)
        return {"task": step.name, "target": step.target, "started_at": started,
                "finished_at": self._clock.get_now(),
                "duration_s": round(self._clock.get_monotonic() - t0, 1),
                "status": "ok" if ok else "failed", "exit_code": code, "attempts": attempts,
                "as_of": self._read_as_of(step) if ok else None, "output": step.output,
                "message": message}  # fmt: skip

    def _read_as_of(self, step: UpdateStep) -> str | None:
        if not step.output:
            return None
        try:
            value = json.loads((self._app_data / step.output).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        as_of = value.get("as_of") if isinstance(value, dict) else None
        return str(as_of) if as_of else None
