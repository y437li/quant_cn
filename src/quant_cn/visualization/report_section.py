"""Base of the optional blocks of the 持仓监测 e-mail (宏观, 期货; plan 15 ph7h-7i)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class ReportSection(ABC):
    """
    Purpose:
        One optional block of the 持仓监测 e-mail fed by one app document: a summary line for
        the summary box and section rows for the body.

    Contract:
        Input:
            (none); subclasses set DOC, the document name (e.g. "macro_monitor")
        Output:
            instance; `build_summary(doc) -> str`, `build_rows(doc) -> str`
        Raises:
            (none at construction)

    Used by:
        visualization.VolatilityReportSection  -- subclass
        visualization.MonitorReportRenderer    -- renders every injected section
        visualization.MacroReportSection       -- subclass
        visualization.FuturesReportSection     -- subclass
        visualization.EtfReportSection         -- subclass
        visualization.BuybackReportSection     -- subclass
        visualization.BuybackMarketReportSection  -- subclass
        visualization.SmallCapReportSection    -- subclass
        visualization.RatesFxReportSection     -- subclass
        visualization.SectorEarningsReportSection  -- subclass
        visualization.TaskStatusReportSection  -- subclass

    Test cases:
        TC-MRR-003  (via MonitorReportRenderer) sections add their summary line and rows
    """

    DOC: ClassVar[str] = ""

    @abstractmethod
    def build_summary(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The block's line for the summary box.

        Contract:
            Input:
                doc: the section's document or None
            Output:
                str  -- plain text; "" for no line
            Raises:
                (none)
        """

    @abstractmethod
    def build_rows(self, doc: dict[str, Any] | None) -> str:
        """
        Purpose:
            The block's section rows.

        Contract:
            Input:
                doc: the section's document or None
            Output:
                str  -- HTML rows; "" for nothing
            Raises:
                (none)
        """
