"""Atomic, hive-named parquet writes into the lake (FOLDER_STRUCTURE §2 conventions)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from quant_cn.core.base_store import BaseStore
from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.rebuild_audit import PREV_SUFFIX

ROW_GROUP_SIZE = 256_000


class ParquetWriter(BaseStore):
    """
    Purpose:
        Write raw fetch results and curated partitions as zstd parquet, atomically
        (write `.tmp`, fsync, rename), so a crash never leaves a half-written file.

    Contract:
        Input:
            lake_root: Path  -- Config.lake.root; created on first write
        Output:
            instance; `write_raw`, `write_curated`, `raw_path`, `curated_path`
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli           -- composition root
        cli.ServiceBuilder       -- injected type or call
        pipeline.UniverseStep    -- injected type or call
        pipeline.EvaluationStep  -- injected type or call
        pipeline.FeatureStep     -- injected type or call

    Test cases:
        TC-PW-001  raw file lands at raw/<dataset>/<param>=<key>.parquet with coerced dtypes
        TC-PW-002  empty frame writes nothing and returns None
        TC-PW-003  failed write leaves no .tmp and no target; raises LakeError
        TC-PW-004  curated partition under year=YYYY, readable by DuckDB with hive partitioning
        TC-PW-005  curated write refuses a frame violating the schema
        TC-PW-006  rewriting a raw file keeps the first previous version as <file>.prev
        TC-PW-007  write_derived lands at derived/<name>/year=<year>/part-0.parquet
        TC-PW-008  write_table writes under derived/ or meta/ only
    """

    def __init__(self, lake_root: Path) -> None:
        self.lake_root = lake_root

    def get_raw_path(self, spec: DatasetSpec, key: str) -> Path:
        """
        Purpose:
            Target path of one raw fetch key.

        Contract:
            Input:
                spec: DatasetSpec; key: str
            Output:
                Path  -- <lake_root>/raw/<name>/<raw_filename>
            Raises:
                (none)
        """
        return self.lake_root / "raw" / spec.name / spec.get_raw_filename(key)

    def get_curated_path(self, spec: DatasetSpec, year: int | None) -> Path:
        """
        Purpose:
            Target path of one curated partition.

        Contract:
            Input:
                spec: DatasetSpec; year: int | None
            Output:
                Path  -- <lake_root>/curated/<path>/year=YYYY/part-0.parquet, or <path>.parquet
            Raises:
                (none)
        """
        base = self.lake_root / "curated" / spec.curated.path
        if year is None:
            return base.with_name(base.name + ".parquet")
        return base / f"year={year}" / "part-0.parquet"

    def write_raw(self, spec: DatasetSpec, key: str, df: pd.DataFrame) -> Path | None:
        """
        Purpose:
            Persist one fetch key's rows, dtypes coerced by the dataset schema (dates stay strings);
            an existing file is kept as `<file>.prev` until `rebuild` confirms it (D-083).

        Contract:
            Input:
                spec: DatasetSpec; key: str; df: DataFrame (may be empty)
            Output:
                Path | None  -- None when df is empty
            Raises:
                SchemaError  -- value not coercible
                LakeError    -- write failed
        """
        if df.empty:
            return None
        coerced = spec.build_schema().normalize(df)
        path = self.get_raw_path(spec, key)
        prev = path.with_name(path.name + PREV_SUFFIX)
        if path.exists() and not prev.exists():  # keep the oldest until rebuild confirms (D-083)
            try:
                shutil.copy2(path, prev)
            except OSError as exc:
                raise LakeError(f"cannot keep previous raw file {path}: {exc}") from exc
        self._write_atomic(coerced, path)
        return path

    def write_curated(self, spec: DatasetSpec, year: int | None, df: pd.DataFrame) -> Path:
        """
        Purpose:
            Replace one curated partition after validating it against the dataset schema.

        Contract:
            Input:
                spec: DatasetSpec; year: int | None; df: DataFrame satisfying spec.build_schema()
            Output:
                Path
            Raises:
                SchemaError  -- schema violation; nothing written
                LakeError    -- write failed
        """
        spec.build_schema().validate(df)
        path = self.get_curated_path(spec, year)
        self._write_atomic(df, path)
        return path

    def write_derived(self, name: str, year: int, df: pd.DataFrame) -> Path:
        """
        Purpose:
            Persist one year of a materialised derived table (e.g. the universe).

        Contract:
            Input:
                name: str  -- folder under derived/, e.g. "universe"
                year: int  -- partition
                df:   DataFrame  -- already validated by its frame schema
            Output:
                Path  -- derived/<name>/year=<year>/part-0.parquet (atomic replace)
            Raises:
                LakeError  -- write failed
        """
        path = self.lake_root / "derived" / name / f"year={year}" / "part-0.parquet"
        self._write_atomic(df, path)
        return path

    def write_table(self, zone: str, rel_path: str, df: pd.DataFrame) -> Path:
        """
        Purpose:
            Persist a whole small table (reports under derived/, logs under meta/).

        Contract:
            Input:
                zone:     str  -- "derived" or "meta"
                rel_path: str  -- path below the zone ending in .parquet
                df:       DataFrame
            Output:
                Path  -- <lake_root>/<zone>/<rel_path> (atomic replace)
            Raises:
                ValueError  -- other zone, or a path escaping the zone
                LakeError   -- write failed
        """
        if zone not in ("derived", "meta") or ".." in Path(rel_path).parts:
            raise ValueError(f"cannot write {zone}/{rel_path}")
        path = self.lake_root / zone / rel_path
        self._write_atomic(df, path)
        return path

    def _write_atomic(self, df: pd.DataFrame, path: Path) -> None:
        tmp = path.with_name(path.name + ".tmp")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            table = pa.Table.from_pandas(df, preserve_index=False)
            pq.write_table(table, tmp, compression="zstd", row_group_size=ROW_GROUP_SIZE)
            fd = os.open(tmp, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(tmp, path)
        except (OSError, pa.ArrowException) as exc:
            tmp.unlink(missing_ok=True)
            raise LakeError(f"failed to write {path}: {exc}") from exc
