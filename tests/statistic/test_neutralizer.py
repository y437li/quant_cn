from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from quant_cn.statistic.neutralizer import Neutralizer


def build_frame(n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    industry = np.array(["bank", "tech", "food"])[np.arange(n) % 3]
    size = rng.standard_normal(n)
    value = (industry == "tech") * 2.0 + 0.5 * size + rng.standard_normal(n)
    return pd.DataFrame(
        {"trade_date": "d1", "value": value, "industry": industry, "log_mcap": size}
    )


# TC-NEU-001
def test_tc_neu_001_orthogonal() -> None:
    out = Neutralizer().compute(build_frame(), categorical=["industry"], numeric=["log_mcap"])
    frame = build_frame()
    assert float(np.dot(out["value"], frame["log_mcap"])) == pytest.approx(0.0, abs=1e-9)
    for level in ("bank", "tech", "food"):
        assert out.loc[frame["industry"] == level, "value"].sum() == pytest.approx(0.0, abs=1e-9)


# TC-NEU-002
def test_tc_neu_002_missing_and_effect() -> None:
    frame = build_frame()
    frame.loc[0, "log_mcap"] = np.nan
    out = Neutralizer().compute(frame, categorical=["industry"], numeric=["log_mcap"])
    assert math.isnan(out["value"].iloc[0])
    tech_mean = out.loc[frame["industry"] == "tech", "value"].mean()
    assert abs(tech_mean) < 1e-9  # the +2 industry effect is gone
