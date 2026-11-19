"""Contract tests for portfolio.WatchlistBuilder (plan 15 phase 7, D-120)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd
import pytest

from quant_cn.core.condition import Condition
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.core.watchlist_entry import WatchlistEntry
from quant_cn.portfolio.condition_evaluator import ConditionEvaluator
from quant_cn.portfolio.watchlist_builder import WatchlistBuilder
from tests.support import MiniLake, SampleFactorLake

FAR, NEAR, IN, GONE = "000001.SZ", "600000.SH", "000002.SZ", "300000.SZ"
AS_OF = "20261106"


def _build_target(code: str, low: float, high: float) -> WatchlistEntry:
    return WatchlistEntry(code=code, buy_low=low, buy_high=high, added="20261108")


def _build_config(config: Config, *entries: WatchlistEntry) -> Config:
    return config.model_copy(update={"watchlist": list(entries)})


def _write_lake(lake: MiniLake, config: Config) -> None:
    w = SampleFactorLake.write
    daily = [
        (FAR, "20251020", 50.0),  # before the 365-day window
        (FAR, "20251110", 40.0),
        (FAR, "20251112", 42.0),  # same ISO week as 20251110: the week's close
        (FAR, "20251117", 30.0),
        (FAR, AS_OF, 44.0),
        (NEAR, AS_OF, 10.5),
        (IN, AS_OF, 9.0),
    ]
    w(lake, config, "daily", [{"ts_code": c, "trade_date": d, "close": v} for c, d, v in daily])
    w(
        lake,
        config,
        "daily_basic",
        [{"ts_code": FAR, "trade_date": AS_OF, "pe_ttm": 15.0, "pb": 2.0, "dv_ttm": 3.0}],
    )
    rc = [
        ("X", "20261020", "2026Q4", 2.0, 40.0, None),
        ("Y", "20261101", "2026Q4", 3.0, None, 60.0),
        ("Y", "20261101", "2027Q4", 5.0, None, 60.0),  # other fiscal year
        ("Z", "20260901", "2026Q4", 9.0, 100.0, 100.0),  # outside consensus_days
    ]
    w(
        lake,
        config,
        "report_rc",
        [
            {
                "ts_code": FAR,
                "org_name": o,
                "report_date": d,
                "quarter": q,
                "eps": e,
                "min_price": lo,
                "max_price": hi,
                "report_title": f"{o}{d}",
            }
            for o, d, q, e, lo, hi in rc
        ],
    )
    w(lake, config, "stock_basic", [{"ts_code": FAR, "name": "远方股份"}])


def _build_builder(lake: MiniLake, config: Config) -> WatchlistBuilder:
    return WatchlistBuilder(config, lake.query, DateCodec())


@pytest.fixture
def built(lake: MiniLake, config: Config) -> dict[str, Any]:
    cfg = _build_config(
        config,
        _build_target(FAR, 25, 30),
        _build_target(NEAR, 10, 10),
        _build_target(IN, 9, 9.5),
        _build_target(GONE, 1, 2),
    )
    _write_lake(lake, cfg)
    return _build_builder(lake, cfg).build()


def _build_index(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {e["code"]: e for e in doc["entries"]}


def test_tc_wb_001_gap_to_buy(built: dict[str, Any]) -> None:
    """TC-WB-001"""
    rows = _build_index(built)
    assert rows[FAR]["gap_to_buy"] == pytest.approx(30 / 44 - 1, abs=1e-4)
    assert rows[IN]["gap_to_buy"] == pytest.approx(0.0)


def test_tc_wb_002_status_edges(built: dict[str, Any]) -> None:
    """TC-WB-002"""
    rows = _build_index(built)
    assert [rows[c]["status"] for c in (FAR, NEAR, IN)] == ["far", "near", "in"]
    assert WatchlistBuilder.compute_status(11.0, 10.0, 0.10) == "near"
    assert WatchlistBuilder.compute_status(11.01, 10.0, 0.10) == "far"
    assert WatchlistBuilder.compute_status(10.0, 10.0, 0.10) == "in"


def test_tc_wb_003_valuation_at_buy(built: dict[str, Any]) -> None:
    """TC-WB-003"""
    rows = _build_index(built)
    assert rows[FAR]["pe_at_buy"] == pytest.approx(12.0)
    assert rows[FAR]["yield_at_buy"] == pytest.approx(44 * 0.03 / 30, abs=1e-4)
    assert rows[FAR]["div_yield"] == pytest.approx(0.03)
    assert rows[NEAR]["pe_at_buy"] is None
    assert rows[NEAR]["yield_at_buy"] is None


def test_tc_wb_004_consensus_window(built: dict[str, Any]) -> None:
    """TC-WB-004"""
    row = _build_index(built)[FAR]
    assert row["eps_year"] == "2026"
    assert row["eps_fy"] == pytest.approx(2.5)
    assert row["eps_brokers"] == 2
    assert (row["target_low"], row["target_high"]) == (40.0, 60.0)


def test_tc_wb_005_range_and_weekly(built: dict[str, Any]) -> None:
    """TC-WB-005"""
    row = _build_index(built)[FAR]
    assert (row["price"], row["price_date"], row["name"]) == (44.0, AS_OF, "远方股份")
    assert (row["low_52w"], row["high_52w"]) == (30.0, 44.0)
    assert row["weekly"] == [
        {"date": "20251112", "close": 42.0},
        {"date": "20251117", "close": 30.0},
        {"date": AS_OF, "close": 44.0},
    ]


def test_tc_wb_006_missing_code(built: dict[str, Any]) -> None:
    """TC-WB-006"""
    assert built["missing"] == [GONE]
    assert [e["code"] for e in built["entries"]] == [FAR, NEAR, IN]
    assert built["as_of"] == AS_OF


def test_tc_wb_007_no_entries(lake: MiniLake, config: Config) -> None:
    """TC-WB-007"""
    doc = _build_builder(lake, config).build()
    assert doc == {"as_of": "", "near_pct": 0.10, "entries": [], "missing": []}


def test_tc_wb_008_write(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-WB-008"""
    cfg = _build_config(config, _build_target(FAR, 25, 30))
    _write_lake(lake, cfg)
    path = _build_builder(lake, cfg).write(tmp_path)
    assert path == tmp_path / "watchlist.json"
    assert json.loads(path.read_text(encoding="utf-8"))["entries"][0]["code"] == FAR
    with pytest.raises(LakeError):
        _build_builder(lake, cfg).write(tmp_path / "absent")


def test_tc_wb_009_empty_daily(lake: MiniLake, config: Config) -> None:
    """TC-WB-009"""
    cfg = _build_config(config, _build_target(FAR, 25, 30))
    with pytest.raises(LakeError):
        _build_builder(lake, cfg).build()


class FakeEvaluator:
    """ConditionEvaluator with fixed metrics per code."""

    METRICS: ClassVar[dict[str, dict[str, float]]] = {
        IN: {"lg_weeks_pos_4w": 3.0, "gm_q": 0.1, "retail_gauge": 0.95, "gauge_avoid": 1.0},
        FAR: {"lg_weeks_pos_4w": 4.0, "gm_q": 0.3},
    }

    def read_metrics(self, closes: dict[str, float], as_of: str, series: list[str]) -> pd.DataFrame:
        return pd.DataFrame.from_dict(self.METRICS, orient="index")

    compute_results = ConditionEvaluator.compute_results
    _is_streak_missing = staticmethod(ConditionEvaluator._is_streak_missing)


def test_tc_wb_010_conditions(lake: MiniLake, config: Config) -> None:
    """TC-WB-010"""
    conds = [
        Condition(label="大单", kind="flow", metric="lg_weeks_pos_4w", op=">=", value=3),
        Condition(label="毛利", kind="statement", metric="gm_q", op=">=", value=0.22),
    ]
    cfg = _build_config(
        config,
        WatchlistEntry(code=IN, buy_low=9, buy_high=9.5, added="20261108", conditions=conds),
        WatchlistEntry(
            code=FAR,
            buy_low=25,
            buy_high=30,
            added="20261108",
            conditions=conds,
            conditions_needed=1,
        ),
        WatchlistEntry(
            code=NEAR,
            buy_low=10,
            buy_high=10.5,
            added="20261108",
            conditions=conds,
            conditions_needed=1,
        ),
    )
    _write_lake(lake, cfg)
    builder = WatchlistBuilder(cfg, lake.query, DateCodec(), FakeEvaluator())  # type: ignore[arg-type]
    rows = _build_index(builder.build())
    assert [c["state"] for c in rows[IN]["conditions"]] == ["met", "unmet"]
    assert rows[IN]["condition_status"] == "near"  # price in range, one condition unmet
    assert rows[FAR]["condition_status"] == "wait"  # price above the range
    assert rows[NEAR]["condition_status"] == "near"  # in range, conditions unknown
    assert [c["state"] for c in rows[NEAR]["conditions"]] == ["unknown", "unknown"]
    assert rows[FAR]["conditions_needed"] == 1
    plain = _build_index(_build_builder(lake, cfg).build())
    assert plain[IN]["conditions"] == [] and plain[IN]["condition_status"] == "buy"
    assert rows[IN]["retail"]["retail_gauge"] == 0.95 and rows[IN]["retail"]["gauge_avoid"] == 1.0
    assert rows[NEAR]["retail"]["retail_gauge"] is None


def test_tc_wb_011_etf_entry(lake: MiniLake, config: Config) -> None:
    """TC-WB-011"""
    etf = "512100.SH"
    cfg = _build_config(config, _build_target(FAR, 25, 30), _build_target(etf, 2.24, 2.47))
    _write_lake(lake, cfg)
    plain = _build_builder(lake, cfg).build()  # no fund views yet: stocks only
    assert plain["missing"] == [etf] and plain["entries"][0]["kind"] == "stock"
    w = SampleFactorLake.write
    w(lake, cfg, "fund_basic", [{"ts_code": etf, "name": "中证1000ETF", "market": "E"}])
    closes = [("20261102", 2.60), ("20261104", 2.50), (AS_OF, 2.46)]
    w(lake, cfg, "fund_daily", [{"ts_code": etf, "trade_date": d, "close": c} for d, c in closes])
    doc = _build_builder(lake, cfg).build()
    assert doc["missing"] == [] and [e["code"] for e in doc["entries"]] == [FAR, etf]
    row = _build_index(doc)[etf]
    assert (row["name"], row["kind"], row["status"]) == ("中证1000ETF", "etf", "in")
    assert [row["price"], row["low_52w"], row["high_52w"]] == pytest.approx([2.46, 2.46, 2.60])
    assert row["pe_ttm"] is None and row["eps_fy"] is None and row["div_yield"] is None
    assert [p["close"] for p in row["weekly"]] == pytest.approx([2.46])  # one ISO week
    assert _build_index(doc)[FAR]["kind"] == "stock"
