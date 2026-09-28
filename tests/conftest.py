"""Shared fixtures: a Config over copies of the committed YAML and a mini lake in tmp_path."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from quant_cn.core.config import Config
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.run_log import RunLog
from tests.support import FakeClock, MiniLake

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A throwaway repo root holding copies of the committed config files."""
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    for name in ("base.yaml", "datasets.yaml"):
        shutil.copy(REPO / "config" / name, root / "config" / name)
    return root


@pytest.fixture
def config(repo: Path, tmp_path: Path) -> Config:
    env = {"QUANT_CN_LAKE_ROOT": str(tmp_path / "lake"), "TUSHARE_TOKEN": "test-token"}
    return Config.load(repo_root=repo, env=env)


@pytest.fixture
def lake(config: Config, clock: FakeClock) -> Iterator[MiniLake]:
    catalog = LakeCatalog(config.lake.root, config.datasets)
    mini = MiniLake(
        lake_root=config.lake.root,
        catalog=catalog,
        writer=ParquetWriter(config.lake.root),
        fetch_log=FetchLog(catalog),
        run_log=RunLog(catalog, clock),
        query=LakeQuery(catalog),
        clock=clock,
    )
    yield mini
    catalog.close()
