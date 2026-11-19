"""`update-all`: every daily update in order with a task ledger (plan 38, D-181)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.core.exceptions import ConfigError, LakeError
from quant_cn.core.update_all_settings import UpdateAllSettings, UpdateStep
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.task_log import TaskLog
from quant_cn.pipeline.make_target_runner import MakeTargetRunner
from quant_cn.pipeline.task_status_builder import TaskStatusBuilder
from quant_cn.pipeline.update_all_runner import UpdateAllRunner

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_STEP = UpdateStep(name="morning-report", target="morning-report")
_COLORS = {"ok": "green", "failed": "red", "skipped": "yellow"}


class UpdateCommands:
    """
    Purpose:
        `update-all --out <APP_DATA> [--only a,b] [--from step] [--dry-run] [--with-report]
        [--trigger manual|launchd]`: check every step target exists in the Makefile, run the
        selected steps with UpdateAllRunner (make subprocesses; the ledger needs no catalog
        lock), print a summary, write `<out>/task_status.json`, then refresh `meta.task_log`
        (a brief catalog write; a held lock only warns). Exit 1 when any step failed.

    Contract:
        Input:
            console:   Console
            repo_root: Path  -- default the repository holding this file
        Output:
            instance; `build_parser`, `_run_update_all` (dispatched by QuantCnCli.run)
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- dispatch

    Test cases:
        TC-UPC-001  --dry-run prints the selected steps, runs nothing, writes no ledger, exit 0
        TC-UPC-002  a run with a fake Makefile: ledger rows and task_status.json written, view
                    refreshed, exit 1 when a step failed and 0 otherwise; a missing make target
                    is a ConfigError
    """

    def __init__(self, console: Console, repo_root: Path = REPO_ROOT) -> None:
        self._console = console
        self._root = repo_root

    @staticmethod
    def build_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
        """
        Purpose:
            Add the `update-all` subcommand.

        Contract:
            Input:
                sub: argparse subparsers of QuantCnCli
            Output:
                None
            Raises:
                (none)
        """
        up = sub.add_parser("update-all", help="run every daily update in order (plan 38)")
        up.add_argument("--out", type=Path, required=True, help="the app's data directory")
        up.add_argument("--only", default=None, help="comma-separated step names")
        up.add_argument("--from", dest="start", default=None, help="first step to run")
        up.add_argument("--dry-run", action="store_true", help="print the steps only")
        up.add_argument("--with-report", action="store_true", help="morning-report at the end")
        up.add_argument("--trigger", default="manual", choices=["manual", "launchd"])

    def _run_update_all(self, config: Config, args: argparse.Namespace) -> int:
        settings = UpdateAllSettings.load(self._root)
        missing = settings.find_missing_targets(self._root / "Makefile")
        if missing:
            raise ConfigError(f"config/update_all.yaml names unknown make targets: {missing}")
        only = [n.strip() for n in args.only.split(",")] if args.only else None
        steps = settings.list_steps(only, args.start) + ([REPORT_STEP] if args.with_report else [])
        if args.dry_run:
            for i, s in enumerate(steps, start=1):
                needs = f"  needs {', '.join(s.needs)}" if s.needs else ""
                self._console.print(f"{i:2d}. {s.name} -> make {s.target}{needs}")
            return 0
        task_log = TaskLog(config.lake.root)
        runner = UpdateAllRunner(
            settings, task_log, MakeTargetRunner(self._root), Clock(), args.out
        )
        rows = runner.run(steps, args.trigger)
        self._render_summary(rows)
        names = [s.name for s in settings.steps]
        TaskStatusBuilder(task_log, settings.history).write(args.out, names)
        self._refresh_view(config, task_log)
        return 1 if any(r["status"] == "failed" for r in rows) else 0

    def _render_summary(self, rows: list[dict[str, Any]]) -> None:
        table = Table(title=f"update-all {rows[0]['run_id'] if rows else ''}")
        for col in ("step", "status", "seconds", "as_of", "note"):
            table.add_column(col)
        for r in rows:
            color = _COLORS[r["status"]]
            note = (r["message"] or "").splitlines()[-1:] if r["status"] != "ok" else []
            state = f"[{color}]{r['status']}[/{color}]"
            secs = f"{r['duration_s']:.0f}"
            table.add_row(r["task"], state, secs, r["as_of"] or "", " ".join(note)[:80])
        self._console.print(table)
        done = sum(r["status"] == "ok" for r in rows)
        self._console.print(f"{done}/{len(rows)} ok")

    def _refresh_view(self, config: Config, task_log: TaskLog) -> None:
        try:
            catalog = LakeCatalog(config.lake.root, config.datasets)
            try:
                task_log.refresh_view(catalog.connection)
            finally:
                catalog.close()
        except LakeError as exc:
            self._console.print(f"[yellow]meta.task_log view not refreshed:[/yellow] {exc}")
