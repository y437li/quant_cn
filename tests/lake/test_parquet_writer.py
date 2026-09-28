from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from quant_cn.core.exceptions import LakeError, SchemaError
from quant_cn.lake.parquet_writer import ParquetWriter
from tests.support import MiniLake, Sample


# TC-PW-001
def test_tc_pw_001_raw_path_and_dtypes(lake: MiniLake) -> None:
    df = Sample.build_bars("20260828").assign(close=["1.5", "2"])
    path = lake.writer.write_raw(Sample.build_spec(), "20260828", df)
    assert path == lake.lake_root / "raw" / "bars" / "trade_date=20260828.parquet"
    back = pd.read_parquet(path)
    assert back["close"].dtype == "float64" and back["trade_date"].iloc[0] == "20260828"


# TC-PW-002
def test_tc_pw_002_empty_writes_nothing(lake: MiniLake) -> None:
    assert (
        lake.writer.write_raw(Sample.build_spec(), "20260828", Sample.build_bars("x").iloc[:0])
        is None
    )
    assert not (lake.lake_root / "raw").exists() or not any(
        (lake.lake_root / "raw").rglob("*.parquet")
    )


# TC-PW-003
def test_tc_pw_003_failed_write_is_clean(lake: MiniLake, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: object, **_kw: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("quant_cn.lake.parquet_writer.os.replace", boom)
    with pytest.raises(LakeError):
        lake.writer.write_raw(Sample.build_spec(), "20260828", Sample.build_bars("20260828"))
    folder = lake.lake_root / "raw" / "bars"
    assert list(folder.iterdir()) == []


# TC-PW-004
def test_tc_pw_004_curated_partition(lake: MiniLake) -> None:
    spec = Sample.build_spec()
    df = spec.build_schema().normalize(Sample.build_bars("20260828"), strict=True)
    path = lake.writer.write_curated(spec, 2026, df)
    assert path == lake.lake_root / "curated" / "bars" / "year=2026" / "part-0.parquet"
    glob = str(lake.lake_root / "curated" / "bars" / "*" / "*.parquet")
    out = duckdb.sql(
        f"SELECT year, count(*) n FROM read_parquet('{glob}', hive_partitioning=true) GROUP BY year"
    ).fetchall()
    assert out == [(2026, 2)]


# TC-PW-005
def test_tc_pw_005_curated_schema_violation(lake: MiniLake) -> None:
    writer = ParquetWriter(lake.lake_root)
    with pytest.raises(SchemaError):
        writer.write_curated(
            Sample.build_spec(), 2026, Sample.build_bars("20260828").drop(columns="close")
        )
    assert not (lake.lake_root / "curated").exists() or not any(
        (lake.lake_root / "curated").rglob("*.parquet")
    )
