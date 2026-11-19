"""The 回购 block of the 持仓监测 e-mail (plan 23 ph6)."""

from __future__ import annotations

from typing import Any, ClassVar

from quant_cn.visualization.email_format import INK, MUTED
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection

PROC = {
    "预案": "新预案",
    "股东大会通过": "股东大会通过",
    "实施": "实施进度",
    "完成": "进度/完成",
    "停止": "终止",
}
MAX_ROWS = 10


class BuybackReportSection(ReportSection):
    """
    Purpose:
        From buybacks.json: one summary line (book events and the count of new large plans) and,
        when there is anything, a table of the book's events and the market's new plans of at
        least 2% of market cap (largest first, at most 10).

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer as its 回购 section

    Test cases:
        TC-BRS-001  summary names book events and counts large plans; "" without events
        TC-BRS-002  rows list book events and large plans; nothing without events
    """

    DOC: ClassVar[str] = "buybacks"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 回购 line for the summary box.

        Contract:
            Input:
                doc: buybacks document or None
            Output:
                str  -- "" when there is no event
            Raises:
                (none)
        """
        if not doc:
            return ""
        mine = doc.get("book_events") or []
        large = doc.get("large_plans") or []
        if not mine and not large:
            return ""
        parts = [f"{e['name']}{PROC.get(e['proc'], e['proc'])}" for e in mine[:3]]
        text = "回购：" + ("、".join(parts) + "；" if parts else "")
        return text + f"近 {doc.get('days', 7)} 天全市场新增 ≥ 2% 市值的回购预案 {len(large)} 只"

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 回购 section rows.

        Contract:
            Input:
                doc: buybacks document or None
            Output:
                str  -- section rows; "" when there is no event
            Raises:
                (none)
        """
        if not doc or not (doc.get("book_events") or doc.get("large_plans")):
            return ""
        head = [
            EmailHtml.build_th(h, "left")
            for h in ("股票", "公告日", "事件", "金额（亿）", "占市值")
        ]
        rows = [
            self._build_row(
                e["name"], e["ann_date"], PROC.get(e["proc"], e["proc"]), e["amount_yi"], None
            )
            for e in (doc.get("book_events") or [])
        ] + [
            self._build_row(p["name"], p["ann_date"], "大额回购预案", p["amount_yi"], p["pct"])
            for p in (doc.get("large_plans") or [])[:MAX_ROWS]
        ]
        sub = (
            "持仓 / 观察股票的回购事件，以及全市场 ≥ 2% 市值的新预案"
            "（2024 年以来 60 日平均超额 +4.6%）"
        )
        return EmailHtml.build_section("回购", sub, EmailHtml.build_table(head, rows))

    @staticmethod
    def _build_row(
        name: str, day: str, what: str, amount: float | None, pct: float | None
    ) -> list[str]:
        return [
            EmailHtml.build_td(name or "", "left", INK, bold=True, mono=False),
            EmailHtml.build_td(f"{day[4:6]}-{day[6:]}", "left", MUTED),
            EmailHtml.build_td(what, "left", INK, mono=False),
            EmailHtml.build_td("—" if amount is None else f"{amount:,.2f}"),
            EmailHtml.build_td("—" if pct is None else f"{pct:.1f}%"),
        ]
