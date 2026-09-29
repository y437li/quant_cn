from __future__ import annotations

import pytest
from pydantic import ValidationError

from quant_cn.core.config import Config
from quant_cn.core.dataset_spec import SweepSpec
from tests.support import Sample


# TC-DS-001
def test_tc_ds_001_yaml_entries_parse(config: Config) -> None:
    daily = config.get_dataset("daily")
    assert daily.sweep.kind == "trade_date" and daily.curated.partition_by == "trade_date"
    assert config.get_dataset("stock_basic").sweep.values == ["L", "D", "P"]
    assert config.get_dataset("fina_indicator_vip").sweep.refetch_recent == 2


# TC-DS-002
def test_tc_ds_002_raw_filename() -> None:
    assert Sample.build_spec().get_raw_filename("20260828") == "trade_date=20260828.parquet"
    assert Sample.build_spec(sweep=SweepSpec(kind="none")).get_raw_filename("all") == "all.parquet"


# TC-DS-003
def test_tc_ds_003_columns_must_be_declared() -> None:
    with pytest.raises(ValidationError):
        Sample.build_spec(primary_key=["ts_code", "missing"])
    with pytest.raises(ValidationError):
        Sample.build_spec(known_on="ann_date")


# TC-DS-004
def test_tc_ds_004_schema_mirrors_spec() -> None:
    schema = Sample.build_spec().build_schema()
    assert schema.columns == ["ts_code", "trade_date", "close"]
    assert schema.primary_key == ["ts_code", "trade_date"]
    assert schema.get_dtype("close") == "float64" and schema.get_dtype("ts_code") == "string"


# TC-DS-005
def test_tc_ds_005_new_fields() -> None:
    spec = Sample.build_spec(source="fred", known_on_rule="next_session")
    assert spec.source == "fred" and spec.release_lag_days == 0
    window = SweepSpec(kind="date_window", window="month")
    assert window.param == "window"
    assert Sample.build_spec(sweep=window).get_raw_filename("202608") == "window=202608.parquet"
    with pytest.raises(ValidationError):
        SweepSpec(kind="date_window")
    with pytest.raises(ValidationError):
        Sample.build_spec(release_lag_days=10)
    with pytest.raises(ValidationError):
        Sample.build_spec(known_on=None, known_on_rule="next_session")
