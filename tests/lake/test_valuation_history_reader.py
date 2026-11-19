"""Contract tests for lake.ValuationHistoryReader (plan 21 ph4)."""

from __future__ import annotations

import math

import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.valuation_history_reader import ValuationHistoryReader
from tests.support import MiniLake, SampleFactorLake

A, B = "000001.SZ", "600000.SH"


# TC-VHR-001
def test_tc_vhr_001_latest_and_median(lake: MiniLake, config: Config) -> None:
    rows = [
        {"ts_code": A, "trade_date": "20191231", "pb": 100.0, "pe_ttm": 1.0},  # before start
        {"ts_code": A, "trade_date": "20210104", "pb": 2.0, "pe_ttm": 10.0},
        {"ts_code": A, "trade_date": "20230104", "pb": 4.0, "pe_ttm": -5.0},
        {"ts_code": A, "trade_date": "20261112", "pb": 3.0, "pe_ttm": None},  # latest: a loss
        {"ts_code": A, "trade_date": "20261113", "pb": 9.0, "pe_ttm": 9.0},  # after as_of
        {"ts_code": B, "trade_date": "20261112", "pb": -1.0, "pe_ttm": None},
    ]
    SampleFactorLake.write(lake, config, "daily_basic", rows)
    reader = ValuationHistoryReader(lake.query)
    pb = reader.read([A, B], "pb", "20211112", "20261112")
    assert pb.loc[A, "value"] == 3.0 and pb.loc[A, "median"] == 3.5  # (3, 4)
    assert pb.loc[A, "n_days"] == 2 and math.isnan(pb.loc[B, "median"])
    pe = reader.read([A], "pe_ttm", "20201112", "20261112")
    assert pe.loc[A, "value"] == 0.0 and pe.loc[A, "median"] == 10.0
    with pytest.raises(LakeError):
        reader.read([A], "ps", "20201112", "20261112")
