from __future__ import annotations

import json

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.lake.compactor import Compactor
from tests.support import Build, MiniLake


@pytest.fixture
def compactor(lake: MiniLake) -> Compactor:
    return Compactor(lake.catalog, lake.query, lake.writer, lake.clock)


def write_days(lake: MiniLake, config: Config, days: list[str]) -> None:
    for day in days:
        lake.writer.write_raw(
            config.dataset("stk_limit"),
            day,
            Build.bars(day).rename(columns={"close": "up_limit"}).assign(down_limit=1.0),
        )


# TC-CO-001
def test_tc_co_001_yearly_partitions(lake: MiniLake, config: Config, compactor: Compactor) -> None:
    write_days(lake, config, ["20251231", "20260105", "20260102"])
    report = compactor.compact(config.dataset("stk_limit"))
    assert (report.keys_total, report.rows) == (2, 6)
    part = pd.read_parquet(lake.root / "curated" / "stk_limit" / "year=2026" / "part-0.parquet")
    assert part["trade_date"].tolist() == sorted(part["trade_date"].tolist())
    assert part["up_limit"].dtype == "float64"


# TC-CO-002
def test_tc_co_002_duplicates_dropped(lake: MiniLake, config: Config, compactor: Compactor) -> None:
    spec = config.dataset("stock_basic")
    row = {c: "x" for c in spec.fields} | {"ts_code": "000001.SZ"}
    lake.writer.write_raw(spec, "L", pd.DataFrame([row]))
    lake.writer.write_raw(spec, "D", pd.DataFrame([row | {"list_status": "D"}]))
    report = compactor.compact(spec)
    assert report.rows == 1 and report.skipped == 1
    manifest = json.loads((lake.root / "meta" / "manifest" / "stock_basic.json").read_text())
    assert manifest["duplicate_keys_dropped"] == 1


# TC-CO-003
def test_tc_co_003_single_file(lake: MiniLake, config: Config, compactor: Compactor) -> None:
    lake.writer.write_raw(
        config.dataset("trade_cal"), "all", Build.trade_cal(["20260828"], ["20260829"])
    )
    compactor.compact(config.dataset("trade_cal"))
    assert (lake.root / "curated" / "reference" / "trade_cal.parquet").exists()


# TC-CO-004
def test_tc_co_004_no_raw(lake: MiniLake, config: Config, compactor: Compactor) -> None:
    report = compactor.compact(config.dataset("daily"))
    assert report.rows == 0 and report.message == "no raw files"
    assert not (lake.root / "curated" / "daily").exists()


# TC-CO-005
def test_tc_co_005_curated_view(lake: MiniLake, config: Config, compactor: Compactor) -> None:
    write_days(lake, config, ["20260102"])
    compactor.compact(config.dataset("stk_limit"))
    df = lake.query.sql("SELECT year, count(*) n FROM curated.stk_limit GROUP BY year")
    assert df.values.tolist() == [[2026, 2]]
