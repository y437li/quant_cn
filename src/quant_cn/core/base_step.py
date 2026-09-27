"""Extension point for pipeline steps run by a runner."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from quant_cn.core.step_report import StepReport

ProgressHook = Callable[[str, str], None]


class BaseStep(ABC):
    """
    Purpose:
        Abstract unit of pipeline work: announce its size, then run and report.

    Contract:
        Input:
            (subclass-specific constructor)
        Output:
            instance with `name`, `prepare`, `run`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        pipeline.FetchStep               -- production subclass
        pipeline.BaseRunner.run          -- step type
        pipeline.LocalRunner.run         -- calls prepare then run

    Test cases:
        TC-BAC-001  abstract bases cannot be instantiated
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Purpose:
            Step name shown in progress and reports.

        Contract:
            Input:
                (none)
            Output:
                str
            Raises:
                (none)
        """

    @abstractmethod
    def prepare(self) -> int:
        """
        Purpose:
            Compute the work units (e.g. keys) just before running.

        Contract:
            Input:
                (none)
            Output:
                int >= 0  -- total units for the progress bar
            Raises:
                QuantCnError  -- prerequisites missing (e.g. calendar not downloaded)
        """

    @abstractmethod
    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        """
        Purpose:
            Do the work prepared by `prepare`.

        Contract:
            Input:
                run_id:   str                   -- id from the run log
                progress: ProgressHook | None   -- called (key, status) per unit
            Output:
                StepReport
            Raises:
                QuantCnError  -- step failure; PermissionDeniedError means blocked
        """
