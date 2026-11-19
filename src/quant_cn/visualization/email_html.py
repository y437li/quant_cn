"""E-mail-safe HTML building blocks for the morning report (tables, inline styles; ph7e)."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

from quant_cn.visualization.email_format import AMBER, BLUE, FONT, INK, LINE, MONO, MUTED, SOFT


class EmailHtml:
    """
    Purpose:
        Layout helpers that render in Gmail and Apple Mail: table cells, sections, two-column
        pairs, signed bars drawn with table cells, KPI tiles and the page shell (desktop width
        960 px, D-136). Number formats live in EmailFormat.

    Contract:
        Input:
            (none; static helpers)
        Output:
            HTML / text fragments as str
        Raises:
            (none)

    Used by:
        visualization.TaskStatusReportSection  -- td / th / table / section
        visualization.VolatilityReportSection  -- 波动率 block
        visualization.MonitorReportRenderer      -- 持仓监测 e-mail
        visualization.OpportunityReportRenderer  -- 机会清单 e-mail
        visualization.MacroReportSection         -- 宏观 block
        visualization.FuturesReportSection       -- 期货 block
        visualization.BuybackReportSection       -- 回购 block
        visualization.BuybackMarketReportSection -- 回购增持（全市场） block
        visualization.SmallCapReportSection      -- 小盘观察 block
        visualization.RatesFxReportSection       -- 利率汇率 block
        visualization.SectorEarningsReportSection  -- 财报季信号 block

    Test cases:
        TC-EH-002  text is escaped; page wraps sections with the date line and summary
    """

    @staticmethod
    def build_td(
        text: str,
        align: str = "right",
        color: str = INK,
        bold: bool = False,
        mono: bool = True,
        bg: str | None = None,
    ) -> str:
        """
        Purpose:
            One table cell; `text` is escaped.

        Contract:
            Input:
                text: str; align, color: str; bold, mono: bool; bg: str | None
            Output:
                str  -- <td> with inline style
            Raises:
                (none)
        """
        style = (
            f"padding:6px 8px;border-bottom:1px solid {LINE};text-align:{align};color:{color};"
            f"font-family:{MONO if mono else FONT};font-size:13px;"
            f"{'font-weight:600;' if bold else ''}{f'background:{bg};' if bg else ''}"
            "white-space:nowrap"
        )
        return f'<td style="{style}">{escape(text)}</td>'

    @staticmethod
    def build_th(text: str, align: str = "right") -> str:
        """
        Purpose:
            One header cell.

        Contract:
            Input:
                text: str; align: str
            Output:
                str  -- <th>
            Raises:
                (none)
        """
        return (
            f'<th style="padding:6px 8px;border-bottom:2px solid {LINE};text-align:{align};'
            f'color:{MUTED};font-weight:500;font-size:12px;font-family:{FONT}">{escape(text)}</th>'
        )

    @staticmethod
    def build_table(head: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
        """
        Purpose:
            A full-width table from header and row cells.

        Contract:
            Input:
                head: header cells; rows: lists of cells (already built)
            Output:
                str  -- <table>
            Raises:
                (none)
        """
        body = "".join("<tr>" + "".join(r) + "</tr>" for r in rows)
        return (
            '<table role="presentation" cellpadding="0" cellspacing="0" '
            f'style="width:100%;border-collapse:collapse"><tr>{"".join(head)}</tr>{body}</table>'
        )

    @staticmethod
    def build_section(title: str, sub: str, body: str) -> str:
        """
        Purpose:
            A titled section as two rows of the page table.

        Contract:
            Input:
                title, sub: str (escaped); body: str (HTML)
            Output:
                str  -- two <tr>
            Raises:
                (none)
        """
        return (
            f'<tr><td style="padding:20px 24px 4px"><div style="font-size:16px;font-weight:600;'
            f'color:{INK}">{escape(title)}<span style="font-size:12px;font-weight:400;'
            f'color:{MUTED};margin-left:8px">{escape(sub)}</span></div></td></tr>'
            f'<tr><td style="padding:6px 24px 4px">{body}</td></tr>'
        )

    @staticmethod
    def build_missing(title: str, file_name: str) -> str:
        """
        Purpose:
            A section saying its input file is missing (the other sections still render).

        Contract:
            Input:
                title: str; file_name: str
            Output:
                str  -- section rows
            Raises:
                (none)
        """
        note = (
            f'<div style="color:{MUTED};font-size:13px">数据缺失：没有 {escape(file_name)}。</div>'
        )
        return EmailHtml.build_section(title, "", note)

    @staticmethod
    def build_pair(left: str, right: str) -> str:
        """
        Purpose:
            Two sections side by side (desktop layout).

        Contract:
            Input:
                left, right: section rows
            Output:
                str  -- one <tr>
            Raises:
                (none)
        """
        cell = (
            '<td style="width:50%;vertical-align:top">'
            '<table role="presentation" style="width:100%">'
        )
        return (
            '<tr><td style="padding:0 12px"><table role="presentation" cellpadding="0" '
            f'cellspacing="0" style="width:100%"><tr>{cell}{left}</table></td>'
            f"{cell}{right}</table></td></tr></table></td></tr>"
        )

    @staticmethod
    def build_bar(v: float | None, scale: float = 2.0) -> str:
        """
        Purpose:
            A signed bar around 0 drawn with table cells (no images): blue right, amber left.

        Contract:
            Input:
                v: float | None; scale: float  -- |v| at full width (60 px)
            Output:
                str  -- one <td>; empty cell for None
            Raises:
                (none)
        """
        if v is None:
            return EmailHtml.build_td("")
        w = int(min(abs(v), scale) / scale * 60)
        span = '<span style="display:inline-block;height:8px;width:{w}px;background:{c}"></span>'
        left = span.format(w=w if v < 0 else 0, c=AMBER)
        right = span.format(w=w if v > 0 else 0, c=BLUE)
        return (
            f'<td style="padding:6px 8px;border-bottom:1px solid {LINE}">'
            '<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
            '<td style="width:60px;padding:0;text-align:right">'
            f'{left}</td><td style="width:1px;padding:0;background:{MUTED}"></td>'
            f'<td style="width:60px;padding:0">{right}</td></tr></table></td>'
        )

    @staticmethod
    def build_tile(label: str, value: str, note: str = "", color: str = INK) -> str:
        """
        Purpose:
            One KPI tile.

        Contract:
            Input:
                label, value, note: str (escaped); color: str
            Output:
                str  -- one <td>
            Raises:
                (none)
        """
        return (
            f'<td style="padding:12px;border:1px solid {LINE};border-radius:8px;background:#fff">'
            f'<div style="font-size:12px;color:{MUTED}">{escape(label)}</div>'
            f'<div style="font-family:{MONO};font-size:20px;color:{color};margin-top:4px">'
            f'{escape(value)}</div><div style="font-size:11px;color:{MUTED};margin-top:2px">'
            f"{escape(note)}</div></td>"
        )

    @staticmethod
    def build_page(kicker: str, day: str, sub: str, summary: Sequence[str], rows: str) -> str:
        """
        Purpose:
            The whole e-mail: header, summary box, sections, footer.

        Contract:
            Input:
                kicker: e-mail name; day: header date line; sub: data line;
                summary: lines (HTML allowed: built by the renderer); rows: section rows
            Output:
                str  -- complete HTML document
            Raises:
                (none)
        """
        box = "<br>".join("· " + s for s in summary)
        return (
            '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<title>{escape(kicker)}</title></head><body style="margin:0;padding:0;'
            f'background:{SOFT};font-family:{FONT};color:{INK}"><table role="presentation" '
            f'cellpadding="0" cellspacing="0" style="width:100%;background:{SOFT}"><tr>'
            '<td align="center" style="padding:16px 8px"><table role="presentation" '
            'cellpadding="0" cellspacing="0" style="width:100%;max-width:960px;min-width:900px;'
            f'background:#fff;border-radius:10px;border:1px solid {LINE}">'
            f'<tr><td style="padding:22px 24px 6px;border-bottom:3px solid {INK}">'
            f'<div style="font-size:12px;color:{MUTED};letter-spacing:.08em">QUANT_CN · '
            f'{escape(kicker)}</div><div style="font-size:22px;font-weight:700;margin-top:4px">'
            f'{escape(day)}</div><div style="font-size:12px;color:{MUTED};margin-top:2px">'
            f'{escape(sub)}</div></td></tr><tr><td style="padding:16px 24px 0"><div style="'
            f"background:{SOFT};border-left:3px solid {BLUE};padding:10px 14px;font-size:14px;"
            f'line-height:1.8">{box}</div></td></tr>{rows}'
            f'<tr><td style="padding:18px 24px 22px;font-size:11px;color:{MUTED};line-height:1.7;'
            f'border-top:1px solid {LINE}">本邮件由 quant_cn 自动生成；完整页面见本地 app。'
            "</td></tr></table></td></tr></table></body></html>"
        )
