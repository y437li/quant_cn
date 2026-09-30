"""Evaluate the campaign's features and persist reports and trials (plan 04 phase 5)."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from quant_cn.core.base_step import BaseStep, ProgressHook
from quant_cn.core.frames import FACTOR_PANEL
from quant_cn.core.step_report import StepReport
from quant_cn.factor.factor_evaluator import FactorEvaluator
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.statistic.trial_log import TrialLog

logger = logging.getLogger(__name__)


class EvaluationStep(BaseStep):
    """
    Purpose:
        Evaluate every factor in derived.features (FactorEvaluator, one factor at a time to bound
        memory, forward returns from the open of t+1 on dense prices), apply the campaign-level
        adjustment once over all factor x horizon tests, and write derived/reports/<campaign>/
        ic_series, ic_test and quantiles; the campaign's TrialLog (meta/trials/<campaign>.parquet)
        is resumed and saved, so re-running the same variants does not inflate N.

    Contract:
        Input:
            query: LakeQuery; reader: LakeReader; evaluator: FactorEvaluator; writer: ParquetWriter
            campaign: str                               -- campaign id
            params:   Mapping[str, Mapping[str, object]] -- factor -> parameters (trial records)
            start:    str                               -- first feature date
        Output:
            instance; BaseStep API
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-ES-001  reports and the trial log are written; campaign adjustment covers all factors
        TC-ES-002  a second run keeps the trial count; without derived.features nothing runs
    """

    def __init__(
        self,
        query: LakeQuery,
        reader: LakeReader,
        evaluator: FactorEvaluator,
        writer: ParquetWriter,
        campaign: str,
        params: Mapping[str, Mapping[str, object]],
        start: str,
    ) -> None:
        self._query = query
        self._reader = reader
        self._evaluator = evaluator
        self._writer = writer
        self._campaign = campaign
        self._params = dict(params)
        self._start = start

    @property
    def name(self) -> str:
        """
        Purpose:
            Step name.

        Contract:
            Input:
                (none)
            Output:
                str  -- "evaluate"
            Raises:
                (none)
        """
        return "evaluate"

    def list_units(self) -> list[str]:
        """
        Purpose:
            Factors to evaluate.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- distinct factors in derived.features (empty without it)
            Raises:
                LakeError  -- query failure
        """
        if not self._query.has_view("derived.features"):
            return []
        names = self._query.sql("SELECT DISTINCT factor FROM derived.features ORDER BY 1")
        return [str(n) for n in names["factor"]]

    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        """
        Purpose:
            Evaluate, adjust, write reports and the trial log.

        Contract:
            Input:
                run_id: str; progress: ProgressHook | None
            Output:
                StepReport  -- keys_total = factors, fetched = evaluated, rows = IC_TEST rows
            Raises:
                LakeError, SchemaError
        """
        units = self.list_units()
        report = StepReport(self.name, keys_total=len(units))
        if not units:
            return report
        last = str(
            self._query.sql("SELECT max(trade_date) AS d FROM derived.features")["d"].iloc[0]
        )
        prices = self._reader.read_prices(self._start, "99991231", dense=True)
        trials = self._load_trials()
        parts = []
        for name in units:
            panel = self._query.sql(
                "SELECT trade_date, ts_code, factor, value, value_raw FROM derived.features "
                "WHERE factor = ? AND trade_date BETWEEN ? AND ? ORDER BY trade_date, ts_code",
                [name, self._start, last],
            )
            panel = FACTOR_PANEL.validate(FACTOR_PANEL.normalize(panel, strict=True))
            parts.append(self._evaluator.compute(panel, prices, trials, self._params, adjust=False))
            report.fetched += 1
            if progress:
                progress(name, "fetched")
        ic_series = pd.concat([p.ic_series for p in parts], ignore_index=True)
        ic_test = self._evaluator.build_campaign(
            ic_series, pd.concat([p.ic_test for p in parts], ignore_index=True)
        )
        quantiles = pd.concat([p.quantiles for p in parts], ignore_index=True)
        folder = f"reports/{self._campaign}"
        self._writer.write_table("derived", f"{folder}/ic_series.parquet", ic_series)
        self._writer.write_table("derived", f"{folder}/ic_test.parquet", ic_test)
        self._writer.write_table("derived", f"{folder}/quantiles.parquet", quantiles)
        self._writer.write_table("meta", f"trials/{self._campaign}.parquet", trials.build_frame())
        report.rows = len(ic_test)
        logger.info("campaign %s: %s trials", self._campaign, trials.n_trials)
        return report

    def _load_trials(self) -> TrialLog:
        path = Path(self._writer.lake_root) / "meta" / "trials" / f"{self._campaign}.parquet"
        if path.exists():
            return TrialLog.from_frame(self._campaign, pd.read_parquet(path))
        return TrialLog(self._campaign)
