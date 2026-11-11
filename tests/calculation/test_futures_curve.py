from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.calculation.futures_curve import CurveSummary, FuturesCurve

CONTRACTS = pd.DataFrame(
    {
        "ts_code": ["AL2611.SHF", "AL2612.SHF", "AL2705.SHF", "AL2711.SHF", "AL2610.SHF",
                    "LC2701.GFE", "LC2707.GFE", "SA2701.ZCE"],
        "fut_code": ["AL", "AL", "AL", "AL", "AL", "LC", "LC", "SA"],
        "exchange": ["SHFE", "SHFE", "SHFE", "SHFE", "SHFE", "GFEX", "GFEX", "CZCE"],
        "d_month": ["202611", "202612", "202705", "202711", "202610", "202701", "202707", "202701"],
    }
)  # fmt: skip
QUOTES = pd.DataFrame(
    {
        "ts_code": ["AL2611.SHF", "AL2612.SHF", "AL2705.SHF", "AL2711.SHF", "AL2610.SHF",
                    "LC2701.GFE", "LC2707.GFE", "SA2701.ZCE", "CU2612.SHF"],
        "trade_date": ["20261106"] * 9,
        "settle": [23355.0, 23080.0, 22795.0, None, 23500.0, 92000.0, 92500.0, 1300.0, 80000.0],
        "close": [23335.0, 23030.0, 22685.0, 22500.0, 23490.0, 91800.0, 92400.0, 1290.0, 80100.0],
        "oi": [20840.0, 227071.0, 19956.0, 3000.0, 0.0, 150000.0, 40000.0, 9000.0, 1.0],
        "vol": [8965.0, 207059.0, 4680.0, 100.0, 0.0, 50000.0, 9000.0, 3000.0, 1.0],
    }
)  # fmt: skip
MATERIALS = {
    "MAT_ALUMINUM": ["AL.SHF"],
    "MAT_LITHIUM_CARBONATE": ["LC.GFE"],
    "MAT_STEEL": ["RB.SHF", "HC.SHF"],
}


def build() -> FuturesCurve:
    return FuturesCurve(CONTRACTS, MATERIALS)


# TC-FCV-001
def test_tc_fcv_001_curve_rows() -> None:
    curve = build().build_curve(QUOTES, "AL.SHF", "20261106")
    assert list(curve["ts_code"]) == ["AL2611.SHF", "AL2612.SHF", "AL2705.SHF", "AL2711.SHF"]
    assert list(curve["months_ahead"]) == [0, 1, 6, 12]
    assert curve["price"].tolist() == [23355.0, 23080.0, 22795.0, 22500.0]  # settle, else close
    assert "AL2610.SHF" not in set(curve["ts_code"])  # expired month dropped
    assert build().build_curve(QUOTES, "ZN.SHF", "20261106").empty
    odd = pd.concat(
        [
            CONTRACTS,
            pd.DataFrame(
                {"ts_code": ["AL.SHF"], "fut_code": ["AL"], "exchange": ["SHFE"], "d_month": [None]}
            ),
        ]
    )
    quotes = pd.concat([QUOTES, QUOTES.iloc[[0]].assign(ts_code="AL.SHF")])
    assert len(FuturesCurve(odd, MATERIALS).build_curve(quotes, "AL.SHF", "20261106")) == 4


# TC-FCV-002
def test_tc_fcv_002_summary_backwardation() -> None:
    fc = build()
    s = fc.compute_summary(fc.build_curve(QUOTES, "AL.SHF", "20261106"), "AL.SHF", "20261106")
    assert s == CurveSummary(
        family="AL.SHF", trade_date="20261106", n_contracts=4, front_month="202611",
        front_price=23355.0, dominant_month="202612", dominant_price=23080.0,
        price_6m=22795.0, price_12m=22500.0, last_month="202711", last_price=22500.0,
        slope_12m=pytest.approx(22500.0 / 23080.0 - 1), shape="backwardation",
    )  # fmt: skip


# TC-FCV-003
def test_tc_fcv_003_short_curve_and_flat() -> None:
    fc = build()
    s = fc.compute_summary(fc.build_curve(QUOTES, "LC.GFE", "20261106"), "LC.GFE", "20261106")
    assert s.price_6m is None and s.price_12m is None  # nearest months are 2 and 8 months out
    assert s.dominant_month == "202701" and s.slope_12m == pytest.approx(92500.0 / 92000.0 - 1)
    assert s.shape == "flat"  # +0.5% from the most-held month
    empty = fc.compute_summary(fc.build_curve(QUOTES, "ZN.SHF", "20261106"), "ZN.SHF", "20261106")
    assert empty.n_contracts == 0 and empty.front_price is None and empty.shape == "none"


# TC-FCV-004
def test_tc_fcv_004_materials() -> None:
    fc = build()
    assert fc.list_families("MAT_STEEL") == ["RB.SHF", "HC.SHF"] and fc.list_families("MAT_X") == []
    summaries = fc.list_material_summaries(QUOTES, "MAT_ALUMINUM", "20261106")
    assert [s.family for s in summaries] == ["AL.SHF"] and summaries[0].n_contracts == 4


# TC-FCV-005
def test_tc_fcv_005_errors() -> None:
    with pytest.raises(ValueError):
        FuturesCurve(CONTRACTS.drop(columns=["d_month"]), MATERIALS)
    with pytest.raises(ValueError):
        build().build_curve(QUOTES, "AL", "20261106")  # family needs <code>.<suffix>
    with pytest.raises(ValueError):
        build().build_curve(QUOTES.drop(columns=["oi"]), "AL.SHF", "20261106")


# TC-FCV-006
def test_tc_fcv_006_dominant_series() -> None:
    later = QUOTES.assign(trade_date="20261201", oi=[1.0, 5.0, 900.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0])
    series = build().build_dominant_series(pd.concat([QUOTES, later]), "AL.SHF")
    assert list(series["trade_date"]) == ["20261106", "20261201"]
    assert list(series["ts_code"]) == ["AL2612.SHF", "AL2705.SHF"]
    assert series["price"].tolist() == [23080.0, 22795.0]
