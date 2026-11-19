"""Check that every plan phase status starts with an allowed state (plan 02 ph5, D-144)."""

from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.base_checker import BaseChecker, Finding
from quant_cn.core.docs.phase_status_parser import STATES
from quant_cn.core.docs.plan_reader import PlanReader

PLANS = Path("plans/execution")


class PlanStatusChecker(BaseChecker):
    """
    Purpose:
        Report every phase in plans/execution/NN_*.md whose Status cell does not start with
        todo, doing, blocked or done (the plan skill's vocabulary).

    Contract:
        Input:
            repo_root: Path
            plans:     PlanReader
        Output:
            instance; `run() -> list[Finding]` with rule "plans"
        Raises:
            (none at construction)

    Used by:
        core.docs.ContractLinter  -- `--plans`

    Test cases:
        TC-PSC-001  an invalid phase status gives one finding naming the plan file and phase;
                    valid statuses and non-plan files give none
    """

    rule = "plans"

    def __init__(self, repo_root: Path, plans: PlanReader) -> None:
        self._root = repo_root
        self._plans = plans

    def run(self) -> list[Finding]:
        """
        Purpose:
            Parse every plan file and check each phase's state.

        Contract:
            Input:
                (none)
            Output:
                list[Finding]  -- sorted; empty when every phase has a valid state
            Raises:
                OSError  -- unreadable plan file
        """
        folder = self._root / PLANS
        findings: list[Finding] = []
        for path in sorted(folder.glob("[0-9][0-9]_*.md")) if folder.exists() else []:
            plan = self._plans.read(path)
            for phase in plan.phases if plan else ():
                if phase.state not in STATES:
                    msg = f"phase {phase.n}: status {phase.status[:40]!r} must start with {STATES}"
                    rel = str(path.relative_to(self._root))
                    findings.append(Finding(rel, 0, self.rule, msg))
        return sorted(findings)
