from __future__ import annotations

import numpy as np
import pytest

from quant_cn.calculation.black76_model import Black76Model
from quant_cn.calculation.forward_price_estimator import ForwardPriceEstimator
from quant_cn.calculation.gamma_exposure_calculator import GammaExposureCalculator
from quant_cn.calculation.option_chain_builder import OptionChainBuilder
from quant_cn.calculation.risk_free_curve import RiskFreeCurve
from tests.support import SampleOptions

STRIKES = tuple(round(2.5 + 0.05 * i, 2) for i in range(21))


def build_calculator(max_days: int = 90) -> GammaExposureCalculator:
    return GammaExposureCalculator(
        RiskFreeCurve(SampleOptions.SHIBOR),
        OptionChainBuilder(),
        ForwardPriceEstimator(),
        Black76Model(),
        max_days=max_days,
    )


def build_chain(side: str | None = None, oi: float = 100.0) -> object:
    chain = SampleOptions.build_chain(strikes=STRIKES).assign(oi=oi)
    return chain if side is None else chain.assign(oi=np.where(chain["call_put"] == side, oi, 0.0))


# TC-GEC-001
def test_tc_gec_001_formula() -> None:
    out = build_calculator().compute(build_chain(), "20260828", multiplier=10000)
    row = out[(out["strike"] == 3.0) & (out["call_put"] == "C")].iloc[0]
    expected = row["sign"] * row["gamma"] * row["oi"] * 10000 * row["forward"] ** 2 * 0.01
    assert row["gex"] == pytest.approx(expected)
    assert row["iv"] == pytest.approx(0.20, abs=2e-3)


# TC-GEC-002
def test_tc_gec_002_signs() -> None:
    calc = build_calculator()
    assert calc.compute(build_chain("P"), "20260828", 10000)["gex"].sum() < 0
    assert calc.compute(build_chain("C"), "20260828", 10000)["gex"].sum() > 0


# TC-GEC-003
def test_tc_gec_003_profile_and_flip() -> None:
    calc = build_calculator()
    exposures = calc.compute(build_chain(), "20260828", 10000)
    levels = np.linspace(2.6, 3.5, 19)
    profile = calc.compute_profile(exposures, levels)
    assert list(profile.columns) == ["level", "gex"] and len(profile) == 19
    flip = calc.find_flip(profile)
    if flip is not None:
        assert 2.6 <= flip <= 3.5
    puts_only = calc.compute_profile(calc.compute(build_chain("P"), "20260828", 10000), levels)
    assert calc.find_flip(puts_only) is None


# TC-GEC-004
def test_tc_gec_004_skips() -> None:
    chain = build_chain()
    chain.loc[chain.index[0], "close"] = 99.0  # above any Black-76 price: no IV
    out = build_calculator(max_days=40).compute(chain, "20260828", 10000)
    assert set(out["maturity_date"]) == {"20260923"}
    assert len(out) == len(chain[chain["maturity_date"] == "20260923"]) - 1
