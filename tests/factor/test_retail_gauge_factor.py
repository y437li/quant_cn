"""Contract tests for factor.library.RetailGaugeFactor (plan 21 ph6)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.factor.base_factor import FactorInputs
from quant_cn.factor.library.retail_gauge_factor import RetailGaugeFactor

A, B = "000001.SZ", "600000.SH"
DAYS = ["20260102", "20260105", "20260202", "20260216", "20260217"]


def _build_inputs(readings: list[tuple[str, str, float]]) -> FactorInputs:
    prices = pd.DataFrame([{"trade_date": d, "ts_code": c} for d in DAYS for c in (A, B)])
    gauge = pd.DataFrame(readings, columns=["as_of", "ts_code", "pct"])
    return FactorInputs(prices=prices, retail_gauge=gauge)


def _get(out: pd.DataFrame, day: str, code: str) -> float:
    row = out[(out["trade_date"] == day) & (out["ts_code"] == code)]
    return float(row["value_raw"].iloc[0])


# TC-RGFA-001
def test_tc_rgfa_001_latest_reading() -> None:
    early = [("20260102", A, 0.2)]
    later = [*early, ("20260202", A, 0.9)]
    first = RetailGaugeFactor("g").compute_raw(_build_inputs(early))
    second = RetailGaugeFactor("g").compute_raw(_build_inputs(later))
    assert _get(first, "20260105", A) == pytest.approx(-0.2)
    assert _get(second, "20260105", A) == pytest.approx(-0.2)  # a later reading changes nothing
    assert _get(second, "20260202", A) == pytest.approx(-0.9)
    assert math.isnan(_get(second, "20260202", B))


# TC-RGFA-002
def test_tc_rgfa_002_max_age() -> None:
    out = RetailGaugeFactor("g", max_age_days=45).compute_raw(_build_inputs([("20260102", A, 0.5)]))
    assert _get(out, "20260216", A) == pytest.approx(-0.5)  # 45 days old
    assert math.isnan(_get(out, "20260217", A))  # 46 days
    empty = RetailGaugeFactor("g").compute_raw(FactorInputs(prices=_build_inputs([]).prices))
    assert empty["value_raw"].isna().all()
    with pytest.raises(ValueError):
        RetailGaugeFactor("g", max_age_days=0)
