"""CLI commands `morning-report` (ph7e), `macro-monitor` (ph7h), `futures-monitor` (ph7i) and
`volatility-monitor` (plan 03 ph6) and `notify` (plan 22)."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from rich.console import Console

from quant_cn.calculation.futures_monitor_builder import FuturesMonitorBuilder
from quant_cn.calculation.macro_monitor_builder import MacroMonitorBuilder
from quant_cn.calculation.margin_ladder_estimator import MarginLadderEstimator
from quant_cn.calculation.rates_fx_monitor_builder import RatesFxMonitorBuilder
from quant_cn.calculation.rates_fx_series_reader import RatesFxSeriesReader
from quant_cn.calculation.realized_vol_calculator import RealizedVolCalculator
from quant_cn.calculation.volatility_monitor_builder import VolatilityMonitorBuilder
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.etf_cta_settings import EtfCtaSettings
from quant_cn.core.etf_cta_views import EtfCtaViews
from quant_cn.core.futures_monitor_settings import FuturesMonitorSettings
from quant_cn.core.mail_sender import MailSender, MailSettings
from quant_cn.core.message_sender import (
    IMessageSender,
    MessageSender,
    NotifyRecipient,
    NotifySettings,
)
from quant_cn.core.positions_book import PositionsBook
from quant_cn.core.rates_fx_monitor_settings import RatesFxMonitorSettings
from quant_cn.core.sent_alert_log import SentAlertLog
from quant_cn.core.small_cap_watch_settings import SmallCapWatchSettings
from quant_cn.core.volatility_monitor_settings import VolatilityMonitorSettings
from quant_cn.lake.buyback_ledger import BuybackLedger
from quant_cn.lake.label_store import LabelStore
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.portfolio.buyback_events_builder import BuybackEventsBuilder
from quant_cn.portfolio.buyback_monitor_builder import BuybackMonitorBuilder
from quant_cn.portfolio.buyback_plan_frame import BuybackPlanFrame
from quant_cn.portfolio.etf_cta_book import EtfCtaBook
from quant_cn.portfolio.etf_flow_calculator import EtfFlowCalculator
from quant_cn.portfolio.margin_panel_builder import MarginPanelBuilder
from quant_cn.portfolio.small_cap_watch_builder import SmallCapWatchBuilder
from quant_cn.portfolio.small_cap_watch_rows import SmallCapWatchRows
from quant_cn.visualization.alert_message_builder import DOCS as ALERT_DOCS
from quant_cn.visualization.alert_message_builder import Alert, AlertMessageBuilder, CardShot
from quant_cn.visualization.buyback_market_report_section import BuybackMarketReportSection
from quant_cn.visualization.buyback_report_section import BuybackReportSection
from quant_cn.visualization.card_screenshotter import CardScreenshotter
from quant_cn.visualization.etf_report_section import EtfReportSection
from quant_cn.visualization.futures_report_section import FuturesReportSection
from quant_cn.visualization.macro_report_section import MacroReportSection
from quant_cn.visualization.monitor_report_renderer import MonitorReportRenderer
from quant_cn.visualization.morning_report_builder import MorningReportBuilder
from quant_cn.visualization.opportunity_report_renderer import OpportunityReportRenderer
from quant_cn.visualization.rates_fx_report_section import RatesFxReportSection
from quant_cn.visualization.sector_earnings_report_section import SectorEarningsReportSection
from quant_cn.visualization.small_cap_report_section import SmallCapReportSection
from quant_cn.visualization.task_status_report_section import TaskStatusReportSection
from quant_cn.visualization.volatility_report_section import VolatilityReportSection

DATA_DIR = Path("research_space/prototypes/chain_view")  # the chain app's data folder
SENT_LOG = "notify_sent.json"  # alert keys already sent (plan 22)


class ReportCommands:
    """
    Purpose:
        Report subcommands, kept out of cli.py (at its size limit). Monitors write the app's
        JSON: `macro-monitor` (plan 15 ph7h), `futures-monitor` (ph7i), `volatility-monitor`
        (plan 03 ph6), `margin-panel` (ph7m), `buyback-events` (plan 23 ph6; also the plan 32
        market monitor), `etf-cta` (plan 27), `smallcap-watch` (plan 30), `rates-fx-monitor`
        (plan 34). `morning-report` builds the 持仓监测 and 机会清单 e-mails for the last session
        before today and sends them (or writes HTML with --dry-run). `notify` sends iMessage
        alerts (plan 22, D-153): `--text` as given, else the new alerts (AlertMessageBuilder,
        SentAlertLog) with card pictures (CardScreenshotter); `--sample` sends today's full set
        without touching the sent log; old pictures are deleted at the next run's start.

    Contract:
        Input:
            console: Console
            sender:  MessageSender | None  -- phone alerts; default IMessageSender()
        Output:
            instance; `build_parser(sub)` (static), `_run_<command>(config, args) -> int` per
            subcommand (dispatched by QuantCnCli.run)
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- parser and dispatch

    Test cases:
        TC-RPC-001  --dry-run writes both HTML files and sends nothing; exit 0
        TC-RPC-002  a stale document is reported as skipped; exit 0
        TC-RPC-003  macro-monitor writes macro_monitor.json from the curated macro tables
        TC-RPC-004  futures-monitor writes futures_monitor.json
        TC-RPC-005  volatility-monitor writes volatility_monitor.json
        TC-RPC-006  notify --text sends to the named recipient; --dry-run sends nothing
        TC-RPC-007  notify from documents sends the new alerts once; the next run sends nothing;
                    the previous run's pictures and their empty folder are deleted on the next run
        TC-RPC-008  notify --sample sends today's full set with the sample note, log untouched
        TC-RPC-009  margin-panel writes margin/<code>.json for stocks with margin data
        TC-RPC-010  buyback-events writes buybacks.json with the large plans of the window and
                    buyback_monitor.json
        TC-RPC-011  etf-cta writes etf_cta.json from fund_daily
        TC-RPC-012  smallcap-watch writes smallcap_watch.json
        TC-RPC-013  rates-fx-monitor writes rates_fx_monitor.json
    """

    def __init__(self, console: Console, sender: MessageSender | None = None) -> None:
        self._console = console
        self._sender = sender or IMessageSender()

    @staticmethod
    def build_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
        """
        Purpose:
            Add every report subcommand listed in the class Purpose.

        Contract:
            Input:
                sub: argparse subparsers of QuantCnCli
            Output:
                None
            Raises:
                (none)
        """
        mr = sub.add_parser("morning-report", help="send the 持仓监测 and 机会清单 e-mails")
        mr.add_argument("--data", type=Path, default=DATA_DIR, help="app data folder")
        mr.add_argument("--dry-run", action="store_true", help="write HTML instead of sending")
        mr.add_argument("--out", type=Path, default=Path("."), help="folder for --dry-run")
        mr.add_argument("--today", default=None, help="YYYYMMDD (default: today)")
        mm = sub.add_parser("macro-monitor", help="write macro_monitor.json (plan 15 ph7h)")
        mm.add_argument("--out", type=Path, default=DATA_DIR, help="app data folder")
        fm = sub.add_parser("futures-monitor", help="write futures_monitor.json (plan 15 ph7i)")
        fm.add_argument("--out", type=Path, default=DATA_DIR, help="app data folder")
        ec = sub.add_parser("etf-cta", help="write etf_cta.json (plan 27)")
        ec.add_argument("--out", type=Path, default=DATA_DIR, help="app data folder")
        bb = sub.add_parser("buyback-events", help="write buybacks.json, buyback_monitor.json")
        bb.add_argument("--out", type=Path, default=DATA_DIR, help="app data folder")
        bb.add_argument("--today", default=None, help="YYYYMMDD (default: today)")
        mp = sub.add_parser("margin-panel", help="write margin/<code>.json (plan 15 ph7m)")
        mp.add_argument("--out", type=Path, default=DATA_DIR, help="app data folder")
        mp.add_argument("--today", default=None, help="YYYYMMDD (default: today)")
        vm = sub.add_parser(
            "volatility-monitor", help="write volatility_monitor.json (plan 03 ph6)"
        )
        vm.add_argument("--out", type=Path, default=DATA_DIR, help="app data folder")
        sw = sub.add_parser("smallcap-watch", help="write smallcap_watch.json (plan 30)")
        sw.add_argument("--out", type=Path, default=DATA_DIR, help="app data folder")
        rf = sub.add_parser("rates-fx-monitor", help="write rates_fx_monitor.json (plan 34)")
        rf.add_argument("--out", type=Path, default=DATA_DIR, help="app data folder")
        nt = sub.add_parser("notify", help="send a phone alert by iMessage (plan 22)")
        nt.add_argument("--text", default=None, help="send this text instead of the alerts")
        nt.add_argument("--to", default=None, help="one recipient by name (default: all)")
        nt.add_argument("--dry-run", action="store_true", help="print instead of sending")
        nt.add_argument("--sample", action="store_true", help="today's full set, not logged")
        nt.add_argument("--data", type=Path, default=DATA_DIR, help="app data folder")
        nt.add_argument("--today", default=None, help="YYYYMMDD for the header")
        nt.add_argument("--node", type=Path, default=None, help="node executable (pictures)")
        nt.add_argument("--shot-script", type=Path, default=None, help="shot_cards.mjs")
        nt.add_argument("--images", type=Path, default=Path("alert_images"), help="PNG folder")
        nt.add_argument("--app-url", default="http://127.0.0.1:8787/", help="running app")

    def _run_notify(self, config: Config, args: argparse.Namespace) -> int:
        settings = NotifySettings.load(config.repo_root)
        people = [settings.find_recipient(args.to)] if args.to else settings.recipients
        if not people:
            self._console.print("notify: no recipients in config/local.notify.yaml")
            return 1
        if args.text:
            return self._run_delivery(people, args.text, [], args.dry_run)
        # last run's pictures: Messages uploads in the background, so a picture is deleted on the
        # next run, never right after sending (deleting at once dropped the picture, 2026-11-13)
        self._remove_images(sorted(args.images.glob("*.png")), args.images)
        data = args.data if args.data.is_absolute() else config.repo_root / args.data
        docs = {n: self._read_doc(data / f"{n}.json") for n in ALERT_DOCS}
        builder = AlertMessageBuilder(settings.triggers, settings.volatility_groups)
        alerts: list[Alert] = builder.list_alerts(docs, full=args.sample)
        log = SentAlertLog(data / SENT_LOG)
        fresh = {a.key for a in alerts} if args.sample else set(log.list_new(a.key for a in alerts))
        new = [a for a in alerts if a.key in fresh]
        if not new:
            self._console.print(f"notify: {len(alerts)} active alerts, none new")
            if not args.dry_run:
                log.write([a.key for a in alerts], [])
            return 0
        today = args.today or dt.date.today().strftime("%Y%m%d")
        text = builder.build_message(new, today, settings.max_items, sample=args.sample)
        # sample: one picture per line, unless pictures are off (max_images 0)
        cap = len(new) if args.sample and settings.max_images else settings.max_images
        shots = [a.shot for a in new[: settings.max_items] if a.shot][:cap]
        images = self._build_images(args, shots)
        code = self._run_delivery(people, text, images, args.dry_run)
        if not args.dry_run and not args.sample:
            log.write([a.key for a in alerts], [a.key for a in new])
        return code

    def _run_delivery(
        self, people: list[NotifyRecipient], text: str, images: list[Path], dry_run: bool
    ) -> int:
        for person in people:
            if dry_run:
                pics = "".join(f"\n[图] {p}" for p in images)
                self._console.print(f"notify (dry run) -> {person.name}:\n{text}{pics}")
                continue
            self._sender.run(person.handle, text, images)
            self._console.print(f"notify: sent to {person.name} ({len(images)} images)")
        return 0

    @staticmethod
    def _build_images(args: argparse.Namespace, shots: list[CardShot]) -> list[Path]:
        if not shots or args.shot_script is None or args.node is None:
            return []
        shooter = CardScreenshotter(args.node, args.shot_script, args.images, args.app_url)
        return shooter.run(shots)

    @staticmethod
    def _remove_images(images: list[Path], folder: Path) -> None:
        """Delete earlier pictures, then the folder when empty (user: clean up after sending)."""
        for image in images:
            image.unlink(missing_ok=True)
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()

    @staticmethod
    def _read_doc(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        doc = json.loads(path.read_text(encoding="utf-8"))
        return doc if isinstance(doc, dict) else None

    def _run_volatility_monitor(self, config: Config, args: argparse.Namespace) -> int:
        out = args.out if args.out.is_absolute() else config.repo_root / args.out
        settings = VolatilityMonitorSettings.load(config.repo_root)
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            path = VolatilityMonitorBuilder(settings, LakeQuery(catalog)).write(out)
        finally:
            catalog.close()
        self._console.print(f"volatility monitor: {len(settings.lines)} lines -> {path}")
        return 0

    def _run_rates_fx_monitor(self, config: Config, args: argparse.Namespace) -> int:
        out = args.out if args.out.is_absolute() else config.repo_root / args.out
        settings = RatesFxMonitorSettings.load(config.repo_root)
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            q = LakeQuery(catalog)
            path = RatesFxMonitorBuilder(settings, RatesFxSeriesReader(settings, q), q).write(out)
        finally:
            catalog.close()
        self._console.print(f"rates-fx monitor: {len(settings.lines)} lines -> {path}")
        return 0

    def _run_smallcap_watch(self, config: Config, args: argparse.Namespace) -> int:
        out = args.out if args.out.is_absolute() else config.repo_root / args.out
        settings = SmallCapWatchSettings.load(config.repo_root)
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            flows, rows = EtfFlowCalculator(config.etf_proxy), SmallCapWatchRows(settings)
            vols = RealizedVolCalculator(settings.pct_window, settings.pct_min_obs)
            path = SmallCapWatchBuilder(settings, LakeQuery(catalog), flows, rows, vols).write(out)
        finally:
            catalog.close()
        self._console.print(f"small-cap watch: {len(settings.levels)} levels -> {path}")
        return 0

    def _run_futures_monitor(self, config: Config, args: argparse.Namespace) -> int:
        out = args.out if args.out.is_absolute() else config.repo_root / args.out
        settings = FuturesMonitorSettings.load(config.repo_root)
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            path = FuturesMonitorBuilder(settings, LakeQuery(catalog)).write(out)
        finally:
            catalog.close()
        self._console.print(f"futures monitor: {len(settings.families)} families -> {path}")
        return 0

    def _run_etf_cta(self, config: Config, args: argparse.Namespace) -> int:
        out = args.out if args.out.is_absolute() else config.repo_root / args.out
        settings = EtfCtaSettings.load(config.repo_root)
        views = EtfCtaViews.load(config.repo_root, settings)
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            book = EtfCtaBook(settings, LakeQuery(catalog), DateCodec(), views=views)
            path = book.write(out)
        finally:
            catalog.close()
        self._console.print(
            f"etf cta: {len(settings.list_codes())} ETFs, {len(views.views)} views -> {path}"
        )
        return 0

    def _run_buyback_events(self, config: Config, args: argparse.Namespace) -> int:
        out = args.out if args.out.is_absolute() else config.repo_root / args.out
        today = args.today or dt.date.today().strftime("%Y%m%d")
        held = [p.code for p in PositionsBook.load(config.repo_root).positions]
        book = sorted(set(held) | {e.code for e in config.watchlist})
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        root = config.lake.root
        try:
            q = LakeQuery(catalog)
            path = BuybackEventsBuilder(q).write(out, today, book)
            labels = LabelStore(ParquetWriter(root), root, DateCodec())
            BuybackMonitorBuilder(q, BuybackLedger(q), labels, BuybackPlanFrame()).write(out, today)
        finally:
            catalog.close()
        self._console.print(f"buyback events: {len(book)} book codes -> {path}; buyback monitor")
        return 0

    def _run_margin_panel(self, config: Config, args: argparse.Namespace) -> int:
        out = args.out if args.out.is_absolute() else config.repo_root / args.out
        today = args.today or dt.date.today().strftime("%Y%m%d")
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            builder = MarginPanelBuilder(LakeQuery(catalog), MarginLadderEstimator())
            n = builder.write(out, today)
        finally:
            catalog.close()
        self._console.print(f"margin panel: {n} stocks -> {out / 'margin'}")
        return 0

    def _run_macro_monitor(self, config: Config, args: argparse.Namespace) -> int:
        out = args.out if args.out.is_absolute() else config.repo_root / args.out
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            path = MacroMonitorBuilder(LakeQuery(catalog)).write(out)
        finally:
            catalog.close()
        self._console.print(f"macro monitor -> {path}")
        return 0

    def _run_morning_report(self, config: Config, args: argparse.Namespace) -> int:
        today = args.today or dt.date.today().strftime("%Y%m%d")
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            last_session = TradingCalendar(LakeQuery(catalog)).get_prev(today)
        finally:
            catalog.close()
        sender = (
            None if args.dry_run else MailSender(MailSettings.load(config.repo_root), os.environ)
        )
        data = args.data if args.data.is_absolute() else config.repo_root / args.data
        sections = [EtfReportSection(), MacroReportSection(), FuturesReportSection(),
                    VolatilityReportSection(), SmallCapReportSection(), RatesFxReportSection(),
                    SectorEarningsReportSection(), BuybackReportSection(),
                    BuybackMarketReportSection(), TaskStatusReportSection()]  # fmt: skip
        builder = MorningReportBuilder(
            data, MonitorReportRenderer(sections), OpportunityReportRenderer(), sender
        )
        out = args.out if args.dry_run else None
        for outcome in builder.run(today, last_session, out):
            self._console.print(f"morning report {outcome.name}: {outcome.action} {outcome.detail}")
        return 0
