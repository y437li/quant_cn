"""Contract tests for portfolio.WatchlistBuilder (plan 15 phase 7, D-120)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.core.watchlist_entry import WatchlistEntry
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
