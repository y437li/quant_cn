"""Tests of EwmWindow."""

from __future__ import annotations

import numpy as np
import pytest

from quant_cn.risk.ewm_window import EwmWindow


# TC-EW-001
def test_tc_ew_001_weights_halve_and_lag() -> None:
    w = EwmWindow(10, 2.0).weights
    assert w.sum() == pytest.approx(1.0)
    assert w[2] / w[0] == pytest.approx(0.5)
    x = np.arange(12, dtype=float)
    lagged = EwmWindow(3, np.inf, lag=2).compute_sum(x)
    assert lagged[11] == pytest.approx(np.mean([7.0, 8.0, 9.0]))


# TC-EW-002
def test_tc_ew_002_sum_matches_explicit_window() -> None:
    rng = np.random.default_rng(0)
    x = rng.standard_normal((40, 3))
    x[5, 1] = np.nan
    window = EwmWindow(8, 3.0)
    out = window.compute_sum(x)
    w = window.weights
    clean = np.nan_to_num(x)
    for t in (7, 20, 39):
        expected = (w[:, None] * clean[t - np.arange(8)]).sum(axis=0)
        np.testing.assert_allclose(out[t], expected, rtol=1e-12, atol=1e-14)
    np.testing.assert_allclose(out[0], w[0] * clean[0])


# TC-EW-003
def test_tc_ew_003_count_and_bad_parameters() -> None:
    valid = np.array([1, 1, 0, 1, 1, 1], dtype=bool)
    np.testing.assert_array_equal(EwmWindow(3, 1.0).compute_count(valid), [1, 2, 2, 2, 2, 3])
    for args in ((0, 1.0, 0), (3, 0.0, 0), (3, 1.0, -1)):
        with pytest.raises(ValueError):
            EwmWindow(*args)
