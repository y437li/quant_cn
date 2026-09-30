from __future__ import annotations

import numpy as np
import pytest

from quant_cn.statistic.block_bootstrap import BlockBootstrap


# TC-BB-001
def test_tc_bb_001_indices() -> None:
    a = BlockBootstrap(resamples=50, seed=3).build_indices(100, 20)
    b = BlockBootstrap(resamples=50, seed=3).build_indices(100, 20)
    assert a.shape == (50, 100) and a.min() >= 0 and a.max() < 100 and np.array_equal(a, b)
    with pytest.raises(ValueError):
        BlockBootstrap(resamples=0)


# TC-BB-002
def test_tc_bb_002_blocks() -> None:
    circ = BlockBootstrap(resamples=20, seed=1, method="circular").build_indices(50, 10)
    steps = np.diff(circ[:, :10], axis=1) % 50
    assert np.all(steps == 1)  # the first block is 10 consecutive (wrapping) positions
    stat = BlockBootstrap(resamples=200, seed=1).build_indices(1000, 20)
    breaks = np.mean((np.diff(stat, axis=1) % 1000) != 1)
    assert 1 / breaks == pytest.approx(20, rel=0.15)  # mean run length ~ b


# TC-BB-003
def test_tc_bb_003_ci_coverage() -> None:
    rng = np.random.default_rng(11)
    boot, cover, sims = BlockBootstrap(resamples=400, seed=5), 0, 200
    for _ in range(sims):
        e = rng.standard_normal(600)
        x = np.empty_like(e)
        x[0] = e[0]
        for t in range(1, len(e)):
            x[t] = 0.3 * x[t - 1] + e[t]
        res = boot.compute_interval(x[100:], np.mean, block=20)
        cover += res["ci_lo"] <= 0 <= res["ci_hi"]
    assert abs(cover / sims - 0.95) <= 0.04


# TC-BB-004
def test_tc_bb_004_block_rule() -> None:
    assert BlockBootstrap.compute_block(5) == 20 and BlockBootstrap.compute_block(60) == 60
