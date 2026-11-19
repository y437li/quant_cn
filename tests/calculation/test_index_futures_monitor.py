"""Contract tests for calculation.IndexFuturesMonitor (plan 15 ph7k)."""

from __future__ import annotations

from typing import Any, cast

import pandas as pd

from quant_cn.calculation.index_futures_monitor import IndexFuturesMonitor
from quant_cn.core.futures_monitor_settings import FuturesMonitorSettings
from quant_cn.lake.lake_query import LakeQuery

SETTINGS = FuturesMonitorSettings(
    index_futures=[{"product": "IF", "name": "沪深300", "index": "000300.SH"}]
)


class EmptyQuery:
    def sql(self, query: str, params: Any = None) -> pd.DataFrame:
        return pd.DataFrame(columns=["ts_code", "trade_date", "close", "oi"])

    def has_view(self, name: str) -> bool:
        return True


def _build_frame(last_basis: float, n: int = 20) -> pd.DataFrame:
    days = [f"202610{d:02d}" for d in range(1, n + 1)]
    basis = [-5.0 - i * 0.1 for i in range(n - 1)] + [last_basis]  # falling: deeper discount
    return pd.DataFrame(
        {
            "trade_date": days,
            "main_contract": "IF2612",
            "price": 3950.0,
            "spot": 4000.0,
            "basis_pct": -1.25,
            "basis_annualised": basis,
            "top20_net": [-20000.0 + 100 * i for i in range(n)],
            "oi_total": [200000.0 + 1000 * i for i in range(n)],
            "regime": "new_shorts",
        }
    )


def _build_monitor() -> IndexFuturesMonitor:
    return IndexFuturesMonitor(SETTINGS, cast(LakeQuery, EmptyQuery()))


def test_tc_ifm_001_summary() -> None:
    """TC-IFM-001"""
    row = _build_monitor().build_product("IF", "沪深300", "000300.SH", _build_frame(-7.0))
    assert row["as_of"] == "20261020" and row["basis_annualised"] == -7.0
    assert row["basis_pct_5y"] == 0.05  # 1 of 20 values <= -7.0 (itself)
    assert row["net"] == -18100.0 and row["net_chg_5d"] == 500.0 and row["net_pct_5y"] == 1.0
    assert row["oi_chg_5d"] == round(219000 / 214000 - 1, 4)
    assert len(row["history"]) == 4 and row["history"][-1]["d"] == "20261020"


def test_tc_ifm_002_flags_and_missing() -> None:
    """TC-IFM-002"""
    m = _build_monitor()
    at = m.list_flags(m.build_product("IF", "沪深300", "000300.SH", _build_frame(-7.0)))
    assert {f["key"] for f in at} == {"basis:IF", "net:IF"}  # 5th pct and 100th pct
    inside = _build_frame(-6.75)  # -6.8 and itself <= latest: 10th pct
    keys = {f["key"] for f in m.list_flags(m.build_product("IF", "x", "y", inside))}
    assert "basis:IF" not in keys
    assert m.build("20210101") == {"products": [], "flags": [], "missing": ["IF"]}
