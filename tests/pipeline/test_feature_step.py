from __future__ import annotations

import json

import pandas as pd

from quant_cn.core.config import Config, FactorSpec
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.frames import FACTOR_PANEL
from quant_cn.factor.factor_factory import FactorFactory
from quant_cn.factor.factor_preprocessor import FactorPreprocessor
from quant_cn.factor.signal_combiner import SignalCombiner
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.exposure_reader import ExposureReader
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.pipeline.curate_pipeline import DeriveStep
from quant_cn.pipeline.feature_step import FeatureStep
from quant_cn.statistic.standardizer import Standardizer
from tests.support import MiniLake, SampleMarket

SPECS = [
    FactorSpec(name="reversal", class_name="ReversalFactor", params={"window": 5}),
    FactorSpec(name="turnover", class_name="TurnoverFactor", params={"window": 5, "min_obs": 3}),
]


def build_step(lake: MiniLake, config: Config) -> FeatureStep:
    calendar, codec = TradingCalendar(lake.query), DateCodec()
    views = DerivedViews(lake.catalog, lake.query, config.datasets)
    aligner = PitAligner(lake.catalog, lake.query, codec)
    reader = LakeReader(
        lake.catalog,
        lake.query,
        config.datasets,
        aligner,
        TickerAliasMap(lake.catalog, lake.query),
        calendar,
    )
    derive = DeriveStep(views, aligner, lake.query, lake.lake_root / "meta" / "manifest")
    return FeatureStep(
        lake.query,
        reader,
        FactorFactory(SPECS, calendar, codec),
        ExposureReader(lake.query),
        FactorPreprocessor(None, Standardizer(), None),
        SignalCombiner({"reversal": 1.0, "turnover": 1.0}, Standardizer(), 2),
        lake.writer,
        views,
        derive,
        SampleMarket.DAYS[0],
    )


# TC-FS-001
def test_tc_fs_001_features(lake: MiniLake, config: Config) -> None:
    SampleMarket.write(lake, config)
    report = build_step(lake, config).run("r1")
    frame = pd.read_parquet(
        lake.lake_root / "derived" / "features" / "year=2026" / "part-0.parquet"
    )
    FACTOR_PANEL.validate(frame)
    assert report.fetched == 1 and report.rows == len(frame)
    assert set(frame["factor"]) == {"reversal", "turnover", "score"}
    assert "830001.BJ" not in set(frame["ts_code"])  # not a universe member
    assert lake.query.has_view("derived.features")
    digests = json.loads(
        (lake.lake_root / "meta" / "manifest" / "derived_digests.json").read_text()
    )
    assert "derived.features" in digests


# TC-FS-002
def test_tc_fs_002_no_universe(lake: MiniLake, config: Config) -> None:
    step = build_step(lake, config)
    assert step.list_units() == [] and step.run("r1").keys_total == 0
