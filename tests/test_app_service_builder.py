"""Contract tests for AppServiceBuilder (plan 15 ph7f)."""

from __future__ import annotations

import json
from pathlib import Path

from quant_cn.app_service_builder import ETF_FILE, AppServiceBuilder
from quant_cn.core.config import Config
from quant_cn.core.positions_book import PositionsBook
from quant_cn.portfolio.condition_evaluator import ConditionEvaluator
from quant_cn.portfolio.holdings_risk_builder import HoldingsRiskBuilder
from quant_cn.portfolio.position_reviewer import PositionReviewer
from quant_cn.portfolio.sector_earnings_signal_builder import SectorEarningsSignalBuilder
from quant_cn.portfolio.sector_monitor_builder import SectorMonitorBuilder
from quant_cn.portfolio.watchlist_builder import WatchlistBuilder
from tests.support import MiniLake


def test_tc_asb_001_wiring(lake: MiniLake, config: Config) -> None:
    """TC-ASB-001"""
    app = AppServiceBuilder()
    evaluator = app.build_evaluator(config, lake.catalog)
    assert isinstance(evaluator, ConditionEvaluator)
    assert evaluator._chips._gauge_age == 45
    watchlist = app.build_watchlist(config, lake.catalog)
    assert isinstance(watchlist, WatchlistBuilder) and watchlist._evaluator is not None
    holdings = app.build_holdings_risk(config, lake.catalog, PositionsBook(), "000300.SH")
    assert isinstance(holdings, HoldingsRiskBuilder)
    assert isinstance(holdings._reviewer, PositionReviewer)


def test_tc_asb_002_heat(lake: MiniLake, config: Config) -> None:
    """TC-ASB-002"""
    app = AppServiceBuilder()
    assert app.build_evaluator(config, lake.catalog)._heat == {}
    path = config.repo_root / ETF_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = [{"metric": "bank_etf_z", "z": 1.99}, {"metric": "dividend_etf_z", "z": None}]
    path.write_text(json.dumps({"styles": styles}), encoding="utf-8")
    assert app.build_evaluator(config, lake.catalog)._heat == {"bank_etf_z": 1.99}


def test_tc_asb_003_sector_monitor(config: Config, lake: MiniLake) -> None:
    """TC-ASB-003"""
    for name in ("sector_monitors.yaml", "app_publishers.yaml"):
        source = Path(__file__).resolve().parents[1] / "config" / name
        (config.repo_root / "config" / name).write_text(
            source.read_text(encoding="utf-8"), encoding="utf-8"
        )
    builder = AppServiceBuilder().build_sector_monitor(config, lake.catalog)
    assert isinstance(builder, SectorMonitorBuilder)


def test_tc_asb_004_sector_earnings_signal(config: Config, lake: MiniLake) -> None:
    """TC-ASB-004"""
    builder = AppServiceBuilder().build_sector_earnings_signal(config, lake.catalog)
    assert isinstance(builder, SectorEarningsSignalBuilder)
    assert builder.build(None, "20250330")["rows"] == []
