"""Tests of risk_model_factory (plan 05)."""

from __future__ import annotations

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.risk_model_settings import RiskModelSettings, StyleSpec
from quant_cn.lake.exposure_reader import ExposureReader
from quant_cn.lake.statement_version_reader import StatementVersionReader
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.risk.risk_input_loader import RiskInputLoader
from quant_cn.risk.risk_model import RiskModel
from quant_cn.risk.risk_model_factory import RiskModelFactory
from quant_cn.service_builder import ServiceBuilder
from tests.risk.synthetic_market import STYLES
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


# TC-RMF-001
def test_tc_rmf_001_build(lake: MiniLake) -> None:
    model = build_model(lake)
    assert isinstance(model, RiskModel) and model.name == "synthetic"
