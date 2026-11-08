from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from quant_cn.calculation.futures_positioning import FuturesPositioning

DAILY = pd.DataFrame(
    {
        "ts_code": [
            "IF2610.CFX",
            "IF2612.CFX",
            "IF2610.CFX",
            "IF2612.CFX",
            "IF2610.CFX",
            "IF2612.CFX",
            "IM2610.CFX",
        ],
        "trade_date": [
            "20260923",
            "20260923",
            "20260924",
            "20260924",
            "20260928",
            "20260928",
            "20260928",
        ],
        "close": [4500.0, 4450.0, 4400.0, 4350.0, 4420.0, 4380.0, 7000.0],
        "oi": [50000.0, 170000.0, 52000.0, 175000.0, 51000.0, 172000.0, 99999.0],
    }
)
HOLDING = pd.DataFrame(
    {
        "trade_date": ["20260928"] * 4,
        "symbol": ["IF2610", "IF2612", "IF2612", "IM2610"],
        "broker": ["A", "A", "B", "A"],
        "long_hld": [100.0, 200.0, 50.0, 999.0],
        "short_hld": [300.0, 100.0, 80.0, 1.0],
        "long_chg": [1.0, 2.0, 3.0, 4.0],
        "short_chg": [5.0, 6.0, 7.0, 8.0],
    }
)
SPOT = pd.Series({"20260923": 4510.0, "20260924": 4439.0, "20260928": 4340.0})


# TC-FP-001
def test_tc_fp_001_regimes() -> None:
    out = FuturesPositioning("IF").compute(DAILY, HOLDING, SPOT)
    assert out["regime"].tolist() == ["unclear", "new_shorts", "short_covering"]


# TC-FP-002
def test_tc_fp_002_top20() -> None:
    out = FuturesPositioning("IF").compute(DAILY, HOLDING, SPOT).set_index("trade_date")
    assert out.at["20260928", "top20_net"] == (100 + 200 + 50) - (300 + 100 + 80)
    assert pd.isna(out.at["20260923", "top20_net"])


# TC-FP-003
def test_tc_fp_003_basis() -> None:
    fp = FuturesPositioning("IF")
    out = fp.compute(DAILY, HOLDING, SPOT).set_index("trade_date")
    assert out.at["20260928", "main_contract"] == "IF2612"
    assert out.at["20260928", "basis_pct"] == pytest.approx((4380 / 4340 - 1) * 100)
    assert fp.get_expiry("IF2612") == dt.date(2026, 12, 18)
    years = (dt.date(2026, 12, 18) - dt.date(2026, 9, 28)).days / 365
    assert out.at["20260928", "basis_annualised"] == pytest.approx((4380 / 4340 - 1) * 100 / years)


# TC-FP-004
def test_tc_fp_004_brokers() -> None:
    brokers = FuturesPositioning("IF").list_brokers(HOLDING, "20260928")
    assert brokers["broker"].tolist() == ["A", "B"] and brokers["net"].tolist() == [-100.0, -30.0]
    with pytest.raises(ValueError):
        FuturesPositioning("IF").get_expiry("bad")
