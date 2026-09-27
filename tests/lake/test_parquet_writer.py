from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from quant_cn.core.exceptions import LakeError, SchemaError
from quant_cn.lake.parquet_writer import ParquetWriter
from tests.support import Build, MiniLake


# TC-PW-001
def test_tc_pw_001_raw_path_and_dtypes(lake: MiniLake) -> None:
    df = Build.bars("20260828").assign(close=["1.5", "2"])
    path = lake.writer.write_raw(Build.spec(), "20260828", df)
    assert path == lake.root / "raw" / "bars" / "trade_date=20260828.parquet"
    back = pd.read_parquet(path)
    assert back["close"].dtype == "float64" and back["trade_date"].iloc[0] == "20260828"


# TC-PW-002
def test_tc_pw_002_empty_writes_nothing(lake: MiniLake) -> None:
    assert lake.writer.write_raw(Build.spec(), "20260828", Build.bars("x").iloc[:0]) is None
    assert not (lake.root / "raw").exists() or not any((lake.root / "raw").rglob("*.parquet"))


# TC-PW-003
def test_tc_pw_003_failed_write_is_clean(lake: MiniLake, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: object, **_kw: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("quant_cn.lake.parquet_writer.os.replace", boom)
    with pytest.raises(LakeError):
        lake.writer.write_raw(Build.spec(), "20260828", Build.bars("20260828"))
    folder = lake.root / "raw" / "bars"
    assert list(folder.iterdir()) == []


# TC-PW-004
def test_tc_pw_004_curated_partition(lake: MiniLake) -> None:
    spec = Build.spec()
    df = spec.frame_schema().coerce(Build.bars("20260828"), strict=True)
    path = lake.writer.write_curated(spec, 2026, df)
    assert path == lake.root / "curated" / "bars" / "year=2026" / "part-0.parquet"
    glob = str(lake.root / "curated" / "bars" / "*" / "*.parquet")
    out = duckdb.sql(
        f"SELECT year, count(*) n FROM read_parquet('{glob}', hive_partitioning=true) GROUP BY year"
    ).fetchall()
    assert out == [(2026, 2)]


# TC-PW-005
def test_tc_pw_005_curated_schema_violation(lake: MiniLake) -> None:
    writer = ParquetWriter(lake.root)
    with pytest.raises(SchemaError):
        writer.write_curated(Build.spec(), 2026, Build.bars("20260828").drop(columns="close"))
    assert not (lake.root / "curated").exists() or not any(
        (lake.root / "curated").rglob("*.parquet")
    )
