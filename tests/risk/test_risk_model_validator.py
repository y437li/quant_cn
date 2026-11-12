"""Tests of RiskModelValidator."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.frames import RISK_VALIDATION
from quant_cn.risk.base_risk_model import BaseRiskModel
from quant_cn.risk.risk_model_validator import RiskModelValidator
from quant_cn.risk.risk_snapshot import RiskSnapshot

DAYS = pd.bdate_range("2024-01-02", periods=400).strftime("%Y%m%d").tolist()


class FlatModel(BaseRiskModel):
    """Every stock: no factor risk, specific vol 0.02."""

    def load_snapshot(self, trade_date: str) -> RiskSnapshot:
        codes = [f"{i:06d}.SZ" for i in range(20)]
        x = pd.DataFrame(0.0, index=codes, columns=["country"])
        cov = pd.DataFrame([[0.0]], index=["country"], columns=["country"])
        return RiskSnapshot(trade_date, x, cov, pd.Series(0.02, index=codes))


# TC-RMV-001
def test_tc_rmv_001_bias_statistic() -> None:
    rng = np.random.default_rng(13)
    good = pd.DataFrame(
        {"trade_date": DAYS, "scope": "a", "sigma": 0.01, "ret": rng.normal(0, 0.01, 400)}
    )
    low = good.assign(scope="b", sigma=0.005)
    out = RiskModelValidator.compute_bias(pd.concat([good, low]))
    bias = out[out["metric"] == "bias"].set_index("scope")["value"]
    assert bias["a"] == pytest.approx(1.0, abs=0.1)
    assert bias["b"] == pytest.approx(2.0, abs=0.2)
    n = out[out["metric"] == "n_obs"].set_index("scope")["value"]
    assert n["a"] == 400
    assert out["window"].iloc[0] == f"{DAYS[0]}-{DAYS[-1]}"


# TC-RMV-002
def test_tc_rmv_002_factor_bias_pairs_next_session() -> None:
    rng = np.random.default_rng(14)
    vol = np.where(np.arange(400) % 2 == 0, 0.01, 0.03)  # vol alternates; forecast at t knows t+1
    rets = rng.standard_normal(400) * vol
    fr = pd.DataFrame(
        {"trade_date": DAYS, "factor": "f", "ret": rets, "t_stat": 0.0, "r2": 0.3, "n_obs": 1.0}
    )
    nxt = np.roll(vol, -1) ** 2
    cov = pd.DataFrame(
        {
            "trade_date": DAYS,
            "factor_i": "f",
            "factor_j": "f",
            "cov": nxt,
            "cov_raw": nxt,
            "horizon_days": 21.0,
        }
    )
    out = RiskModelValidator(FlatModel("m")).compute_factor_bias(fr, cov, DAYS[0], DAYS[-2])
    assert out.set_index(["metric", "scope"]).loc[("bias", "factor:f"), "value"] == pytest.approx(
        1.0, abs=0.1
    )


# TC-RMV-003
def test_tc_rmv_003_random_portfolios() -> None:
    names = [f"{i:06d}.SZ" for i in range(100)]
    v = RiskModelValidator(FlatModel("m"), seed=1)
    a, b = v.build_random_portfolios(names, 5, 10), v.build_random_portfolios(names, 5, 10)
    pd.testing.assert_frame_equal(a, b)
    assert (a["weight"] > 0).all()
    np.testing.assert_allclose(a.groupby("portfolio")["weight"].sum(), 1.0)
    assert a.groupby("portfolio").size().eq(10).all()
    with pytest.raises(ValueError):
        v.build_random_portfolios([], 1, 1)


# TC-RMV-004
def test_tc_rmv_004_portfolio_forecasts_and_fit() -> None:
    codes = [f"{i:06d}.SZ" for i in range(20)]
    rng = np.random.default_rng(15)
    returns = pd.DataFrame(
        [
            {"trade_date": d, "ts_code": c, "ret": rng.normal(0, 0.02)}
            for d in DAYS[:60]
            for c in codes
        ]
    )
    v = RiskModelValidator(FlatModel("m"))
    portfolios = pd.DataFrame({"portfolio": "p", "ts_code": codes[:1], "weight": [1.0]})
    paired = v.compute_portfolio_forecasts(portfolios, DAYS[:60], returns)
    assert len(paired) == 59 and paired["sigma"].eq(0.02).all()
    first = returns[(returns["trade_date"] == DAYS[1]) & (returns["ts_code"] == codes[0])][
        "ret"
    ].iloc[0]
    assert paired["ret"].iloc[0] == pytest.approx(first)
    fr = pd.DataFrame(
        {
            "trade_date": DAYS[:3],
            "factor": "f",
            "ret": 0.0,
            "t_stat": 0.0,
            "r2": [0.1, 0.3, 0.5],
            "n_obs": 100.0,
        }
    )
    fit = v.compute_fit(fr, DAYS[0], DAYS[2]).set_index("metric")["value"]
    assert fit["median_r2"] == pytest.approx(0.3) and fit["mean_r2"] == pytest.approx(0.3)
    assert fit["median_adj_r2"] == pytest.approx(1 - 0.7 * 99 / 100)  # one factor: p = 0
    RISK_VALIDATION.validate(v.compute_fit(fr, DAYS[0], DAYS[2]))
