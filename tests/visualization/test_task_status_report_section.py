"""Contract tests for visualization.TaskStatusReportSection (plan 38 ph3)."""

from __future__ import annotations

from typing import Any

from quant_cn.visualization.task_status_report_section import TaskStatusReportSection


def build_doc(*states: str) -> dict[str, Any]:
    steps = [{"task": f"s{i}", "status": st, "note": f"note {i}"} for i, st in enumerate(states)]
    counts = {k: sum(s == k for s in states) for k in ("ok", "failed", "skipped")}
    return {"last_run": {"run_id": "20261118T060001", "trigger": "launchd",
                         "started_at": "2026-11-18 06:00:01", "counts": counts, "steps": steps},
            "steps": []}  # fmt: skip


# TC-TSR-001
def test_tc_tsr_001_summary() -> None:
    sec = TaskStatusReportSection()
    assert sec.build_summary(build_doc("ok", "failed", "skipped", "failed")) == (
        "数据更新 11-18 06:00（自动）：1/4 成功；失败：s1、s3；跳过 1。"
    )
    assert sec.build_summary(build_doc("ok", "ok")) == "数据更新 11-18 06:00（自动）：2/2 成功。"
    assert sec.build_summary(None) == "" and sec.build_summary({"last_run": None}) == ""


# TC-TSR-002
def test_tc_tsr_002_rows() -> None:
    sec = TaskStatusReportSection()
    html = sec.build_rows(build_doc("ok", "skipped", "failed"))
    assert html.index(">s2<") < html.index(">s1<") and "note 2" in html and ">s0<" not in html
    assert sec.build_rows(build_doc("ok")) == "" and sec.build_rows(None) == ""
