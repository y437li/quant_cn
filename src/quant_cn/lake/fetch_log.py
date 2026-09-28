"""Done-keys for resumable downloads: `meta.fetch_log` + a durable parquet mirror (D-012)."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from quant_cn.core.base_fetch_log import BaseFetchLog
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_catalog import LakeCatalog

_TABLE = "meta.fetch_log"


class FetchLog(BaseFetchLog):
    """
    Purpose:
        Record finished (dataset, key) pairs in `meta.fetch_log`, mirror them to
        `meta/fetch_log.parquet` on save, and rebuild the table after the DuckDB file is lost.

    Contract:
        Input:
            catalog: LakeCatalog  -- provides the connection and raw file listing
        Output:
            instance; BaseFetchLog API plus `rebuild_from_mirror`, `mirror_path`
        Raises:
            LakeError  -- table cannot be created

    Used by:
        core.BaseFetcher.run             -- via BaseFetchLog
        pipeline.DownloadPipeline.run    -- pending counts in dry runs
        cli.QuantCnCli                   -- composition root; restore on rebuild

    Test cases:
        TC-FL-001  mark_done then is_done round trip
        TC-FL-002  flush writes the mirror; restore reloads it into a fresh catalog
        TC-FL-003  pending keeps input order and drops done keys
        TC-FL-004  restore adds raw files missing from the mirror
        TC-FL-005  mark_done twice for a key keeps one row with the latest values
    """

    def __init__(self, catalog: LakeCatalog) -> None:
        self._catalog = catalog
        self._ensure_table()

    @property
    def mirror_path(self) -> Path:
        """
        Purpose:
            Location of the durable parquet copy.

        Contract:
            Input:
                (none)
            Output:
                Path  -- <lake_root>/meta/fetch_log.parquet
            Raises:
                (none)
        """
        return self._catalog.lake_root / "meta" / "fetch_log.parquet"

    def read_done_keys(self, dataset: str) -> set[str]:
        """
        Purpose:
            Keys recorded for `dataset`.

        Contract:
            Input:
                dataset: str
            Output:
                set[str]
            Raises:
                LakeError  -- query failed
        """
        rows = self._query(f"SELECT key FROM {_TABLE} WHERE dataset = ?", [dataset])
        return {str(r[0]) for r in rows}

    def mark_done(self, dataset: str, key: str, n_rows: int, path: Path | None) -> None:
        """
        Purpose:
            Upsert one finished key.

        Contract:
            Input:
                dataset: str; key: str; n_rows: int >= 0; path: Path | None
            Output:
                None
            Raises:
                LakeError  -- write failed
        """
        self._query(f"DELETE FROM {_TABLE} WHERE dataset = ? AND key = ?", [dataset, key])
        self._query(
            f"INSERT INTO {_TABLE} VALUES (?, ?, ?, ?, current_timestamp)",
            [dataset, key, n_rows, str(path) if path else None],
        )

    def save(self) -> Path:
        """
        Purpose:
            Atomically rewrite `meta/fetch_log.parquet` from the table.

        Contract:
            Input:
                (none)
            Output:
                Path  -- the mirror file
            Raises:
                LakeError  -- write failed
        """
        tmp = self.mirror_path.with_name("fetch_log.parquet.tmp")
        target = str(tmp).replace("'", "''")
        self._query(
            f"COPY (SELECT * FROM {_TABLE} ORDER BY dataset, key) TO '{target}' (FORMAT parquet)"
        )
        try:
            os.replace(tmp, self.mirror_path)
        except OSError as exc:
            raise LakeError(f"cannot replace {self.mirror_path}: {exc}") from exc
        return self.mirror_path

    def rebuild_from_mirror(self) -> int:
        """
        Purpose:
            Rebuild the table from the parquet mirror, then add raw files the mirror does not know.

        Contract:
            Input:
                (none)
            Output:
                int  -- rows in the table afterwards
            Raises:
                LakeError  -- mirror unreadable
        """
        self._ensure_table()
        self._query(f"DELETE FROM {_TABLE}")
        if self.mirror_path.exists():
            src = str(self.mirror_path).replace("'", "''")
            self._query(f"INSERT INTO {_TABLE} SELECT * FROM read_parquet('{src}')")
        for spec in self._catalog.datasets.values():
            done = self.read_done_keys(spec.name)
            for path in self._catalog.list_raw_files(spec):
                key = path.stem.split("=", 1)[-1]
                if key not in done:
                    n_rows = pq.ParquetFile(path).metadata.num_rows
                    self.mark_done(spec.name, key, n_rows, path)
        self.save()
        count = self._query(f"SELECT count(*) FROM {_TABLE}")[0][0]
        return int(str(count))

    def _ensure_table(self) -> None:
        self._query(
            f"CREATE TABLE IF NOT EXISTS {_TABLE} (dataset VARCHAR, key VARCHAR, n_rows BIGINT, "
            "path VARCHAR, fetched_at TIMESTAMP, PRIMARY KEY (dataset, key))"
        )

    def _query(self, sql: str, params: list[object] | None = None) -> list[tuple[object, ...]]:
        try:
            return self._catalog.connection.execute(sql, params or []).fetchall()
        except duckdb.Error as exc:
            raise LakeError(f"fetch_log: {exc}") from exc
