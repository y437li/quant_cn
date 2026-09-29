"""Run pipeline steps as a Prefect 3 flow so runs are visible in the Prefect UI (D-022)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast
from uuid import UUID

from prefect import flow, task
from prefect.artifacts import create_progress_artifact, update_progress_artifact

from quant_cn.core.base_run_log import BaseRunLog
from quant_cn.core.base_step import BaseStep
from quant_cn.core.exceptions import PermissionDeniedError, QuantCnError
from quant_cn.core.step_report import StepReport
from quant_cn.pipeline.runner import BaseRunner, PipelineReport


class PrefectRunner(BaseRunner):
    """
    Purpose:
        Same contract as LocalRunner, executed as a Prefect flow named "quant_cn <kind>" whose run
        name is the RunLog run id; every step is a Prefect task with a progress artifact over its
        units (keys). RunLog stays the source of truth (D-022); steps and fetchers never import
        Prefect. A permission failure marks the step blocked and continues; any other project
        error fails the flow, closes the run as failed and re-raises.

    Contract:
        Input:
            run_log:        BaseRunLog
            progress_every: int > 0  -- update the progress artifact every N units
        Output:
            instance; `run`
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-PFR-001  steps run in order inside one flow; the report lists each; run log closed ok
        TC-PFR-002  permission error marks the step blocked and later steps still run
        TC-PFR-003  other project error fails the run, closes it as failed and re-raises
    """

    def __init__(self, run_log: BaseRunLog, progress_every: int = 50) -> None:
        self._run_log = run_log
        self._every = max(progress_every, 1)

    def run(self, kind: str, steps: Sequence[BaseStep]) -> PipelineReport:
        """
        Purpose:
            See BaseRunner.run; the flow appears in the Prefect UI while it runs.

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
        pipeline_flow = flow(
            name=f"quant_cn {kind}", flow_run_name=run_id, validate_parameters=False
        )(self._run_steps)
        try:
            report.steps = pipeline_flow(run_id, list(steps))
        except QuantCnError as exc:
            report.status = "failed"
            self._run_log.close_run(run_id, "failed", str(exc))
            raise
        blocked = report.list_blocked()
        self._run_log.close_run(run_id, "ok", f"blocked: {blocked}" if blocked else "")
        return report

    def _run_steps(self, run_id: str, steps: list[BaseStep]) -> list[StepReport]:
        reports = []
        for step in steps:
            step_task = task(name=step.name, task_run_name=step.name, retries=0)(self._run_step)
            reports.append(step_task(run_id, step))
        return reports

    def _run_step(self, run_id: str, step: BaseStep) -> StepReport:
        try:
            units = step.list_units()
            description = f"{step.name}: {len(units)} units"
            artifact = cast(UUID, create_progress_artifact(progress=0.0, description=description))
            done = [0]

            def advance(_key: str, _status: str) -> None:
                done[0] += 1
                if done[0] % self._every == 0 or done[0] == len(units):
                    self._refresh_progress(artifact, done[0], len(units))

            return step.run(run_id, advance)
        except PermissionDeniedError as exc:
            self._run_log.record_event(run_id, step.name, "*", "blocked", message=str(exc))
            return StepReport(step.name, status="blocked", message=str(exc))

    @staticmethod
    def _refresh_progress(artifact: UUID, done: int, total: int) -> None:
        update_progress_artifact(artifact_id=artifact, progress=100.0 * done / max(total, 1))
