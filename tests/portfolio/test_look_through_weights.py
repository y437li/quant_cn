"""Contract tests for portfolio.LookThroughWeights (plan 15 phase 7q)."""

from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.positions_book import Position
from quant_cn.portfolio.look_through_weights import LookThroughWeights
from tests.support import MiniLake, SampleFactorLake

A, B, C, OUT = "000001.SZ", "600000.SH", "300001.SZ", "000002.SZ"
UNIVERSE = pd.Index([A, B, C])
ETF = Position(code="512100.SH", shares=1, cost=1, tracks="000852.SH")


def _write(lake: MiniLake, config: Config) -> None:
    rows = [
        ("20261031", B, 10.0),
        ("20261031", C, 10.0),
        ("20261031", OUT, 20.0),
        ("20261130", B, 99.0),  # after the session: ignored
    ]
    SampleFactorLake.write(
        lake,
        config,
        "index_weight",
        [
            {"index_code": "000852.SH", "con_code": c, "trade_date": d, "weight": v}
            for d, c, v in rows
        ],
    )


# TC-LTW-001
def test_tc_ltw_001_stock_rows(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    stocks = [Position(code=A, shares=1, cost=1), Position(code=OUT, shares=1, cost=1)]
    m = LookThroughWeights(lake.query).build(stocks, "20261119", UNIVERSE)
    assert list(m.index) == [A] and list(m.columns) == list(UNIVERSE)
    assert m.loc[A].tolist() == [1.0, 0.0, 0.0]


# TC-LTW-002
def test_tc_ltw_002_etf_basket(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    m = LookThroughWeights(lake.query).build([ETF], "20261119", UNIVERSE)
    assert m.loc[ETF.code].tolist() == pytest.approx([0.0, 0.5, 0.5])


# TC-LTW-003
def test_tc_ltw_003_unresolvable(lake: MiniLake, config: Config) -> None:
    loose = Position(code="510300.SH", shares=1, cost=1)
    other = Position(code="159915.SZ", shares=1, cost=1, tracks="399006.SZ")
    builder = LookThroughWeights(lake.query)
    assert builder.build([ETF], "20261119", UNIVERSE).empty  # no index_weight view
    _write(lake, config)
    assert builder.build([loose, other], "20261119", UNIVERSE).empty
    empty = builder.build([], "20261119", UNIVERSE)
    assert empty.empty and list(empty.columns) == list(UNIVERSE)
