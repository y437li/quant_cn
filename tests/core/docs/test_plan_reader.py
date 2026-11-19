from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.phase_status_parser import PhaseStatusParser
from quant_cn.core.docs.plan_reader import PlanReader

PLAN = """# 07 — Sample plan

| | |
|---|---|
| Status | doing |
| Decisions | D-010, D-011 |
| Depends on plans | 01 |

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Build | code | tests pass | — | done |
| 2 | Ship | release | tagged | 1 | todo |
| 3 | Fix | patch | merged | 2 | **done** 2026-11-13 (a1b2c3d) — shipped |
"""


# TC-PR-001
def test_tc_pr_001_plan(tmp_path: Path) -> None:
    path = tmp_path / "07_sample.md"
    path.write_text(PLAN)
    plan = PlanReader(MarkdownTableReader(), PhaseStatusParser()).read(path)
    assert plan is not None
    assert (plan.nn, plan.title, plan.status, plan.depends_on) == (
        "07",
        "Sample plan",
        "doing",
        "01",
    )
    assert plan.decisions == ("D-010", "D-011")
    assert [(p.n, p.state) for p in plan.phases][:2] == [("1", "done"), ("2", "todo")]


# TC-PR-002
def test_tc_pr_002_not_a_plan(tmp_path: Path) -> None:
    path = tmp_path / "ROADMAP.md"
    path.write_text("# Roadmap\n")
    assert PlanReader(MarkdownTableReader(), PhaseStatusParser()).read(path) is None


# TC-PR-003
def test_tc_pr_003_status_split(tmp_path: Path) -> None:
    path = tmp_path / "07_sample.md"
    path.write_text(PLAN)
    plan = PlanReader(MarkdownTableReader(), PhaseStatusParser()).read(path)
    assert plan is not None
    last = plan.phases[-1]
    assert (last.state, last.state_date, last.commit, last.note) == (
        "done",
        "2026-11-13",
        "a1b2c3d",
        "2026-11-13 (a1b2c3d) — shipped",
    )
