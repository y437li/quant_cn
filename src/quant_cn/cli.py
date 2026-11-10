"""Command-line entry point and composition root (L6): wires config, lake and pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from collections.abc import Sequence
from pathlib import Path

import duckdb
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError, QuantCnError
from quant_cn.data_loading.document_downloader import DocumentDownloader
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.document_views import DocumentViews
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.rebuild_audit import RebuildAudit
from quant_cn.lake.release_lag_checker import ReleaseLagChecker
from quant_cn.lake.run_log import RunLog
from quant_cn.pipeline.curate_pipeline import DIGEST_FILE
from quant_cn.pipeline.runner import PipelineReport
from quant_cn.portfolio.watchlist_builder import WatchlistBuilder
from quant_cn.service_builder import ServiceBuilder

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
        cli.DocumentCommands            -- parser and dispatch

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
            handler = (
                getattr(self, method, None)
                or getattr(ResearchCommands(self._console), method, None)
                or getattr(DocumentCommands(self._console), method)
            )
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
        phase 5) and `watchlist` (the app's 观察账本 data, D-120). QuantCnCli parses the
        arguments and dispatches here.

    Contract:
        Input:
            console: Console
        Output:
            instance; `build_parser`, `_run_release_lags`, `_run_evaluate`, `_run_watchlist`
            (dispatched by QuantCnCli.run)
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- dispatch fallback

    Test cases:
        TC-QCC-008  release-lags prints one line per checked dataset and exits 0 on warnings
        TC-QCC-009  evaluate without features exits 0 and writes nothing
        TC-QCC-011  watchlist without entries writes an empty watchlist.json and exits 0
    """

    def __init__(self, console: Console) -> None:
        self._console = console

    @staticmethod
    def build_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
        """
        Purpose:
            Add the `release-lags`, `watchlist` and `evaluate` subcommands to the CLI parser.

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
        ev = sub.add_parser(
            "evaluate", help="evaluate the factor campaign; write reports and trials"
        )
        ev.add_argument("--no-progress", action="store_true")

    def _run_release_lags(self, config: Config, _args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            frame = ReleaseLagChecker(LakeQuery(catalog), config.datasets).compute()
        finally:
            catalog.close()
        self._console.print("\n".join(ReleaseLagChecker.build_lines(frame)))
        return 0  # a warning, not a failure (D-086)

    def _run_watchlist(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            path = WatchlistBuilder(config, LakeQuery(catalog), DateCodec()).write(args.out)
        finally:
            catalog.close()
        self._console.print(f"watchlist: {len(config.watchlist)} entries -> {path}")
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


class DocumentCommands:
    """
    Purpose:
        The document-side CLI command `download-docs` (plan 12 phase 2, D-101): for each source,
        list the PDFs not yet in the manifest (counts per doc type), release the catalog, then
        download them (unless `--dry-run`) and refresh `meta.documents`.

    Contract:
        Input:
            console: Console
        Output:
            instance; `build_parser`, `_run_download_docs` (dispatched by QuantCnCli.run)
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- dispatch fallback

    Test cases:
        TC-QCC-010  download-docs --dry-run prints counts per type to download and exits 0
    """

    def __init__(self, console: Console) -> None:
        self._console = console

    @staticmethod
    def build_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
        """
        Purpose:
            Add the `download-docs` subcommand and its options to the CLI parser.

        Contract:
            Input:
                sub: argparse subparsers of QuantCnCli
            Output:
                None
            Raises:
                (none)
        """
        dd = sub.add_parser("download-docs", help="download listed PDFs into documents/ (D-101)")
        dd.add_argument(
            "--sources", required=True, help="comma-separated config/documents.yaml keys"
        )
        dd.add_argument("--types", help="comma-separated doc types (default: all of the source)")
        dd.add_argument("--start", help="publication date from, YYYYMMDD")
        dd.add_argument("--end", help="publication date to, YYYYMMDD")
        dd.add_argument("--limit", type=int, help="at most this many downloads per source")
        dd.add_argument(
            "--workers", type=int, help="override the source's workers in documents.yaml"
        )
        dd.add_argument("--dry-run", action="store_true", help="count candidates per type only")

    def _run_download_docs(self, config: Config, args: argparse.Namespace) -> int:
        types = QuantCnCli._parse_list(args.types)
        sources = QuantCnCli._parse_list(args.sources) or []
        catalog = LakeCatalog(config.lake.root, config.datasets)
        downloader = DocumentDownloader(
            config.lake.root,
            LakeQuery(catalog),
            config.documents,
            Clock(),
            workers_override=args.workers,
        )
        try:
            todo = {s: downloader.list_todo(s, types, args.start, args.end) for s in sources}
        finally:
            catalog.close()  # downloads need no catalog: a metadata sweep may run meanwhile
        for source, frame in todo.items():
            counts = frame["doc_type"].value_counts().sort_index()
            self._console.print(f"{source}: {len(frame)} to download")
            for doc_type, n in counts.items():
                self._console.print(f"  {doc_type}: {n}")
            if not args.dry_run:
                report = downloader.run(frame, args.limit)
                self._console.print(f"{report.name}: {report.message}, {report.rows / 1e6:.1f} MB")
        if not args.dry_run:
            self._refresh_views(config)
        return 0

    def _refresh_views(self, config: Config) -> None:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            DocumentViews(config.lake.root, catalog.connection).refresh()
        except (LakeError, duckdb.Error) as exc:  # catalog busy: views refresh on the next run
            self._console.print(f"[yellow]meta.documents not refreshed:[/yellow] {exc}")
        finally:
            catalog.close()


if __name__ == "__main__":
    sys.exit(QuantCnCli().run())
