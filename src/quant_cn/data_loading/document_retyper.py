"""Re-apply the document title rules to files already downloaded (plan 18 ph2, D-149)."""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.document_source import DocumentSource
from quant_cn.core.exceptions import ConfigError, LakeError
from quant_cn.core.step_report import StepReport
from quant_cn.data_loading.document_classifier import DocumentClassifier
from quant_cn.data_loading.document_manifest_writer import DocumentManifestWriter
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)
TYPE_SEGMENT = 2  # documents/<folder>/<doc_type>/<YYYY>/<MM>/<file>


class DocumentRetyper:
    """
    Purpose:
        After the title rules in config/documents.yaml change, bring the downloaded documents in
        line: for the latest manifest row of every `ok` document of a source, classify its title
        again (DocumentClassifier). A new type moves the file to that type's folder and appends
        a manifest row with the new doc_type and local_path; a title no rule matches any more
        appends an `excluded` row and keeps the file. Unchanged documents are not touched, so a
        second run changes nothing. Inquiry replies typed annual were the case that needed it.

    Contract:
        Input:
            lake_root: Path; query: LakeQuery (reads the manifest parquet only);
            sources: Mapping[str, DocumentSource]; clock: Clock; writer: DocumentManifestWriter
        Output:
            instance; `run(source_name) -> StepReport`
        Raises:
            (none at construction)

    Used by:
        (none yet)  -- run once 2026-11-12 from a script (D-149); a `download-docs --retype` flag
                       waits for the cli.py split in progress (file at the 600-line limit)

    Test cases:
        TC-DRT-001  a reply typed annual is moved to inquiry_reply with a new manifest row; an
                    H-share filing becomes excluded (file kept); the report counts both; a
                    second run moves nothing; an unknown source raises ConfigError
    """

    def __init__(
        self,
        lake_root: Path,
        query: LakeQuery,
        sources: Mapping[str, DocumentSource],
        clock: Clock,
        writer: DocumentManifestWriter,
    ) -> None:
        self._root = lake_root
        self._query = query
        self._sources = sources
        self._clock = clock
        self._writer = writer

    def run(self, source_name: str) -> StepReport:
        """
        Purpose:
            Re-type every downloaded document of one source.

        Contract:
            Input:
                source_name: str  -- key of Config.documents
            Output:
                StepReport  -- keys_total = documents checked, fetched = moved, empty = excluded
            Raises:
                ConfigError  -- unknown source
                LakeError    -- a file cannot be moved or the manifest written
        """
        if source_name not in self._sources:
            raise ConfigError(f"unknown document source {source_name!r}")
        report = StepReport(f"retype:{source_name}")
        if not self._writer.has_parts():
            return report
        latest = self._query.sql(
            "SELECT * FROM read_parquet(?) WHERE source = ? QUALIFY row_number() OVER "
            "(PARTITION BY doc_id ORDER BY downloaded_at DESC) = 1",
            [self._writer.get_glob(), source_name],
        )
        done = latest[latest["status"] == "ok"].reset_index(drop=True)
        report.keys_total = len(done)
        types = DocumentClassifier(self._sources[source_name]).compute_doc_types(done["title"])
        now = self._clock.get_now()
        changes: list[dict[str, Any]] = []
        for record, new in zip(done.to_dict("records"), types, strict=True):
            if new == record["doc_type"]:
                continue
            change = {str(k): v for k, v in record.items()}
            change["downloaded_at"] = now.strftime("%Y%m%d %H:%M:%S")
            if new is None or pd.isna(new):
                change |= {"status": "excluded", "message": "retype: no title rule matches"}
                report.empty += 1
            else:
                change |= self._write_moved_file(change, str(new))
                report.fetched += 1
            changes.append(change)
        self._writer.write_part(changes, f"{now.strftime('%Y%m%d%H%M%S')}-retype")
        report.message = f"moved {report.fetched}, excluded {report.empty}"
        logger.info("retype %s: %s of %d", source_name, report.message, report.keys_total)
        return report

    def _write_moved_file(self, row: dict[str, Any], doc_type: str) -> dict[str, Any]:
        parts = str(row["local_path"]).split("/")
        parts[TYPE_SEGMENT] = doc_type
        path = "/".join(parts)
        old, new = self._root / str(row["local_path"]), self._root / path
        try:
            if old.exists():
                new.parent.mkdir(parents=True, exist_ok=True)
                os.replace(old, new)
        except OSError as exc:
            raise LakeError(f"cannot move {old} -> {new}: {exc}") from exc
        message = f"retype from {row['doc_type']}"
        return {"doc_type": doc_type, "local_path": path, "message": message}
