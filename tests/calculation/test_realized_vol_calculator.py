"""Contract tests for calculation.RealizedVolCalculator (plans 30 and 31)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from quant_cn.calculation.realized_vol_calculator import RealizedVolCalculator


# TC-RVC-001
def test_tc_rvc_001_vol() -> None:
    closes = pd.DataFrame({"A": [100.0, 101.0, 99.0, 102.0, 103.0]})
    vol = RealizedVolCalculator(10, 2).compute_vol(closes, 3)
    rets = np.log(closes["A"] / closes["A"].shift(1))
    expected = rets.iloc[1:4].std() * math.sqrt(252) * 100
    assert vol["A"].iloc[:3].isna().all()
    assert vol["A"].iloc[3] == pytest.approx(expected)


# TC-RVC-002
def test_tc_rvc_002_rank_pct() -> None:
    series = pd.Series([3.0, 1.0, np.nan, 2.0, 5.0])
    pct = RealizedVolCalculator(3, 2).compute_rank_pct(series)
    assert math.isnan(pct.iloc[0]) and math.isnan(pct.iloc[2])
    assert pct.iloc[1] == pytest.approx(0.5)  # 1 of (3, 1) at or below 1
    assert pct.iloc[3] == pytest.approx(2 / 3)  # (3, 1, 2): 1 and 2 at or below 2
    assert pct.iloc[4] == pytest.approx(1.0)
