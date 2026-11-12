"""Fit the risk model and materialise its frames under derived/risk_* (plan 05 phase 5)."""

from __future__ import annotations

import logging

import pandas as pd

from quant_cn.core.base_step import BaseStep, ProgressHook
from quant_cn.core.risk_model_settings import RiskModelSettings
from quant_cn.core.step_report import StepReport
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.pipeline.curate_pipeline import DeriveStep
from quant_cn.pipeline.risk_validation_writer import RiskValidationWriter
from quant_cn.risk.risk_input_loader import RiskInputLoader
from quant_cn.risk.risk_model import RiskModel

logger = logging.getLogger(__name__)

TABLES = {
    "exposure": "risk_exposure",
    "factor_return": "risk_factor_return",
    "specific_return": "risk_specific_return",
    "factor_cov": "risk_factor_cov",
    "specific_risk": "risk_specific_risk",
}


class RiskModelStep(BaseStep):
    """
    Purpose:
        Fit the configured RiskModel from `settings.start` to the last universe session and
        write one file per year of each frame (derived/risk_exposure, risk_factor_return,
        risk_specific_return, risk_factor_cov, risk_specific_risk). Stage A per year: inputs
        (from the session before the year so the first regression has exposures at t-1) ->
        exposures -> factor returns and residuals. Stage B: factor covariance over the whole
        factor-return history. Stage C: specific risk from the residual history and each
        session's exposures (read back from derived.risk_exposure). Then refreshes the views,
        merges their digests (rebuilds are checked like features), writes the validation
        report (RiskValidationWriter) and the monitor-style returns
        (derived/reports/risk_<name>/monitor_returns.parquet, D-130). A full refit; seeded,
        so reruns are byte-identical.

    Contract:
        Input:
            query: LakeQuery; loader: RiskInputLoader; model: RiskModel
            calendar: TradingCalendar; writer: ParquetWriter; views: DerivedViews
            digests: DeriveStep; validation: RiskValidationWriter; settings: RiskModelSettings
        Output:
            instance; BaseStep API
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-RMST-001  list_units = years from settings.start to the last universe session;
                     none without a universe
        TC-RMST-002  run writes every frame per year, refreshes the views and records digests
    """

    def __init__(
        self,
        query: LakeQuery,
        loader: RiskInputLoader,
        model: RiskModel,
        calendar: TradingCalendar,
        writer: ParquetWriter,
        views: DerivedViews,
        digests: DeriveStep,
        validation: RiskValidationWriter,
        settings: RiskModelSettings,
    ) -> None:
        self._query = query
        self._loader = loader
        self._model = model
        self._calendar = calendar
        self._writer = writer
        self._views = views
        self._digests = digests
        self._validation = validation
        self._s = settings
        self._monitor: list[pd.DataFrame] = []

    @property
    def name(self) -> str:
        """
        Purpose:
            Step name.

        Contract:
            Input:
                (none)
            Output:
                str  -- "risk_model"
            Raises:
                (none)
        """
        return "risk_model"

    def list_units(self) -> list[str]:
        """
        Purpose:
            Years from the model start to the last universe session.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- empty without derived.universe
            Raises:
                LakeError  -- query failure
        """
        if not self._query.has_view("derived.universe"):
            return []
        last = self._query.sql(
            "SELECT max(trade_date) AS d FROM derived.universe WHERE in_universe = 1"
        )["d"].iloc[0]
        if not isinstance(last, str) or last < self._s.start:
            return []
        return [str(y) for y in range(int(self._s.start[:4]), int(last[:4]) + 1)]

    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        """
        Purpose:
            Refit the model over every year and write all frames.

        Contract:
            Input:
                run_id: str; progress: ProgressHook | None
            Output:
                StepReport  -- keys_total = years, fetched = years written, rows = rows written
            Raises:
                LakeError, SchemaError
        """
        units = self.list_units()
        report = StepReport(self.name, keys_total=len(units))
        if not units:
            return report
        factor_returns, resid_parts, cap_parts = [], [], []
        previous = pd.DataFrame()
        for year in units:
            fr, resid, caps, previous = self._compute_year(year, previous, report)
            factor_returns.append(fr)
            resid_parts.append(resid)
            cap_parts.append(caps)
            if progress:
                progress(year, "fetched")
        history = pd.concat(factor_returns, ignore_index=True)
        self._write_by_year(TABLES["factor_cov"], self._model.compute_covariance(history), report)
        self._views.refresh_tables()
        resid = pd.concat(resid_parts).sort_index()
        caps = pd.concat(cap_parts).sort_index()
        self._write_specific(units, resid, caps, report)
        created = self._views.refresh_tables()
        risk_views = [v for v in created if v.startswith("derived.risk_")]
        self._digests.refresh_digests(risk_views, scalable=True)  # 100 M+ rows (D-135)
        self._validation.write(history, run_id)
        monitor = pd.concat(self._monitor, ignore_index=True)
        if not monitor.empty:
            rel = f"reports/risk_{self._s.name}/monitor_returns.parquet"
            self._writer.write_table("derived", rel, monitor)
            report.rows += len(monitor)
        self._monitor = []
        return report

    def _compute_year(
        self, year: str, previous: pd.DataFrame, report: StepReport
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        start, end = max(self._s.start, f"{year}0101"), f"{year}1231"
        inputs = self._loader.load(start, end)
        exposures = self._model.compute_exposures(inputs)
        both = pd.concat([previous, exposures], ignore_index=True)
        fr, resid = self._model.compute_factor_returns(both, inputs)
        self._monitor.append(self._model.compute_monitor_returns(both, inputs))
        for key, frame in (
            ("exposure", exposures),
            ("factor_return", fr),
            ("specific_return", resid),
        ):
            self._writer.write_derived(TABLES[key], int(year), frame)
            report.rows += len(frame)
        report.fetched += 1
        last = exposures["trade_date"].max() if not exposures.empty else None
        carry = exposures[exposures["trade_date"] == last] if last else pd.DataFrame()
        resid_wide = resid.pivot(index="trade_date", columns="ts_code", values="resid")
        caps = inputs.basic[inputs.basic["trade_date"] >= start]
        cap_wide = caps.pivot(index="trade_date", columns="ts_code", values="circ_mv") * 1e4
        logger.info("risk %s: %d exposures, %d factor returns", year, len(exposures), len(fr))
        return fr, resid_wide.astype("float32"), cap_wide.astype("float32"), carry

    def _write_specific(
        self, units: list[str], resid: pd.DataFrame, caps: pd.DataFrame, report: StepReport
    ) -> None:
        sigma_ts, obs = self._model.compute_specific_time_series(resid.astype(float))
        pre_parts = []
        for year in units:
            exposures = self._query.sql(
                "SELECT trade_date, ts_code, factor, exposure FROM derived.risk_exposure "
                "WHERE trade_date BETWEEN ? AND ?",
                [f"{year}0101", f"{year}1231"],
            )
            for date, part in exposures.groupby("trade_date", sort=True):
                ts, h, cap = (self._get_row(m, str(date)) for m in (sigma_ts, obs, caps))
                pre_parts.append(
                    self._model.compute_specific_session(ts, h, part, cap).assign(trade_date=date)
                )
        pre = pd.concat(pre_parts, ignore_index=True)
        final = self._model.compute_specific_final(pre, resid.astype(float))
        self._write_by_year(TABLES["specific_risk"], final, report)

    @staticmethod
    def _get_row(wide: pd.DataFrame, date: str) -> pd.Series:
        if date not in wide.index:
            return pd.Series(dtype=float)
        row = wide.loc[date]
        return row if isinstance(row, pd.Series) else row.iloc[0]

    def _write_by_year(self, table: str, frame: pd.DataFrame, report: StepReport) -> None:
        years = frame["trade_date"].str[:4]
        for year in sorted(years.unique()):
            part = frame[years == year].reset_index(drop=True)
            self._writer.write_derived(table, int(year), part)
            report.rows += len(part)
        logger.info("%s: %d rows", table, len(frame))
