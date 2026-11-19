"""Contract tests for calculation.FuturesBrokerNets (plan 15 ph7l)."""

from __future__ import annotations

from typing import Any, cast

import pandas as pd

from quant_cn.calculation.futures_broker_nets import FuturesBrokerNets
from quant_cn.core.futures_monitor_settings import FuturesMonitorSettings
from quant_cn.lake.lake_query import LakeQuery

DAYS = [f"202611{d:02d}" for d in range(1, 21)]
SETTINGS = FuturesMonitorSettings(
    families=[
        {"family": "CU.SHF", "name": "铜", "group": "有色"},
        {"family": "I.DCE", "name": "铁矿石", "group": "黑色"},
    ]
)


class RowsQuery:
    """Stands in for the aggregate query: per day and family code the summed long / short."""

    def __init__(self, rows: pd.DataFrame) -> None:
        self.rows = rows

    def sql(self, query: str, params: Any = None) -> pd.DataFrame:
        return self.rows

    def has_view(self, name: str) -> bool:
        return not self.rows.empty


def _build_rows(last_long: float) -> pd.DataFrame:
    cu = [("SHFE", "CU", d, 10000.0 + 100 * i, 10000.0) for i, d in enumerate(DAYS)]
    cu[-1] = ("SHFE", "CU", DAYS[-1], last_long, 10000.0)
    other = [("DCE", "CU", d, 99999.0, 0.0) for d in DAYS]  # same code, wrong exchange
    return pd.DataFrame(cu + other, columns=["exchange", "code", "trade_date", "long", "short"])


def test_tc_fbn_001_metrics() -> None:
    """TC-FBN-001"""
    out = FuturesBrokerNets(SETTINGS, cast(LakeQuery, RowsQuery(_build_rows(13000.0)))).build(
        "20210101"
    )
    cu = out["CU.SHF"]
    assert set(out) == {"CU.SHF"}  # no 铁矿石 rows; the DCE "CU" rows are ignored
    assert cu["net"] == 3000.0 and cu["gross"] == 23000.0
    assert cu["net_share"] == round(3000 / 23000, 4) and cu["net_share_pct_5y"] == 1.0
    assert cu["net_share_chg_5d"] == round(3000 / 23000 - 1400 / 21400, 4)


def test_tc_fbn_002_flags() -> None:
    """TC-FBN-002"""
    nets = FuturesBrokerNets(SETTINGS, cast(LakeQuery, RowsQuery(_build_rows(13000.0))))
    m = nets.build("20210101")["CU.SHF"]
    assert nets.list_flags("CU.SHF", "铜", m)[0]["message"].endswith("偏多到 5 年最高")
    assert nets.list_flags("CU.SHF", "铜", m | {"gross": 100.0}) == []
    assert nets.list_flags("CU.SHF", "铜", m | {"net_share_pct_5y": 0.9}) == []
    assert "偏空" in nets.list_flags("CU.SHF", "铜", m | {"net_share_pct_5y": 0.05})[0]["message"]


def test_tc_fbn_003_no_view() -> None:
    """TC-FBN-003"""
    nets = FuturesBrokerNets(SETTINGS, cast(LakeQuery, RowsQuery(pd.DataFrame())))
    assert nets.build("20210101") == {}
