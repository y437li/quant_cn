from __future__ import annotations

import pytest

from quant_cn.core.base_step import BaseStep, ProgressHook
from quant_cn.core.exceptions import DataSourceError, PermissionDeniedError, QuantCnError
from quant_cn.core.step_report import StepReport
from quant_cn.pipeline.runner import LocalRunner
from tests.support import MiniLake


class ScriptStep(BaseStep):
    def __init__(self, name: str, error: QuantCnError | None = None) -> None:
        self._name = name
        self._error = error
        self.ran = False

    @property
    def name(self) -> str:
        return self._name

    def list_units(self) -> list[str]:
        return ["k"]

    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        self.ran = True
        if self._error:
            raise self._error
        if progress:
            progress("k", "fetched")
        return StepReport(self._name, fetched=1)


# TC-LR-001
def test_tc_lr_001_order(lake: MiniLake) -> None:
    steps = [ScriptStep("a"), ScriptStep("b")]
    report = LocalRunner(lake.run_log, show_progress=False).run("t", steps)
    assert [s.name for s in report.steps] == ["a", "b"] and report.status == "ok"
    assert report.to_frame()["fetched"].tolist() == [1, 1]


# TC-LR-002
def test_tc_lr_002_blocked_continues(lake: MiniLake) -> None:
    later = ScriptStep("c")
    report = LocalRunner(lake.run_log, show_progress=False).run(
        "t", [ScriptStep("vip", PermissionDeniedError("no points")), later]
    )
    assert report.list_blocked() == ["vip"] and later.ran
    events = lake.query.sql("SELECT dataset FROM meta.run_log WHERE status = 'blocked'")
    assert events["dataset"].tolist() == ["vip"]


# TC-LR-003
def test_tc_lr_003_failure_reraises(lake: MiniLake) -> None:
    later = ScriptStep("c")
    with pytest.raises(DataSourceError):
        LocalRunner(lake.run_log, show_progress=False).run(
            "t", [ScriptStep("x", DataSourceError("boom")), later]
        )
    assert not later.ran
    run = lake.query.sql("SELECT status FROM meta.run_log WHERE dataset IS NULL")
    assert run["status"].tolist() == ["failed"]
