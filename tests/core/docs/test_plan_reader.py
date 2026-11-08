from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader
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
"""


# TC-PR-001
def test_tc_pr_001_plan(tmp_path: Path) -> None:
    path = tmp_path / "07_sample.md"
    path.write_text(PLAN)
    plan = PlanReader(MarkdownTableReader()).read(path)
    assert plan is not None
    assert (plan.nn, plan.title, plan.status, plan.depends_on) == (
        "07",
        "Sample plan",
        "doing",
        "01",
    )
    assert plan.decisions == ("D-010", "D-011")
    assert [(p.n, p.status) for p in plan.phases] == [("1", "done"), ("2", "todo")]


# TC-PR-002
def test_tc_pr_002_not_a_plan(tmp_path: Path) -> None:
    path = tmp_path / "ROADMAP.md"
    path.write_text("# Roadmap\n")
    assert PlanReader(MarkdownTableReader()).read(path) is None
