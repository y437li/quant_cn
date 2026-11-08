from __future__ import annotations

import numpy as np
import pytest

from quant_cn.statistic.hac_variance import HacVariance


def build_ar1(phi: float, n: int, rng: np.random.Generator) -> np.ndarray:
    e = rng.standard_normal(n + 200)
    x = np.empty_like(e)
    x[0] = e[0]
    for t in range(1, len(e)):
        x[t] = phi * x[t - 1] + e[t]
    return x[200:]


# TC-HAC-001
def test_tc_hac_001_lag_rule() -> None:
    hac = HacVariance()
    assert hac.compute_lag(500, 1) == 5  # floor(4 * 5**(2/9)) = floor(5.72)
    assert hac.compute_lag(500, 20) == 19
    assert HacVariance(fixed_lag=3).compute_lag(500, 20) == 3


# TC-HAC-002
def test_tc_hac_002_lag_zero() -> None:
    x = np.random.default_rng(1).standard_normal(300)
    assert HacVariance().compute_long_run_variance(x, 0) == pytest.approx(x.var())


# TC-HAC-003
@pytest.mark.parametrize("phi", [0.3, 0.6])
def test_tc_hac_003_ar1_coverage(phi: float) -> None:
    rng = np.random.default_rng(20260930)
    hac, n, sims = HacVariance(), 1000, 1000
    nw_cover = naive_cover = 0
    for _ in range(sims):
        x = build_ar1(phi, n, rng)  # true mean 0
        res = hac.compute_t(x)
        nw_cover += abs(res["t"]) <= 1.962
        naive_cover += abs(x.mean() / (x.std(ddof=1) / np.sqrt(n))) <= 1.962
    nw_rate, naive_rate = nw_cover / sims, naive_cover / sims
    assert naive_rate < 0.90  # the naive t ignores autocorrelation and over-rejects
    assert abs(nw_rate - 0.95) <= 0.02


# TC-HAC-004
def test_tc_hac_004_too_short() -> None:
    with pytest.raises(ValueError):
        HacVariance().compute_t([0.1, float("nan"), 0.2])
    with pytest.raises(ValueError):
        HacVariance(fixed_lag=-1)


# TC-HAC-005
def test_tc_hac_005_overlapping_ma() -> None:
    rng = np.random.default_rng(7)
    hac, h, n, cover = HacVariance(), 20, 1000, 0
    for _ in range(500):
        e = rng.standard_normal(n + h)
        x = np.convolve(e, np.ones(h), "valid")[:n]  # 20-session overlapping sums: MA(19)
        cover += abs(hac.compute_t(x, horizon=h)["t"]) <= 1.962
    assert cover / 500 >= 0.93
