"""Command-line entry point and composition root (L6): wires config, lake and pipeline."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from collections.abc import Sequence
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from quant_cn.app_service_builder import AppServiceBuilder
from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError, QuantCnError
from quant_cn.core.positions_book import PositionsBook
from quant_cn.document_commands import DocumentCommands
from quant_cn.gauge_commands import GaugeCommands
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.rebuild_audit import RebuildAudit
from quant_cn.lake.release_lag_checker import ReleaseLagChecker
from quant_cn.lake.run_log import RunLog
from quant_cn.pipeline.curate_pipeline import DIGEST_FILE
from quant_cn.pipeline.runner import PipelineReport
from quant_cn.portfolio.etf_flow_calculator import EtfFlowCalculator
from quant_cn.portfolio.etf_proxy_builder import EtfProxyBuilder
from quant_cn.report_commands import ReportCommands
from quant_cn.risk.factor_monitor_builder import FactorMonitorBuilder
from quant_cn.service_builder import ServiceBuilder
from quant_cn.update_commands import UpdateCommands

MIN_FREE_GB = 20
MIN_CALENDAR_DAYS = 90
DEFAULT_PREFECT_API_URL = "http://127.0.0.1:4200/api"  # D-067


class QuantCnCli:
    """
    Purpose:
        `python -m quant_cn.cli <command>`: doctor, download, compact, curate, rebuild, backup,
        project-catalog, query.
        Builds every service from Config (the only place objects are wired) and prints summaries.

    Contract:
        Input:
            config:  Config | None   -- default Config.load()
            console: Console | None  -- default stdout console
        Output:
            instance; `main(argv) -> int` exit code (0 ok, 1 project error, 2 usage error)
        Raises:
            (none; project errors become exit code 1)

    Used by:
        Makefile targets doctor, download, compact, lake-rebuild, lake-backup

    Test cases:
        TC-QCC-001  doctor reports lake root and token presence without printing the token
        TC-QCC-002  download --dry-run on an empty lake exits 0 and lists datasets
        TC-QCC-003  curate on a mini lake exits 0 and reports derived digests unchanged on rerun
        TC-QCC-004  query runs read-only SQL and prints rows; a write statement fails with exit 1
        TC-QCC-005  doctor reports the trade_cal horizon and warns under 90 days
        TC-QCC-006  doctor warns (exit code unchanged) when the Prefect API is unreachable
        TC-QCC-007  rebuild removes fetch-log orphans and writes fetch_log_orphans.json
    """

    def __init__(self, config: Config | None = None, console: Console | None = None) -> None:
        self._config = config
        self._console = console or Console()

    def run(self, argv: Sequence[str] | None = None) -> int:
        """
        Purpose:
            Parse arguments and dispatch to a command.

        Contract:
            Input:
                argv: Sequence[str] | None  -- default sys.argv[1:]
            Output:
                int  -- exit code
            Raises:
                SystemExit  -- from argparse on usage errors (code 2)
        """
        args = self._build_parser().parse_args(argv)
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format="%(message)s",
            handlers=[RichHandler(console=Console(stderr=True), show_path=False)],
        )
        try:
            config = self._config or Config.load()
            method = f"_run_{args.command.replace('-', '_')}"
            groups = (ResearchCommands, ReportCommands, GaugeCommands, UpdateCommands)
            handler = getattr(self, method, None) or next(
                (h for g in groups if (h := getattr(g(self._console), method, None))), None
            )
            handler = handler or getattr(DocumentCommands(self._console), method)
            return int(handler(config, args))
        except QuantCnError as exc:
            self._console.print(f"[red]error:[/red] {exc}")
            return 1

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="quant_cn")
        parser.add_argument("-v", "--verbose", action="store_true")
        sub = parser.add_subparsers(dest="command", required=True)
        sub.add_parser("doctor", help="check lake root, free space and token")
        dl = sub.add_parser("download", help="download datasets into the lake")
        dl.add_argument("--datasets", help="comma-separated subset (default: download.order)")
        dl.add_argument("--start", help="YYYYMMDD, overrides every dataset's start")
        dl.add_argument("--end", help="YYYYMMDD, default today")
        dl.add_argument("--dry-run", action="store_true")
        dl.add_argument("--force", action="store_true", help="refetch keys already done")
        dl.add_argument("--no-progress", action="store_true")
        dl.add_argument("--runner", choices=["local", "prefect"], default="local")
        cp = sub.add_parser("compact", help="rebuild curated partitions from raw")
        cp.add_argument("--datasets", help="comma-separated subset (default: all)")
        cu = sub.add_parser("curate", help="compact, build derived views and PIT states, digests")
        cu.add_argument("--datasets", help="comma-separated subset to compact (default: all)")
        cu.add_argument("--no-progress", action="store_true")
        cu.add_argument("--runner", choices=["local", "prefect"], default="local")
        sub.add_parser("rebuild", help="recreate the DuckDB catalog and fetch log from parquet")
        sub.add_parser("backup", help="rsync raw/, documents/ and the fetch log to backup_target")
        pc = sub.add_parser("project-catalog", help="rebuild schema project from repo + markdown")
        pc.add_argument("--no-lint", action="store_true", help="skip lint_findings")
        qy = sub.add_parser("query", help="run read-only SQL against the lake catalog")
        qy.add_argument("sql", help='SQL, e.g. "SELECT * FROM project.todo"')
        qy.add_argument("--limit", type=int, default=50)
        ResearchCommands.build_parser(sub)
        DocumentCommands.build_parser(sub)
        GaugeCommands.build_parser(sub)
        UpdateCommands.build_parser(sub)
        ReportCommands.build_parser(sub)
        return parser

    def _run_doctor(self, config: Config, _args: argparse.Namespace) -> int:
        root = config.lake.root
        exists = root.exists()
        free_gb = shutil.disk_usage(root if exists else root.parent).free / 1e9
        rows = [
            ("lake root", str(root)),
            ("exists / writable", f"{exists} / {exists and self._is_writable(root)}"),
            ("free space", f"{free_gb:.0f} GB" + ("" if free_gb >= MIN_FREE_GB else "  (low)")),
            ("inside a git tree", str(self._is_in_git(root))),
            ("TUSHARE_TOKEN", "set" if config.tushare.token else "MISSING"),
            ("backup target", str(config.lake.backup_target or "not set")),
            ("calendar horizon", self._get_calendar_horizon(config)),
            ("prefect server", self._get_prefect_status()),
        ]
        table = Table("check", "value", title="quant_cn doctor")
        for row in rows:
            table.add_row(*row)
        self._console.print(table)
        ok = exists and bool(config.tushare.token) and not self._is_in_git(root)
        return 0 if ok else 1

    @staticmethod
    def _get_calendar_horizon(config: Config) -> str:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            if not catalog.catalog_path.exists():
                return "no catalog yet"
            last = (
                LakeQuery(catalog)
                .sql("SELECT max(cal_date) AS d FROM curated.trade_cal")["d"]
                .iloc[0]
            )
        except LakeError as exc:
            return f"unknown ({str(exc)[:40]})"
        finally:
            catalog.close()
        if not isinstance(last, str):
            return "trade_cal not curated"
        days = (DateCodec().to_date(last) - Clock().get_now().date()).days
        warn = "" if days >= MIN_CALENDAR_DAYS else "  (low: refresh trade_cal)"
        return f"{last} ({days} days ahead){warn}"

    @staticmethod
    def _get_prefect_status() -> str:
        url = os.environ.get("PREFECT_API_URL") or DEFAULT_PREFECT_API_URL
        try:
            with urllib.request.urlopen(f"{url.rstrip('/')}/health", timeout=2):
                return f"{url} reachable"
        except (OSError, ValueError):
            return f"{url} unreachable  (RUNNER=prefect needs: make prefect-server)"

    def _run_download(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            pipeline = ServiceBuilder().build_download_pipeline(
                config, catalog, show_progress=not args.no_progress, runner=args.runner
            )
            report = pipeline.run(
                datasets=self._parse_list(args.datasets),
                start=args.start,
                end=args.end,
                dry_run=args.dry_run,
                force=args.force,
            )
        finally:
            catalog.close()
        self._render_report(report)
        return 0

    def _run_compact(self, config: Config, args: argparse.Namespace) -> int:
        clock = Clock()
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            query = LakeQuery(catalog)
            compactor = Compactor(catalog, query, ParquetWriter(config.lake.root), clock)
            names = self._parse_list(args.datasets) or list(config.datasets)
            report = PipelineReport(run_id="compact", status="ok")
            report.steps = [compactor.rebuild(config.get_dataset(n)) for n in names]
            catalog.write_indexes()
        finally:
            catalog.close()
        self._render_report(report)
        return 0

    def _run_curate(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        digest_path = config.lake.root / "meta" / "manifest" / DIGEST_FILE
        before = self._read_digests(digest_path)
        try:
            pipeline = ServiceBuilder().build_curate_pipeline(
                config, catalog, not args.no_progress, args.runner
            )
            report = pipeline.run(self._parse_list(args.datasets))
        finally:
            catalog.close()
        self._render_report(report)
        after = self._read_digests(digest_path)
        for view, digest in sorted(after.items()):
            state = (
                "new"
                if view not in before
                else "unchanged"
                if before[view] == digest
                else "CHANGED"
            )
            self._console.print(f"{view}: {digest} ({state})")
        return 0

    @staticmethod
    def _read_digests(path: Path) -> dict[str, str]:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in data.items()}

    def _run_project_catalog(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            project = ServiceBuilder().build_project_catalog(config, catalog)
            counts = project.rebuild(run_lint=not args.no_lint)
            stale = LakeQuery(catalog).sql("SELECT count(*) AS n FROM project.stale")["n"].iloc[0]
        finally:
            catalog.close()
        self._console.print(", ".join(f"{k} {v}" for k, v in counts.items()))
        self._console.print(f"project.stale: {stale} row(s)")
        return 0 if stale == 0 else 1

    def _run_query(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            frame = LakeQuery(catalog).sql(args.sql)
        finally:
            catalog.close()
        table = Table(*[str(c) for c in frame.columns], title=f"{len(frame)} row(s)")
        for row in frame.head(args.limit).itertuples(index=False):
            table.add_row(*(str(v) for v in row))
        self._console.print(table)
        return 0

    def _run_rebuild(self, config: Config, _args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            catalog.rebuild()
            fetch_log = FetchLog(catalog)
            restored = fetch_log.rebuild_from_mirror()
            orphans = fetch_log.remove_orphans()
            audit = RebuildAudit(config.lake.root, Clock())
            audit.record_orphans(orphans)
            rewrites = audit.record_rewrites()
            RunLog(catalog, Clock())
            catalog.write_indexes()
        finally:
            catalog.close()
        removed = sum(len(keys) for keys in orphans.values())
        self._console.print(
            f"catalog rebuilt at {catalog.catalog_path}; fetch_log rows: {restored - removed}"
            f" ({removed} orphan rows removed; {len(rewrites)} rewritten raw files confirmed)"
        )
        return 0

    def _run_backup(self, config: Config, _args: argparse.Namespace) -> int:
        target = config.lake.backup_target
        if target is None:
            raise LakeError("lake.backup_target is not set in config/local.yaml")
        root = config.lake.root
        sources = [
            str(root / "raw"),
            str(root / "documents"),
            str(root / "meta" / "fetch_log.parquet"),
        ]
        cmd = ["rsync", "-a", "--delete", *sources, f"{target}/"]
        self._console.print(" ".join(cmd))
        return subprocess.run(cmd, check=False).returncode

    def _render_report(self, report: PipelineReport) -> None:
        frame = report.to_frame()
        table = Table(*frame.columns, title=f"run {report.run_id}: {report.status}")
        for row in frame.itertuples(index=False):
            table.add_row(*(str(v) for v in row))
        self._console.print(table)
        if report.list_blocked():
            self._console.print(f"[yellow]blocked (permissions):[/yellow] {report.list_blocked()}")

    @staticmethod
    def _parse_list(value: str | None) -> list[str] | None:
        return [v.strip() for v in value.split(",") if v.strip()] if value else None

    @staticmethod
    def _is_writable(path: Path) -> bool:
        probe = path / ".doctor_probe"
        try:
            probe.write_text("ok")
            probe.unlink()
        except OSError:
            return False
        return True

    @staticmethod
    def _is_in_git(path: Path) -> bool:
        return any((p / ".git").exists() for p in (path, *path.parents))


class ResearchCommands:
    """
    Purpose:
        The research-side CLI commands, kept apart so QuantCnCli stays within its size limit:
        `release-lags` (D-086), `evaluate` (factor campaign reports and trial log, plan 04
        phase 5), `risk-model` (plan 05, D-127), `watchlist` (the app's 观察账本 data,
        D-120), `etf-proxy` (the 国家队 ETF panel, D-126), `factor-monitor` and `holdings-risk` (the
        因子监控 and 持仓 pages, D-132), `sector-monitor` (the 行业监控 page, plan 31). QuantCnCli
        parses the arguments and dispatches here.

    Contract:
        Input:
            console: Console
        Output:
            instance; `build_parser`, `_run_release_lags`, `_run_evaluate`, `_run_risk_model`,
            `_run_watchlist`, `_run_etf_proxy`, `_run_factor_monitor`, `_run_holdings_risk`,
            `_run_sector_monitor`, `_run_sector_earnings_signal` (dispatched by QuantCnCli.run)
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- dispatch fallback

    Test cases:
        TC-QCC-008  release-lags prints one line per checked dataset and exits 0 on warnings
        TC-QCC-009  evaluate without features exits 0 and writes nothing
        TC-QCC-011  watchlist without entries writes an empty watchlist.json and exits 0
        TC-QCC-012  etf-proxy without configured indices writes an empty etf_proxy.json, exits 0
        TC-QCC-013  factor-monitor without risk-model frames: the LakeError is printed, exit 1
        TC-QCC-014  holdings-risk with an empty book writes an empty holdings_risk.json, exits 0
        TC-QCC-017  sector-monitor writes sector_monitor.json and exits 0 on an empty lake
        TC-QCC-018  sector-earnings-signal writes sector_earnings_signal.json (empty lake: no
                    rows) and exits 0
    """

    def __init__(self, console: Console) -> None:
        self._console = console

    @staticmethod
    def build_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
        """
        Purpose:
            Add the `release-lags`, `watchlist`, `etf-proxy`, `factor-monitor`, `holdings-risk`,
            `sector-monitor`, `sector-earnings-signal`, `evaluate` and `risk-model` subcommands.

        Contract:
            Input:
                sub: argparse subparsers of QuantCnCli
            Output:
                None
            Raises:
                (none)
        """
        sub.add_parser("release-lags", help="warn when a release-lag rule is earlier than observed")
        wl = sub.add_parser("watchlist", help="write watchlist.json for the chain app (D-120)")
        wl.add_argument("--out", type=Path, required=True, help="the app's data directory")
        ep = sub.add_parser("etf-proxy", help="write etf_proxy.json for the chain app (D-126)")
        ep.add_argument("--out", type=Path, required=True, help="the app's data directory")
        fm = sub.add_parser("factor-monitor", help="write factor_monitor.json (D-132)")
        fm.add_argument("--out", type=Path, required=True, help="the app's data directory")
        fm.add_argument("--days", type=int, default=504, help="sessions kept in the daily series")
        hr = sub.add_parser("holdings-risk", help="write holdings_risk.json + lake history (D-132)")
        hr.add_argument("--out", type=Path, required=True, help="the app's data directory")
        hr.add_argument("--date", default="99991231", help="YYYYMMDD; default the last session")
        hr.add_argument("--benchmark", default="000300.SH", help="index_code for active risk")
        ev = sub.add_parser(
            "evaluate", help="evaluate the factor campaign; write reports and trials"
        )
        ev.add_argument("--no-progress", action="store_true")
        sm = sub.add_parser("sector-monitor", help="write sector_monitor.json (plan 31)")
        sm.add_argument("--out", type=Path, required=True, help="the app's data directory")
        se = sub.add_parser("sector-earnings-signal", help="write sector_earnings_signal.json")
        se.add_argument("--out", type=Path, required=True, help="the app's data directory")
        se.add_argument("--date", default=None, help="YYYYMMDD as of (default: today)")
        rm = sub.add_parser("risk-model", help="fit the risk model (config/risk_model.yaml)")
        rm.add_argument("--no-progress", action="store_true")

    def _run_release_lags(self, config: Config, _args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            frame = ReleaseLagChecker(LakeQuery(catalog), config.datasets).compute()
        finally:
            catalog.close()
        self._console.print("\n".join(ReleaseLagChecker.build_lines(frame)))
        return 0  # a warning, not a failure (D-086)

    def _run_risk_model(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            step = ServiceBuilder().build_risk_model(config, catalog)
            runner = ServiceBuilder().build_runner(
                RunLog(catalog, Clock()), "local", not args.no_progress
            )
            report = runner.run("risk-model", [step])
        finally:
            catalog.close()
        self._console.print(f"run {report.run_id}: {report.status}")
        for step_report in report.steps:
            self._console.print(
                f"{step_report.name}: {step_report.fetched} years, {step_report.rows} rows"
            )
        return 0

    def _run_watchlist(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            path = AppServiceBuilder().build_watchlist(config, catalog).write(args.out)
        finally:
            catalog.close()
        self._console.print(f"watchlist: {len(config.watchlist)} entries -> {path}")
        return 0

    def _run_sector_monitor(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            path = AppServiceBuilder().build_sector_monitor(config, catalog).write(args.out)
        finally:
            catalog.close()
        self._console.print(f"sector monitor -> {path}")
        return 0

    def _run_sector_earnings_signal(self, config: Config, args: argparse.Namespace) -> int:
        as_of = args.date or dt.date.today().strftime("%Y%m%d")
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            builder = AppServiceBuilder().build_sector_earnings_signal(config, catalog)
            path = builder.write(args.out, as_of)
        finally:
            catalog.close()
        self._console.print(f"sector earnings signal -> {path}")
        return 0

    def _run_factor_monitor(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:  # a LakeError (no risk model yet) reaches QuantCnCli.run: printed, exit 1
            builder = FactorMonitorBuilder(LakeQuery(catalog), config.risk_model.name, args.days)
            path = builder.write(args.out)
        finally:
            catalog.close()
        self._console.print(f"factor monitor: {config.risk_model.name} -> {path}")
        return 0

    def _run_holdings_risk(self, config: Config, args: argparse.Namespace) -> int:
        book = PositionsBook.load(config.repo_root)
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            builder = AppServiceBuilder().build_holdings_risk(config, catalog, book, args.benchmark)
            path = builder.write(args.out, args.date)
            DerivedViews(catalog, LakeQuery(catalog), config.datasets).refresh_tables()
        finally:
            catalog.close()
        self._console.print(f"holdings risk: {len(book.positions)} positions -> {path}")
        return 0

    def _run_etf_proxy(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            calculator = EtfFlowCalculator(config.etf_proxy)
            builder = EtfProxyBuilder(config, LakeQuery(catalog), DateCodec(), calculator)
            path = builder.write(args.out)
        finally:
            catalog.close()
        self._console.print(f"etf proxy: {len(config.etf_proxy.indices)} indices -> {path}")
        return 0

    def _run_evaluate(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            step = ServiceBuilder().build_evaluation(config, catalog)
            runner = ServiceBuilder().build_runner(
                RunLog(catalog, Clock()), "local", not args.no_progress
            )
            report = runner.run("evaluate", [step])
        finally:
            catalog.close()
        self._console.print(f"run {report.run_id}: {report.status}")
        for step_report in report.steps:
            self._console.print(
                f"{step_report.name}: {step_report.fetched} factors, {step_report.rows} test rows"
            )
        return 0


if __name__ == "__main__":
    sys.exit(QuantCnCli().run())
