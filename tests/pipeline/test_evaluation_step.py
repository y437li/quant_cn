from __future__ import annotations

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.factor.factor_evaluator import FactorEvaluator
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.pipeline.evaluation_step import EvaluationStep
from quant_cn.statistic.block_bootstrap import BlockBootstrap
from quant_cn.statistic.hac_variance import HacVariance
from quant_cn.statistic.ic_calculator import IcCalculator
from quant_cn.statistic.ic_significance import IcSignificance
from quant_cn.statistic.multiple_testing_adjuster import MultipleTestingAdjuster
from quant_cn.statistic.quantile_returns import QuantileReturns
from quant_cn.statistic.return_stats import ReturnStats
from tests.pipeline.test_feature_step import build_step
from tests.support import MiniLake, SampleMarket


def build_evaluation(lake: MiniLake, config: Config) -> EvaluationStep:
    boot = BlockBootstrap(resamples=50, seed=0)
    evaluator = FactorEvaluator(
        IcCalculator(),
        IcSignificance(HacVariance(), boot),
        MultipleTestingAdjuster(),
        QuantileReturns(5),
        ReturnStats(),
        boot,
        [1],
    )
    reader = LakeReader(
        lake.catalog,
        lake.query,
        config.datasets,
        PitAligner(lake.catalog, lake.query, DateCodec()),
        TickerAliasMap(lake.catalog, lake.query),
        TradingCalendar(lake.query),
    )
    return EvaluationStep(
        lake.query,
        reader,
        evaluator,
        lake.writer,
        "c01",
        {"reversal": {"window": 5}},
        SampleMarket.DAYS[0],
    )


# TC-ES-001
def test_tc_es_001_reports(lake: MiniLake, config: Config) -> None:
    SampleMarket.write(lake, config)
    build_step(lake, config).run("r1")
    report = build_evaluation(lake, config).run("r2")
    folder = lake.lake_root / "derived" / "reports" / "c01"
    ic_test = pd.read_parquet(folder / "ic_test.parquet")
    assert (
        report.fetched == 3
        and (folder / "ic_series.parquet").exists()
        and (folder / "quantiles.parquet").exists()
    )
    main = ic_test[(ic_test["metric"] == "ic_mean") & (ic_test["window"] == "full")]
    assert (
        set(main["factor"]) == {"reversal", "turnover", "score"}
        and main["p_adj_holm"].notna().all()
    )
    trials = pd.read_parquet(lake.lake_root / "meta" / "trials" / "c01.parquet")
    assert len(trials) == 3


# TC-ES-002
def test_tc_es_002_rerun_and_empty(lake: MiniLake, config: Config) -> None:
    assert build_evaluation(lake, config).list_units() == []
    SampleMarket.write(lake, config)
    build_step(lake, config).run("r1")
    build_evaluation(lake, config).run("r2")
    build_evaluation(lake, config).run("r3")
    assert len(pd.read_parquet(lake.lake_root / "meta" / "trials" / "c01.parquet")) == 3
