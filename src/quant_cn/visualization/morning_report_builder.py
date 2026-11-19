"""Build, check and send the two morning e-mails (持仓监测, 机会清单; plan 15 ph7e, D-136)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_cn.core.exceptions import LakeError
from quant_cn.core.mail_sender import MailContent, MailSender
from quant_cn.visualization.monitor_report_renderer import MonitorReportRenderer
from quant_cn.visualization.opportunity_report_renderer import OpportunityReportRenderer

logger = logging.getLogger(__name__)
MONITOR_DOCS = (
    "holdings_risk",
    "factor_monitor",
    "etf_proxy",
    "macro_monitor",
    "futures_monitor",
    "volatility_monitor",
    "smallcap_watch",
    "rates_fx_monitor",
    "sector_earnings_signal",
    "buybacks",
    "buyback_monitor",
    "task_status",
)
OPPORTUNITY_DOCS = ("opportunities", "watchlist")
FRESH_DOCS = {"monitor": ("holdings_risk", "factor_monitor"), "opportunity": ("watchlist",)}


@dataclass(frozen=True)
class ReportOutcome:
    """
    Purpose:
        What happened to one e-mail: written, sent, or skipped and why.

    Contract:
        Input:
            name: str ("monitor" | "opportunity"); action: str ("written" | "sent" | "skipped");
            detail: str  -- file path, subject or the reason for skipping
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        visualization.MorningReportBuilder.run  -- return items

    Test cases:
        TC-MRB-002  stale data -> skipped with the dates in the reason
    """

    name: str
    action: str
    detail: str


class MorningReportBuilder:
    """
    Purpose:
        Read the app's JSON documents from the data directory, render the 持仓监测 and 机会清单
        e-mails, refuse an e-mail whose data is older than the last trading session (it logs
        and skips instead of sending yesterday's numbers), and either write the HTML files
        (dry run) or send them.

    Contract:
        Input:
            data_dir:    Path  -- the chain app's data directory (holdings_risk.json, …)
            monitor:     MonitorReportRenderer
            opportunity: OpportunityReportRenderer
            sender:      MailSender | None  -- None allows dry runs only
        Output:
            instance; `read_documents()`, `build(today)`, `run(today, last_session, out_dir)`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `morning-report` command

    Test cases:
        TC-MRB-001  dry run writes both HTML files; missing documents are passed as None
        TC-MRB-002  stale data -> skipped with the dates in the reason; nothing sent
        TC-MRB-003  send mode sends both through the sender; no sender -> LakeError
    """

    def __init__(
        self,
        data_dir: Path,
        monitor: MonitorReportRenderer,
        opportunity: OpportunityReportRenderer,
        sender: MailSender | None,
    ) -> None:
        self._dir = data_dir
        self._monitor = monitor
        self._opportunity = opportunity
        self._sender = sender

    def read_documents(self) -> dict[str, dict[str, Any] | None]:
        """
        Purpose:
            Every input document by name; None when its file is missing.

        Contract:
            Input:
                (none)
            Output:
                dict  -- MONITOR_DOCS + OPPORTUNITY_DOCS names -> parsed JSON or None
            Raises:
                LakeError  -- a file exists but is not valid JSON
        """
        out: dict[str, dict[str, Any] | None] = {}
        for name in MONITOR_DOCS + OPPORTUNITY_DOCS:
            path = self._dir / f"{name}.json"
            try:
                out[name] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            except json.JSONDecodeError as exc:
                raise LakeError(f"morning report: {path} is not valid JSON: {exc}") from exc
        return out

    def build(self, today: str) -> dict[str, MailContent]:
        """
        Purpose:
            Render both e-mails without any freshness check.

        Contract:
            Input:
                today: str  -- YYYYMMDD of the report
            Output:
                dict  -- {"monitor": MailContent, "opportunity": MailContent}
            Raises:
                LakeError  -- malformed document
        """
        docs = self.read_documents()
        return {
            "monitor": self._monitor.render(docs, today),
            "opportunity": self._opportunity.render(docs, today),
        }

    def run(self, today: str, last_session: str, out_dir: Path | None) -> list[ReportOutcome]:
        """
        Purpose:
            Check freshness, then write (out_dir given) or send each e-mail.

        Contract:
            Input:
                today:        str          -- YYYYMMDD of the report
                last_session: str          -- YYYYMMDD; the data must be at least this recent
                out_dir:      Path | None  -- dry run into this directory; None = send
            Output:
                list[ReportOutcome]  -- one per e-mail, in order monitor, opportunity
            Raises:
                LakeError    -- malformed document; send mode without a sender
                ConfigError  -- mail settings or password missing (from MailSender)
        """
        if out_dir is None and self._sender is None:
            raise LakeError("morning report: no mail sender configured; use --dry-run")
        docs = self.read_documents()
        mails = {
            "monitor": self._monitor.render(docs, today),
            "opportunity": self._opportunity.render(docs, today),
        }
        outcomes = []
        for name, mail in mails.items():
            stale = self._list_stale(docs, name, last_session)
            if stale:
                reason = f"data older than {last_session}: {', '.join(stale)}"
                logger.warning("morning report %s skipped: %s", name, reason)
                outcomes.append(ReportOutcome(name, "skipped", reason))
            elif out_dir is not None:
                path = out_dir / f"morning_{name}_{today}.html"
                path.write_text(mail.html, encoding="utf-8")
                outcomes.append(ReportOutcome(name, "written", str(path)))
            elif self._sender is not None:
                self._sender.run(mail)
                outcomes.append(ReportOutcome(name, "sent", mail.subject))
        return outcomes

    @staticmethod
    def _list_stale(
        docs: dict[str, dict[str, Any] | None], name: str, last_session: str
    ) -> list[str]:
        out = []
        for key in FRESH_DOCS[name]:
            doc = docs.get(key)
            as_of = str(doc.get("as_of", "")) if doc else ""
            if doc is not None and as_of < last_session:
                out.append(f"{key} {as_of or 'empty'}")
        return out
