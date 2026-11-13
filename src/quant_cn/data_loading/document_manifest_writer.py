"""Append-only manifest of downloaded documents: `meta/document_manifest/part-*.parquet` (D-101)."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.exceptions import LakeError

MANIFEST_DIR = Path("meta") / "document_manifest"
MANIFEST_COLUMNS = [
    "doc_id", "source", "doc_type", "code", "title", "publish_date", "url", "local_path",
    "bytes", "sha256", "status", "message", "downloaded_at",
]  # fmt: skip


class DocumentManifestWriter:
    """
    Purpose:
        Write one manifest part file (MANIFEST_COLUMNS, zstd parquet, tmp + rename) under
        `<lake_root>/meta/document_manifest/`. Rows are never rewritten: a later row for the same
        doc_id (later `downloaded_at`) supersedes the earlier one for readers.

    Contract:
        Input:
            lake_root: Path
        Output:
            instance; `write_part(rows, name) -> Path | None`, `get_glob() -> str`
        Raises:
            (none at construction)

    Used by:
        data_loading.DocumentDownloader  -- download attempts
        data_loading.DocumentRetyper     -- type changes (D-149)

    Test cases:
        TC-DMW-001  rows are written with MANIFEST_COLUMNS and int64 bytes; no rows -> no file
    """

    def __init__(self, lake_root: Path) -> None:
        self._folder = lake_root / MANIFEST_DIR

    def get_glob(self) -> str:
        """
        Purpose:
            The glob of every part file, for read_parquet.

        Contract:
            Input:
                (none)
            Output:
                str  -- "<lake_root>/meta/document_manifest/part-*.parquet"
            Raises:
                (none)
        """
        return str(self._folder / "part-*.parquet")

    def has_parts(self) -> bool:
        """
        Purpose:
            Whether any part file exists.

        Contract:
            Input:
                (none)
            Output:
                bool
            Raises:
                (none)
        """
        return any(self._folder.glob("part-*.parquet"))

    def write_part(self, rows: Sequence[Mapping[str, Any]], name: str) -> Path | None:
        """
        Purpose:
            Persist `rows` as `part-<name>.parquet`.

        Contract:
            Input:
                rows: Sequence[Mapping[str, Any]]  -- MANIFEST_COLUMNS keys
                name: str                          -- unique part suffix, e.g. "<stamp>-00001"
            Output:
                Path | None  -- the file, None when rows is empty
            Raises:
                LakeError  -- the file cannot be written
        """
        if not rows:
            return None
        path = self._folder / f"part-{name}.parquet"
        frame = pd.DataFrame(list(rows), columns=MANIFEST_COLUMNS)
        frame["bytes"] = frame["bytes"].astype("int64")
        try:
            self._folder.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            frame.to_parquet(tmp, index=False, compression="zstd")
            os.replace(tmp, path)
        except OSError as exc:
            raise LakeError(f"cannot write manifest {path}: {exc}") from exc
        return path
