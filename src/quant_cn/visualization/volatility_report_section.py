"""The 波动率 block of the 持仓监测 e-mail (plan 03 ph6, D-152)."""

from __future__ import annotations

from typing import Any, ClassVar

from quant_cn.visualization.email_format import AMBER, INK, MUTED, EmailFormat
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection


class VolatilityReportSection(ReportSection):
    """
    Purpose:
        Turn volatility_monitor.json into the e-mail's 波动率 parts: a summary line every day
        (each line's value and 1-year percentile, then the alert count with new ones named) and
        a small table of every line (value, one-day change, percentile, 1-year range) with
        alerting lines in amber and the alert messages under it.

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer as its 波动率 section

    Test cases:
        TC-VRS-001  summary names every line with value and percentile and counts alerts,
                    naming new ones; "" without a document
        TC-VRS-002  rows: one row per line, alerting line amber, alert messages listed;
                    数据缺失 when no document
    """

    DOC: ClassVar[str] = "volatility_monitor"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The one-line volatility summary for the e-mail's summary box.

        Contract:
            Input:
                doc: volatility_monitor document or None
            Output:
                str  -- plain text; "" when there is no document
            Raises:
                (none)
        """
        if not doc or not doc.get("lines"):
            return ""
        parts = [f"{x['name']} {x['value']:.1f}{self._format_pct(x, '（', '）')}"
                 for x in doc["lines"]]  # fmt: skip
        flags = doc.get("flags") or []
        new = [f["message"] for f in flags if f["key"] in set(doc.get("new_flags") or [])]
        tail = "；没有提醒。" if not flags else f"；{len(flags)} 个提醒"
        if flags and new:
            tail += f"，新增：{'、'.join(new)}"
        return "波动率：" + "，".join(parts) + tail

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 波动率 section rows: every line, then the alert messages.

        Contract:
            Input:
                doc: volatility_monitor document or None
            Output:
                str  -- section rows; 数据缺失 note without a document
            Raises:
                (none)
        """
        if not doc or not doc.get("lines"):
            return EmailHtml.build_missing("波动率", "volatility_monitor.json")
        alerting = {f["key"].split(":")[0] for f in doc.get("flags") or []}
        rows = []
        for x in doc["lines"]:
            color = AMBER if x["key"] in alerting else INK
            chg = x.get("chg")
            rows.append([
                EmailHtml.build_td(x["name"], "left", color, bold=True, mono=False),
                EmailHtml.build_td(f"{x['value']:.1f}", "right", color, bold=True),
                EmailHtml.build_td("" if chg is None else f"{chg:+.1f}", "right",
                                   EmailFormat.get_color(chg)),
                EmailHtml.build_td(self._format_pct(x, "", ""), "right", MUTED),
                EmailHtml.build_td(f"{x['low']:.1f}–{x['high']:.1f}", "right", MUTED),
                EmailHtml.build_td(x["date"], "right", MUTED),
            ])  # fmt: skip
        for f in doc.get("flags") or []:
            rows.append([EmailHtml.build_td(f["message"], "left", AMBER, mono=False)]
                        + [EmailHtml.build_td("", "right")] * 5)  # fmt: skip
        head = [EmailHtml.build_th(h, a) for h, a in (("指数", "left"), ("最新", "right"),
                ("日变化", "right"), ("1年分位", "right"), ("1年区间", "right"),
                ("日期", "right"))]  # fmt: skip
        sub = f"A 股按 CBOE 方法由期权计算，数据截至 {doc.get('as_of', '')}；美国 VIX 为 CBOE 收盘"
        return EmailHtml.build_section("波动率", sub, EmailHtml.build_table(head, rows))

    @staticmethod
    def _format_pct(x: dict[str, Any], left: str, right: str) -> str:
        pct = x.get("pct")
        return "" if pct is None else f"{left}1年 {pct * 100:.0f}% 分位{right}"
