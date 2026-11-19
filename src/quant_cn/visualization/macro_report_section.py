"""The 宏观 block of the 持仓监测 e-mail (plan 15 ph7h, D-143)."""

from __future__ import annotations

from typing import Any, ClassVar

from quant_cn.visualization.email_format import AMBER, INK, MUTED, EmailFormat
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection

SUMMARY_KEYS = ("cpi", "ppi", "pmi_mfg", "m1_m2", "sf_stock_yoy")
DIGITS = {"sf_stock_yoy": 2}  # decimals per line; 1 elsewhere (NBS prints one decimal)
EXTREME = 0.1  # percentile at or beyond which a line is marked (bottom / top 10% of 5 years)


class MacroReportSection(ReportSection):
    """
    Purpose:
        Turn macro_monitor.json into the e-mail's 宏观 parts: one summary line every day, and
        on days with a new print the full table (latest, previous, change, 5-year percentile,
        new marker) grouped by 价格 / 景气 / 货币 / 社融.

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer as its 宏观 section

    Test cases:
        TC-MRS-001  summary names the five headline lines with month and change
        TC-MRS-002  rows: full table with a new print; nothing without one; 数据缺失 when no doc
    """

    DOC: ClassVar[str] = "macro_monitor"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The one-line macro summary for the e-mail's summary box.

        Contract:
            Input:
                doc: macro_monitor document or None
            Output:
                str  -- plain text; "" when there is no document
            Raises:
                (none)
        """
        if not doc or not doc.get("series"):
            return ""
        by_key = {s["key"]: s for s in doc["series"]}
        parts = [self._format_short(by_key[k]) for k in SUMMARY_KEYS if k in by_key]
        new = len(doc.get("new_prints") or [])
        return "宏观：" + " · ".join(parts) + (f"（{new} 项新发布）" if new else "")

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 宏观 section rows: the full table when any line has a new print.

        Contract:
            Input:
                doc: macro_monitor document or None
            Output:
                str  -- section rows; "" with no new print; 数据缺失 note without a document
            Raises:
                (none)
        """
        if not doc or not doc.get("series"):
            return EmailHtml.build_missing("宏观", "macro_monitor.json")
        if not doc.get("new_prints"):
            return ""
        head = [
            EmailHtml.build_th(h, a)
            for h, a in (("指标", "left"), ("月份", "left"), ("最新", "right"), ("前值", "right"))
        ] + [EmailHtml.build_th(h) for h in ("变化", "5年分位", "")]
        rows = [self._build_row(s) for s in doc["series"]]
        missing = doc.get("missing") or []
        sub = "社融单位亿元；新发布标 ●；分位 ≤10% 或 ≥90% 标橙" + (
            f"；缺 {', '.join(missing)}" if missing else ""
        )
        return EmailHtml.build_section("宏观", sub, EmailHtml.build_table(head, rows))

    @staticmethod
    def _format_value(s: dict[str, Any], v: float | None, signed: bool = False) -> str:
        if v is None:
            return "—"
        sign = ("+" if v > 0 else "−" if v < 0 else "") if signed else ("−" if v < 0 else "")
        if s["unit"] == "亿元":
            return sign + f"{abs(round(v)):,}"
        digits = DIGITS.get(s["key"], 1)
        return sign + f"{abs(v):.{digits}f}" + ("%" if s["unit"] == "%" else "")

    @classmethod
    def _format_short(cls, s: dict[str, Any]) -> str:
        change = s.get("change")
        delta = "" if change is None else "，" + cls._format_value(s, change, signed=True)
        return f"{s['name']} {cls._format_value(s, s['value'])}（{int(s['month'][4:])}月{delta}）"

    @classmethod
    def _build_row(cls, s: dict[str, Any]) -> list[str]:
        pct = s.get("pct_5y")
        extreme = pct is not None and (pct <= EXTREME or pct >= 1 - EXTREME)
        change = s.get("change")
        return [
            EmailHtml.build_td(f"{s['group']} · {s['name']}", "left", INK, mono=False),
            EmailHtml.build_td(f"{s['month'][:4]}-{s['month'][4:]}", "left", MUTED),
            EmailHtml.build_td(cls._format_value(s, s["value"]), bold=True),
            EmailHtml.build_td(cls._format_value(s, s.get("prev")), color=MUTED),
            EmailHtml.build_td(
                cls._format_value(s, change, signed=True),
                color=EmailFormat.get_color(change),
            ),
            EmailHtml.build_td(
                "—" if pct is None else f"{pct * 100:.0f}%", color=AMBER if extreme else INK
            ),
            EmailHtml.build_td("●" if s.get("new_print") else "", "center", AMBER),
        ]
