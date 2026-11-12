"""Tests of risk_model (plan 05)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.core.frames import FACTOR_COV, SPECIFIC_RISK
from quant_cn.core.risk_model_settings import RiskModelSettings, StyleSpec
from quant_cn.lake.exposure_reader import ExposureReader
from quant_cn.lake.statement_version_reader import StatementVersionReader
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.risk.risk_input_loader import RiskInputLoader
from quant_cn.risk.risk_model import RiskModel
from quant_cn.risk.risk_model_factory import RiskModelFactory
from quant_cn.service_builder import ServiceBuilder
from tests.risk.risk_fakes import InputsBuilder
from tests.risk.sample_risk_lake import SampleRiskLake
from tests.risk.synthetic_market import STYLES, SyntheticFactorMarket
from tests.support import MiniLake


def build_model(lake: MiniLake) -> RiskModel:
    settings = RiskModelSettings(
        name="synthetic",
        styles=[StyleSpec(name=s, descriptors={s: 1.0}) for s in STYLES],
        min_regression_names=20,
        eigen_sims=10,
        min_factor_obs=30,
        specific_min_obs=20,
        specific_full_obs=40,
    )
    return RiskModelFactory(lake.query).build(settings)


def build_loader(lake: MiniLake, config: Config) -> RiskInputLoader:
    reader = ServiceBuilder().build_reader(config, lake.catalog)
    calendar, codec = TradingCalendar(lake.query), DateCodec()
    versions = StatementVersionReader(lake.query, TickerAliasMap(lake.catalog, lake.query), codec)
    return RiskInputLoader(reader, ExposureReader(lake.query), versions, calendar, codec)


# TC-RM-001
def test_tc_rm_001_stages_on_synthetic_market(lake: MiniLake) -> None:
    market = SyntheticFactorMarket(n_days=120, noise=0.1)
    model = build_model(lake)
    inputs = InputsBuilder.build(market)
    fr, resid = model.compute_factor_returns(market.build_exposures(), inputs)
    est = fr.pivot(index="trade_date", columns="factor", values="ret")
    for name in ("country", "size", "beta", "ind_I0"):
        assert np.corrcoef(est[name], market.factor_ret.loc[est.index, name])[0, 1] > 0.99
    FACTOR_COV.validate(model.compute_covariance(fr, start=market.days[60]))
    wide = resid.pivot(index="trade_date", columns="ts_code", values="resid")
    sigma_ts, obs = model.compute_specific_time_series(wide)
    exp = market.build_exposures()
    day = market.days[-1]
    cap = pd.Series(market.cap, index=market.codes)
    pre = model.compute_specific_session(
        sigma_ts.loc[day], obs.loc[day], exp[exp["trade_date"] == day], cap
    )
    final = model.compute_specific_final(pre.assign(trade_date=day), wide)
    SPECIFIC_RISK.validate(final)
    ratio = final.set_index("ts_code")["sigma"] / pd.Series(market.spec_vol, index=market.codes)
    assert ratio.median() == pytest.approx(1.0, abs=0.25)


# TC-RM-002
def test_tc_rm_002_exposures_at_t_minus_1(lake: MiniLake) -> None:
    market = SyntheticFactorMarket(n_stocks=60, n_days=5)
    exp = market.build_exposures()
    panel = build_model(lake).build_regression_panel(exp, InputsBuilder.build(market))
    assert panel["trade_date"].min() == market.days[1]
    row = panel[
        (panel["trade_date"] == market.days[2]) & (panel["ts_code"] == market.codes[0])
    ].iloc[0]
    close = 10 * np.cumprod(1 + market.returns, axis=0)
    assert row["ret"] == pytest.approx(close[2, 0] / close[1, 0] - 1)
    assert row["circ_mv"] == pytest.approx(market.cap[0])


# TC-RM-003
def test_tc_rm_003_load_snapshot(lake: MiniLake, config: Config) -> None:
    SampleRiskLake.write(lake, config)
    cfg = config.model_copy(update={"risk_model": SampleRiskLake.build_settings()})
    step = ServiceBuilder().build_risk_model(cfg, lake.catalog)
    model = RiskModelFactory(lake.query).build(cfg.risk_model)
    with pytest.raises(LakeError):
        model.load_snapshot(SampleRiskLake.DAYS[-1])
    step.run("r1")
    snap = model.load_snapshot(SampleRiskLake.DAYS[-1])
    assert (snap.exposures["country"] == 1.0).all()
    assert list(snap.exposures.columns) == list(snap.cov.columns)
    assert snap.specific.index.isin(snap.exposures.index).all()
    with pytest.raises(LakeError):
        model.load_snapshot("19990101")


# TC-RM-004
def test_tc_rm_004_monitor_returns(lake: MiniLake) -> None:
    market = SyntheticFactorMarket(n_stocks=200, n_days=30, noise=0.1)
    inputs = InputsBuilder.build(market)
    exp = market.build_exposures()
    assert build_model(lake).compute_monitor_returns(exp, inputs).empty
    settings = RiskModelSettings(
        name="m",
        styles=[StyleSpec(name="size", descriptors={"size": 1.0})],
        monitor_styles=[StyleSpec(name="beta", descriptors={"beta": 1.0})],
        min_regression_names=20,
    )
    out = RiskModelFactory(lake.query).build(settings).compute_monitor_returns(exp, inputs)
    assert set(out["factor"]) == {"beta"} and len(out) == market.n_days - 1
    est = out.set_index("trade_date")["ret"]
    assert np.corrcoef(est, market.factor_ret.loc[est.index, "beta"])[0, 1] > 0.99
