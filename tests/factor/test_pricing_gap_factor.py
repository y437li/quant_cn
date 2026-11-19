"""Contract tests for factor.library.PricingGapFactor (plan 36, D-173)."""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd
import pytest

from quant_cn.factor.base_factor import FactorInputs
from quant_cn.factor.library.pricing_gap_factor import PricingGapFactor


def compute_reference(f1: float, f2: float, f3: float, t: float) -> float:
    """The research formula (pricing_gap_factor.py run 20261118) written out."""
    r, v = 1.09, f1 / 1.09**t + f2 / 1.09 ** (t + 1) + f3 / 1.09 ** (t + 2)
    g, x = min(max(f3 / f2 - 1, -0.3), 1.0), f3
    for k in range(1, 8):
        g *= 0.7
        x *= 1 + g
        v += x / r ** (t + 2 + k)
    return v + 15 * x / r ** (t + 9)


# TC-LPG-001
def test_tc_lpg_001_value() -> None:
    f = PricingGapFactor("pricing_gap")
    arr = np.array
    got = f.compute_value(arr([100.0]), arr([120.0]), arr([144.0]), arr([0.5]))
    assert got[0] == pytest.approx(compute_reference(100, 120, 144, 0.5))
    filled = f.compute_value(arr([100.0]), arr([120.0]), arr([np.nan]), arr([0.5]))
    assert filled[0] == pytest.approx(got[0])  # FY3 = 120 x 120 / 100 = 144
    clipped = f.compute_value(arr([10.0]), arr([10.0]), arr([50.0]), arr([0.0]))
    assert clipped[0] == pytest.approx(
        compute_reference(10, 10, 50, 0.1)
    )  # +400% clipped, t floored
    bad = f.compute_value(arr([-1.0, 10.0]), arr([5.0, 0.0]), arr([6.0, 6.0]), arr([0.5, 0.5]))
    assert np.isnan(bad).all()


# TC-LPG-002
def test_tc_lpg_002_raw_pit() -> None:
    basic = pd.DataFrame({
        "trade_date": ["20260630", "20260701", "20260731", "20260803"],
        "ts_code": ["A"] * 4, "total_mv": [1000.0] * 4,
    })  # fmt: skip
    cons = pd.DataFrame({
        "trade_date": ["20260630", "20260731"], "ts_code": ["A", "A"], "fy1": [2026, 2026],
        "np1": [100.0, 50.0], "np2": [120.0, 60.0], "np3": [144.0, 72.0], "n_brokers": [3, 3],
    })  # fmt: skip
    f = PricingGapFactor("pricing_gap")
    out = f.compute_raw(FactorInputs(prices=pd.DataFrame(), daily_basic=basic, consensus=cons))
    out = out.set_index("trade_date")["value_raw"]
    t = (dt.date(2026, 12, 31) - dt.date(2026, 7, 1)).days / 365.25
    assert out["20260701"] == pytest.approx(-math.log(1000 / compute_reference(100, 120, 144, t)))
    assert out["20260803"] < out["20260701"]  # the July reading halved the consensus: dearer
    cut = f.compute_raw(FactorInputs(prices=pd.DataFrame(), daily_basic=basic, consensus=cons[:1]))
    assert cut.set_index("trade_date")["value_raw"]["20260701"] == pytest.approx(out["20260701"])
    mixed = basic.assign(ts_code=basic["ts_code"].astype(pd.StringDtype(na_value=np.nan)))
    cons_na = cons.assign(ts_code=cons["ts_code"].astype(pd.StringDtype()))
    same = f.compute_raw(FactorInputs(prices=pd.DataFrame(), daily_basic=mixed, consensus=cons_na))
    assert same["value_raw"].tolist() == pytest.approx(out.tolist())  # lake string dtypes differ
    empty = f.compute_raw(FactorInputs(prices=pd.DataFrame(), daily_basic=basic))
    assert empty.empty


# TC-LPG-003
def test_tc_lpg_003_params() -> None:
    assert PricingGapFactor("x", window_days=60).consensus_days == 60
    with pytest.raises(ValueError):
        PricingGapFactor("x", fade=0.0)
    with pytest.raises(ValueError):
        PricingGapFactor("x", exit_pe=-1.0)
    with pytest.raises(ValueError):
        PricingGapFactor("x", growth_floor=1.0)
    with pytest.raises(ValueError):
        PricingGapFactor("x", window_days=0)
