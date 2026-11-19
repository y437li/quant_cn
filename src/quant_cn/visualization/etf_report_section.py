"""The ETF 资金强度 line of the 持仓监测 e-mail (plan 15 ph7g)."""

from __future__ import annotations

from typing import Any, ClassVar

from quant_cn.visualization.report_section import ReportSection

STATUS = {"hot": "过热", "cooled": "降温", "normal": "正常"}


class EtfReportSection(ReportSection):
    """
    Purpose:
        One summary line from the `styles` of etf_proxy.json: per style (银行, 红利) its status
        (过热 / 降温 / 正常), z-score and 20-day flow as a share of AUM. The ETF table itself
        stays in MonitorReportRenderer, so this section adds no rows.

    Contract:
        Input:
            (none)
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> ""`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- passed to MonitorReportRenderer as its ETF style section

    Test cases:
        TC-ERS-001  summary names each style with status, z and flow share; "" without styles
    """

    DOC: ClassVar[str] = "etf_proxy"

    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The style ETF line for the summary box.

        Contract:
            Input:
                doc: etf_proxy document or None
            Output:
                str  -- "" when there are no styles
            Raises:
                (none)
        """
        styles = (doc or {}).get("styles") or []
        parts = []
        for s in styles:
            z, pct = s.get("z"), s.get("flow_pct")
            text = f"{s['name']} {STATUS.get(s.get('status', ''), '—')}"
            if z is not None:
                text += f"（z {z:+.1f}"
                text += f"，20 日流入占规模 {pct * 100:+.1f}%）" if pct is not None else "）"
            parts.append(text)
        return "ETF 资金强度：" + " · ".join(parts) if parts else ""

    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            No rows: the ETF section is drawn by MonitorReportRenderer.

        Contract:
            Input:
                doc: etf_proxy document or None
            Output:
                str  -- always ""
            Raises:
                (none)
        """
        return ""
