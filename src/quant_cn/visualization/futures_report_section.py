"""The 期货 block of the 持仓监测 e-mail (plan 15 ph7i, D-145)."""

from __future__ import annotations

from typing import Any, ClassVar

from quant_cn.visualization.email_format import AMBER, INK, MUTED
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection

KIND = {"curve": "期限结构", "oi": "持仓", "spread": "价差", "basis": "基差", "net": "前20名持仓"}


class FuturesReportSection(ReportSection):
    """
    Purpose:
        Turn futures_monitor.json into the e-mail's 期货 parts: one summary line every day
        (signal count, new ones named), and the table of new signals only (curve or spread at a
        5-year extreme, open-interest jump).

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer as its 期货 section

    Test cases:
        TC-FRS-001  summary counts signals and names the new ones; "" without a document
        TC-FRS-002  rows list only new signals; nothing without one; 数据缺失 when no doc
    """

    DOC: ClassVar[str] = "futures_monitor"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The one-line futures summary for the e-mail's summary box.

        Contract:
            Input:
                doc: futures_monitor document or None
            Output:
                str  -- plain text; "" when there is no document
            Raises:
                (none)
        """
        if not doc or not doc.get("families"):
            return ""
        flags = doc.get("flags") or []
        new = set(doc.get("new_flags") or [])
        if not flags:
            return "期货：没有异常信号。"
        names = "、".join(dict.fromkeys(f["name"] for f in flags if f["key"] in new))
        return f"期货：{len(flags)} 个信号" + (f"，新增 {len(new)} 个（{names}）" if new else "")

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 期货 section rows: new signals only.

        Contract:
            Input:
                doc: futures_monitor document or None
            Output:
                str  -- section rows; "" with no new signal; 数据缺失 note without a document
            Raises:
                (none)
        """
        if not doc or not doc.get("families"):
            return EmailHtml.build_missing("期货", "futures_monitor.json")
        new = set(doc.get("new_flags") or [])
        rows = [
            [
                EmailHtml.build_td(f["name"], "left", INK, bold=True, mono=False),
                EmailHtml.build_td(KIND.get(f["kind"], f["kind"]), "left", MUTED, mono=False),
                EmailHtml.build_td(f["message"], "left", AMBER, mono=False),
            ]
            for f in doc.get("flags") or []
            if f["key"] in new
        ]
        if not rows:
            return ""
        head = [EmailHtml.build_th(h, "left") for h in ("品种 / 价差", "类型", "信号")]
        sub = f"数据截至 {doc.get('as_of', '')}；只列新出现的信号，完整页面见 app 期货监测"
        return EmailHtml.build_section("期货", sub, EmailHtml.build_table(head, rows))
