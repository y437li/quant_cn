"""Fetch listed PDFs into documents/ with a manifest of hashes (plan 12 phase 2, D-101)."""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import urllib.error
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.document_source import DocumentSource
from quant_cn.core.exceptions import ConfigError, DataSourceError, LakeError
from quant_cn.core.step_report import StepReport
from quant_cn.data_loading.document_classifier import DocumentClassifier
from quant_cn.data_loading.http_transport import HttpTransport
from quant_cn.data_loading.request_pacer import RequestPacer
from quant_cn.lake.lake_query import LakeQuery

MANIFEST_DIR = Path("meta") / "document_manifest"
MANIFEST_COLUMNS = [
    "doc_id", "source", "doc_type", "code", "title", "publish_date", "url", "local_path",
    "bytes", "sha256", "status", "message", "downloaded_at",
]  # fmt: skip
PDF_MAGIC = b"%PDF-"
logger = logging.getLogger(__name__)
Progress = Callable[[str, str], None]


class DocumentDownloader:
    """
    Purpose:
        Download the PDFs listed in a document source's curated metadata (config/documents.yaml)
        into `documents/<folder>/<doc_type>/<YYYY>/<MM>/<file>` (D-101). Rows are typed by
        DocumentClassifier, optionally limited to A-share codes (`curated.stock_basic.symbol`),
        de-duplicated on the document id, and skipped when the manifest already holds an `ok`
        attempt whose file exists. Each file is written atomically (tmp + rename) after its
        body is checked to start with %PDF-; one manifest row per attempt (sha256, bytes,
        status ok | not_pdf | failed) is appended to `meta/document_manifest/part-*.parquet`
        every `flush_every` documents, so an interrupted run resumes where it stopped.

    Contract:
        Input:
            lake_root:      Path
            query:          LakeQuery                    -- curated metadata and the manifest
            sources:        Mapping[str, DocumentSource] -- Config.documents
            clock:          Clock
            transport:      HttpTransport | None
            workers_override: int | None  -- replaces the source's `workers` for this instance
            retries:        int >= 0
            timeout_s:      float > 0
            flush_every:    int >= 1      -- manifest rows per part file
        Output:
            instance; `list_candidates`, `list_todo`, `run`
        Raises:
            (none at construction)

    Used by:
        cli.DocumentCommands  -- `download-docs`

    Test cases:
        TC-DD-001  candidates: typed, A-share filtered, de-duplicated, paths from the templates
        TC-DD-002  run writes PDFs and ok manifest rows; list_todo then excludes them
        TC-DD-003  a non-PDF body is recorded not_pdf and no file is written; a network failure
                   is recorded failed and retried on the next run
        TC-DD-004  unknown source raises ConfigError; doc_types and limit narrow the candidates
        TC-DD-005  run spaces requests by the source's min_interval_s
        TC-DD-006  a throttle status pauses all requests for cooldown_s, then the retry succeeds
    """

    def __init__(
        self,
        lake_root: Path,
        query: LakeQuery,
        sources: Mapping[str, DocumentSource],
        clock: Clock,
        transport: HttpTransport | None = None,
        workers_override: int | None = None,
        retries: int = 3,
        timeout_s: float = 120.0,
        flush_every: int = 200,
    ) -> None:
        self._root = lake_root
        self._query = query
        self._sources = sources
        self._clock = clock
        self._transport = transport or HttpTransport()
        self._workers_override = workers_override
        self._retries = retries
        self._timeout_s = timeout_s
        self._flush_every = flush_every
        self._pacer = RequestPacer(clock, "documents", 0.25, retries, 10.0)  # replaced per run
        self._lock = threading.Lock()
        self._throttle: tuple[set[int], float] = (set(), 0.0)
        self._pending: list[dict[str, Any]] = []
        self._parts = 0
        self._stamp = ""

    def list_candidates(
        self,
        source_name: str,
        doc_types: Sequence[str] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            Every wanted document of a source, typed and with its URL and target path.

        Contract:
            Input:
                source_name: str                   -- key of Config.documents
                doc_types:   Sequence[str] | None  -- keep these types only (None = all)
                start, end:  str | None            -- publication date bounds, YYYYMMDD
            Output:
                DataFrame  -- MANIFEST_COLUMNS[:8], newest first
            Raises:
                ConfigError  -- unknown source
                LakeError    -- metadata dataset not curated yet
        """
        source = self._get_source(source_name)
        view = f"curated.{source.dataset}"
        if not self._query.has_view(view):
            raise LakeError(f"{view} missing: download and compact {source.dataset} first")
        where, params = [], []
        if start:
            where.append(f"{source.date_column} >= ?")
            params.append(start)
        if end:
            where.append(f"{source.date_column} <= ?")
            params.append(end)
        clause = f" WHERE {' AND '.join(where)}" if where else ""
        rows = self._query.sql(f"SELECT * FROM {view}{clause}", params)
        rows["doc_type"] = DocumentClassifier(source).compute_doc_types(rows[source.title_column])
        rows = rows[rows["doc_type"].notna()]
        if doc_types:
            rows = rows[rows["doc_type"].isin(list(doc_types))]
        if source.a_share_only:
            symbols = set(self._query.sql("SELECT symbol FROM curated.stock_basic")["symbol"])
            rows = rows[rows[source.code_column].isin(symbols)]
        rows = rows.drop_duplicates(subset=[source.id_column])
        return self._build_targets(source_name, source, rows)

    def list_todo(
        self,
        source_name: str,
        doc_types: Sequence[str] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            Candidates without an `ok` manifest attempt whose file exists: the work of `run`.
            The only catalog reads of a download, so the caller can release the catalog
            (another process may hold it for a metadata sweep) before downloading.

        Contract:
            Input:
                source_name, doc_types, start, end  -- as list_candidates
            Output:
                DataFrame  -- list_candidates columns, newest first
            Raises:
                ConfigError, LakeError  -- as list_candidates
        """
        candidates = self.list_candidates(source_name, doc_types, start, end)
        return candidates[~candidates["doc_id"].isin(self._list_done())].reset_index(drop=True)

    def run(
        self, todo: pd.DataFrame, limit: int | None = None, progress: Progress | None = None
    ) -> StepReport:
        """
        Purpose:
            Download the documents of `todo` (from list_todo, one source) with that source's
            workers and min_interval_s from config/documents.yaml; no catalog access.

        Contract:
            Input:
                todo:     DataFrame        -- list_todo output
                limit:    int | None       -- at most this many downloads this run
                progress: Progress | None  -- called (doc_id, status) per document
            Output:
                StepReport  -- keys_total = len(todo), fetched ok, empty failed or not_pdf,
                               rows bytes written; message counts
            Raises:
                LakeError  -- manifest cannot be written
        """
        name = str(todo["source"].iloc[0]) if len(todo) else "none"
        report = StepReport(f"documents:{name}", keys_total=len(todo))
        source = self._sources.get(name)
        interval = source.min_interval_s if source else 0.25
        workers = self._workers_override or (source.workers if source else 1)
        self._pacer = RequestPacer(self._clock, f"documents:{name}", interval, self._retries, 10.0)
        self._throttle = (set(source.throttle_codes), source.cooldown_s) if source else (set(), 0.0)
        if limit is not None:
            todo = todo.head(limit)
        self._stamp = self._clock.get_now().strftime("%Y%m%d%H%M%S")
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for row in pool.map(self._fetch_one, todo.to_dict("records")):
                self._record(row, report, progress)
        self._write_manifest_part()
        report.message = f"downloaded {report.fetched}, failed {report.empty}"
        return report

    def _get_source(self, name: str) -> DocumentSource:
        if name not in self._sources:
            raise ConfigError(f"unknown document source {name!r}; known: {sorted(self._sources)}")
        return self._sources[name]

    @staticmethod
    def _build_targets(name: str, source: DocumentSource, rows: pd.DataFrame) -> pd.DataFrame:
        folder = source.folder or name
        records = []
        for row in rows.to_dict("records"):
            fill = {str(k): ("" if v is None else str(v)) for k, v in row.items()}
            day = fill[source.date_column]
            file_name = source.file_template.format(**fill).replace("/", "_")
            records.append(
                {
                    "doc_id": f"{name}:{fill[source.id_column]}",
                    "source": name,
                    "doc_type": fill["doc_type"],
                    "code": fill[source.code_column],
                    "title": fill[source.title_column],
                    "publish_date": day,
                    "url": source.url_template.format(**fill),
                    "local_path": "/".join(
                        ["documents", folder, fill["doc_type"], day[:4], day[4:6], file_name]
                    ),
                }
            )
        frame = pd.DataFrame(records, columns=MANIFEST_COLUMNS[:8])
        return frame.sort_values("publish_date", ascending=False, kind="stable").reset_index(
            drop=True
        )

    def _list_done(self) -> set[str]:
        folder = self._root / MANIFEST_DIR
        if not any(folder.glob("part-*.parquet")):
            return set()
        latest = self._query.sql(
            "SELECT doc_id, local_path FROM read_parquet(?) WHERE status = 'ok'",
            [str(folder / "part-*.parquet")],
        )
        return {
            d
            for d, p in zip(latest["doc_id"], latest["local_path"], strict=True)
            if (self._root / p).exists()
        }

    def _fetch_bytes(self, url: str) -> bytes:
        try:
            return self._transport.fetch_bytes(url, self._timeout_s)
        except urllib.error.HTTPError as exc:
            codes, cooldown = self._throttle
            if exc.code in codes:  # the site says slow down: every worker pauses (D-110)
                self._pacer.record_throttle(cooldown)
            raise

    def _fetch_one(self, row: dict[str, Any]) -> dict[str, Any]:
        out = {**row, "bytes": 0, "sha256": None, "status": "ok", "message": ""}
        try:
            body = self._pacer.run(row["doc_id"], lambda: self._fetch_bytes(row["url"]))
        except DataSourceError as exc:
            return {**out, "status": "failed", "message": str(exc)[:500]}
        if not body.startswith(PDF_MAGIC):
            return {**out, "status": "not_pdf", "message": f"body starts {body[:20]!r}"}
        target = self._root / row["local_path"]
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".tmp")
            tmp.write_bytes(body)
            os.replace(tmp, target)
        except OSError as exc:
            return {**out, "status": "failed", "message": f"write: {exc}"}
        return {**out, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}

    def _record(self, row: dict[str, Any], report: StepReport, progress: Progress | None) -> None:
        row["downloaded_at"] = self._clock.get_now().strftime("%Y%m%d %H:%M:%S")
        if row["status"] == "ok":
            report.fetched += 1
            report.rows += int(row["bytes"])
        else:
            report.empty += 1
            logger.warning("%s %s: %s", row["doc_id"], row["status"], row["message"])
        if progress:
            progress(row["doc_id"], row["status"])
        with self._lock:
            self._pending.append(row)
            if len(self._pending) >= self._flush_every:
                self._write_manifest_part()

    def _write_manifest_part(self) -> None:
        if not self._pending:
            return
        folder = self._root / MANIFEST_DIR
        path = folder / f"part-{self._stamp}-{self._parts:05d}.parquet"
        frame = pd.DataFrame(self._pending, columns=MANIFEST_COLUMNS)
        frame["bytes"] = frame["bytes"].astype("int64")
        try:
            folder.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            frame.to_parquet(tmp, index=False, compression="zstd")
            os.replace(tmp, path)
        except OSError as exc:
            raise LakeError(f"cannot write manifest {path}: {exc}") from exc
        self._pending = []
        self._parts += 1
