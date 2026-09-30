from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from quant_cn.statistic.standardizer import Standardizer


# TC-STD-001
def test_tc_std_001_zscore() -> None:
    frame = pd.DataFrame(
        {"trade_date": ["a"] * 4 + ["b"] * 3, "value": [1.0, 2.0, 3.0, 4.0, 10.0, 20.0, np.nan]}
    )
    out = Standardizer().compute(frame)
    for _, part in out.dropna().groupby("trade_date"):
        assert part["value"].mean() == pytest.approx(0.0) and part["value"].std() == pytest.approx(
            1.0
        )
    assert math.isnan(out["value"].iloc[6])


# TC-STD-002
def test_tc_std_002_weights_and_constant() -> None:
    frame = pd.DataFrame({"trade_date": "a", "value": [0.0, 10.0], "w": [3.0, 1.0]})
    out = Standardizer().compute(frame, weight_column="w")
    sd = np.std([0.0, 10.0], ddof=1)
    assert out["value"].tolist() == pytest.approx([-2.5 / sd, 7.5 / sd])  # weighted mean 2.5
    flat = Standardizer().compute(pd.DataFrame({"trade_date": "a", "value": [1.0, 1.0]}))
    assert flat["value"].isna().all()
