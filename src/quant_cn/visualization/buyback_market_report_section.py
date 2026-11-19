"""The 回购增持（全市场） block of the 持仓监测 e-mail (plan 32 ph4, D-169)."""

from __future__ import annotations

from collections import Counter
from typing import Any, ClassVar

from quant_cn.visualization.email_format import INK, MUTED
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection

KINDS = (("buyback", "回购"), ("increase", "增持"))
LOAN = "专项贷款"
MAX_ROWS = 8  # new programmes per kind in the table, largest planned high first
TOP_TAGS = 3
WHOLE_YI = 100  # amounts at or above this many 亿 show no decimals


class BuybackMarketReportSection(ReportSection):
    """
    Purpose:
        From buyback_monitor.json, the market side of buybacks and 增持, the two kinds apart:
        a summary line per kind (new programmes in the window by purpose or holder type, how
        many use 专项贷款 and the loans, live programmes' planned and executed totals), and a
        table of each kind's largest new programmes with their labels (purpose / holder type,
        funding, planned range, % of market cap).

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer after the 回购 section

    Test cases:
        TC-BMR-001  summary: per kind new count with top labels and loans, live totals; ""
                    without a document
        TC-BMR-002  rows: new programmes of both kinds, largest first, at most MAX_ROWS per
                    kind, labels and 专项贷款 shown; 数据缺失 without a document
    """

    DOC: ClassVar[str] = "buyback_monitor"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 回购增持 line for the summary box.

        Contract:
            Input:
                doc: buyback_monitor document or None
            Output:
                str  -- plain text; "" without a document
            Raises:
                (none)
        """
        if not doc:
            return ""
        parts = []
        for key, name in KINDS:
            sec = doc.get(key) or {}
            new = self._list_new(sec)
            tags = Counter(t for r in new for t in r.get("tags") or [])
            top = "、".join(f"{t} {n}" for t, n in tags.most_common(TOP_TAGS))
            loans = [r for r in new if LOAN in (r.get("funding") or [])]
            total = (sec.get("totals") or {}).get("all") or {}
            parts.append(
                f"新{name} {len(new)} 个" + (f"（{top}）" if top else "")
                + (f"，其中{LOAN} {len(loans)} 个" if loans else "")
                + f"；在执行 {total.get('count', 0)} 个，计划上限 "
                f"{self._format_yi(total.get('high_yi'))}、已执行 "
                f"{self._format_yi(total.get('executed_yi'))}"
            )  # fmt: skip
        return f"全市场回购增持（近 {doc.get('days', 7)} 天）：" + "。".join(parts) + "。"

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 回购增持（全市场） section: the largest new programmes of each kind.

        Contract:
            Input:
                doc: buyback_monitor document or None
            Output:
                str  -- section rows; 数据缺失 note without a document
            Raises:
                (none)
        """
        if not doc:
            return EmailHtml.build_missing("回购增持（全市场）", "buyback_monitor.json")
        rows = []
        for key, name in KINDS:
            new = sorted(self._list_new(doc.get(key) or {}), key=lambda r: -(r.get("high_yi") or 0))
            for r in new[:MAX_ROWS]:
                funding = "、".join(r.get("funding") or []) or "—"
                if r.get("loan_yi") is not None:
                    funding += f"（贷 {self._format_yi(r['loan_yi'])}）"
                mv = r.get("mv_pct")
                rows.append([
                    EmailHtml.build_td(name, "left", MUTED, mono=False),
                    EmailHtml.build_td(r.get("name") or r["code"], "left", INK, bold=True,
                                       mono=False),
                    EmailHtml.build_td("、".join(r.get("tags") or []) or "—", "left", INK,
                                       mono=False),
                    EmailHtml.build_td(funding, "left", MUTED, mono=False),
                    EmailHtml.build_td(self._format_range(r.get("low_yi"), r.get("high_yi"))),
                    EmailHtml.build_td("—" if mv is None else f"{mv * 100:.2f}%", "right", MUTED),
                ])  # fmt: skip
        head = [EmailHtml.build_th(h, a) for h, a in (("类别", "left"), ("股票", "left"),
                ("用途 / 主体", "left"), ("资金", "left"), ("计划", "right"),
                ("占市值", "right"))]  # fmt: skip
        sub = (f"近 {doc.get('days', 7)} 天全市场新公告的回购与增持计划（各取计划上限最大的 "
               f"{MAX_ROWS} 个），标签由方舟大模型读公告原文，"
               f"截至 {doc.get('as_of', '')}")  # fmt: skip
        body = EmailHtml.build_table(head, rows) if rows else ""
        return EmailHtml.build_section("回购增持（全市场）", sub, body)

    @staticmethod
    def _list_new(sec: dict[str, Any]) -> list[dict[str, Any]]:
        return [e for e in sec.get("events") or [] if e.get("event") == "new"]

    @staticmethod
    def _format_yi(v: float | None) -> str:
        if v is None:
            return "—"
        return f"{v:,.0f}亿" if v >= WHOLE_YI else f"{v:.2f}亿" if v >= 1 else f"{v * 1e4:,.0f}万"

    @staticmethod
    def _format_range(low: float | None, high: float | None) -> str:
        f = BuybackMarketReportSection._format_yi
        if low is not None and high is not None:
            return f(low) if low == high else f"{f(low)}–{f(high)}"
        return f"≥{f(low)}" if low is not None else f"≤{f(high)}" if high is not None else "—"
