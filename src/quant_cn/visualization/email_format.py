"""Number and date formats of the morning report e-mails (plan 15 ph7e)."""

from __future__ import annotations

import datetime as dt

INK, MUTED, LINE, SOFT = "#1d2733", "#6b7785", "#e3e8ee", "#f4f6f9"
UP, DOWN, BLUE, AMBER, RED = "#c4372d", "#2f7d63", "#2f6fdb", "#d08a2e", "#c4372d"
FONT = "-apple-system,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',Helvetica,Arial,sans-serif"
MONO = "'SF Mono',Menlo,Consolas,monospace"
WEEKDAYS = "一二三四五六日"


class EmailFormat:
    """
    Purpose:
        Turn report numbers into display text: dates with the Chinese weekday, signed
        percentages, vols, CNY with separators, sigmas, and the colour of a signed number
        (red up, green down, as on Chinese quote screens).

    Contract:
        Input:
            (none; static helpers)
        Output:
            str
        Raises:
            (none)

    Used by:
        visualization.VolatilityReportSection  -- change colour
        visualization.MonitorReportRenderer      -- 持仓监测 numbers
        visualization.OpportunityReportRenderer  -- 机会清单 dates
        visualization.MacroReportSection         -- 宏观 numbers

    Test cases:
        TC-EH-001  number formats: ymd, pct, vol, yuan, sig; None -> "—"
    """

    @staticmethod
    def format_ymd(d: str | None) -> str:
        """
        Purpose:
            YYYYMMDD -> YYYY-MM-DD.

        Contract:
            Input:
                d: str | None
            Output:
                str  -- "—" for empty
            Raises:
                (none)
        """
        return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "—"

    @staticmethod
    def format_day(d: str) -> str:
        """
        Purpose:
            Header date with the Chinese weekday.

        Contract:
            Input:
                d: str  -- YYYYMMDD
            Output:
                str  -- "2026-11-13 星期五"
            Raises:
                ValueError  -- malformed date
        """
        day = dt.datetime.strptime(d, "%Y%m%d")
        return f"{EmailFormat.format_ymd(d)} 星期{WEEKDAYS[day.weekday()]}"

    @staticmethod
    def format_pct(v: float | None, digits: int = 2) -> str:
        """
        Purpose:
            Signed percentage of a fraction.

        Contract:
            Input:
                v: float | None; digits: int
            Output:
                str  -- 0.0123 -> "+1.23%"; None -> "—"
            Raises:
                (none)
        """
        if v is None:
            return "—"
        sign = "+" if v > 0 else "−" if v < 0 else ""
        return f"{sign}{abs(v) * 100:.{digits}f}%"

    @staticmethod
    def format_vol(v: float | None) -> str:
        """
        Purpose:
            Unsigned percentage with one decimal (vols, weights).

        Contract:
            Input:
                v: float | None
            Output:
                str  -- 0.1637 -> "16.4%"; None -> "—"
            Raises:
                (none)
        """
        return "—" if v is None else f"{v * 100:.1f}%"

    @staticmethod
    def format_yuan(v: float | None) -> str:
        """
        Purpose:
            CNY without decimals and with thousands separators.

        Contract:
            Input:
                v: float | None
            Output:
                str  -- -50000.4 -> "−50,000"; None -> "—"
            Raises:
                (none)
        """
        return "—" if v is None else ("−" if v < 0 else "") + f"{abs(round(v)):,}"

    @staticmethod
    def format_sigma(v: float | None) -> str:
        """
        Purpose:
            Signed move in standard deviations.

        Contract:
            Input:
                v: float | None
            Output:
                str  -- -2.31 -> "−2.3σ"; None -> "—"
            Raises:
                (none)
        """
        if v is None:
            return "—"
        return ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.1f}σ"

    @staticmethod
    def get_color(v: float | None) -> str:
        """
        Purpose:
            Colour of a signed number (red up, green down).

        Contract:
            Input:
                v: float | None
            Output:
                str  -- hex colour; MUTED for 0 / None
            Raises:
                (none)
        """
        return UP if (v or 0) > 0 else DOWN if (v or 0) < 0 else MUTED
