"""The DuckDB catalog over the lake: views per dataset and zone, metadata, generated indexes."""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Mapping
from pathlib import Path

import duckdb

from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.exceptions import LakeError

ZONES = ("raw", "curated", "meta", "external")
DB_NAME = "quant_cn.duckdb"


class LakeCatalog:
    """
    Purpose:
        Own the lake's single DuckDB connection (`meta/quant_cn.duckdb`): schemas `raw`, `curated`,
        `meta`; one view per dataset and zone; `meta.dataset_meta`; generated INDEX.md files.
        The DuckDB file is disposable: `rebuild()` recreates it from the parquet files.

    Contract:
        Input:
            lake_root: Path                     -- zone folders created if missing
            datasets: Mapping[str, DatasetSpec] -- Config.datasets
        Output:
            instance; `connection`, `refresh_view(s)`, `rebuild`, `write_indexes`, `close`
        Raises:
            LakeError  -- DuckDB file cannot be opened

    Used by:
        lake.FetchLog                  -- shares the connection
        lake.RunLog                    -- shares the connection
        lake.LakeQuery                 -- shares the connection
        lake.Compactor                 -- raw file listing, view refresh
        pipeline.FetchStep.run         -- refresh_view after each dataset
        pipeline.DownloadPipeline.run  -- write_indexes after a run
        cli.QuantCnCli                 -- composition root, rebuild

    Test cases:
        TC-LC-001  raw and curated views exist after refresh and return the written rows
        TC-LC-002  datasets without files get no view; refresh is idempotent
        TC-LC-003  rebuild after deleting the DuckDB file restores views and dataset_meta
        TC-LC-004  write_indexes writes INDEX.md in the lake root and every zone
    """

    def __init__(self, lake_root: Path, datasets: Mapping[str, DatasetSpec]) -> None:
        self.lake_root = lake_root
        self.datasets = dict(datasets)
        self._con: duckdb.DuckDBPyConnection | None = None

    @property
    def catalog_path(self) -> Path:
        """
        Purpose:
            Location of the DuckDB catalog file.

        Contract:
            Input:
                (none)
            Output:
                Path  -- <lake_root>/meta/quant_cn.duckdb
            Raises:
                (none)
        """
        return self.lake_root / "meta" / DB_NAME

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """
        Purpose:
            The shared DuckDB connection, opened lazily with zones, schemas and dataset_meta.

        Contract:
            Input:
                (none)
            Output:
                duckdb.DuckDBPyConnection
            Raises:
                LakeError  -- the file cannot be opened
        """
        if self._con is None:
            for zone in ZONES:
                (self.lake_root / zone).mkdir(parents=True, exist_ok=True)
            try:
                self._con = duckdb.connect(str(self.catalog_path))
            except duckdb.Error as exc:
                raise LakeError(f"cannot open catalog {self.catalog_path}: {exc}") from exc
            for schema in ("raw", "curated", "meta"):
                self._con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            self._write_dataset_meta(self._con)
        return self._con

    def list_raw_files(self, spec: DatasetSpec) -> list[Path]:
        """
        Purpose:
            Raw parquet files of a dataset, sorted by name.

        Contract:
            Input:
                spec: DatasetSpec
            Output:
                list[Path]  -- may be empty
            Raises:
                (none)
        """
        folder = self.lake_root / "raw" / spec.name
        return sorted(folder.glob("*.parquet")) if folder.exists() else []

    def refresh_view(self, spec: DatasetSpec) -> None:
        """
        Purpose:
            (Re)create `raw.<name>` and `curated.<name>` views for whatever files exist.

        Contract:
            Input:
                spec: DatasetSpec
            Output:
                None  -- a zone without files gets no view (and any stale view is dropped)
            Raises:
                LakeError  -- DuckDB rejects the view
        """
        con = self.connection
        raw_glob = self.lake_root / "raw" / spec.name / "*.parquet"
        self._refresh_one_view(
            con, f"raw.{spec.name}", raw_glob, bool(self.list_raw_files(spec)), hive=False
        )
        curated = self.lake_root / "curated" / spec.curated.path
        if spec.curated.partition_by:
            glob = curated / "year=*" / "*.parquet"
            present = any(curated.glob("year=*/*.parquet")) if curated.exists() else False
            self._refresh_one_view(con, f"curated.{spec.name}", glob, present, hive=True)
        else:
            single = curated.with_name(curated.name + ".parquet")
            self._refresh_one_view(con, f"curated.{spec.name}", single, single.exists(), hive=False)

    def refresh_views(self) -> None:
        """
        Purpose:
            refresh_view for every configured dataset.

        Contract:
            Input:
                (none)
            Output:
                None
            Raises:
                LakeError
        """
        for spec in self.datasets.values():
            self.refresh_view(spec)

    def rebuild(self) -> None:
        """
        Purpose:
            Delete the DuckDB file and recreate schemas, dataset_meta and all views from parquet.
            Tables owned by FetchLog/RunLog are restored by their own classes.

        Contract:
            Input:
                (none)
            Output:
                None
            Raises:
                LakeError  -- file cannot be removed or reopened
        """
        self.close()
        for path in (self.catalog_path, self.catalog_path.with_name(DB_NAME + ".wal")):
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                raise LakeError(f"cannot remove {path}: {exc}") from exc
        self.refresh_views()

    def write_indexes(self) -> list[Path]:
        """
        Purpose:
            Generate INDEX.md in the lake root and each zone: datasets, file counts, last update.

        Contract:
            Input:
                (none)
            Output:
                list[Path]  -- files written
            Raises:
                LakeError  -- a file cannot be written
        """
        written = [self._write_index(self.lake_root, self._build_root_index())]
        for zone in ZONES:
            written.append(self._write_index(self.lake_root / zone, self._build_zone_index(zone)))
        return written

    def close(self) -> None:
        """
        Purpose:
            Close the DuckDB connection if open.

        Contract:
            Input:
                (none)
            Output:
                None
            Raises:
                (none)
        """
        if self._con is not None:
            self._con.close()
            self._con = None

    def _refresh_one_view(
        self, con: duckdb.DuckDBPyConnection, name: str, glob: Path, present: bool, hive: bool
    ) -> None:
        try:
            if not present:
                con.execute(f"DROP VIEW IF EXISTS {name}")
                return
            path = str(glob).replace("'", "''")
            opts = "union_by_name=true" + (", hive_partitioning=true" if hive else "")
            con.execute(
                f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet('{path}', {opts})"
            )
        except duckdb.Error as exc:
            raise LakeError(f"cannot create view {name}: {exc}") from exc

    def _write_dataset_meta(self, con: duckdb.DuckDBPyConnection) -> None:
        con.execute(
            "CREATE OR REPLACE TABLE meta.dataset_meta (name VARCHAR PRIMARY KEY, "
            "endpoint VARCHAR, sweep VARCHAR, primary_key VARCHAR, known_on VARCHAR, "
            "refresh VARCHAR, curated_path VARCHAR, partition_by VARCHAR, fields VARCHAR)"
        )
        rows = [
            (
                s.name,
                s.endpoint,
                s.sweep.kind,
                ",".join(s.primary_key),
                s.known_on,
                s.refresh,
                s.curated.path,
                s.curated.partition_by,
                json.dumps(s.fields),
            )
            for s in self.datasets.values()
        ]
        if rows:
            con.executemany(
                "INSERT INTO meta.dataset_meta VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows
            )

    def _build_root_index(self) -> str:
        lines = [
            "# lake/",
            "",
            "Generated by `LakeCatalog.write_indexes()`; do not edit. Zones: FOLDER_STRUCTURE §2.",
            "",
            "## Folders",
            "| Folder | Purpose |",
            "|---|---|",
            "| [`curated/`](curated/INDEX.md) | typed, deduped, yearly partitions |",
            "| [`external/`](external/INDEX.md) | files not downloaded here, read-only |",
            "| [`meta/`](meta/INDEX.md) | DuckDB catalog, fetch log, manifests |",
            "| [`raw/`](raw/INDEX.md) | exactly what Tushare returned, one file per key |",
        ]
        return "\n".join(lines) + "\n"

    def _build_zone_index(self, zone: str) -> str:
        base = self.lake_root / zone
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# lake/{zone}/",
            "",
            f"Generated by `LakeCatalog.write_indexes()` at {stamp}.",
            "",
        ]
        entries = sorted(p for p in base.iterdir() if not p.name.startswith(("INDEX", ".")))
        if not entries:
            return "\n".join([*lines, "_Empty._"]) + "\n"
        lines += ["| Entry | Parquet files | Last update |", "|---|---|---|"]
        for entry in entries:
            files = [entry] if entry.is_file() else list(entry.rglob("*.parquet"))
            files = [f for f in files if f.suffix == ".parquet"]
            latest = max((f.stat().st_mtime for f in files), default=None)
            when = dt.datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M") if latest else "-"
            lines.append(f"| `{entry.name}` | {len(files)} | {when} |")
        return "\n".join(lines) + "\n"

    def _write_index(self, folder: Path, text: str) -> Path:
        path = folder / "INDEX.md"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        except OSError as exc:
            raise LakeError(f"cannot write {path}: {exc}") from exc
        return path
