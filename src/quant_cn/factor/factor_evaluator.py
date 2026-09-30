"""Evaluate a campaign of factors: IC, significance, adjustments, ladders (SRC_DESIGN §2.5)."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from quant_cn.core.frames import FACTOR_PANEL, IC_SERIES, IC_TEST, QUANTILE_RETURNS
from quant_cn.statistic.block_bootstrap import BlockBootstrap
from quant_cn.statistic.ic_calculator import IcCalculator
from quant_cn.statistic.ic_significance import IcSignificance
from quant_cn.statistic.multiple_testing_adjuster import MultipleTestingAdjuster
from quant_cn.statistic.quantile_returns import QuantileReturns
from quant_cn.statistic.return_stats import ReturnStats
from quant_cn.statistic.trial_log import TrialLog

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FactorReport:
    """
    Purpose:
        The evaluation of one campaign: IC series, every test result, quantile ladders.

    Contract:
        Input:
            ic_series: DataFrame  -- IC_SERIES
            ic_test:   DataFrame  -- IC_TEST (per factor and horizon, campaign-adjusted)
            quantiles: DataFrame  -- QUANTILE_RETURNS
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        factor.FactorEvaluator  -- compute output

    Test cases:
        TC-FEV-001  (built by FactorEvaluator.compute)
    """

    ic_series: pd.DataFrame
    ic_test: pd.DataFrame
    quantiles: pd.DataFrame


class FactorEvaluator:
    """
    Purpose:
        Evaluate every factor of a campaign (FACTOR_TESTING_DESIGN §2, §3, §6): tradeable forward
        returns from the open of t+1, IC series per horizon, the IcSignificance tests, decay across
        horizons (half-life), rank autocorrelation (turnover proxy), quantile ladders and long-short
        statistics on non-overlapping samples, then the campaign-level Holm / BHY / Romano-Wolf
        adjustment and HLZ flag over all factor x horizon mean-IC tests. Records each variant in
        the TrialLog (identical variants are not recorded twice).

    Contract:
        Input:
            ic_calculator: IcCalculator; significance: IcSignificance
            adjuster: MultipleTestingAdjuster; quantiles: QuantileReturns
            return_stats: ReturnStats; bootstrap: BlockBootstrap  -- Romano-Wolf draws
            horizons: Sequence[int]
        Output:
            instance; `compute`, `build_campaign`
        Raises:
            ValueError  -- no horizons

    Used by:
        notebooks                -- factor campaign (phase 6)
        pipeline.EvaluationStep  -- injected type or call
        cli.ServiceBuilder       -- injected type or call

    Test cases:
        TC-FEV-001  a factor that predicts returns gets a positive mean IC, hlz_pass at high t,
                    an increasing ladder; noise does not; rows per factor x horizon exist
        TC-FEV-002  campaign adjustment fills p_adj_holm/bhy/romano_wolf on the full-window ic_mean
                    rows; decay and turnover rows present
        TC-FEV-003  TrialLog gets one trial per factor x horizon; a second run adds none
    """

    def __init__(
        self,
        ic_calculator: IcCalculator,
        significance: IcSignificance,
        adjuster: MultipleTestingAdjuster,
        quantiles: QuantileReturns,
        return_stats: ReturnStats,
        bootstrap: BlockBootstrap,
        horizons: Sequence[int],
    ) -> None:
        if not horizons:
            raise ValueError("need at least one horizon")
        self._ic = ic_calculator
        self._sig = significance
        self._adj = adjuster
        self._quantiles = quantiles
        self._stats = return_stats
        self._boot = bootstrap
        self._horizons = list(horizons)

    def compute(
        self,
        factors: pd.DataFrame,
        prices: pd.DataFrame,
        trial_log: TrialLog | None = None,
        params: Mapping[str, Mapping[str, object]] | None = None,
        adjust: bool = True,
    ) -> FactorReport:
        """
        Purpose:
            The campaign report.

        Contract:
            Input:
                factors:   DataFrame           -- FACTOR_PANEL, processed values, universe applied
                prices:    DataFrame           -- dense PRICE_PANEL covering the horizons
                trial_log: TrialLog | None     -- variants recorded here
                params:    Mapping | None      -- factor -> parameters (for the TrialLog)
                adjust:    bool                -- apply the campaign adjustment (False when the
                                                  caller evaluates factor by factor and calls
                                                  build_campaign once on the concatenation)
            Output:
                FactorReport
            Raises:
                SchemaError  -- inputs not FACTOR_PANEL / PRICE_PANEL
        """
        panel = FACTOR_PANEL.validate(factors)
        ic_series, ladder = self._compute_series(panel, prices)
        rows = [
            self._build_factor_rows(ic_series, ladder, name)
            for name in sorted(panel["factor"].unique())
        ]
        rows.append(self._build_autocorr_rows(panel))
        ic_test = pd.concat([r for r in rows if not r.empty], ignore_index=True)
        if adjust:
            ic_test = self.build_campaign(ic_series, ic_test)
        if trial_log is not None:
            self._record_trials(trial_log, ic_test, params or {})
        logger.info(
            "evaluated %s factors x %s horizons", panel["factor"].nunique(), len(self._horizons)
        )
        return FactorReport(
            ic_series=IC_SERIES.validate(ic_series),
            ic_test=IC_TEST.validate(ic_test),
            quantiles=QUANTILE_RETURNS.validate(ladder),
        )

    def build_campaign(self, ic_series: pd.DataFrame, ic_test: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Campaign-level adjustment over every factor x horizon mean-IC test.

        Contract:
            Input:
                ic_series: DataFrame  -- IC_SERIES of the whole campaign
                ic_test:   DataFrame  -- IC_TEST of the whole campaign
            Output:
                DataFrame  -- IC_TEST with p_adj_holm, p_adj_bhy, p_adj_romano_wolf (block-bootstrap
                              draws shared across the family, recentred t) and hlz_pass on the
                              full-window ic_mean rows
            Raises:
                SchemaError  -- not IC_TEST
        """
        t_boot = self._build_t_boot(ic_series, ic_test)
        return self._adj.build_adjusted(ic_test, "ic_mean", "full", t_boot)

    def _compute_series(
        self, panel: pd.DataFrame, prices: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        ic_parts, ladder_parts = [], []
        for h in self._horizons:  # one horizon at a time keeps memory to one return panel
            returns = self._ic.build_forward_returns(prices, [h])
            ic_parts.append(self._ic.compute(panel, returns))
            ladder_parts.append(self._quantiles.compute(panel, returns))
        return pd.concat(ic_parts, ignore_index=True), pd.concat(ladder_parts, ignore_index=True)

    def _build_factor_rows(
        self, ic_series: pd.DataFrame, ladder: pd.DataFrame, name: str
    ) -> pd.DataFrame:
        rows, mean_ic = [], {}
        for h in self._horizons:
            series = ic_series[(ic_series["factor"] == name) & (ic_series["horizon"] == float(h))]
            if len(series) < 20:  # noqa: PLR2004 -- tests need a minimal sample
                continue
            rows.append(self._sig.compute(series))
            mean_ic[h] = float(series["ic"].mean())
            ls = ladder[
                (ladder["factor"] == name)
                & (ladder["horizon"] == float(h))
                & (ladder["quantile"] == 0)
            ]
            sampled = ls.sort_values("trade_date")["ret"].to_numpy()[::h]
            if len(sampled) >= 3:  # noqa: PLR2004
                st = self._stats.compute(sampled, horizon=h)
                rows.append(
                    self._build_scalar(
                        name,
                        h,
                        {
                            "ls_mean": st["mean"],
                            "ls_sharpe": st["sharpe"],
                            "ls_sharpe_period": st["sharpe_period"],
                        },
                    )
                )
        if len(mean_ic) >= 2 and all(v for v in mean_ic.values()):  # noqa: PLR2004
            decay = self._sig.compute_decay(mean_ic)
            rows.append(
                self._build_scalar(
                    name,
                    0,
                    {
                        "half_life": decay["half_life"],
                        "decay_r2": decay["r2"],
                        "peak_horizon": decay["peak_horizon"],
                        "accumulation_ratio": decay["accumulation_ratio"],
                    },
                )
            )
        return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=IC_TEST.columns)

    def _build_autocorr_rows(self, panel: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for name, frame in panel.groupby("factor"):
            ranks = frame.assign(r=frame.groupby("trade_date")["value"].rank(pct=True))
            wide = ranks.pivot_table(index="trade_date", columns="ts_code", values="r").sort_index()
            ac = [wide.iloc[i].corr(wide.iloc[i - 1]) for i in range(1, len(wide))]
            if ac:
                rows.append(
                    self._build_scalar(str(name), 1, {"rank_autocorr": float(np.nanmean(ac))})
                )
        return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=IC_TEST.columns)

    def _build_t_boot(self, ic_series: pd.DataFrame, ic_test: pd.DataFrame) -> np.ndarray | None:
        chosen = ic_test[(ic_test["metric"] == "ic_mean") & (ic_test["window"] == "full")]
        if len(chosen) < 2:  # noqa: PLR2004 -- a family needs two members
            return None
        wide = ic_series.pivot_table(index="trade_date", columns=["factor", "horizon"], values="ic")
        cols = list(zip(chosen["factor"], chosen["horizon"], strict=True))
        matrix = wide[cols].dropna().to_numpy()
        if len(matrix) < 20:  # noqa: PLR2004
            return None
        se = chosen["se"].to_numpy(float)
        block = self._boot.compute_block(int(max(self._horizons)))
        indices = self._boot.build_indices(len(matrix), block)
        means = matrix.mean(axis=0)
        return np.array([(matrix[idx].mean(axis=0) - means) / se for idx in indices])

    def _record_trials(
        self, trial_log: TrialLog, ic_test: pd.DataFrame, params: Mapping[str, Mapping[str, object]]
    ) -> None:
        main = ic_test[(ic_test["metric"] == "ic_mean") & (ic_test["window"] == "full")]
        sharpe = ic_test[ic_test["metric"] == "ls_sharpe_period"].set_index(["factor", "horizon"])[
            "value"
        ]
        columns = zip(
            main["factor"].astype(str).tolist(),
            main["horizon"].astype(int).tolist(),
            main["value"].astype(float).tolist(),
            strict=True,
        )
        for factor, horizon, ic_mean in columns:
            p = params.get(factor, {})
            if trial_log.find_trial(factor, p, horizon) is None:
                sr = sharpe.get((factor, float(horizon)))
                trial_log.add_trial(factor, p, horizon, None if sr is None else float(sr), ic_mean)

    @staticmethod
    def _build_scalar(factor: str, horizon: int, metrics: Mapping[str, float]) -> pd.DataFrame:
        base = {c: None for c in IC_TEST.columns}
        rows = [
            base
            | {
                "factor": factor,
                "horizon": float(horizon),
                "metric": m,
                "value": v,
                "window": "full",
            }
            for m, v in metrics.items()
        ]
        return IC_TEST.normalize(pd.DataFrame(rows), strict=True)
