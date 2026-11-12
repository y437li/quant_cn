"""Contract tests for portfolio.HoldingsHistoryWriter (plan 15 phase 7d, D-132)."""

from __future__ import annotations

from typing import Any

from quant_cn.core.config import Config
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.portfolio.holdings_history_writer import HoldingsHistoryWriter
from tests.support import MiniLake


def _build_doc(day: str, close: float) -> dict[str, Any]:
    position = {"code": "A", "shares": 100.0, "cost": 8.0, "close": close, "value": 100 * close}
    return {
        "as_of": day,
        "cash": 100.0,
        "value": 100 * close + 100.0,
        "positions": [position | {"pnl": 100 * (close - 8.0), "weight": 0.9}],
        "risk": {"total": 0.2, "factor": 0.15},
        "factors": [{"factor": "size", "exposure": -0.5, "contrib": 0.1}],
    }


# TC-HHW-001
def test_tc_hhw_001_sessions_replace(lake: MiniLake, config: Config) -> None:
    writer = HoldingsHistoryWriter(lake.query, lake.writer)
    views = DerivedViews(lake.catalog, lake.query, config.datasets)
    writer.write(_build_doc("20261111", 10.0))
    views.refresh_tables()
    writer.write(_build_doc("20261112", 11.0))
    writer.write(_build_doc("20261112", 12.0))  # rerun replaces the session
    rows = lake.query.sql("SELECT * FROM derived.holdings_positions ORDER BY trade_date, code")
    assert rows[["trade_date", "code"]].values.tolist() == [
        ["20261111", "A"],
        ["20261111", "CASH"],
        ["20261112", "A"],
        ["20261112", "CASH"],
    ]
    assert rows.loc[rows["trade_date"] == "20261112", "close"].dropna().tolist() == [12.0]
    risk = lake.query.sql(
        "SELECT component FROM derived.holdings_risk WHERE trade_date = '20261112'"
    )
    assert sorted(risk["component"]) == ["c:size", "factor", "total", "x:size"]
