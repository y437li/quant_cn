"""raw -> curated -> derived: compaction, derived views, PIT states, indexes, digests."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path

from quant_cn.core.base_step import BaseStep, ProgressHook
from quant_cn.core.config import Config
from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.exceptions import ConfigError, LakeError
from quant_cn.core.step_report import StepReport
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.pipeline.runner import BaseRunner, PipelineReport

DIGEST_FILE = "derived_digests.json"


class CompactStep(BaseStep):
    """
    Purpose:
        Adapt Compactor to a pipeline step: one unit per dataset.

    Contract:
        Input:
            compactor: Compactor; specs: Sequence[DatasetSpec]
        Output:
            instance; BaseStep API
        Raises:
            (none at construction)

    Used by:
        pipeline.CuratePipeline  -- first step

    Test cases:
        TC-CP-001  curate compacts, builds derived views, PIT states and writes digests
    """

    def __init__(self, compactor: Compactor, specs: Sequence[DatasetSpec]) -> None:
        self._compactor = compactor
        self._specs = list(specs)

    @property
    def name(self) -> str:
        """
        Purpose:
            Step name.

        Contract:
            Input:
                (none)
            Output:
                str  -- "compact"
            Raises:
                (none)
        """
        return "compact"

    def list_units(self) -> list[str]:
        """
        Purpose:
            Datasets to compact.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- dataset names
            Raises:
                (none)
        """
        return [s.name for s in self._specs]

    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        """
        Purpose:
            Rebuild curated partitions for every dataset.

        Contract:
            Input:
                run_id: str; progress: ProgressHook | None
            Output:
                StepReport  -- keys_total = partitions, rows written, skipped = duplicates
            Raises:
                SchemaError, LakeError
        """
        report = StepReport(self.name)
        for spec in self._specs:
            part = self._compactor.rebuild(spec)
            report.keys_total += part.keys_total
            report.rows += part.rows
            report.skipped += part.skipped
            report.fetched += 1 if part.rows else 0
            report.empty += 0 if part.rows else 1
            if progress:
                progress(spec.name, "fetched" if part.rows else "empty")
        return report


class DeriveStep(BaseStep):
    """
    Purpose:
        Build the derived views and the PIT states view, then record a digest per derived view.

    Contract:
        Input:
            views: DerivedViews; aligner: PitAligner; query: LakeQuery; manifest_dir: Path
        Output:
            instance; BaseStep API, `build_digests`
        Raises:
            (none at construction)

    Used by:
        pipeline.CuratePipeline  -- second step

    Test cases:
        TC-CP-001  curate compacts, builds derived views, PIT states and writes digests
        TC-CP-002  digests are identical after deleting the catalog and curating again
    """

    def __init__(
        self, views: DerivedViews, aligner: PitAligner, query: LakeQuery, manifest_dir: Path
    ) -> None:
        self._views = views
        self._aligner = aligner
        self._query = query
        self._manifest_dir = manifest_dir

    @property
    def name(self) -> str:
        """
        Purpose:
            Step name.

        Contract:
            Input:
                (none)
            Output:
                str  -- "derive"
            Raises:
                (none)
        """
        return "derive"

    def list_units(self) -> list[str]:
        """
        Purpose:
            One unit: the derived layer.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- ["derived"]
            Raises:
                (none)
        """
        return ["derived"]

    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        """
        Purpose:
            Refresh derived views (and PIT states when fundamentals exist), write digests.

        Contract:
            Input:
                run_id: str; progress: ProgressHook | None
            Output:
                StepReport  -- keys_total = views built; message lists them
            Raises:
                LakeError
        """
        views = self._views.refresh()
        if "derived.fundamentals_long" in views and self._query.has_view("curated.trade_cal"):
            views.append(self._aligner.refresh())
        digests = self.build_digests(views)
        self._write_digests(digests)
        if progress:
            progress("derived", "fetched")
        return StepReport(self.name, keys_total=len(views), message=", ".join(views))

    def build_digests(self, views: Sequence[str]) -> dict[str, str]:
        """
        Purpose:
            md5 over every row of each view, rows ordered by their text form; equal digests mean
            byte-identical derived data.

        Contract:
            Input:
                views: Sequence[str]  -- existing view names
            Output:
                dict[str, str]  -- view -> md5 hex ("" for an empty view)
            Raises:
                LakeError  -- query failure
        """
        out: dict[str, str] = {}
        for view in views:
            rows = "string_agg(t::VARCHAR, chr(10) ORDER BY t::VARCHAR)"
            sql = f"SELECT md5({rows}) AS h FROM {view} t"
            value = self._query.sql(sql)["h"].iloc[0]
            out[view] = str(value) if isinstance(value, str) else ""
        return out

    def _write_digests(self, digests: dict[str, str]) -> None:
        path = self._manifest_dir / DIGEST_FILE
        try:
            self._manifest_dir.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_text(json.dumps(digests, indent=2, sort_keys=True), encoding="utf-8")
            os.replace(tmp, path)
        except OSError as exc:
            raise LakeError(f"cannot write {path}: {exc}") from exc


class CuratePipeline:
    """
    Purpose:
        Rebuild everything below raw/: compact every dataset, create derived views and PIT
        states, regenerate lake indexes, and record digests in meta/manifest/derived_digests.json.

    Contract:
        Input:
            config:    Config
            compactor: Compactor
            views:     DerivedViews
            aligner:   PitAligner
            query:     LakeQuery
            catalog:   LakeCatalog
            runner:    BaseRunner
        Output:
            instance; `run(datasets=None) -> PipelineReport`
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- `curate` command, `make lake-rebuild`

    Test cases:
        TC-CP-001  curate compacts, builds derived views, PIT states and writes digests
        TC-CP-002  digests are identical after deleting the catalog and curating again
        TC-CP-003  unknown dataset raises ConfigError
    """

    def __init__(
        self,
        config: Config,
        compactor: Compactor,
        views: DerivedViews,
        aligner: PitAligner,
        query: LakeQuery,
        catalog: LakeCatalog,
        runner: BaseRunner,
    ) -> None:
        self._config = config
        self._compactor = compactor
        self._views = views
        self._aligner = aligner
        self._query = query
        self._catalog = catalog
        self._runner = runner

    def run(self, datasets: Sequence[str] | None = None) -> PipelineReport:
        """
        Purpose:
            Compact the datasets (default all), then derive and index.

        Contract:
            Input:
                datasets: Sequence[str] | None  -- subset to compact; derived views always rebuilt
            Output:
                PipelineReport  -- steps "compact" and "derive"
            Raises:
                ConfigError  -- unknown dataset
                SchemaError, LakeError
        """
        names = list(datasets) if datasets else list(self._config.datasets)
        unknown = [n for n in names if n not in self._config.datasets]
        if unknown:
            raise ConfigError(f"unknown datasets: {unknown}")
        manifest = self._catalog.lake_root / "meta" / "manifest"
        steps: list[BaseStep] = [
            CompactStep(self._compactor, [self._config.get_dataset(n) for n in names]),
            DeriveStep(self._views, self._aligner, self._query, manifest),
        ]
        report = self._runner.run("curate", steps)
        self._catalog.write_indexes()
        return report
