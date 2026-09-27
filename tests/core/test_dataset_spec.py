from __future__ import annotations

import pytest
from pydantic import ValidationError

from quant_cn.core.config import Config
from quant_cn.core.dataset_spec import SweepSpec
from tests.support import Build


# TC-DS-001
def test_tc_ds_001_yaml_entries_parse(config: Config) -> None:
    daily = config.dataset("daily")
    assert daily.sweep.kind == "trade_date" and daily.curated.partition_by == "trade_date"
    assert config.dataset("stock_basic").sweep.values == ["L", "D", "P"]
    assert config.dataset("fina_indicator_vip").sweep.refetch_recent == 2


# TC-DS-002
def test_tc_ds_002_raw_filename() -> None:
    assert Build.spec().raw_filename("20260828") == "trade_date=20260828.parquet"
    assert Build.spec(sweep=SweepSpec(kind="none")).raw_filename("all") == "all.parquet"


# TC-DS-003
def test_tc_ds_003_columns_must_be_declared() -> None:
    with pytest.raises(ValidationError):
        Build.spec(primary_key=["ts_code", "missing"])
    with pytest.raises(ValidationError):
        Build.spec(known_on="ann_date")


# TC-DS-004
def test_tc_ds_004_schema_mirrors_spec() -> None:
    schema = Build.spec().frame_schema()
    assert schema.columns == ["ts_code", "trade_date", "close"]
    assert schema.primary_key == ["ts_code", "trade_date"]
    assert schema.dtype("close") == "float64" and schema.dtype("ts_code") == "string"
