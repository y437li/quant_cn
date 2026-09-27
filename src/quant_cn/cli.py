"""Command-line entry point and composition root (L6): wires config, lake and pipeline."""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError, QuantCnError
from quant_cn.data_loading.fetcher_factory import FetcherFactory
from quant_cn.data_loading.tushare_client import TushareClient
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.run_log import RunLog
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.pipeline.download_pipeline import DownloadPipeline
from quant_cn.pipeline.runner import LocalRunner, PipelineReport

MIN_FREE_GB = 20


class QuantCnCli:
    """
    Purpose:
        `python -m quant_cn.cli <command>`: doctor, download, compact, rebuild, backup. Builds every
        service from Config (the only place objects are wired together) and prints summaries.

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
    """

    def __init__(self, config: Config | None = None, console: Console | None = None) -> None:
        self._config = config
        self._console = console or Console()

    def main(self, argv: Sequence[str] | None = None) -> int:
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
        args = self._parser().parse_args(argv)
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format="%(message)s",
            handlers=[RichHandler(console=Console(stderr=True), show_path=False)],
        )
        try:
            config = self._config or Config.load()
            handler = getattr(self, f"_cmd_{args.command}")
            return int(handler(config, args))
        except QuantCnError as exc:
            self._console.print(f"[red]error:[/red] {exc}")
            return 1

    def _parser(self) -> argparse.ArgumentParser:
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
        cp = sub.add_parser("compact", help="rebuild curated partitions from raw")
        cp.add_argument("--datasets", help="comma-separated subset (default: all)")
        sub.add_parser("rebuild", help="recreate the DuckDB catalog and fetch log from parquet")
        sub.add_parser("backup", help="rsync raw/ and the fetch log to lake.backup_target")
        return parser

    def _cmd_doctor(self, config: Config, _args: argparse.Namespace) -> int:
        root = config.lake.root
        exists = root.exists()
        free_gb = shutil.disk_usage(root if exists else root.parent).free / 1e9
        rows = [
            ("lake root", str(root)),
            ("exists / writable", f"{exists} / {exists and self._writable(root)}"),
            ("free space", f"{free_gb:.0f} GB" + ("" if free_gb >= MIN_FREE_GB else "  (low)")),
            ("inside a git tree", str(self._in_git(root))),
            ("TUSHARE_TOKEN", "set" if config.tushare.token else "MISSING"),
            ("backup target", str(config.lake.backup_target or "not set")),
        ]
        table = Table("check", "value", title="quant_cn doctor")
        for row in rows:
            table.add_row(*row)
        self._console.print(table)
        ok = exists and bool(config.tushare.token) and not self._in_git(root)
        return 0 if ok else 1

    def _cmd_download(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            pipeline = self._download_pipeline(config, catalog, show_progress=not args.no_progress)
            report = pipeline.run(
                datasets=self._split(args.datasets),
                start=args.start,
                end=args.end,
                dry_run=args.dry_run,
                force=args.force,
            )
        finally:
            catalog.close()
        self._print_report(report)
        return 0

    def _cmd_compact(self, config: Config, args: argparse.Namespace) -> int:
        clock = Clock()
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            query = LakeQuery(catalog)
            compactor = Compactor(catalog, query, ParquetWriter(config.lake.root), clock)
            names = self._split(args.datasets) or list(config.datasets)
            report = PipelineReport(run_id="compact", status="ok")
            report.steps = [compactor.compact(config.dataset(n)) for n in names]
            catalog.write_indexes()
        finally:
            catalog.close()
        self._print_report(report)
        return 0

    def _cmd_rebuild(self, config: Config, _args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            catalog.rebuild()
            restored = FetchLog(catalog).restore()
            RunLog(catalog, Clock())
            catalog.write_indexes()
        finally:
            catalog.close()
        self._console.print(f"catalog rebuilt at {catalog.db_path}; fetch_log rows: {restored}")
        return 0

    def _cmd_backup(self, config: Config, _args: argparse.Namespace) -> int:
        target = config.lake.backup_target
        if target is None:
            raise LakeError("lake.backup_target is not set in config/local.yaml")
        root = config.lake.root
        sources = [str(root / "raw"), str(root / "meta" / "fetch_log.parquet")]
        cmd = ["rsync", "-a", "--delete", *sources, f"{target}/"]
        self._console.print(" ".join(cmd))
        return subprocess.run(cmd, check=False).returncode

    def _download_pipeline(
        self, config: Config, catalog: LakeCatalog, show_progress: bool
    ) -> DownloadPipeline:
        clock, codec = Clock(), DateCodec()
        writer = ParquetWriter(config.lake.root)
        fetch_log = FetchLog(catalog)
        run_log = RunLog(catalog, clock)
        calendar = TradingCalendar(LakeQuery(catalog))
        client = TushareClient(config.tushare, clock)
        factory = FetcherFactory(config, client, writer, fetch_log, run_log, clock, calendar, codec)
        runner = LocalRunner(run_log, show_progress=show_progress)
        return DownloadPipeline(config, factory, runner, catalog, fetch_log, clock, codec)

    def _print_report(self, report: PipelineReport) -> None:
        frame = report.to_frame()
        table = Table(*frame.columns, title=f"run {report.run_id}: {report.status}")
        for row in frame.itertuples(index=False):
            table.add_row(*(str(v) for v in row))
        self._console.print(table)
        if report.blocked():
            self._console.print(f"[yellow]blocked (permissions):[/yellow] {report.blocked()}")

    @staticmethod
    def _split(value: str | None) -> list[str] | None:
        return [v.strip() for v in value.split(",") if v.strip()] if value else None

    @staticmethod
    def _writable(path: Path) -> bool:
        probe = path / ".doctor_probe"
        try:
            probe.write_text("ok")
            probe.unlink()
        except OSError:
            return False
        return True

    @staticmethod
    def _in_git(path: Path) -> bool:
        return any((p / ".git").exists() for p in (path, *path.parents))


if __name__ == "__main__":
    sys.exit(QuantCnCli().main())
