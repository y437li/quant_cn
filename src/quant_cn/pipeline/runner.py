"""Runners execute BaseSteps in order; LocalRunner adds rich progress and RunLog events (D-022)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

import pandas as pd
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

from quant_cn.core.base_run_log import BaseRunLog
from quant_cn.core.base_step import BaseStep
from quant_cn.core.exceptions import PermissionDeniedError, QuantCnError
from quant_cn.core.step_report import StepReport


@dataclass
class PipelineReport:
    """
    Purpose:
        Result of one pipeline run: its id, overall status and one StepReport per step.

    Contract:
        Input:
            run_id: str; status: str ("ok" | "failed" | "dry_run"); steps: list[StepReport]
        Output:
            dataclass; `blocked`, `to_frame`
        Raises:
            (none)

    Used by:
        pipeline.LocalRunner.run         -- return value
        pipeline.DownloadPipeline.run    -- return value
        cli.QuantCnCli                   -- prints the summary table

    Test cases:
        TC-LR-001  steps run in order and the report lists each
    """

    run_id: str
    status: str
    steps: list[StepReport] = field(default_factory=list)

    def list_blocked(self) -> list[str]:
        """
        Purpose:
            Names of steps blocked by missing permissions.

        Contract:
            Input:
                (none)
            Output:
                list[str]
            Raises:
                (none)
        """
        return [s.name for s in self.steps if s.status == "blocked"]

    def to_frame(self) -> pd.DataFrame:
        """
        Purpose:
            One row per step for display or logging.

        Contract:
            Input:
                (none)
            Output:
                DataFrame  -- name, status, keys_total, fetched, skipped, empty, rows, message
            Raises:
                (none)
        """
        cols = ["name", "status", "keys_total", "fetched", "skipped", "empty", "rows", "message"]
        return pd.DataFrame([[getattr(s, c) for c in cols] for s in self.steps], columns=cols)


class BaseRunner(ABC):
    """
    Purpose:
        Extension point for how steps are executed (local now, Prefect later, D-022); steps never
        import the runner's backend.

    Contract:
        Input:
            (subclass-specific constructor)
        Output:
            instance; `run`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        pipeline.LocalRunner             -- subclass
        pipeline.DownloadPipeline        -- injected runner type

    Test cases:
        TC-LR-001  steps run in order and the report lists each
    """

    @abstractmethod
    def run(self, kind: str, steps: Sequence[BaseStep]) -> PipelineReport:
        """
        Purpose:
            Execute steps in order under one run id.

        Contract:
            Input:
                kind: str; steps: Sequence[BaseStep]
            Output:
                PipelineReport
            Raises:
                QuantCnError  -- a step failed for a reason other than permissions
        """


class LocalRunner(BaseRunner):
    """
    Purpose:
        Run steps serially in this process with a rich progress bar per step; a permission
        failure marks the step blocked and continues; any other project error closes the run
        as failed and re-raises (finished keys stay done).

    Contract:
        Input:
            run_log:       BaseRunLog
            console:       rich Console | None  -- default stderr console
            show_progress: bool                  -- False in tests and non-interactive use
        Output:
            instance; `run`
        Raises:
            (none at construction)

    Used by:
        pipeline.DownloadPipeline        -- runs fetch steps
        cli.QuantCnCli                   -- composition root

    Test cases:
        TC-LR-001  steps run in order and the report lists each
        TC-LR-002  permission error marks the step blocked, logs it and continues
        TC-LR-003  other project error finishes the run as failed and re-raises
    """

    def __init__(
        self, run_log: BaseRunLog, console: Console | None = None, show_progress: bool = True
    ) -> None:
        self._run_log = run_log
        self._console = console or Console(stderr=True)
        self._show = show_progress

    def run(self, kind: str, steps: Sequence[BaseStep]) -> PipelineReport:
        """
        Purpose:
            See BaseRunner.run.

        Contract:
            Input:
                kind: str; steps: Sequence[BaseStep]
            Output:
                PipelineReport  -- status "ok" when no step failed (blocked steps allowed)
            Raises:
                QuantCnError  -- first non-permission failure, after closing the run
        """
        run_id = self._run_log.open_run(kind)
        report = PipelineReport(run_id=run_id, status="ok")
        progress = Progress(
            TextColumn("{task.description:<20}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self._console,
            disable=not self._show,
        )
        try:
            with progress:
                for step in steps:
                    report.steps.append(self._run_step(run_id, step, progress))
        except QuantCnError as exc:
            report.status = "failed"
            self._run_log.close_run(run_id, "failed", str(exc))
            raise
        blocked = report.list_blocked()
        self._run_log.close_run(run_id, "ok", f"blocked: {blocked}" if blocked else "")
        return report

    def _run_step(self, run_id: str, step: BaseStep, progress: Progress) -> StepReport:
        try:
            units = step.list_units()
            task = progress.add_task(step.name, total=len(units))
            return step.run(run_id, lambda _key, _status: progress.advance(task))
        except PermissionDeniedError as exc:
            self._run_log.record_event(run_id, step.name, "*", "blocked", message=str(exc))
            return StepReport(step.name, status="blocked", message=str(exc))
