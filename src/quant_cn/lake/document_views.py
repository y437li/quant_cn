"""Catalog views over the document download manifest (D-101)."""

from __future__ import annotations

from pathlib import Path

import duckdb

from quant_cn.core.exceptions import LakeError

MANIFEST_GLOB = "meta/document_manifest/part-*.parquet"  # written by DocumentDownloader


class DocumentViews:
    """
    Purpose:
        Expose the document manifest in the catalog. `meta.document_attempts` holds every
        manifest row (one per download attempt). `meta.documents` holds the latest attempt per
        doc_id, so `WHERE status = 'ok'` lists the PDFs present under `documents/`.

    Contract:
        Input:
            lake_root:  Path
            connection: duckdb.DuckDBPyConnection  -- the catalog connection (schema meta exists)
        Output:
            instance; `refresh`
        Raises:
            (none at construction)

    Used by:
        lake.LakeCatalog.refresh_views  -- after the dataset views
        cli.DocumentCommands            -- after a download-docs run

    Test cases:
        TC-DOV-001  no manifest: no views; with manifest: latest attempt per doc_id wins
    """

    def __init__(self, lake_root: Path, connection: duckdb.DuckDBPyConnection) -> None:
        self._root = lake_root
        self._con = connection

    def refresh(self) -> None:
        """
        Purpose:
            (Re)create both views, or drop them when no manifest file exists.

        Contract:
            Input:
                (none)
            Output:
                None
            Raises:
                LakeError  -- DuckDB rejects a view
        """
        try:
            if not any(self._root.glob(MANIFEST_GLOB)):
                self._con.execute("DROP VIEW IF EXISTS meta.documents")
                self._con.execute("DROP VIEW IF EXISTS meta.document_attempts")
                return
            path = str(self._root / MANIFEST_GLOB).replace("'", "''")
            self._con.execute(
                "CREATE OR REPLACE VIEW meta.document_attempts AS SELECT * FROM "
                f"read_parquet('{path}', union_by_name=true)"
            )
            self._con.execute(
                "CREATE OR REPLACE VIEW meta.documents AS SELECT * FROM meta.document_attempts"
                " QUALIFY row_number() OVER (PARTITION BY doc_id ORDER BY downloaded_at DESC) = 1"
            )
        except duckdb.Error as exc:
            raise LakeError(f"cannot create document views: {exc}") from exc
