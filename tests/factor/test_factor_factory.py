from __future__ import annotations

import pytest

from quant_cn.core.config import FactorSpec
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError
from quant_cn.factor.factor_factory import FactorFactory
from quant_cn.factor.library.momentum_factor import MomentumFactor
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.trading_calendar import TradingCalendar
from tests.support import MiniLake


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
