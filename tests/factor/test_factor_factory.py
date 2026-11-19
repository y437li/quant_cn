from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.calculation.consensus_panel_builder import ConsensusPanelBuilder
from quant_cn.calculation.retail_gauge_nowcaster import GAUGE_COLUMNS
from quant_cn.core.config import Config, FactorSpec
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError
from quant_cn.factor.factor_factory import FactorFactory
from quant_cn.factor.library.momentum_factor import MomentumFactor
from quant_cn.lake.dated_table_store import DatedTableStore
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.trading_calendar import TradingCalendar
from tests.support import MiniLake, SampleFactorLake


def build_factory(lake: MiniLake, specs: list[FactorSpec]) -> FactorFactory:
    return FactorFactory(specs, TradingCalendar(lake.query), DateCodec())


# TC-FAF-001
def test_tc_faf_001_build_all(lake: MiniLake) -> None:
    specs = [
        FactorSpec(name="mom", class_name="MomentumFactor", params={"window": 60, "skip": 5}),
        FactorSpec(name="ep", class_name="EarningsYieldFactor"),
    ]
    factors = build_factory(lake, specs).build_all()
    assert [f.name for f in factors] == ["mom", "ep"] and isinstance(factors[0], MomentumFactor)
    assert factors[0].lookback == 60


# TC-FAF-002
def test_tc_faf_002_unknown(lake: MiniLake) -> None:
    with pytest.raises(ConfigError):
        build_factory(lake, [FactorSpec(name="x", class_name="NoSuchFactor")]).build_all()
    with pytest.raises(ConfigError):
        build_factory(
            lake,
            [FactorSpec(name="m", class_name="MomentumFactor", params={"window": 1, "skip": 5})],
        ).build_all()


# TC-FAF-003
def test_tc_faf_003_build_inputs(lake: MiniLake, reader: LakeReader) -> None:
    specs = [
        FactorSpec(name="mom", class_name="MomentumFactor", params={"window": 20, "skip": 5}),
        FactorSpec(name="ep", class_name="EarningsYieldFactor"),
        FactorSpec(name="turn", class_name="TurnoverFactor", params={"window": 10, "min_obs": 5}),
    ]
    factory = build_factory(lake, specs)
    inputs = factory.build_inputs(reader, factory.build_all(), "20260401", "20260430")
    sessions = TradingCalendar(lake.query).list_sessions("20260101", "20260331")
    assert inputs.prices["trade_date"].min() == sessions[-20]  # 20 sessions of history
    assert set(inputs.fundamentals["field"]) == {"n_income_attr_p_ttm"}
    assert set(inputs.daily_basic.columns) == {
        "trade_date",
        "ts_code",
        "total_mv",
        "turnover_rate_f",
    }


# TC-FAF-004
def test_tc_faf_004_consensus(lake: MiniLake, reader: LakeReader, config: Config) -> None:
    SampleFactorLake.write(lake, config, "report_rc", [
        {"ts_code": "000001.SZ", "report_date": "20260310", "org_name": "A",
         "report_title": "t", "quarter": "2025Q4", "np": 10.0},
    ])  # fmt: skip
    gap = FactorSpec(name="gap", class_name="PricingGapFactor", params={"window_days": 60})
    mom = FactorSpec(name="mom", class_name="MomentumFactor", params={"window": 20, "skip": 5})
    calendar = TradingCalendar(lake.query)
    factory = FactorFactory(
        [gap, mom], calendar, DateCodec(), ConsensusPanelBuilder(lake.query, DateCodec())
    )
    inputs = factory.build_inputs(reader, factory.build_all(), "20260401", "20260415")
    # month ends from 40 days before the start, then the last session
    assert sorted(inputs.consensus["trade_date"].unique()) == ["20260331", "20260415"]
    assert inputs.consensus["np1"].tolist() == [10.0, 10.0]
    plain = FactorFactory([mom], calendar, DateCodec())
    assert plain.build_inputs(reader, plain.build_all(), "20260401", "20260415").consensus.empty
    bare = FactorFactory([gap], calendar, DateCodec())
    with pytest.raises(ConfigError):
        bare.build_inputs(reader, bare.build_all(), "20260401", "20260415")


# TC-FAF-005
def test_tc_faf_005_retail_gauge(lake: MiniLake, reader: LakeReader, config: Config) -> None:
    rows = pd.DataFrame(
        {"ts_code": ["000001.SZ"] * 3, "as_of": ["20260115", "20260215", "20260420"],
         "pct": [0.1, 0.2, 0.3]}
    )  # fmt: skip
    lake.writer.write_derived("retail_gauge", 2026, rows.reindex(columns=GAUGE_COLUMNS))
    gauge = FactorSpec(name="g", class_name="RetailGaugeFactor", params={"max_age_days": 30})
    mom = FactorSpec(name="mom", class_name="MomentumFactor", params={"window": 20, "skip": 5})
    calendar = TradingCalendar(lake.query)
    store = DatedTableStore(lake.writer)
    factory = FactorFactory([gauge, mom], calendar, DateCodec(), gauge=store)
    inputs = factory.build_inputs(reader, factory.build_all(), "20260401", "20260415")
    # readings from 60 days before the start, none after the end
    assert inputs.retail_gauge["as_of"].tolist() == ["20260215"]
    plain = FactorFactory([mom], calendar, DateCodec())
    assert plain.build_inputs(reader, plain.build_all(), "20260401", "20260415").retail_gauge.empty
    bare = FactorFactory([gauge], calendar, DateCodec())
    with pytest.raises(ConfigError):
        bare.build_inputs(reader, bare.build_all(), "20260401", "20260415")
