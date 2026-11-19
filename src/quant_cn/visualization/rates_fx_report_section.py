"""The 利率汇率 block of the 持仓监测 e-mail (plan 34 ph4, D-171)."""

from __future__ import annotations

from typing import Any, ClassVar

from quant_cn.visualization.email_format import INK, MUTED, RED
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection

SUMMARY_KEYS = ("cn_10y", "usdcnh")
BIG_RATE = 100  # FX levels at or above this (USDJPY, dollar index) show 2 decimals, others 4
TABLE_KEYS = ("cn_10y", "cn_30y", "term_10_1", "credit_bank", "erp", "usdcnh", "fix_gap",
              "eurcnh", "cnhjpy", "cn_us_10y")  # fmt: skip


class RatesFxReportSection(ReportSection):
    """
    Purpose:
        Turn rates_fx_monitor.json into the e-mail's 利率汇率 parts: a summary line every day
        (10Y yield and USDCNH with their one-week change and 5-year percentile, then the
        alerts, new ones marked) and a table of the key rows (TABLE_KEYS in that order: level,
        1w / 1m / 1y change, 5-year percentile) with alerting rows in red.

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer as its 利率汇率 section

    Test cases:
        TC-RRS-001  summary: 10Y and USDCNH lines, alerts with new ones marked; 没有提醒
                    when none; "" without a document
        TC-RRS-002  rows: TABLE_KEYS order, missing keys skipped, alerting rows red, values
                    and changes by unit (yield %, bp, rate, gap); 数据缺失 without a document
    """

    DOC: ClassVar[str] = "rates_fx_monitor"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The one-line 利率汇率 summary for the e-mail's summary box.

        Contract:
            Input:
                doc: rates_fx_monitor document or None
            Output:
                str  -- plain text; "" when there is no document or no rows
            Raises:
                (none)
        """
        if not doc or not doc.get("rows"):
            return ""
        by = {r["key"]: r for r in doc["rows"]}
        parts = [
            f"{r['name']} {self._format_level(r['value'], r['unit'])}（一周 "
            f"{self._format_change(r['chg'].get('1w'), r['unit'])}，5年分位 {self._format_pct(r)}）"
            for r in (by.get(k) for k in SUMMARY_KEYS)
            if r
        ]
        new = set(doc.get("new_flags") or [])
        alerts = [f["message"] + ("（新）" if f["key"] in new else "")
                  for f in doc.get("flags") or []]  # fmt: skip
        tail = f"提醒：{'；'.join(alerts)}" if alerts else "没有提醒"
        return "利率汇率：" + "；".join(parts) + f"。{tail}。"

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 利率汇率 section: the key rows of both groups.

        Contract:
            Input:
                doc: rates_fx_monitor document or None
            Output:
                str  -- section rows; 数据缺失 note without a document
            Raises:
                (none)
        """
        if not doc or not doc.get("rows"):
            return EmailHtml.build_missing("利率汇率", "rates_fx_monitor.json")
        by = {r["key"]: r for r in doc["rows"]}
        rows = []
        for r in (by[k] for k in TABLE_KEYS if k in by):
            alerting = bool(r.get("alerts"))
            color = RED if alerting else INK
            unit, chg = r["unit"], r["chg"]
            rows.append([
                EmailHtml.build_td(r.get("group", ""), "left", MUTED, mono=False),
                EmailHtml.build_td(r["name"], "left", color, bold=alerting, mono=False),
                EmailHtml.build_td(self._format_level(r["value"], unit), "right", color, bold=True),
                *[EmailHtml.build_td(self._format_change(chg.get(h), unit), "right", MUTED)
                  for h in ("1w", "1m", "1y")],
                EmailHtml.build_td(self._format_pct(r), "right", MUTED),
            ])  # fmt: skip
        head = [EmailHtml.build_th(h, a) for h, a in (("组", "left"), ("项目", "left"),
                ("最新", "right"), ("1周", "right"), ("1月", "right"), ("1年", "right"),
                ("5年分位", "right"))]  # fmt: skip
        sub = f"国债、利差、股债性价比与人民币汇率，数据截至 {doc.get('as_of', '')}；红色为触发提醒"
        return EmailHtml.build_section("利率汇率", sub, EmailHtml.build_table(head, rows))

    @staticmethod
    def _format_level(v: float | None, unit: str) -> str:
        if v is None:
            return "—"
        if unit == "yield":
            return f"{v:.4f}%"
        if unit == "bp":
            return f"{v:+.1f}bp"
        if unit == "gap":
            return f"{v * 100:+.2f}%"
        return f"{v:.2f}" if v >= BIG_RATE else f"{v:.4f}"

    @staticmethod
    def _format_change(v: float | None, unit: str) -> str:
        if v is None:
            return "—"
        if unit in ("yield", "bp"):
            return f"{round(v):+d}bp" if round(v) else "0bp"
        if unit == "gap":
            return f"{v * 100:+.2f}pp"
        return f"{v * 100:+.2f}%"

    @staticmethod
    def _format_pct(r: dict[str, Any]) -> str:
        pct = r.get("pct")
        return "—" if pct is None else f"{pct * 100:.0f}%"
