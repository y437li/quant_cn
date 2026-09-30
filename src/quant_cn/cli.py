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

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.code_table_builder import CodeTableBuilder
from quant_cn.core.docs.contract_linter import ContractLinter
from quant_cn.core.docs.decisions_reader import DecisionsReader
from quant_cn.core.docs.doc_table_builder import DocTableBuilder
from quant_cn.core.docs.docstring_parser import DocstringParser
from quant_cn.core.docs.index_reader import IndexReader
from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.plan_reader import PlanReader
from quant_cn.core.docs.registry_reader import RegistryReader
from quant_cn.core.docs.repo_files import RepoFiles
from quant_cn.core.exceptions import LakeError, QuantCnError
from quant_cn.data_loading.akshare_client import AkshareClient
from quant_cn.data_loading.baostock_client import BaostockClient
from quant_cn.data_loading.fetcher_factory import FetcherFactory
from quant_cn.data_loading.tushare_client import TushareClient
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.panel_cache import PanelCache
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.lake.project_catalog import ProjectCatalog
from quant_cn.lake.rebuild_audit import RebuildAudit
from quant_cn.lake.release_lag_checker import ReleaseLagChecker
from quant_cn.lake.run_log import RunLog
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.pipeline.curate_pipeline import DIGEST_FILE, CuratePipeline
from quant_cn.pipeline.download_pipeline import DownloadPipeline
from quant_cn.pipeline.runner import BaseRunner, LocalRunner, PipelineReport
from quant_cn.pipeline.universe_step import UniverseStep

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
        TC-QCC-008  release-lags prints one line per checked dataset and exits 0 on warnings
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
            handler = getattr(self, f"_run_{args.command.replace('-', '_')}")
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
        sub.add_parser("backup", help="rsync raw/ and the fetch log to lake.backup_target")
        pc = sub.add_parser("project-catalog", help="rebuild schema project from repo + markdown")
        pc.add_argument("--no-lint", action="store_true", help="skip lint_findings")
        qy = sub.add_parser("query", help="run read-only SQL against the lake catalog")
        qy.add_argument("sql", help='SQL, e.g. "SELECT * FROM project.todo"')
        qy.add_argument("--limit", type=int, default=50)
        sub.add_parser("release-lags", help="warn when a release-lag rule is earlier than observed")
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

    def _run_release_lags(self, config: Config, _args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            frame = ReleaseLagChecker(LakeQuery(catalog), config.datasets).compute()
        finally:
            catalog.close()
        self._console.print("\n".join(ReleaseLagChecker.build_lines(frame)))
        return 0  # a warning, not a failure (D-086)

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
        sources = [str(root / "raw"), str(root / "meta" / "fetch_log.parquet")]
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


class ServiceBuilder:
    """
    Purpose:
        Wire services for the CLI commands (the composition root's constructors): download and
        curate pipelines with the chosen runner, and the project catalog.

    Contract:
        Input:
            (none)
        Output:
            instance; `build_download_pipeline`, `build_curate_pipeline`, `build_runner`,
            `build_project_catalog`
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- download, curate, project-catalog commands

    Test cases:
        TC-QCC-002  download --dry-run on an empty lake exits 0 and lists datasets
        TC-QCC-003  curate on a mini lake exits 0 and reports derived digests unchanged on rerun
    """

    def build_download_pipeline(
        self, config: Config, catalog: LakeCatalog, show_progress: bool, runner: str = "local"
    ) -> DownloadPipeline:
        """
        Purpose:
            DownloadPipeline wired to the lake, Tushare client and chosen runner.

        Contract:
            Input:
                config, catalog; show_progress: bool; runner: "local" | "prefect"
            Output:
                DownloadPipeline
            Raises:
                (none)
        """
        clock, codec = Clock(), DateCodec()
        writer = ParquetWriter(config.lake.root)
        fetch_log = FetchLog(catalog)
        run_log = RunLog(catalog, clock)
        calendar = TradingCalendar(LakeQuery(catalog))
        client = TushareClient(config.tushare, clock)
        factory = FetcherFactory(
            config,
            client,
            writer,
            fetch_log,
            run_log,
            clock,
            calendar,
            codec,
            extra_clients={"akshare": AkshareClient(clock), "baostock": BaostockClient(clock)},
            query=LakeQuery(catalog),
        )
        executor = self.build_runner(run_log, runner, show_progress)
        return DownloadPipeline(config, factory, executor, catalog, fetch_log, clock, codec)

    def build_curate_pipeline(
        self, config: Config, catalog: LakeCatalog, show_progress: bool, runner_name: str = "local"
    ) -> CuratePipeline:
        """
        Purpose:
            CuratePipeline wired to compactor, derived views, PIT aligner and chosen runner.

        Contract:
            Input:
                config, catalog; show_progress: bool; runner_name: "local" | "prefect"
            Output:
                CuratePipeline
            Raises:
                (none)
        """
        clock, query = Clock(), LakeQuery(catalog)
        compactor = Compactor(catalog, query, ParquetWriter(config.lake.root), clock)
        views = DerivedViews(
            catalog, query, config.datasets, config.futures_categories, config.ticker_aliases
        )
        aligner = PitAligner(catalog, query, DateCodec())
        runner = self.build_runner(RunLog(catalog, clock), runner_name, show_progress)
        universe = UniverseStep(query, ParquetWriter(config.lake.root), config.universe)
        return CuratePipeline(config, compactor, views, aligner, query, catalog, runner, universe)

    def build_runner(self, run_log: RunLog, name: str, show_progress: bool) -> BaseRunner:
        """
        Purpose:
            LocalRunner, or PrefectRunner for name "prefect" (optional extra "flows", D-022).

        Contract:
            Input:
                run_log: RunLog; name: "local" | "prefect"; show_progress: bool
            Output:
                BaseRunner
            Raises:
                ModuleNotFoundError  -- prefect requested but the "flows" extra is not installed
        """
        if name == "prefect":
            from quant_cn.pipeline import prefect_runner  # noqa: PLC0415 -- optional extra (D-022)

            return prefect_runner.PrefectRunner(run_log)
        return LocalRunner(run_log, show_progress=show_progress)

    def build_reader(self, config: Config, catalog: LakeCatalog, cache: bool = False) -> LakeReader:
        """
        Purpose:
            The lake read API (D-089): PIT aligner, alias map, calendar and an optional cache.

        Contract:
            Input:
                config: Config; catalog: LakeCatalog (read-only is fine)
                cache:  bool  -- True in notebooks (PanelCache), False in pipelines
            Output:
                LakeReader
            Raises:
                (none)
        """
        query = LakeQuery(catalog)
        return LakeReader(
            catalog,
            query,
            config.datasets,
            PitAligner(catalog, query, DateCodec()),
            TickerAliasMap(catalog, query, config.ticker_aliases),
            TradingCalendar(query),
            PanelCache() if cache else None,
        )

    def build_project_catalog(self, config: Config, catalog: LakeCatalog) -> ProjectCatalog:
        """
        Purpose:
            ProjectCatalog over the repository with the contract linter.

        Contract:
            Input:
                config, catalog
            Output:
                ProjectCatalog
            Raises:
                (none)
        """
        root = config.repo_root
        tables, scanner = MarkdownTableReader(), CodeScanner()
        code = CodeTableBuilder(root, scanner, DocstringParser(), RegistryReader(tables))
        files = RepoFiles(root)
        docs = DocTableBuilder(
            root, files, IndexReader(tables), DecisionsReader(tables), PlanReader(tables)
        )
        return ProjectCatalog(catalog, code, docs, config.datasets, ContractLinter(root), Clock())


if __name__ == "__main__":
    sys.exit(QuantCnCli().run())
