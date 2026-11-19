"""Contract tests for calculation.RetailGaugeMatrices (plan 21 ph2, D-142)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from quant_cn.calculation.retail_gauge_matrices import RetailGaugeMatrices
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings

DAYS = [f"202501{d:02d}" for d in range(1, 12)]  # 11 sessions; the last one is "after b"
SETTINGS = RetailGaugeSettings(
    windows=[2],
    halflives=[2],
    trel_window=3,
    trel_min=2,
    slope_window=3,
    edge_sessions=2,
    year_back=5,
    half_year=3,
    top_turnover_days=2,
    min_window_sessions=3,
)


def build_frames(shock: float = 1.0) -> dict[str, pd.DataFrame]:
    px = [10, 10, 10, 10, 11, 12, 11, 11.5, 12, 13, 13 * shock]
    tov = [1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 9 * shock]
    lg = [1, 1, 1, 1, 1, -1, -1, -1, 1, 1, -50 * shock]
    rz = [100, 100, 100, 100, np.nan, 100, 100, 100, 100, 120, 500 * shock]

    def frame(x: list[float], y: float) -> pd.DataFrame:
        return pd.DataFrame({"X": [float(v) for v in x], "Y": [y] * len(x)}, index=DAYS)

    return {
        "px": frame(px, 10.0),
        "tov": frame(tov, 1.0),
        "cmv": frame([100.0] * 11, 100.0),
        "lg": frame(lg, 0.0),
        "elg": frame([0.0] * 11, 0.0),
        "sm": frame([0.0] * 11, 0.0),
        "rz": frame(rz, 50.0),
    }


# TC-RGM-001
def test_tc_rgm_001_path() -> None:
    m = RetailGaugeMatrices(SETTINGS, build_frames())
    f = m.compute_path("20250103", "20250110").loc["X"]
    assert f["ret_q"] == pytest.approx(math.log(13 / 10))
    assert f["dd_qhigh"] == pytest.approx(0.0)
    assert (f["n_bigup"], f["n_bigdn"]) == (3, 1)
    assert f["tov_acc"] == pytest.approx(math.log(4.0))
    assert f["big_cum"] == pytest.approx(0.01)  # 1+1-1-1-1+1+1 over a cap of 100
    assert (f["out_maxrun"], f["lg_inrun"]) == (3, 2)
    assert f["mchg"] == pytest.approx(0.2)
    assert m.compute_path("20250108", "20250110").empty  # 2 sessions < 3


# TC-RGM-002
def test_tc_rgm_002_scale_pit() -> None:
    m = RetailGaugeMatrices(SETTINGS, build_frames())
    f = m.compute_scale("20250110").loc["X"]
    assert f["ret_2"] == pytest.approx(math.log(13 / 11.5))
    assert f["lg_2"] == pytest.approx(0.02)
    assert f["rz_2"] == pytest.approx(math.log(1.2))
    assert f["tov_slope3"] == pytest.approx(math.log(4 / 3) / 2)
    shocked = RetailGaugeMatrices(SETTINGS, build_frames(shock=7.0))
    pd.testing.assert_frame_equal(shocked.compute_scale("20250110"), m.compute_scale("20250110"))
    pd.testing.assert_frame_equal(
        shocked.compute_path("20250103", "20250110"), m.compute_path("20250103", "20250110")
    )
