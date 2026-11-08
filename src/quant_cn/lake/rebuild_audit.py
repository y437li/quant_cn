"""What `rebuild` confirms: fetch-log orphans (D-073) and rewritten raw files (D-083)."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from quant_cn.core.clock import Clock
from quant_cn.core.exceptions import LakeError

ORPHAN_FILE = "fetch_log_orphans.json"
REWRITE_FILE = "raw_rewrites.json"
PREV_SUFFIX = ".prev"  # "<key>.parquet.prev": outside the raw views' *.parquet glob


class RebuildAudit:
    """
    Purpose:
        Record, on `rebuild`, what changed below raw/ since the last one. Fetch-log rows whose raw
        file is gone go to meta/manifest/fetch_log_orphans.json (D-073). Raw files rewritten by a
        refetch keep their previous version as `<file>.prev` (ParquetWriter); `record_rewrites`
        lists each with old and new row counts in meta/manifest/raw_rewrites.json and then
        deletes the `.prev` copies, so every forced refetch is auditable (D-083).

    Contract:
        Input:
            lake_root: Path   -- the lake
            clock:     Clock  -- manifest timestamps
        Output:
            instance; `record_orphans`, `record_rewrites`
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- `rebuild` command

    Test cases:
        TC-RA-001  record_orphans writes the removed keys with a timestamp
        TC-RA-002  record_rewrites lists old/new row counts, then deletes the .prev files
    """

    def __init__(self, lake_root: Path, clock: Clock) -> None:
        self._root = lake_root
        self._clock = clock

    def record_orphans(self, orphans: dict[str, list[str]]) -> Path:
        """
        Purpose:
            Write the fetch-log orphans removed by this rebuild.

        Contract:
            Input:
                orphans: dict[str, list[str]]  -- FetchLog.remove_orphans() output
            Output:
                Path  -- the manifest written
            Raises:
                LakeError  -- write failed
        """
        return self._write(ORPHAN_FILE, {"removed": orphans})

    def record_rewrites(self) -> list[dict[str, object]]:
        """
        Purpose:
            Record every rewritten raw file (old vs new rows) and delete the kept `.prev` copies.

        Contract:
            Input:
                (none)
            Output:
                list[dict]  -- dataset, file, previous_rows, current_rows (None if file gone)
            Raises:
                LakeError  -- manifest write or delete failed
        """
        rewrites: list[dict[str, object]] = []
        prev_files = sorted((self._root / "raw").glob(f"*/*.parquet{PREV_SUFFIX}"))
        for prev in prev_files:
            current = prev.with_name(prev.name.removesuffix(PREV_SUFFIX))
            rewrites.append(
                {
                    "dataset": prev.parent.name,
                    "file": current.name,
                    "previous_rows": pq.ParquetFile(prev).metadata.num_rows,
                    "current_rows": (
                        pq.ParquetFile(current).metadata.num_rows if current.exists() else None
                    ),
                }
            )
        self._write(REWRITE_FILE, {"rewrites": rewrites})
        try:
            for prev in prev_files:
                prev.unlink()
        except OSError as exc:
            raise LakeError(f"cannot delete kept raw file: {exc}") from exc
        return rewrites

    def _write(self, name: str, payload: dict[str, object]) -> Path:
        folder = self._root / "meta" / "manifest"
        record = {"checked_at": self._clock.get_now().isoformat(timespec="seconds"), **payload}
        try:
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / name
            path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError as exc:
            raise LakeError(f"cannot write manifest {name}: {exc}") from exc
        return path
