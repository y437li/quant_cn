"""Atomic, hive-named parquet writes into the lake (FOLDER_STRUCTURE §2 conventions)."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from quant_cn.core.base_store import BaseStore
from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.exceptions import LakeError

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
        core.BaseFetcher.run             -- via BaseStore.write_raw
        lake.Compactor.rebuild           -- write_curated
        data_loading.FetcherFactory      -- injected into every fetcher
        cli.QuantCnCli                   -- composition root

    Test cases:
        TC-PW-001  raw file lands at raw/<dataset>/<param>=<key>.parquet with coerced dtypes
        TC-PW-002  empty frame writes nothing and returns None
        TC-PW-003  failed write leaves no .tmp and no target; raises LakeError
        TC-PW-004  curated partition under year=YYYY, readable by DuckDB with hive partitioning
        TC-PW-005  curated write refuses a frame violating the schema
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
            Persist one fetch key's rows, dtypes coerced by the dataset schema (dates stay strings).

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
