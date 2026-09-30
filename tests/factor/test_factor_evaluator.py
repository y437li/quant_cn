from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.core.frames import PRICE_PANEL
from quant_cn.factor.factor_evaluator import FactorEvaluator
from quant_cn.statistic.block_bootstrap import BlockBootstrap
from quant_cn.statistic.hac_variance import HacVariance
from quant_cn.statistic.ic_calculator import IcCalculator
from quant_cn.statistic.ic_significance import IcSignificance
from quant_cn.statistic.multiple_testing_adjuster import MultipleTestingAdjuster
from quant_cn.statistic.quantile_returns import QuantileReturns
from quant_cn.statistic.return_stats import ReturnStats
from quant_cn.statistic.trial_log import TrialLog

N, T = 80, 260
DAYS = pd.bdate_range("2024-01-01", periods=T).strftime("%Y%m%d").tolist()
CODES = [f"{i:06d}.SH" for i in range(N)]


def build_market() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(7)
    signal = rng.standard_normal((T, N))
    noise = rng.standard_normal((T, N))
    ret = np.zeros((T, N))
    ret[1:] = 0.02 * signal[:-1] + 0.01 * rng.standard_normal(
        (T - 1, N)
    )  # r(t+1) driven by signal(t)
    close = 10 * np.cumprod(1 + ret, axis=0)
    opens = np.vstack([close[:1], close[:-1]])  # open(t) = close(t-1)
    prices = pd.DataFrame({c: np.nan for c in PRICE_PANEL.columns}, index=range(T * N)).assign(
        trade_date=np.repeat(DAYS, N),
        ts_code=np.tile(CODES, T),
        open=opens.ravel(),
        close=close.ravel(),
        adj_factor=1.0,
        close_adj=close.ravel(),
    )
    factors = pd.concat(
        [
            pd.DataFrame(
                {
                    "trade_date": np.repeat(DAYS, N),
                    "ts_code": np.tile(CODES, T),
                    "factor": name,
                    "value": values.ravel(),
                    "value_raw": values.ravel(),
                }
            )
            for name, values in (("good", signal), ("noise", noise))
        ],
        ignore_index=True,
    )
    return factors, PRICE_PANEL.normalize(prices, strict=True)


def build_evaluator() -> FactorEvaluator:
    boot = BlockBootstrap(resamples=200, seed=1)
    return FactorEvaluator(
        IcCalculator(),
        IcSignificance(HacVariance(), boot),
        MultipleTestingAdjuster(),
        QuantileReturns(5),
        ReturnStats(),
        boot,
        horizons=[1, 5],
    )


# TC-FEV-001
def test_tc_fev_001_signal_vs_noise() -> None:
    report = build_evaluator().compute(*build_market())
    main = report.ic_test[
        (report.ic_test["metric"] == "ic_mean") & (report.ic_test["window"] == "full")
    ]
    good = main[(main["factor"] == "good") & (main["horizon"] == 1.0)].iloc[0]
    noise = main[(main["factor"] == "noise") & (main["horizon"] == 1.0)].iloc[0]
    assert good["value"] > 0.5 and good["hlz_pass"] == 1.0
    assert abs(noise["value"]) < 0.05 and noise["hlz_pass"] == 0.0
    ladder = (
        report.quantiles[
            (report.quantiles["factor"] == "good")
            & (report.quantiles["horizon"] == 1.0)
            & (report.quantiles["quantile"] > 0)
        ]
        .groupby("quantile")["ret"]
        .mean()
    )
    assert ladder.is_monotonic_increasing
    assert set(main["horizon"]) == {1.0, 5.0} and set(main["factor"]) == {"good", "noise"}


# TC-FEV-002
def test_tc_fev_002_adjusted_and_extras() -> None:
    report = build_evaluator().compute(*build_market())
    main = report.ic_test[
        (report.ic_test["metric"] == "ic_mean") & (report.ic_test["window"] == "full")
    ]
    assert main[["p_adj_holm", "p_adj_bhy", "p_adj_romano_wolf"]].notna().all().all()
    metrics = set(report.ic_test["metric"])
    assert {"half_life", "rank_autocorr", "ls_sharpe", "icir", "fisher_z"} <= metrics


# TC-FEV-003
def test_tc_fev_003_trials() -> None:
    log, evaluator, inputs = TrialLog("c01"), build_evaluator(), build_market()
    evaluator.compute(*inputs, trial_log=log, params={"good": {"lag": 1}})
    assert log.n_trials == 4  # 2 factors x 2 horizons
    evaluator.compute(*inputs, trial_log=log, params={"good": {"lag": 1}})
    assert log.n_trials == 4
