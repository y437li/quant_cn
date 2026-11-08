from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.calculation.forward_price_estimator import ForwardPriceEstimator
from quant_cn.calculation.option_chain_builder import OptionChainBuilder
from quant_cn.calculation.variance_strip_calculator import VarianceStripCalculator
from tests.support import SampleOptions


def build_quotes(**kw: object) -> pd.DataFrame:
    quotes, _ = OptionChainBuilder().build_quotes(
        SampleOptions.build_chain(expiries=(("20261028", 61),), **kw)
    )  # type: ignore[arg-type]
    return quotes


# TC-VSC-001
def test_tc_vsc_001_flat_vol() -> None:
    quotes, t = build_quotes(), 61 / 365
    forward, k0 = ForwardPriceEstimator().compute(quotes, 0.014, t)
    var, n = VarianceStripCalculator("price").compute(quotes, forward, k0, 0.014, t)
    assert var == pytest.approx(0.04, rel=0.01) and 40 < n <= 71


# TC-VSC-002
def test_tc_vsc_002_zero_cutoff() -> None:
    quotes, t = build_quotes(), 61 / 365
    forward, k0 = ForwardPriceEstimator().compute(quotes, 0.014, t)
    quotes.loc[[2.5, 2.45], ("price", "P")] = 0.0  # two consecutive zeros: stop below 2.55
    quotes.loc[3.5, ("price", "C")] = 0.0  # a single zero: skipped, walk continues
    _, n = VarianceStripCalculator("price").compute(quotes, forward, k0, 0.014, t)
    kept_puts = len([k for k in quotes.index if 2.5 < k < k0])
    kept_calls = len([k for k in quotes.index if k > k0]) - 1
    assert n == 1 + kept_puts + kept_calls


# TC-VSC-003
def test_tc_vsc_003_delta_k() -> None:
    quotes = build_quotes(strikes=(2.9, 3.0, 3.2))
    forward, k0 = 3.04, 3.0
    var, n = VarianceStripCalculator("price").compute(quotes, forward, k0, 0.0, 1.0)
    p29, c32 = quotes.loc[2.9, ("price", "P")], quotes.loc[3.2, ("price", "C")]
    q30 = (quotes.loc[3.0, ("price", "C")] + quotes.loc[3.0, ("price", "P")]) / 2
    expected = (
        2 * (0.1 / 2.9**2 * p29 + 0.15 / 3.0**2 * q30 + 0.2 / 3.2**2 * c32)
        - (forward / k0 - 1) ** 2
    )
    assert n == 3 and var == pytest.approx(expected)
    assert not math.isnan(var)
