"""Contract tests for lake.ChipStructureReader (plan 15 ph7f)."""

from __future__ import annotations

import math

import pandas as pd

from quant_cn.calculation.retail_gauge_nowcaster import GAUGE_COLUMNS
from quant_cn.core.config import Config
from quant_cn.lake.chip_structure_reader import COLUMNS, ChipStructureReader
from quant_cn.lake.derived_views import DerivedViews
from tests.support import MiniLake, SampleFactorLake

A, B = "000001.SZ", "600000.SH"
AS_OF = "20261112"


def _write(lake: MiniLake, config: Config) -> None:
    w = SampleFactorLake.write
    w(
        lake,
        config,
        "stk_holdernumber",
        [
            {"ts_code": A, "end_date": "20260630", "ann_date": "20260820", "holder_num": 100.0},
            {"ts_code": A, "end_date": "20260930", "ann_date": "20261025", "holder_num": 110.0},
            {"ts_code": A, "end_date": "20261231", "ann_date": "20270120", "holder_num": 500.0},
        ],
    )
    w(
        lake,
        config,
        "top10_floatholders",
        [
            {
                "ts_code": A,
                "end_date": "20260630",
                "ann_date": "20260820",
                "holder_name": "某某基金",
                "hold_float_ratio": 2.0,
            },
            {
                "ts_code": A,
                "end_date": "20260930",
                "ann_date": "20261025",
                "holder_name": "某某基金",
                "hold_float_ratio": 3.5,
            },
            {
                "ts_code": A,
                "end_date": "20260930",
                "ann_date": "20261025",
                "holder_name": "张三",
                "hold_float_ratio": 9.0,
            },
        ],
    )


def _write_market(lake: MiniLake, config: Config) -> None:
    w = SampleFactorLake.write
    w(
        lake,
        config,
        "hk_hold",
        [
            {"ts_code": A, "code": "1", "exchange": "SZ", "trade_date": "20260901", "ratio": 1.0},
            {"ts_code": A, "code": "1", "exchange": "SZ", "trade_date": AS_OF, "ratio": 1.4},
            {"ts_code": B, "code": "2", "exchange": "SH", "trade_date": "20260930", "ratio": 2.0},
        ],
    )
    w(
        lake,
        config,
        "margin_detail",
        [
            {"ts_code": A, "trade_date": "20260901", "rzye": 100.0},
            {"ts_code": A, "trade_date": AS_OF, "rzye": 80.0},
        ],
    )


def _write_flows(lake: MiniLake, config: Config) -> None:
    w = SampleFactorLake.write
    days = ["20261020", "20261027", "20261103", "20261110", "20261111"]  # Mondays + one more day
    lg = [1e4, -2e4, 3e4, 4e4, 1e4]  # 万: weeks +1, -2, +3, +5 亿
    sm = [-1e4, -1e4, 2e4, -3e4, 0.0]
    w(
        lake,
        config,
        "moneyflow",
        [
            {
                "ts_code": A,
                "trade_date": d,
                "buy_lg_amount": max(x, 0.0),
                "sell_lg_amount": max(-x, 0.0),
                "buy_sm_amount": max(y, 0.0),
                "sell_sm_amount": max(-y, 0.0),
            }
            for d, x, y in zip(days, lg, sm, strict=True)
        ],
    )


def _write_events(lake: MiniLake, config: Config) -> None:
    w = SampleFactorLake.write
    w(
        lake,
        config,
        "share_float",
        [
            {
                "ts_code": A,
                "ann_date": "20261001",
                "float_date": "20270101",
                "holder_name": "x",
                "share_type": "s",
                "float_ratio": 2.5,
            },
            {
                "ts_code": A,
                "ann_date": "20261001",
                "float_date": "20271001",
                "holder_name": "y",
                "share_type": "s",
                "float_ratio": 9.0,
            },
        ],
    )
    w(
        lake,
        config,
        "stk_holdertrade",
        [
            {"ts_code": A, "ann_date": "20260801", "in_de": "DE", "change_ratio": 0.5},
            {"ts_code": A, "ann_date": "20260801", "in_de": "IN", "change_ratio": 0.7},
            {"ts_code": A, "ann_date": "20260101", "in_de": "DE", "change_ratio": 3.0},
        ],
    )


def _read(lake: MiniLake, config: Config) -> pd.DataFrame:
    for write in (_write, _write_market, _write_flows, _write_events):
        write(lake, config)
    return ChipStructureReader(lake.query).read([A, B], AS_OF)


def test_tc_csr_001_announced_changes(lake: MiniLake, config: Config) -> None:
    """TC-CSR-001"""
    out = _read(lake, config)
    assert list(out.columns) == COLUMNS and list(out.index) == [A, B]
    assert round(out.loc[A, "holders_chg_q"], 9) == 0.1  # the Q4 count is announced after as_of
    assert out.loc[A, "inst_top10_dq_pp"] == 1.5  # 张三 is not an institution
    assert round(out.loc[A, "north_chg_pp"], 6) == 0.4
    assert math.isnan(out.loc[B, "north_chg_pp"])  # one quarterly disclosure: unknown, not 0
    assert round(out.loc[A, "margin_chg_60d"], 6) == -0.2
    assert math.isnan(out.loc[B, "holders_chg_q"])


def test_tc_csr_002_weekly_flows(lake: MiniLake, config: Config) -> None:
    """TC-CSR-002"""
    out = _read(lake, config)
    assert out.loc[A, "lg_weeks_pos_4w"] == 3.0 and out.loc[A, "lg_net_4w"] == 7.0
    assert out.loc[A, "lg_net_20d"] == 7.0
    assert out.loc[A, "sm_weeks_neg_4w"] == 3.0 and out.loc[A, "sm_net_4w"] == -3.0


def test_tc_csr_003_unlocks_insiders_gauge(lake: MiniLake, config: Config) -> None:
    """TC-CSR-003"""
    out = _read(lake, config)
    assert out.loc[A, "unlock_6m_pct"] == 2.5 and out.loc[B, "unlock_6m_pct"] == 0.0
    assert out.loc[A, "insider_sell_6m_pct"] == 0.5
    assert out["retail_gauge"].isna().all() and out["winner_rate"].isna().all()
    rows = pd.DataFrame(
        {"ts_code": [A, A, B], "as_of": ["20261001", "20261111", "20260901"],
         "pct": [0.5, 0.25, 0.9], "exp_change": [0.0, -0.04, 0.1], "avoid": [False, False, True],
         "avoid_strong": [False, False, True], "retail_leaving": [False, True, False],
         "lo_streak": [1, 3, 0], "hi_streak": [0, 0, 3]}
    ).reindex(columns=GAUGE_COLUMNS)  # fmt: skip
    lake.writer.write_derived("retail_gauge", 2026, rows)
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh_tables()
    gauge = ChipStructureReader(lake.query).read([A, B], AS_OF)
    assert gauge.loc[A, "retail_gauge"] == 0.25 and gauge.loc[A, "gauge_leaving"] == 1.0
    assert gauge.loc[A, "gauge_lo_streak"] == 3.0 and gauge.loc[A, "gauge_exp_change"] == -0.04
    assert math.isnan(gauge.loc[B, "retail_gauge"])  # 20260901 is older than 45 days
    assert ChipStructureReader(lake.query).read([], AS_OF).empty


def test_tc_csr_004_sales_dedup_winner(lake: MiniLake, config: Config) -> None:
    """TC-CSR-004"""
    for write in (_write, _write_market, _write_flows, _write_events):
        write(lake, config)
    w = SampleFactorLake.write
    sale = {
        "ts_code": A,
        "ann_date": "20260801",
        "in_de": "DE",
        "change_ratio": 0.5,
        "holder_name": "x",
    }
    late = {
        "ts_code": A,
        "ann_date": "20260920",
        "in_de": "DE",
        "change_ratio": 0.2,
        "holder_name": "y",
    }
    w(lake, config, "stk_holdertrade", [sale, dict(sale), late])  # vendor repeats the first row
    w(lake, config, "cyq_perf", [{"ts_code": A, "trade_date": "20261111", "winner_rate": 11.0}])
    out = ChipStructureReader(lake.query).read([A, B], AS_OF)
    assert out.loc[A, "insider_sell_6m_pct"] == 0.7  # 0.5 once + 0.2
    assert out.loc[A, "holder_sell_90d_pct"] == 0.2
    assert out.loc[A, "winner_rate"] == 11.0 and math.isnan(out.loc[B, "winner_rate"])


def test_tc_csr_005_cost_band_gaps(lake: MiniLake, config: Config) -> None:
    """TC-CSR-005"""
    for write in (_write, _write_market, _write_flows, _write_events):
        write(lake, config)
    w = SampleFactorLake.write
    chips = [
        {"ts_code": A, "trade_date": "20261110", "winner_rate": 9.0, "cost_15pct": 1.0,
         "cost_85pct": 1.0},
        {"ts_code": A, "trade_date": "20261111", "winner_rate": 11.0, "cost_15pct": 8.0,
         "cost_85pct": 12.5},
    ]  # fmt: skip
    w(lake, config, "cyq_perf", chips)
    w(lake, config, "daily", [{"ts_code": A, "trade_date": "20261111", "close": 10.0}])
    out = ChipStructureReader(lake.query).read([A, B], AS_OF)
    assert math.isclose(out.loc[A, "cost_lo_gap"], 0.25)  # 10 / 8 - 1
    assert math.isclose(out.loc[A, "cost_hi_gap"], -0.2)  # 10 / 12.5 - 1
    assert math.isnan(out.loc[B, "cost_lo_gap"])
