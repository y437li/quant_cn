from __future__ import annotations

import math

import pytest

from quant_cn.calculation.term_interpolator import TermInterpolator

N365, N30 = 525600, 43200


# TC-TI-001
def test_tc_ti_001_equal_variances() -> None:
    assert TermInterpolator().compute(0.04, 26 * 1440, 0.04, 61 * 1440, N30, N365) == pytest.approx(
        20.0
    )


# TC-TI-002
def test_tc_ti_002_edges() -> None:
    near = TermInterpolator().compute(0.09, N30, 0.04, 61 * 1440, N30, N365)
    assert near == pytest.approx(100 * math.sqrt(0.09))
    with pytest.raises(ValueError):
        TermInterpolator().compute(0.04, N30, 0.04, N30, N30, N365)
    with pytest.raises(ValueError):
        TermInterpolator().compute(-1.0, 26 * 1440, 0.0, 61 * 1440, N30, N365)
