from __future__ import annotations

import pytest

from quant_cn.calculation.forward_price_estimator import ForwardPriceEstimator
from quant_cn.calculation.option_chain_builder import OptionChainBuilder
from tests.support import SampleOptions


# TC-FPE-001
def test_tc_fpe_001_forward() -> None:
    chain = SampleOptions.build_chain(expiries=(("20260923", 26),))
    quotes, _ = OptionChainBuilder().build_quotes(chain)
    forward, k0 = ForwardPriceEstimator().compute(quotes, 0.014, 26 / 365)
    assert forward == pytest.approx(3.04, abs=1e-9) and k0 == 3.0


# TC-FPE-002
def test_tc_fpe_002_errors() -> None:
    chain = SampleOptions.build_chain(expiries=(("20260923", 26),))
    quotes, _ = OptionChainBuilder().build_quotes(chain[chain["call_put"] == "C"])
    with pytest.raises((ValueError, KeyError)):
        ForwardPriceEstimator().compute(quotes, 0.014, 26 / 365)
    high, _ = OptionChainBuilder().build_quotes(
        SampleOptions.build_chain(expiries=(("20260923", 26),), strikes=(3.5, 3.6))
    )
    with pytest.raises(ValueError):
        ForwardPriceEstimator().compute(high, 0.014, 26 / 365)
