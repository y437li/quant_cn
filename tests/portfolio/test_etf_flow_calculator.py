"""Contract tests for portfolio.EtfFlowCalculator (plan 15 phase 7b, D-126)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.core.etf_proxy_settings import EtfProxyIndex, EtfProxySettings
from quant_cn.portfolio.etf_flow_calculator import EtfFlowCalculator

CORE, OTHER, FEEDER, BOND = "510300.SH", "159925.SZ", "000051.OF", "511010.SH"
D1, D2, D3, D4 = "20260105", "20260106", "20260107", "20260112"  # D4 in the next ISO week
SETTINGS = EtfProxySettings(
    start=D1,
    core=[CORE],
    indices=[EtfProxyIndex(name="沪深300", benchmark="沪深300指数", reference=CORE)],
    recent_days=2,
)
_SETTINGS_X = EtfProxySettings(indices=[EtfProxyIndex(name="X", benchmark="x", reference="A")])
MEMBERS = pd.DataFrame({"ts_code": ["A"], "index": ["X"], "is_core": [True]})


def _compute(
    prices: list[tuple[str, float, float]], shares: list[tuple[str, float]]
) -> pd.DataFrame:
    px = pd.DataFrame(
        [("A", d, c, p) for d, c, p in prices],
        columns=["ts_code", "trade_date", "close", "pre_close"],
    )
    sh = pd.DataFrame(
        [("A", d, s) for d, s in shares], columns=["ts_code", "trade_date", "fd_share"]
    )
    return EtfFlowCalculator(_SETTINGS_X).compute_daily(px, sh, MEMBERS).set_index("trade_date")


# TC-EFC-001
def test_tc_efc_001_flow_formula() -> None:
    out = _compute(
        [(D1, 1.0, 1.0), (D2, 1.1, 1.0), (D3, 1.1, 1.1)], [(D1, 1e4), (D2, 1e4), (D3, 2e4)]
    )
    assert math.isnan(out.at[D1, "flow"])
    assert out.at[D2, "flow"] == pytest.approx(0.0)
    assert out.at[D3, "flow"] == pytest.approx(1.1)  # 1 亿份 more at 1.1 元
    assert out.at[D3, "aum"] == pytest.approx(2.2)


# TC-EFC-002
def test_tc_efc_002_split_day() -> None:
    out = _compute([(D1, 1.0, 1.0), (D2, 0.55, 0.5)], [(D1, 1e4), (D2, 2e4)])
    assert out.at[D2, "flow"] == pytest.approx(0.0)


# TC-EFC-003
def test_tc_efc_003_missing_share_day() -> None:
    out = _compute([(D1, 1.0, 1.0), (D2, 1.1, 1.0), (D3, 1.21, 1.1)], [(D1, 1e4), (D3, 1e4)])
    assert math.isnan(out.at[D2, "flow"])
    assert out.at[D2, "aum"] == pytest.approx(1.1)  # shares carried forward for the position
    assert out.at[D3, "flow"] == pytest.approx(0.0)


# TC-EFC-004
def test_tc_efc_004_position_at_today_price() -> None:
    out = _compute(
        [(D1, 1.0, 1.0), (D2, 1.2, 1.0), (D3, 0.9, 1.2)], [(D1, 1e4), (D2, 1e4), (D3, 1e4)]
    )
    assert out["position"].tolist() == pytest.approx([0.9, 0.9, 0.9])


# TC-EFC-005
def test_tc_efc_005_members() -> None:
    settings = SETTINGS.model_copy(
        update={
            "indices": [
                EtfProxyIndex(name="中证A500", benchmark="中证A500", reference="X"),
                EtfProxyIndex(name="沪深300", benchmark="300", reference=CORE),
            ]
        }
    )
    funds = pd.DataFrame(
        [
            (CORE, "沪深300ETF", "沪深300指数\u00d7100%"),
            ("563360.SH", "A500ETF", "中证A500指数收益率\u00d7100%"),  # also has "500", A500 first
            (FEEDER, "沪深300ETF联接A", "沪深300指数\u00d795%"),
            ("159673.SZ", "沪深300增强ETF", "沪深300指数\u00d7100%"),
            ("515330.SH", "300价值ETF", "沪深300指数\u00d795%+活期\u00d75%"),
            (BOND, "国债ETF", "上证5年期国债指数\u00d7100%"),
        ],
        columns=["ts_code", "name", "benchmark"],
    )
    out = EtfFlowCalculator(settings).build_members(funds)
    assert out.to_dict("records") == [
        {"ts_code": CORE, "index": "沪深300", "is_core": True},
        {"ts_code": "563360.SH", "index": "中证A500", "is_core": False},
    ]


# TC-EFC-006
def test_tc_efc_006_exclude() -> None:
    settings = SETTINGS.model_copy(
        update={
            "indices": [EtfProxyIndex(name="红利", benchmark="红利", exclude="港股", reference="X")]
        }
    )
    funds = pd.DataFrame(
        [
            ("510880.SH", "红利ETF", "上证红利指数\u00d7100%"),
            ("513690.SH", "港股通红利ETF", "恒生港股通红利指数\u00d7100%"),
        ],
        columns=["ts_code", "name", "benchmark"],
    )
    assert EtfFlowCalculator(settings).build_members(funds)["ts_code"].tolist() == ["510880.SH"]
