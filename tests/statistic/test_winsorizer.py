from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from quant_cn.statistic.winsorizer import Winsorizer


def build_frame() -> pd.DataFrame:
    values = [1.0, 2.0, 3.0, 4.0, 100.0, np.nan]
    return pd.DataFrame({"trade_date": "d1", "value": values})


# TC-WZ-001
def test_tc_wz_001_mad() -> None:
    out = Winsorizer(k=2.0).compute(build_frame())
    med, mad = 3.0, 1.0 * 1.4826  # |x - 3| = 2,1,0,1,97 -> median 1
    assert out["value"].iloc[4] == pytest.approx(med + 2 * mad)
    assert out["value"].iloc[:4].tolist() == [1.0, 2.0, 3.0, 4.0] and math.isnan(
        out["value"].iloc[5]
    )
    with pytest.raises(ValueError):
        Winsorizer(k=0)


# TC-WZ-002
def test_tc_wz_002_quantile() -> None:
    frame = pd.DataFrame({"trade_date": "d1", "value": np.arange(101, dtype=float)})
    out = Winsorizer(method="quantile", q=0.05).compute(frame)
    assert out["value"].min() == pytest.approx(5.0) and out["value"].max() == pytest.approx(95.0)
