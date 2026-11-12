"""Tests of DescriptorBuilder."""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from quant_cn.risk.descriptor_builder import BASE_COLUMNS, DESCRIPTORS, DescriptorBuilder
from quant_cn.risk.fundamental_descriptors import FundamentalDescriptors
from quant_cn.risk.price_descriptors import PriceDescriptors
from quant_cn.statistic.standardizer import Standardizer
from tests.risk.risk_fakes import InputsBuilder
from tests.risk.synthetic_market import SyntheticFactorMarket


def build() -> DescriptorBuilder:
    prices = PriceDescriptors(beta_window=60, beta_half_life=20, vol_window=60, min_obs=30)
    return DescriptorBuilder(prices, FundamentalDescriptors(), Standardizer(), (".BJ",))


# TC-DB-001
def test_tc_db_001_rows_and_columns() -> None:
    market = SyntheticFactorMarket(n_stocks=60, n_days=120)
    inputs = InputsBuilder.build(market, start_index=100)
    bj = inputs.members.iloc[:1].assign(ts_code="830001.BJ")
    inputs = dataclasses.replace(inputs, members=pd.concat([inputs.members, bj]))
    out = build().compute(inputs)
    assert list(out.columns) == BASE_COLUMNS + DESCRIPTORS
    assert len(out) == 20 * 60 and not out["ts_code"].str.endswith(".BJ").any()
    assert out[["trade_date", "ts_code"]].duplicated().sum() == 0
    assert out["beta"].notna().all() and out["stom"].notna().all()
    assert out["circ_mv"].iloc[0] == pytest.approx(market.cap[0])


# TC-DB-002
def test_tc_db_002_no_look_ahead() -> None:
    market = SyntheticFactorMarket(n_stocks=60, n_days=120)
    base = build().compute(InputsBuilder.build(market, start_index=100))
    market.returns[110:] *= 5.0
    shocked = build().compute(InputsBuilder.build(market, start_index=100))
    early = base["trade_date"] < market.days[110]
    cols = ["beta", "hsigma", "dastd", "rstr"]
    pd.testing.assert_frame_equal(base.loc[early, cols], shocked.loc[early, cols])
    assert not np.allclose(base.loc[~early, "dastd"], shocked.loc[~early, "dastd"])


# TC-DB-003
def test_tc_db_003_growth_from_latest_snapshot() -> None:
    market = SyntheticFactorMarket(n_stocks=30, n_days=80)
    inputs = InputsBuilder.build(market, start_index=60)
    code = market.codes[0]
    snap = lambda as_of, top: [  # noqa: E731 -- local row builder
        {"as_of": as_of, "ts_code": code, "end_date": f"{y}1231", "field": "eps", "value": v}
        for y, v in zip((2020, 2021, 2022), (1.0, 2.0, top), strict=True)
    ]
    mid = market.days[70]
    annual = pd.DataFrame(snap("20000101", 3.0) + snap(mid, 6.0))
    out = build().compute(dataclasses.replace(inputs, annual=annual))
    mine = out[out["ts_code"] == code].set_index("trade_date")["egro"]
    assert mine[market.days[69]] == pytest.approx(1.0 / 2.0)
    assert mine[mid] == pytest.approx(2.5 / 3.0)


# TC-DB-004
def test_tc_db_004_overnight_foreign_return() -> None:
    sessions = ["20250929", "20250930", "20251009", "20251010", "20251013"]
    foreign = pd.DataFrame(
        {
            "trade_date": ["20250929", "20251001", "20251008", "20251009", "20251010"],
            "pct_chg": [1.0, 2.0, -1.0, 0.5, 3.0],
        }
    )
    out = DescriptorBuilder.compute_overnight_return(sessions, foreign)
    assert np.isnan(out[0])
    assert out[1] == pytest.approx(0.01)  # US 09-29 closes before China 09-30
    assert out[2] == pytest.approx(1.02 * 0.99 - 1)  # holiday gap: US 10-01 and 10-08
    assert out[3] == pytest.approx(0.005)
    assert out[4] == pytest.approx(0.03)
    none = DescriptorBuilder.compute_overnight_return(sessions, foreign.iloc[:0])
    assert np.isnan(none).all()
    stale = DescriptorBuilder.compute_overnight_return(
        [*sessions, "20251014", "20251015", "20251016", "20251017"], foreign
    )
    assert stale[5] == 0.0 and np.isnan(stale[-1])


# TC-DB-005
def test_tc_db_005_theme_basket() -> None:
    returns = np.array([[0.01, 0.03, -0.02], [0.02, np.nan, 0.04]])
    weights = np.array([[1.0, 3.0, 2.0], [1.0, 3.0, 2.0]])
    member = np.array([True, True, False])
    out = DescriptorBuilder.compute_theme_return(returns, weights, member)
    assert out[0, 0] == pytest.approx(0.03)  # the other member only
    assert out[0, 1] == pytest.approx(0.01)
    assert out[0, 2] == pytest.approx((0.01 * 1 + 0.03 * 3) / 4)  # non-member: whole basket
    assert np.isnan(out[1, 0])  # the other member did not trade
    market = SyntheticFactorMarket(n_stocks=40, n_days=130)
    inputs = InputsBuilder.build(market, start_index=110)
    themed = dataclasses.replace(
        inputs, themes={"theme_beta": (tuple(market.codes[:10]), market.days[115])}
    )
    frame = build().compute(themed)
    assert "theme_beta" in frame.columns
    assert frame.loc[frame["trade_date"] < market.days[115], "theme_beta"].isna().all()
