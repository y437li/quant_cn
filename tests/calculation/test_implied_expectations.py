from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.calculation.implied_expectations import ImpliedExpectations
from quant_cn.core.discovery_settings import DiscoverySettings

YI = 1e8


def build() -> ImpliedExpectations:
    return ImpliedExpectations(DiscoverySettings())


# TC-IE-001
def test_tc_ie_001_years() -> None:
    ie = build()
    # 5 years of 10 at 9%: annuity factor (1 - 1.09^-5) / 0.09
    factor = (1 - 1.09**-5) / 0.09
    assert ie.compute_years(100 + 10 * factor, 100, 10) == pytest.approx(5.0)
    assert ie.compute_years(90, 100, 10) == 0.0
    assert ie.compute_years(100 + 10 / 0.09 + 1, 100, 10) == 50.0  # more than a perpetuity
    assert math.isnan(ie.compute_years(200, 100, 0)) and math.isnan(
        ie.compute_years(math.nan, 100, 5)
    )


# TC-IE-002
def test_tc_ie_002_implied_growth() -> None:
    ie = build()
    value = ie._compute_value(10.0, 0.15)  # build a cap from a known growth
    assert ie.compute_implied_growth(value, 10.0) == pytest.approx(0.15, abs=1e-6)
    assert (
        ie.compute_implied_growth(1.0, 10.0) == -0.5 and ie.compute_implied_growth(1e9, 10.0) == 1.0
    )
    assert math.isnan(ie.compute_implied_growth(100.0, -1.0))


# TC-IE-003
def test_tc_ie_003_build() -> None:
    panel = pd.DataFrame(
        {"ts_code": ["A", "B", "C"], "np_ttm": [30 * YI, 5 * YI, 8 * YI],
         "np_dedt_ttm": [28 * YI, 5 * YI, 8 * YI], "np_med": [10 * YI, 6 * YI, 4 * YI]}
    )  # fmt: skip
    market = pd.DataFrame(
        {"ts_code": ["A", "B", "D"], "total_mv": [300 * YI, 60 * YI, 10 * YI],
         "pe_med": [20.0, None, 10.0], "precycle_mv": [150 * YI, None, None]}
    )  # fmt: skip
    out = build().build(panel, market).set_index("ts_code")
    assert list(out.index) == ["A", "B"]  # C has no market cap, D no panel row
    a = out.loc["A"]
    assert (
        a["base_normal"] == 120 * YI
        and a["base_own_pe"] == 200 * YI
        and a["base_precycle"] == 150 * YI
    )
    assert a["years_normal"] > a["years_precycle"] > a["years_own_pe"] > 0
    assert a["years_normal_dedt"] > a["years_normal"]  # smaller excess on deducted profit
    assert a["premium_normal"] == pytest.approx(300 / 120 - 1)
    b = out.loc["B"]
    assert math.isnan(b["years_normal"]) and math.isnan(b["years_own_pe"])  # profit below normal
    assert not math.isnan(b["implied_growth"])


# TC-IE-004
def test_tc_ie_004_missing_columns() -> None:
    with pytest.raises(ValueError):
        build().build(
            pd.DataFrame({"ts_code": ["A"]}), pd.DataFrame({"ts_code": ["A"], "total_mv": [1.0]})
        )
    with pytest.raises(ValueError):
        build().build(
            pd.DataFrame(
                {"ts_code": ["A"], "np_ttm": [1.0], "np_dedt_ttm": [1.0], "np_med": [1.0]}
            ),
            pd.DataFrame({"ts_code": ["A"]}),
        )


# TC-IE-005
def test_tc_ie_005_check_values() -> None:
    # 2026-11-06 inputs from the phase-1 panel and daily_basic (CNY 亿)
    rows = {"000807.SZ": (850.4, 132.7, 21.1, 7.6), "601600.SH": (1474.0, 197.2, 27.9, 10.8),
            "601919.SH": (2659.0, 344.5, 168.9, 4.5)}  # fmt: skip
    ie = build()
    for mv, ttm, med, years in rows.values():
        assert ie.compute_years(mv * YI, 12 * med * YI, (ttm - med) * YI) == pytest.approx(
            years, abs=0.15
        )


# TC-IE-006
def test_tc_ie_006_sensitivity() -> None:
    periods = [f"{y}{md}" for y in (2024, 2025, 2026) for md in ("0331", "0630", "0930", "1231")][
        :11
    ]
    price = [20000 + 500 * i for i in range(11)]
    quarters = pd.DataFrame({"period": periods, "np_q": [1e8 + 2e5 * (p - 20000) for p in price]})
    days = pd.DataFrame(
        {
            "trade_date": [
                p[:4] + {"0331": "0215", "0630": "0515", "0930": "0815", "1231": "1115"}[p[4:]]
                for p in periods
            ],
            "price": price,
        }
    )
    out = ImpliedExpectations.compute_sensitivity(quarters, days)
    assert (
        out["slope"] == pytest.approx(4 * 2e5)
        and out["r2"] == pytest.approx(1.0)
        and out["n"] == 11
    )
    assert math.isnan(ImpliedExpectations.compute_sensitivity(quarters.head(5), days)["slope"])
    noisy = quarters.assign(np_q=[1e8, -1e8] * 5 + [1e8])
    assert math.isnan(ImpliedExpectations.compute_sensitivity(noisy, days)["slope"])


# TC-IE-007
def test_tc_ie_007_implied_price() -> None:
    ie = build()
    # cap 1200, profit 50 at price 100, +1 profit per +1 price:
    # 12 x (50 + (p - 100)) = 1200 -> p = 150
    assert ie.compute_implied_price(1200.0, 50.0, 100.0, 1.0) == pytest.approx(150.0)
    assert math.isnan(ie.compute_implied_price(1200.0, 50.0, 100.0, 0.0))
