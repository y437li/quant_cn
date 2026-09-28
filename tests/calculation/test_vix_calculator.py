from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.calculation.expiry_clock import ExpiryClock
from quant_cn.calculation.forward_price_estimator import ForwardPriceEstimator
from quant_cn.calculation.option_chain_builder import OptionChainBuilder
from quant_cn.calculation.risk_free_curve import RiskFreeCurve
from quant_cn.calculation.term_interpolator import TermInterpolator
from quant_cn.calculation.term_selector import TermSelector
from quant_cn.calculation.variance_strip_calculator import VarianceStripCalculator
from quant_cn.calculation.vix_calculator import VixCalculator
from quant_cn.core.frames import VIX_PANEL
from tests.support import SampleOptions

SESSIONS = [d.strftime("%Y%m%d") for d in pd.bdate_range("20260829", "20261231")]


def build_calculator(clock: ExpiryClock) -> VixCalculator:
    return VixCalculator(
        RiskFreeCurve(SampleOptions.SHIBOR),
        OptionChainBuilder(),
        TermSelector(7),
        ForwardPriceEstimator(),
        VarianceStripCalculator("price"),
        TermInterpolator(),
        clock,
    )


# TC-VC-001
@pytest.mark.parametrize("clock", [ExpiryClock(), ExpiryClock("trading", SESSIONS)])
def test_tc_vc_001_flat_vol(clock: ExpiryClock) -> None:
    out = build_calculator(clock).compute(SampleOptions.build_chain(), "TEST")
    assert out["vix"].iloc[0] == pytest.approx(20.0, abs=0.3) or clock.mode == "trading"
    if clock.mode == "calendar":
        assert out["vix"].iloc[0] == pytest.approx(20.0, abs=0.3)
    else:
        assert 15.0 < out["vix"].iloc[0] < 30.0


# TC-VC-002
def test_tc_vc_002_schema() -> None:
    chain = pd.concat(
        [SampleOptions.build_chain("20260827"), SampleOptions.build_chain("20260828")]
    )
    out = build_calculator(ExpiryClock()).compute(chain, "TEST")
    VIX_PANEL.validate(out)
    assert out["trade_date"].tolist() == ["20260827", "20260828"] and set(out["quality_flag"]) == {
        "ok"
    }


# TC-VC-003
def test_tc_vc_003_failed_day() -> None:
    one_term = SampleOptions.build_chain("20260827", expiries=(("20260923", 27),))
    chain = pd.concat([one_term, SampleOptions.build_chain("20260828")])
    out = build_calculator(ExpiryClock()).compute(chain, "TEST")
    assert pd.isna(out["vix"].iloc[0]) and out["quality_flag"].iloc[0].startswith("failed")
    assert out["vix"].iloc[1] == pytest.approx(20.0, abs=0.3)
