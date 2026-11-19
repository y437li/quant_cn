"""The 小盘观察 block of the 持仓监测 e-mail (plan 30 ph2)."""

from __future__ import annotations

from typing import Any, ClassVar

from quant_cn.visualization.email_format import AMBER, INK, MUTED, RED
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection

STATE = {"on": "已触发", "near": "接近", "off": "未到", "info": "参考"}
STATE_COLOR = {"on": RED, "near": AMBER}


class SmallCapReportSection(ReportSection):
    """
    Purpose:
        Turn smallcap_watch.json into the e-mail's 小盘观察 parts: a summary line every day
        (triggered rows named, new ones marked, then rows near their trigger) and a table of
        every row (group, name, latest value, percentile, trigger, state, note) with triggered
        rows first and in red, near rows in amber.

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer as its 小盘观察 section

    Test cases:
        TC-SRS-001  summary names triggered rows (new ones marked) and near rows;
                    没有触发 when none fired; "" without a document
        TC-SRS-002  rows: triggered rows first and red, near rows amber, values formatted
                    by unit (只, 占比, 点, %, 亿), None value as "—"; 数据缺失 without a document
        TC-SRS-003  涨跌 rows (ph5 放量大跌): value "-1.9%", trigger "≤ -3%"
    """

    DOC: ClassVar[str] = "smallcap_watch"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The one-line 小盘观察 summary for the e-mail's summary box.

        Contract:
            Input:
                doc: smallcap_watch document or None
            Output:
                str  -- plain text; "" when there is no document or no rows
            Raises:
                (none)
        """
        if not doc or not doc.get("rows"):
            return ""
        new = set(doc.get("new_triggered") or [])
        on = [r["name"] + ("（新）" if r["key"] in new else "")
              for r in doc["rows"] if r.get("state") == "on"]  # fmt: skip
        near = [f"{r['name']} {self._format_value(r)}"
                for r in doc["rows"] if r.get("state") == "near"]  # fmt: skip
        head = f"已触发 {'、'.join(on)}" if on else "没有触发"
        return "小盘观察：" + head + (f"；接近：{'、'.join(near)}" if near else "") + "。"

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The 小盘观察 section: every row, triggered ones first.

        Contract:
            Input:
                doc: smallcap_watch document or None
            Output:
                str  -- section rows; 数据缺失 note without a document
            Raises:
                (none)
        """
        if not doc or not doc.get("rows"):
            return EmailHtml.build_missing("小盘观察", "smallcap_watch.json")
        ordered = [r for r in doc["rows"] if r.get("state") == "on"]
        ordered += [r for r in doc["rows"] if r.get("state") != "on"]
        rows = []
        for r in ordered:
            state = r.get("state", "")
            color = STATE_COLOR.get(state, INK)
            pct = r.get("pct")
            rows.append([
                EmailHtml.build_td(r.get("group", ""), "left", MUTED, mono=False),
                EmailHtml.build_td(r["name"], "left", color, bold=state == "on", mono=False),
                EmailHtml.build_td(self._format_value(r), "right", color, bold=True),
                EmailHtml.build_td("" if pct is None else f"{pct * 100:.0f}%", "right", MUTED),
                EmailHtml.build_td(self._format_trigger(r), "right", MUTED),
                EmailHtml.build_td(STATE.get(state, state), "right", color, mono=False),
                EmailHtml.build_td(r.get("note", ""), "left", MUTED, mono=False),
            ])  # fmt: skip
        head = [EmailHtml.build_th(h, a) for h, a in (("组", "left"), ("指标", "left"),
                ("最新", "right"), ("3年分位", "right"), ("触发线", "right"),
                ("状态", "right"), ("说明", "left"))]  # fmt: skip
        sub = f"中证1000 / 科创50 抄底信号，数据截至 {doc.get('as_of', '')}；已触发的排在最前"
        return EmailHtml.build_section("小盘观察", sub, EmailHtml.build_table(head, rows))

    @staticmethod
    def _format_value(r: dict[str, Any]) -> str:
        v, unit = r.get("value"), r.get("unit", "")
        if v is None:
            return "—"
        by_unit = {
            "占比": f"{v * 100:.0f}%",
            "点": f"{v:,.0f}",
            "%": f"{v:.1f}%",
            "亿": f"{v:+,.1f}亿",
            "涨跌": f"{v * 100:+.1f}%",  # day return as a fraction (ph5 放量大跌)
        }
        return by_unit.get(unit, f"{v:,.0f}{unit}")

    @staticmethod
    def _format_trigger(r: dict[str, Any]) -> str:
        t, unit = r.get("trigger"), r.get("unit", "")
        if t is None:
            return ""
        if unit == "%":  # vol rows: the trigger is a percentile
            return f"≥ {t * 100:.0f}% 分位"
        if unit == "点":
            return f"≤ {t:,.0f}"
        if unit == "占比":
            return f"≥ {t * 100:.0f}%"
        if unit == "涨跌":
            return f"≤ {t * 100:.0f}%"
        return f"≥ {t:,.0f}{unit}"
