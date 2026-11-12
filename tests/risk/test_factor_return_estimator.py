"""Tests of FactorReturnEstimator on a synthetic market."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.frames import FACTOR_RETURN, SPECIFIC_RETURN
from quant_cn.risk.factor_return_estimator import FactorReturnEstimator
from tests.risk.synthetic_market import STYLES, SyntheticFactorMarket


@pytest.fixture(scope="module")
def market() -> SyntheticFactorMarket:
    return SyntheticFactorMarket(n_days=60, noise=0.1)


@pytest.fixture(scope="module")
def fitted(market: SyntheticFactorMarket) -> tuple[pd.DataFrame, pd.DataFrame]:
    return FactorReturnEstimator(STYLES, 1.0).compute(market.build_panel())


# TC-FRE-001
def test_tc_fre_001_recovers_planted_returns(
    market: SyntheticFactorMarket, fitted: tuple[pd.DataFrame, pd.DataFrame]
) -> None:
    est = fitted[0].pivot(index="trade_date", columns="factor", values="ret")
    for name in market.factor_ret.columns:
        corr = np.corrcoef(est[name], market.factor_ret.loc[est.index, name])[0, 1]
        assert corr > 0.99, name


# TC-FRE-002
def test_tc_fre_002_industry_constraint(
    market: SyntheticFactorMarket, fitted: tuple[pd.DataFrame, pd.DataFrame]
) -> None:
    est = fitted[0].pivot(index="trade_date", columns="factor", values="ret")
    share = np.array([market.cap[market.industry == i].sum() for i in range(market.n_ind)])
    total = est[[f"ind_I{i}" for i in range(market.n_ind)]].to_numpy() @ (share / share.sum())
    assert np.abs(total).max() < 1e-10


# TC-FRE-003
def test_tc_fre_003_residual_orthogonality_and_weights(market: SyntheticFactorMarket) -> None:
    panel = market.build_panel()
    part = panel[panel["trade_date"] == market.days[0]]
    result = FactorReturnEstimator(STYLES, 0.9).compute_date(part)
    assert result is not None
    factors, resid = result
    w = resid["weight"].to_numpy()
    assert w.max() == pytest.approx(np.quantile(np.sqrt(market.cap), 0.9))
    u = resid["resid"].to_numpy()
    for k in range(len(STYLES)):
        assert abs((w * u * market.styles[:, k]).sum()) < 1e-8
    assert abs((w * u).sum()) < 1e-8  # country column
    assert 0.0 <= factors["r2"].iloc[0] <= 1.0


# TC-FRE-004
def test_tc_fre_004_missing_style_thin_session_and_schemas(market: SyntheticFactorMarket) -> None:
    panel = market.build_panel()
    panel.loc[panel["trade_date"] == market.days[1], "beta"] = np.nan
    thin = panel[panel["trade_date"] == market.days[2]].head(50)
    panel = pd.concat([panel[panel["trade_date"] != market.days[2]], thin])
    factors, resid = FactorReturnEstimator(STYLES, 1.0, min_names=100).compute(panel)
    day1 = factors[factors["trade_date"] == market.days[1]]
    assert "beta" not in set(day1["factor"]) and "size" in set(day1["factor"])
    assert market.days[2] not in set(factors["trade_date"])
    FACTOR_RETURN.validate(factors)
    SPECIFIC_RETURN.validate(resid)
    with pytest.raises(ValueError):
        FactorReturnEstimator(STYLES, 0.0)


# TC-FRE-005
def test_tc_fre_005_monitor_style() -> None:
    market = SyntheticFactorMarket(n_days=40, noise=0.1)
    panel = market.build_panel()
    rng = np.random.default_rng(9)
    theme = rng.standard_normal(market.n_stocks)
    planted = rng.normal(0, 0.004, market.n_days)
    day_index = {d: i for i, d in enumerate(market.days)}
    panel["theme"] = np.tile(theme, market.n_days)
    panel["ret"] = panel["ret"] + panel["theme"] * panel["trade_date"].map(day_index).map(
        lambda i: planted[i]
    )
    est = FactorReturnEstimator(STYLES, 1.0)
    out = est.compute_monitor(panel, ["theme"]).set_index("trade_date")
    assert np.corrcoef(out["ret"], planted)[0, 1] > 0.99
    assert (out["r2"] >= -1e-12).all() and set(out["factor"]) == {"theme"}
    base = est.compute(panel)[0]
    assert "theme" not in set(base["factor"])  # the model itself ignores the monitor column
