"""Contract tests for cli.UpdateCommands (plan 38)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest
from rich.console import Console

from quant_cn.core.config import Config
from quant_cn.core.exceptions import ConfigError
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.task_log import TaskLog
from quant_cn.update_commands import UpdateCommands

STEPS = (
    "steps:\n  - {name: a, target: a}\n  - {name: b, target: b, needs: [a]}\n"
    "  - {name: c, target: c}\n"
)


def _build_repo(root: Path, makefile: str, steps: str = STEPS) -> Path:
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "update_all.yaml").write_text(steps, encoding="utf-8")
    (root / "Makefile").write_text(makefile, encoding="utf-8")
    return root


def _build_args(out: Path, **kw: object) -> argparse.Namespace:
    base = {"out": out, "only": None, "start": None, "dry_run": False, "with_report": False,
            "trigger": "manual"}  # fmt: skip
    return argparse.Namespace(**(base | kw))


# TC-UPC-001
def test_tc_upc_001_dry_run(config: Config, tmp_path: Path) -> None:
    repo = _build_repo(tmp_path / "ua_repo", "a:\n\t@exit 1\nb:\nc:\n")
    console = Console(record=True, width=200)
    code = UpdateCommands(console, repo)._run_update_all(
        config, _build_args(tmp_path, dry_run=True)
    )
    text = console.export_text()
    assert code == 0 and "2. b -> make b  needs a" in text
    assert TaskLog(config.lake.root).read_rows().empty


# TC-UPC-002
def test_tc_upc_002_run(config: Config, tmp_path: Path) -> None:
    LakeCatalog(config.lake.root, config.datasets).close()
    repo = _build_repo(
        tmp_path / "ua_repo", "a:\n\t@echo fail-a\n\t@exit 1\nb:\n\t@true\nc:\n\t@true\n"
    )
    console = Console(record=True, width=200)
    commands = UpdateCommands(console, repo)
    assert commands._run_update_all(config, _build_args(tmp_path)) == 1
    rows = TaskLog(config.lake.root).read_rows()
    assert list(rows.status) == ["failed", "skipped", "ok"]
    assert "1/3 ok" in console.export_text()
    assert (tmp_path / "task_status.json").exists()
    catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
    assert catalog.connection.execute("SELECT count(*) FROM meta.task_log").fetchall() == [(3,)]
    catalog.close()
    assert commands._run_update_all(config, _build_args(tmp_path, only="c")) == 0
    bad = _build_repo(tmp_path / "bad", "a:\n", STEPS)
    with pytest.raises(ConfigError):
        UpdateCommands(console, bad)._run_update_all(config, _build_args(tmp_path))
