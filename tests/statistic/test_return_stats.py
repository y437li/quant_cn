from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from quant_cn.statistic.return_stats import ReturnStats


# TC-RS-001
def test_tc_rs_001_constant() -> None:
    out = ReturnStats().compute([0.01] * 10)
    assert out["sd"] == 0 and out["max_drawdown"] == 0 and math.isinf(out["sharpe"])
    assert out["ann_return"] == pytest.approx(0.01 * 244)
    with pytest.raises(ValueError):
        ReturnStats().compute([0.01])


# TC-RS-002
def test_tc_rs_002_drawdown_moments() -> None:
    assert ReturnStats().compute([0.2, -0.25])["max_drawdown"] == pytest.approx(-0.25)
    r = np.random.default_rng(1).standard_t(5, 500) / 100
    out = ReturnStats().compute(r, horizon=5)
    assert out["kurtosis"] == pytest.approx(stats.kurtosis(r, fisher=False))
    assert out["skew"] == pytest.approx(stats.skew(r))
    assert out["sharpe"] == pytest.approx(r.mean() / r.std(ddof=1) * math.sqrt(244 / 5))
