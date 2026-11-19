"""The 财报季信号 block of the 持仓监测 e-mail (plan 35, D-172)."""

from __future__ import annotations

from typing import Any, ClassVar

from quant_cn.visualization.email_format import INK, MUTED, RED
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection

SHOWN = ("firing", "provisional")
STATUS = {"firing": "触发", "provisional": "临时"}
HEAD = (
    ("行业", "left"),
    ("状态", "left"),
    ("已披露", "right"),
    ("前60天", "right"),
    ("当天", "right"),
    ("此前120天", "right"),
    ("股东户数", "right"),
)


class SectorEarningsReportSection(ReportSection):
    """
    Purpose:
        Turn sector_earnings_signal.json into the e-mail's 财报季信号 parts: a summary line
        (the season, the firing sectors with pre / reaction excess and prior rally, new ones
        marked, and the historical record after a rally) and a table of the firing and
        provisional sectors (firing in red).

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer as its 财报季信号 section

    Test cases:
        TC-SER-001  summary: season label, firing sectors with numbers, new ones marked, the
                    rally record; 没有行业触发 when none; "" without a document or season
        TC-SER-002  rows: firing then provisional, firing rows red, share / pre / react /
                    back / holders formatted; "" when nothing is shown; 数据缺失 without a
                    document
    """

    DOC: ClassVar[str] = "sector_earnings_signal"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The one-line 财报季信号 summary.

        Contract:
            Input:
                doc: sector_earnings_signal document or None
            Output:
                str  -- plain text; "" without a document or season
            Raises:
                (none)
        """
        if not doc or not doc.get("season"):
            return ""
        head = f"财报季信号（{self._format_season(doc['season'])}）："
        new = set(doc.get("new_flags") or [])
        fired = [r for r in doc.get("rows", []) if r["status"] == "firing"]
        if not fired:
            return head + "没有行业触发。"
        pct = self._format_pct
        parts = [
            f"{r['name']}（前60天 {pct(r['pre'])}，当天 {pct(r['react'])}，"
            f"此前120天 {pct(r['back'])}）" + ("（新）" if r["code"] in new else "")
            for r in fired
        ]
        rec = (doc.get("record") or {}).get("rally") or {}
        tail = ""
        if rec.get("n"):
            tail = f"历史上大涨后触发 {rec['n']} 次，之后 60 天平均 {pct(rec.get('fwd60'))}。"
        return head + "好消息涨不动：" + "；".join(parts) + "。" + tail

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 财报季信号 section: firing and provisional sectors of the season.

        Contract:
            Input:
                doc: sector_earnings_signal document or None
            Output:
                str  -- section rows; "" when no sector is shown; 数据缺失 without a document
            Raises:
                (none)
        """
        if not doc:
            return EmailHtml.build_missing("财报季信号", "sector_earnings_signal.json")
        shown = [r for r in doc.get("rows", []) if r["status"] in SHOWN]
        if not shown:
            return ""
        rows = [self._build_row(r) for r in shown]
        head = [EmailHtml.build_th(h, a) for h, a in HEAD]
        sub = (
            f"{self._format_season(doc['season'])}：超预期最好的公司披露前已大涨、披露当天涨不动；"
            "超额相对全市场 / 全部二级行业，数据截至 " + str(doc.get("as_of", ""))
        )
        return EmailHtml.build_section("财报季信号", sub, EmailHtml.build_table(head, rows))

    def _build_row(self, r: dict[str, Any]) -> list[str]:
        firing = r["status"] == "firing"
        color = RED if firing else INK
        return [
            EmailHtml.build_td(r["name"], "left", color, bold=firing, mono=False),
            EmailHtml.build_td(STATUS[r["status"]], "left", color, mono=False),
            EmailHtml.build_td(f"{r['share'] * 100:.0f}%", "right", MUTED),
            EmailHtml.build_td(self._format_pct(r["pre"]), "right", color),
            EmailHtml.build_td(self._format_pct(r["react"]), "right", color),
            EmailHtml.build_td(self._format_pct(r["back"]), "right", MUTED),
            EmailHtml.build_td(self._format_pct(r["hchg"]), "right", MUTED),
        ]

    @staticmethod
    def _format_season(end_date: str) -> str:
        return f"{end_date[:4]}Q{int(end_date[4:6]) // 3}"

    @staticmethod
    def _format_pct(v: float | None) -> str:
        return "—" if v is None else f"{v:+.1f}%"
