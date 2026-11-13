"""Tests of risk_input_loader (plan 05)."""

from __future__ import annotations

import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.risk_model_settings import (
    ExternalSeriesSpec,
    RiskModelSettings,
    StyleSpec,
    ThemeBasketSpec,
)
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.exposure_reader import ExposureReader
from quant_cn.lake.statement_version_reader import StatementVersionReader
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.risk.risk_input_loader import RiskInputLoader
from quant_cn.risk.risk_model import RiskModel
from quant_cn.risk.risk_model_factory import RiskModelFactory
from quant_cn.service_builder import ServiceBuilder
from tests.risk.sample_risk_lake import SampleRiskLake
from tests.risk.synthetic_market import STYLES
from tests.support import MiniLake, SampleFactorLake


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


def build_loader(
    lake: MiniLake,
    config: Config,
    external: tuple[ExternalSeriesSpec, ...] = (),
    themes: tuple[ThemeBasketSpec, ...] = (),
) -> RiskInputLoader:
    reader = ServiceBuilder().build_reader(config, lake.catalog)
    calendar, codec = TradingCalendar(lake.query), DateCodec()
    versions = StatementVersionReader(lake.query, TickerAliasMap(lake.catalog, lake.query), codec)
    exposures = ExposureReader(lake.query)
    return RiskInputLoader(
        reader, exposures, versions, calendar, codec, lake.query, external, themes
    )


# TC-RIL-001
def test_tc_ril_001_load_window(lake: MiniLake, config: Config) -> None:
    SampleRiskLake.write(lake, config)
    days = SampleRiskLake.DAYS
    inputs = build_loader(lake, config).load(days[100], days[110])
    assert inputs.prices["trade_date"].min() == days[0]  # all history before start (< 530)
    assert inputs.members["trade_date"].min() == days[100]
    assert set(inputs.members["l1_code"]) == {"800", "801", "802"}
    assert {"total_mv", "circ_mv", "turnover_rate_f", "dv_ttm"} <= set(inputs.basic.columns)
    assert set(inputs.fundamentals["field"]) <= {"total_hldr_eqy_exc_min_int"}
    with pytest.raises(ValueError):
        build_loader(lake, config).load(days[10], days[5])


# TC-RIL-002
def test_tc_ril_002_snapshot_dates(lake: MiniLake, config: Config) -> None:
    SampleRiskLake.write(lake, config)
    days = SampleRiskLake.DAYS
    dates = build_loader(lake, config).list_snapshot_dates("20251015", "20251231")
    month_end = [d for i, d in enumerate(days[:-1]) if days[i + 1][:6] != d[:6]]
    assert dates[0] == max(d for d in days if d < "20251015")
    assert dates[1:] == [d for d in month_end if "20251015" <= d <= "20251231"]


# TC-RIL-003
def test_tc_ril_003_external_series_and_themes(lake: MiniLake, config: Config) -> None:
    SampleRiskLake.write(lake, config)
    days = SampleRiskLake.DAYS
    rows = [{"ts_code": c, "trade_date": d, "pct_chg": 1.0} for d in days for c in ("SPX", "HSI")]
    SampleFactorLake.write(lake, config, "index_global", rows)
    fx = [
        {"ts_code": "USDCNH.FXCM", "trade_date": d, "bid_close": 7.0 + 0.01 * i}
        for i, d in enumerate(days)
    ]
    SampleFactorLake.write(lake, config, "fx_daily", fx)
    members = [
        {"ts_code": "885887.TI", "con_code": c, "con_name": "x"} for c in SampleRiskLake.CODES[:5]
    ]
    SampleFactorLake.write(lake, config, "ths_member", members)
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    spx = ExternalSeriesSpec(descriptor="us_beta", dataset="index_global", code="SPX")
    usd = ExternalSeriesSpec(
        descriptor="usd_beta",
        dataset="fx_daily",
        code="USDCNH.FXCM",
        column="bid_close",
        kind="price",
        date_shift_days=1,
    )
    theme = ThemeBasketSpec(descriptor="aidc_beta", concept="885887.TI", start="20251001")
    inputs = build_loader(lake, config, (spx, usd), (theme,)).load(days[100], days[110])
    us, fxr = inputs.external["us_beta"], inputs.external["usd_beta"]
    assert list(us.columns) == ["trade_date", "pct_chg"] and us["trade_date"].min() == days[0]
    assert len(us) == 111
    assert fxr["trade_date"].iloc[0] > days[1]  # shifted one calendar day; first diff dropped
    assert fxr["pct_chg"].iloc[0] == pytest.approx((7.01 / 7.00 - 1) * 100)
    assert inputs.themes["aidc_beta"] == (tuple(SampleRiskLake.CODES[:5]), "20251001")
    assert build_loader(lake, config).load(days[100], days[110]).external == {}
