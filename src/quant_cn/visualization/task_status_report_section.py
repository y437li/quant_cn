"""The 数据更新 line and failed-step rows of the 持仓监测 e-mail (plan 38 ph3, D-181)."""

from __future__ import annotations

from typing import Any, ClassVar

from quant_cn.visualization.email_format import INK, MUTED, RED
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection

TRIGGER = {"launchd": "自动", "manual": "手动"}


class TaskStatusReportSection(ReportSection):
    """
    Purpose:
        From task_status.json, whether the data behind the e-mail was updated: a summary line
        with the latest update-all run (time, trigger, ok count, failed steps) and, only when a
        step failed or was skipped, a table of those steps with the last output line.

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer, last section

    Test cases:
        TC-TSR-001  summary: "数据更新 11-18 06:00（自动）：17/19 成功；失败：a、b；跳过 1。";
                    all ok has no 失败 part; no document or no run -> ""
        TC-TSR-002  rows: failed and skipped steps with their note, failed first; all ok or no
                    document -> ""
    """

    DOC: ClassVar[str] = "task_status"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 数据更新 line for the summary box.

        Contract:
            Input:
                doc: task_status document or None
            Output:
                str  -- plain text; "" without a run
            Raises:
                (none)
        """
        run = (doc or {}).get("last_run")
        if not run:
            return ""
        steps = run.get("steps") or []
        failed = [s["task"] for s in steps if s.get("status") == "failed"]
        counts = run.get("counts") or {}
        when = f"{str(run.get('started_at', ''))[5:16]}（{TRIGGER.get(run.get('trigger'), '')}）"
        text = f"数据更新 {when}：{counts.get('ok', 0)}/{len(steps)} 成功"
        if failed:
            text += "；失败：" + "、".join(failed)
        if counts.get("skipped"):
            text += f"；跳过 {counts['skipped']}"
        return text + "。"

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 数据更新 section: failed and skipped steps of the latest run.

        Contract:
            Input:
                doc: task_status document or None
            Output:
                str  -- section rows; "" when every step was ok or there is no run
            Raises:
                (none)
        """
        run = (doc or {}).get("last_run") or {}
        bad = [s for s in run.get("steps") or [] if s.get("status") in ("failed", "skipped")]
        if not bad:
            return ""
        bad.sort(key=lambda s: s.get("status") != "failed")
        rows = [[
            EmailHtml.build_td(s["task"], "left", INK, bold=True, mono=False),
            EmailHtml.build_td("失败" if s["status"] == "failed" else "跳过", "left",
                               RED if s["status"] == "failed" else MUTED, mono=False),
            EmailHtml.build_td((s.get("note") or "")[:120], "left", MUTED, mono=False),
        ] for s in bad]  # fmt: skip
        head = [EmailHtml.build_th(h, "left") for h in ("步骤", "状态", "说明")]
        sub = f"make update-all {run.get('run_id', '')}，失败的步骤可以用 --from 重跑"
        return EmailHtml.build_section("数据更新", sub, EmailHtml.build_table(head, rows))
