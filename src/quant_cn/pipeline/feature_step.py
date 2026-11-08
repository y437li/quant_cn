"""Processed factors and the combined score, materialised to derived/features (plan 04 phase 5)."""

from __future__ import annotations

import logging

import pandas as pd

from quant_cn.core.base_step import BaseStep, ProgressHook
from quant_cn.core.step_report import StepReport
from quant_cn.factor.base_factor import BaseFactor
from quant_cn.factor.factor_factory import FactorFactory
from quant_cn.factor.factor_preprocessor import FactorPreprocessor
from quant_cn.factor.signal_combiner import SignalCombiner
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.exposure_reader import ExposureReader
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.pipeline.curate_pipeline import DeriveStep

logger = logging.getLogger(__name__)
TABLE = "features"


class FeatureStep(BaseStep):
    """
    Purpose:
        Build derived/features, one file per year from the campaign start: the six library
        factors (FactorFactory, PIT inputs from LakeReader), restricted to universe members,
        preprocessed (winsorise -> standardise -> neutralise on Shenwan L1 + log market cap,
        D-093) and the combined "score" (SignalCombiner), as FACTOR_PANEL. Runs inside curate
        after the derived views; then refreshes derived.features and merges its digest so
        `make lake-rebuild` proves the features byte-identical.

    Contract:
        Input:
            query: LakeQuery; reader: LakeReader; factory: FactorFactory
            exposures: ExposureReader
            preprocessor: FactorPreprocessor; combiner: SignalCombiner
            writer: ParquetWriter; views: DerivedViews; digests: DeriveStep
            start: str  -- first feature date (campaign start)
        Output:
            instance; BaseStep API
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-FS-001  writes one file per year with processed factors and the score for universe
                   members only; derived.features exists and its digest is recorded
        TC-FS-002  no universe yet -> no units, nothing written
    """

    def __init__(
        self,
        query: LakeQuery,
        reader: LakeReader,
        factory: FactorFactory,
        exposures: ExposureReader,
        preprocessor: FactorPreprocessor,
        combiner: SignalCombiner,
        writer: ParquetWriter,
        views: DerivedViews,
        digests: DeriveStep,
        start: str,
    ) -> None:
        self._query = query
        self._reader = reader
        self._factory = factory
        self._exposures = exposures
        self._preprocessor = preprocessor
        self._combiner = combiner
        self._writer = writer
        self._views = views
        self._digests = digests
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
                str  -- "features"
            Raises:
                (none)
        """
        return TABLE

    def list_units(self) -> list[str]:
        """
        Purpose:
            Years from the campaign start to the last universe session.

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
        if not isinstance(last, str):
            return []
        return [str(y) for y in range(int(self._start[:4]), int(last[:4]) + 1)]

    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        """
        Purpose:
            Build and write every year, then refresh the view and its digest.

        Contract:
            Input:
                run_id: str; progress: ProgressHook | None
            Output:
                StepReport  -- keys_total = years, fetched = years written, rows = rows written
            Raises:
                LakeError, SchemaError, ConfigError
        """
        units = self.list_units()
        report = StepReport(self.name, keys_total=len(units))
        factors = self._factory.build_all() if units else []
        for year in units:
            start, end = max(self._start, f"{year}0101"), f"{year}1231"
            panel = self._build_year(factors, start, end)
            self._writer.write_derived(TABLE, int(year), panel)
            report.fetched += 1
            report.rows += len(panel)
            if progress:
                progress(year, "fetched")
        if units:
            created = self._views.refresh_tables()
            self._digests.refresh_digests([v for v in created if v.endswith(TABLE)])
        return report

    def _build_year(self, factors: list[BaseFactor], start: str, end: str) -> pd.DataFrame:
        inputs = self._factory.build_inputs(self._reader, factors, start, end)
        raw = pd.concat([f.compute(inputs, start, end) for f in factors], ignore_index=True)
        members = self._reader.read_universe(start, end, members_only=True)[
            ["trade_date", "ts_code"]
        ]
        raw = raw.merge(members, on=["trade_date", "ts_code"])
        has_industry = self._query.has_view("derived.industry_l1")
        exposures = self._exposures.read_exposures(start, end) if has_industry else None
        processed = self._preprocessor.compute(raw, exposures)
        out = pd.concat([processed, self._combiner.compute(processed)], ignore_index=True)
        logger.info("features %s..%s: %s rows", start, end, len(out))
        return out.sort_values(["trade_date", "ts_code", "factor"]).reset_index(drop=True)
