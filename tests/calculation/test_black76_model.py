from __future__ import annotations

import math

import pytest

from quant_cn.calculation.black76_model import Black76Model


# TC-BM-001
def test_tc_bm_001_parity() -> None:
    model = Black76Model()
    c = model.compute_price(3.04, 3.0, 0.2, 0.014, 0.2, "C")
    p = model.compute_price(3.04, 3.0, 0.2, 0.014, 0.2, "P")
    assert c - p == pytest.approx(math.exp(-0.014 * 0.2) * 0.04)


# TC-BM-002
@pytest.mark.parametrize("side", ["C", "P"])
def test_tc_bm_002_implied_vol(side: str) -> None:
    model = Black76Model()
    price = model.compute_price(3.04, 3.1, 0.3, 0.014, 0.27, side)  # type: ignore[arg-type]
    assert model.compute_implied_vol(price, 3.04, 3.1, 0.3, 0.014, side) == pytest.approx(
        0.27, abs=1e-6
    )  # type: ignore[arg-type]


# TC-BM-003
def test_tc_bm_003_out_of_bounds() -> None:
    with pytest.raises(ValueError):
        Black76Model().compute_implied_vol(10.0, 3.04, 3.0, 0.2, 0.014, "C")
