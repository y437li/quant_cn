"""Contract tests for lake.StatementVersionReader (plan 16 phase 1)."""

from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.config import Config, TickerAlias
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.statement_version_reader import COLUMNS, StatementVersionReader
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from tests.support import MiniLake, SampleFactorLake

OLD, NEW = "000043.SZ", "001914.SZ"
ALIASES = [TickerAlias(old_code=OLD, new_code=NEW)]
# (code, end_date, f_ann_date, revenue, total_profit)
ROWS = [
    (NEW, "20250630", "20250820", 10.0, 1.0),
    (NEW, "20250630", "20251010", 10.0, 1.5),  # restatement
    (NEW, "20240630", "20240820", 8.0, 0.8),
    (OLD, "20231231", "20240320", 7.0, 0.7),  # filed under the retired code
]


def _write_lake(lake: MiniLake, config: Config) -> None:
    base = {"report_type": "1", "update_flag": "1"}
    keys = ("ts_code", "end_date", "f_ann_date", "revenue", "total_profit")
    rows = [base | dict(zip(keys, r, strict=True)) | {"ann_date": r[2]} for r in ROWS]
    SampleFactorLake.write(lake, config, "income_vip", rows)
    SampleFactorLake.write(lake, config, "stock_basic", [{"ts_code": NEW, "list_status": "L"}])
    days = ["20250105", "20250106"]
    bars = [{"ts_code": c, "trade_date": d, "close": 9.0} for c in (OLD, NEW) for d in days]
    SampleFactorLake.write(lake, config, "daily", bars)
    DerivedViews(lake.catalog, lake.query, config.datasets, aliases=ALIASES).refresh()


def _build_reader(lake: MiniLake) -> StatementVersionReader:
    alias_map = TickerAliasMap(lake.catalog, lake.query, ALIASES)
    return StatementVersionReader(lake.query, alias_map, DateCodec())


def _find_value(frame: pd.DataFrame, end: str, field: str) -> float:
    hit = frame[(frame["end_date"] == end) & (frame["field"] == field)]
    return float(hit["value"].iloc[0])


def test_tc_svr_001_latest_known_version(lake: MiniLake, config: Config) -> None:
    """TC-SVR-001"""
    _write_lake(lake, config)
    reader = _build_reader(lake)
    before = reader.read_versions(["total_profit"], "20250901", "20200101")
    after = reader.read_versions(["total_profit"], "20251101", "20200101")
    assert _find_value(before, "20250630", "total_profit") == pytest.approx(1.0)
    assert _find_value(after, "20250630", "total_profit") == pytest.approx(1.5)
    assert "20250630" not in set(reader.read_versions(["revenue"], "20250801", "20200101").end_date)


def test_tc_svr_002_filters(lake: MiniLake, config: Config) -> None:
    """TC-SVR-002"""
    _write_lake(lake, config)
    out = _build_reader(lake).read_versions(["revenue"], "20251101", "20250101")
    assert list(out.columns) == COLUMNS
    assert out[["end_date", "field"]].values.tolist() == [["20250630", "revenue"]]


def test_tc_svr_003_retired_code(lake: MiniLake, config: Config) -> None:
    """TC-SVR-003"""
    _write_lake(lake, config)
    out = _build_reader(lake).read_versions(["revenue"], "20251101", "20200101")
    assert set(out["ts_code"]) == {NEW}
    assert _find_value(out, "20231231", "revenue") == pytest.approx(7.0)


def test_tc_svr_004_errors(lake: MiniLake, config: Config) -> None:
    """TC-SVR-004"""
    reader = _build_reader(lake)
    with pytest.raises(LakeError):
        reader.read_versions(["revenue"], "20251101", "20200101")  # view missing
    _write_lake(lake, config)
    with pytest.raises(LakeError):
        reader.read_versions(["revenue"], "2025-11-01", "20200101")
