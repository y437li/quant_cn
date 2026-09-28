"""raw/ -> curated/: typed, deduplicated, yearly partitions with manifests (D-012)."""

from __future__ import annotations

import json
import logging
import os

import pandas as pd

from quant_cn.core.base_store import BaseStore
from quant_cn.core.clock import Clock
from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.exceptions import LakeError
from quant_cn.core.step_report import StepReport
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)


class Compactor:
    """
    Purpose:
        Rebuild a dataset's curated partitions from its raw files: select declared fields, cast
        dtypes, drop duplicate primary keys (keeping one), sort by partition date then key,
        validate, write, and record a manifest in `meta/manifest/<dataset>.json`.

    Contract:
        Input:
            catalog: LakeCatalog  -- views and paths
            query:   LakeQuery    -- reads raw.<dataset>
            store:   BaseStore    -- write_curated
            clock:   Clock        -- manifest timestamp
        Output:
            instance; `compact`
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli           -- `compact` and `rebuild` commands
        pipeline.CompactStep     -- injected type or call
        pipeline.CuratePipeline  -- injected type or call

    Test cases:
        TC-CO-001  daily raw files compact into one partition per year, sorted, typed
        TC-CO-002  duplicate primary keys are dropped and counted in the manifest
        TC-CO-003  unpartitioned dataset compacts into a single curated file
        TC-CO-004  dataset without raw files returns a report with zero rows and writes nothing
        TC-CO-005  curated view is queryable after compaction
    """

    def __init__(
        self, catalog: LakeCatalog, query: LakeQuery, store: BaseStore, clock: Clock
    ) -> None:
        self._catalog = catalog
        self._query = query
        self._store = store
        self._clock = clock

    def rebuild(self, spec: DatasetSpec, years: set[int] | None = None) -> StepReport:
        """
        Purpose:
            Replace the curated partitions of `spec` (all years, or only `years`).

        Contract:
            Input:
                spec:  DatasetSpec
                years: set[int] | None  -- restrict to these partition years; ignored when the
                                           dataset is unpartitioned
            Output:
                StepReport  -- keys_total = partitions written, rows = rows written,
                               skipped = duplicate primary keys dropped
            Raises:
                SchemaError  -- a partition violates the schema; that partition is not written
                LakeError    -- read or write failure
        """
        report = StepReport(f"compact:{spec.name}")
        self._catalog.refresh_view(spec)
        view = f"raw.{spec.name}"
        if not self._query.has_view(view):
            report.message = "no raw files"
            return report
        partitions: dict[str, int] = {}
        column = spec.curated.partition_by
        if column is None:
            df = self._normalize_frame(spec, self._query.sql(f"SELECT * FROM {view}"), report)
            self._store.write_curated(spec, None, df)
            partitions["all"] = len(df)
        else:
            for year in self._list_years(view, column, years):
                sql = f"SELECT * FROM {view} WHERE {column} BETWEEN ? AND ?"
                raw = self._query.sql(sql, [f"{year}0101", f"{year}1231"])
                df = self._normalize_frame(spec, raw, report)
                self._store.write_curated(spec, year, df)
                partitions[str(year)] = len(df)
        report.keys_total = len(partitions)
        report.rows = sum(partitions.values())
        self._write_manifest(spec, partitions, report.skipped)
        self._catalog.refresh_view(spec)
        logger.info("compacted %s: %s partitions, %s rows", spec.name, len(partitions), report.rows)
        return report

    def _list_years(self, view: str, column: str, only: set[int] | None) -> list[int]:
        found = self._query.sql(f"SELECT DISTINCT substr({column}, 1, 4) AS y FROM {view}")
        years = sorted(int(y) for y in found["y"].dropna())
        return [y for y in years if only is None or y in only]

    def _normalize_frame(
        self, spec: DatasetSpec, raw: pd.DataFrame, report: StepReport
    ) -> pd.DataFrame:
        df = spec.build_schema().normalize(raw, strict=True).drop_duplicates()
        before = len(df)
        if spec.primary_key:
            df = df.drop_duplicates(subset=spec.primary_key, keep="last")
        order = [c for c in [spec.curated.partition_by, *spec.primary_key] if c]
        if order:
            df = df.sort_values(list(dict.fromkeys(order)), kind="stable")
        report.skipped += before - len(df)
        return df.reset_index(drop=True)

    def _write_manifest(self, spec: DatasetSpec, partitions: dict[str, int], dropped: int) -> None:
        folder = self._catalog.lake_root / "meta" / "manifest"
        path = folder / f"{spec.name}.json"
        body = {
            "dataset": spec.name,
            "compacted_at": self._clock.get_now().isoformat(timespec="seconds"),
            "curated_path": spec.curated.path,
            "partition_by": spec.curated.partition_by,
            "partitions": partitions,
            "duplicate_keys_dropped": dropped,
        }
        try:
            folder.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_text(json.dumps(body, indent=2), encoding="utf-8")
            os.replace(tmp, path)
        except OSError as exc:
            raise LakeError(f"cannot write manifest {path}: {exc}") from exc
