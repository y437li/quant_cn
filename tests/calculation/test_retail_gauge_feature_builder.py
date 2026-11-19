"""Contract tests for calculation.RetailGaugeFeatureBuilder (plan 21 ph2, D-142)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.calculation.holder_count_panel import HolderCountPanel
from quant_cn.calculation.retail_gauge_feature_builder import RetailGaugeFeatureBuilder
from quant_cn.core.config import Config
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings
from quant_cn.lake.dated_table_store import DatedTableStore
from quant_cn.lake.derived_views import DerivedViews
from tests.support import MiniLake, SampleFactorLake

A, B, C = "000001.SZ", "000002.SZ", "000003.SZ"
Q4 = ["20241227", "20241230", "20241231"]
Q1 = ["20250102", "20250103", "20250106", "20250107"]
Q2 = ["20250401", "20250402", "20250403", "20250407"]
SETTINGS = RetailGaugeSettings(
    start="20241201",
    first_quarter="20241231",
    windows=[2],
    halflives=[2],
    trel_window=3,
    trel_min=2,
    slope_window=3,
    edge_sessions=2,
    year_back=5,
    half_year=3,
    top_turnover_days=2,
    min_window_sessions=3,
    lagged=["ret_q"],
)
PX_A = dict(zip(Q4 + Q1 + Q2, [10, 10, 8, 10, 10, 11, 10, 11, 11, 12, 12], strict=True))


def write_lake(lake: MiniLake, config: Config, late: bool = False) -> None:
    days = Q4 + Q1 + Q2 + (["20250408"] if late else [])
    px = PX_A | {"20250408": 30.0}
    daily = [{"ts_code": A, "trade_date": d, "close": float(px[d])} for d in days]
    daily += [{"ts_code": B, "trade_date": d, "close": 5.0} for d in days]
    daily += [{"ts_code": C, "trade_date": d, "close": 7.0} for d in Q4]
    SampleFactorLake.write(lake, config, "daily", daily)
    adj = [
        {"ts_code": r["ts_code"], "trade_date": r["trade_date"], "adj_factor": 1.0} for r in daily
    ]
    SampleFactorLake.write(lake, config, "adj_factor", adj)
    basic = [r | {"turnover_rate_f": 1.0, "circ_mv": 100.0} for r in adj]
    SampleFactorLake.write(
        lake,
        config,
        "daily_basic",
        [{k: v for k, v in r.items() if k != "adj_factor"} for r in basic],
    )
    flow = {
        "buy_lg_amount": 1.0,
        "sell_lg_amount": 0.0,
        "buy_elg_amount": 0.0,
        "sell_elg_amount": 0.0,
        "buy_sm_amount": 0.0,
        "sell_sm_amount": 1.0,
    }
    SampleFactorLake.write(
        lake,
        config,
        "moneyflow",
        [{"ts_code": r["ts_code"], "trade_date": r["trade_date"]} | flow for r in daily],
    )
    SampleFactorLake.write(
        lake,
        config,
        "margin_detail",
        [{"ts_code": A, "trade_date": d, "rzye": 100.0} for d in days],
    )
    write_events(lake, config, late)


CHIP = {"ts_code": A, "cost_15pct": 9.0, "cost_50pct": 10.0}


def write_events(lake: MiniLake, config: Config, late: bool) -> None:
    chips = [
        CHIP
        | {"trade_date": "20250107", "winner_rate": 50.0, "cost_85pct": 11.0, "weight_avg": 10.0},
        CHIP
        | {"trade_date": "20250403", "winner_rate": 70.0, "cost_85pct": 12.0, "weight_avg": 11.0},
    ]
    if late:
        chips.append(chips[1] | {"trade_date": "20250408", "winner_rate": 99.0})
    SampleFactorLake.write(lake, config, "cyq_perf", chips)
    counts = [("20240930", "20241020", 90), ("20241231", "20250115", 100)]
    if late:
        counts.append(("20250331", "20250408", 150))
    rows = [{"ts_code": A, "end_date": e, "ann_date": a, "holder_num": n} for e, a, n in counts]
    SampleFactorLake.write(lake, config, "stk_holdernumber", rows)


def build(lake: MiniLake) -> RetailGaugeFeatureBuilder:
    tables = DatedTableStore(lake.writer)
    return RetailGaugeFeatureBuilder(SETTINGS, lake.query, HolderCountPanel(lake.query), tables)


# TC-RGF-001
def test_tc_rgf_001_rows(lake: MiniLake, config: Config) -> None:
    write_lake(lake, config)
    out = build(lake).build(["20250405"]).set_index("ts_code")
    assert sorted(out.index) == [A, B]  # C has no turnover in the window
    a = out.loc[A]
    assert (a["q"], a["as_of"]) == ("20250630", "20250403")
    assert (a["win_b"], a["dwin"]) == (70.0, 20.0)
    assert a["conc_b"] == pytest.approx(0.3) and a["dconc"] == pytest.approx(0.1)
    assert a["pc50_b"] == pytest.approx(math.log(1.2)) and a["dpc50"] == pytest.approx(
        math.log(1.2)
    )
    assert a["wavg_gap"] == pytest.approx(math.log(1.1))
    assert a["ret_q_lag1"] == pytest.approx(math.log(10 / 8))  # quarter 20250331 row
    assert math.isnan(a["prev"]) and a["prev2"] == pytest.approx(math.log(100 / 90))
    assert a["qtr"] == 2.0
    q1 = build(lake).build(["20250331"]).set_index("ts_code")
    assert math.isnan(q1.loc[A, "ret_q_lag1"])  # the first quarter end has no row


# TC-RGF-002
def test_tc_rgf_002_pit(lake: MiniLake, config: Config) -> None:
    write_lake(lake, config)
    before = build(lake).build(["20250407"])
    write_lake(lake, config, late=True)
    after = build(lake).build(["20250407"])
    pd.testing.assert_frame_equal(before, after)


# TC-RGF-003
def test_tc_rgf_003_write(lake: MiniLake, config: Config) -> None:
    write_lake(lake, config)
    builder = build(lake)
    views = DerivedViews(lake.catalog, lake.query, config.datasets)
    builder.write(builder.build(["20250403", "20250407"]))
    views.refresh_tables()
    again = builder.build(["20250407"])
    again["ret_q"] = 9.0
    builder.write(again)
    rows = lake.query.sql(
        "SELECT as_of, ts_code, ret_q FROM derived.retail_gauge_features ORDER BY 1, 2"
    )
    assert rows["as_of"].tolist() == ["20250403", "20250403", "20250407", "20250407"]
    assert rows["ret_q"].tolist()[2:] == [9.0, 9.0] and rows["ret_q"].tolist()[0] != 9.0
