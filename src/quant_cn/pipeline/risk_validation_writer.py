"""The risk model's acceptance report: bias statistics and fit (plan 05 phase 5)."""

from __future__ import annotations

import logging

import pandas as pd

from quant_cn.core.frames import RISK_VALIDATION
from quant_cn.core.risk_model_settings import RiskModelSettings
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.risk.risk_model_validator import RiskModelValidator

logger = logging.getLogger(__name__)

_BENCHMARK_SQL = """
WITH w AS (SELECT * FROM curated.index_weight
           WHERE list_contains(?, index_code) AND trade_date <= ?)
SELECT index_code AS portfolio, con_code AS ts_code, weight FROM w
QUALIFY trade_date = max(trade_date) OVER (PARTITION BY index_code)
ORDER BY portfolio, ts_code"""
BAND = (0.85, 1.15)  # plan 05 phase 5 acceptance band for random-portfolio bias statistics


class RiskValidationWriter:
    """
    Purpose:
        After a fit, test the stored model over the last `validation_sessions` forecast
        sessions and write derived/reports/risk_<name>/validation.parquet (RISK_VALIDATION):
        median / mean R^2 (whole history and window), the bias statistic of every factor, of
        `validation_portfolios` random long-only portfolios of `validation_names` stocks drawn
        from the names with a forecast on the first window session, and of each benchmark index
        (index_weight weights on or before the window start, held fixed), plus the summary
        rows share_in_band and median_bias over the random portfolios.

    Contract:
        Input:
            query: LakeQuery; reader: LakeReader; validator: RiskModelValidator
            writer: ParquetWriter; settings: RiskModelSettings
        Output:
            instance; `write(factor_returns, run_id) -> pd.DataFrame`
        Raises:
            (none at construction)

    Used by:
        pipeline.RiskModelStep  -- report after the fit
        cli.ServiceBuilder      -- injected type or call

    Test cases:
        TC-RVW-001  writes fit, factor, random-portfolio, benchmark and summary rows for the
                    window; notes carry the run id
        TC-RVW-002  fewer than two forecast sessions -> nothing written, empty frame returned
    """

    def __init__(
        self,
        query: LakeQuery,
        reader: LakeReader,
        validator: RiskModelValidator,
        writer: ParquetWriter,
        settings: RiskModelSettings,
    ) -> None:
        self._query = query
        self._reader = reader
        self._validator = validator
        self._writer = writer
        self._s = settings

    def write(self, factor_returns: pd.DataFrame, run_id: str) -> pd.DataFrame:
        """
        Purpose:
            Compute and persist the validation report.

        Contract:
            Input:
                factor_returns: DataFrame  -- FACTOR_RETURN, full history
                run_id: str
            Output:
                DataFrame  -- RISK_VALIDATION rows written (empty when the window is too short)
            Raises:
                LakeError  -- views missing; SchemaError
        """
        sessions = self._query.sql(
            "SELECT DISTINCT trade_date FROM derived.risk_specific_risk ORDER BY 1"
        )["trade_date"].tolist()
        window = sessions[-(self._s.validation_sessions + 1) :]
        if len(window) < 2:  # noqa: PLR2004 -- one forecast and one realised session
            return RISK_VALIDATION.normalize(
                pd.DataFrame(columns=RISK_VALIDATION.columns), strict=True
            )
        start, end = window[0], window[-2]
        cov = self._query.sql(
            "SELECT * FROM derived.risk_factor_cov "
            "WHERE factor_i = factor_j AND trade_date BETWEEN ? AND ?",
            [start, end],
        )
        parts = [
            self._validator.compute_fit(factor_returns, factor_returns["trade_date"].min(), end),
            self._validator.compute_fit(factor_returns, start, end).assign(scope="window"),
            self._validator.compute_factor_bias(factor_returns, cov, start, end),
            self._compute_portfolios(window),
        ]
        out = pd.concat(parts, ignore_index=True).assign(
            notes=f"run {run_id}; model {self._s.name}"
        )
        out = RISK_VALIDATION.validate(RISK_VALIDATION.normalize(out, strict=True))
        self._writer.write_table("derived", f"reports/risk_{self._s.name}/validation.parquet", out)
        logger.info("risk validation %s..%s: %d rows", start, end, len(out))
        return out

    def _compute_portfolios(self, window: list[str]) -> pd.DataFrame:
        names = self._query.sql(
            "SELECT ts_code FROM derived.risk_specific_risk WHERE trade_date = ?", [window[0]]
        )["ts_code"].tolist()
        random = self._validator.build_random_portfolios(
            names, self._s.validation_portfolios, self._s.validation_names
        )
        portfolios = pd.concat([random, self._read_benchmarks(window[0])], ignore_index=True)
        prices = self._reader.read_prices(
            window[0], window[-1], tickers=sorted(set(portfolios["ts_code"])), dense=True
        )
        close = prices.pivot(index="trade_date", columns="ts_code", values="close_adj").sort_index()
        returns = (
            (close / close.shift(1) - 1.0)
            .reset_index()
            .melt(id_vars="trade_date", var_name="ts_code", value_name="ret")
        )
        paired = self._validator.compute_portfolio_forecasts(portfolios, window, returns.dropna())
        bias = self._validator.compute_bias(paired)
        rp = bias[(bias["metric"] == "bias") & bias["scope"].str.startswith("rp_")]["value"]
        last, span = bias["trade_date"].max(), bias["window"].iloc[0]
        summary = pd.DataFrame(
            [
                {
                    "trade_date": last,
                    "metric": "share_in_band",
                    "scope": "random_portfolios",
                    "value": float(rp.between(*BAND).mean()),
                    "window": span,
                    "notes": "",
                },
                {
                    "trade_date": last,
                    "metric": "median_bias",
                    "scope": "random_portfolios",
                    "value": float(rp.median()),
                    "window": span,
                    "notes": "",
                },
            ]
        )
        return pd.concat([bias, summary], ignore_index=True)

    def _read_benchmarks(self, date: str) -> pd.DataFrame:
        if not self._s.benchmarks or not self._query.has_view("curated.index_weight"):
            return pd.DataFrame(columns=["portfolio", "ts_code", "weight"])
        frame = self._query.sql(_BENCHMARK_SQL, [list(self._s.benchmarks), date])
        return frame.assign(weight=frame["weight"] / 100.0)
