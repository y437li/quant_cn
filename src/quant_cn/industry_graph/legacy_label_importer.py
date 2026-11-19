"""Import earlier jsonl / parse-parquet label files into the parquet LabelStore (plan 28 ph0)."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_cn.core.label_source import LabelSource
from quant_cn.core.ticker_normalizer import TickerNormalizer
from quant_cn.lake.label_store import KEY, LabelStore
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

QUARTER_END = {"Q1": "0331", "Q2": "0630", "Q3": "0930", "Q4": "1231", "H1": "0630"}
_QUARTER_LEN = 6  # "2026Q3"
Anchors = dict[tuple[str, str], tuple[str, str | None, str | None]]
DATE_LISTS = (  # (curated view, id column, public date column)
    ("cninfo_announcements", "ann_id", "ann_date"),
    ("cninfo_keyword_announcements", "ann_id", "ann_date"),
    ("em_stock_reports", "info_code", "publish_date"),
)
_DATES = "SELECT {key} AS id, min({day}) AS d FROM curated.{view} GROUP BY 1"
_VIEWS = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'curated'"


class LegacyLabelImporter:
    """
    Purpose:
        Turn the label files of earlier runs (config/label_sources.yaml) into LabelStore rows:
        one row per record with ts_code, doc_key ("annual:<ann_id>", "em_stock:<info_code>", …),
        doc_type, period (YYYYMMDD; "2026Q3" -> 20260930), known_on (the announcement or publish
        date of the document, looked up by id; or the record's date field), taxonomy_version and
        the whole record as JSON payload. A record without a document key (business modes, moat
        claims, pricing verdicts) takes the key, doc type and date of its anchor set's row for the
        same company and period. Records whose code cannot be normalised are skipped and counted;
        so are records whose document was public before the period they claim ended (an earlier
        report, e.g. a corrected 2025 Q3 report labelled as 2026 Q3), each logged.

    Contract:
        Input:
            store:      LabelStore
            query:      LakeQuery         -- curated document lists (public dates)
            lake_root:  Path              -- where the label files live
            normalizer: TickerNormalizer
        Output:
            instance; `run(sources) -> dict[str, int]` (rows written per set),
            `build_rows(source, records, dates, anchors)` (pure), `read_dates()`, `read_records()`
        Raises:
            (none at construction)

    Used by:
        cli.DocumentCommands  -- `import-labels`

    Test cases:
        TC-LLI-001  keyed records: doc_key with prefix, doc_type from the record or key prefix,
                    period from the record ("2026Q3" -> 20260930) or the source, known_on by id
        TC-LLI-002  date_field gives known_on and, without a period, the period; a record
                    without the date field takes both from its document's listed date
        TC-LLI-003  anchored records take doc_key / doc_type / known_on of the anchor row; with
                    no anchor row they get "<label_set>:<period>" and no known_on
        TC-LLI-005  a record whose document date is before its period end is skipped
        TC-LLI-006  read_dates skips document lists the catalog does not have (empty lake: {})
        TC-LLI-007  records listed in exclude_file are not read; re-running a source removes
                    the rows it no longer holds
        TC-LLI-004  bad codes are skipped; payload round-trips the record; run writes each source
                    and later anchored sources see earlier anchors
    """

    def __init__(
        self, store: LabelStore, query: LakeQuery, lake_root: Path, normalizer: TickerNormalizer
    ) -> None:
        self._store = store
        self._query = query
        self._root = lake_root
        self._normalizer = normalizer

    def run(self, sources: Sequence[LabelSource]) -> dict[str, int]:
        """
        Purpose:
            Import every source in order into the store. Each source file is authoritative for
            its own rows: rows it wrote before and no longer holds are removed.

        Contract:
            Input:
                sources: LabelSource list, anchors listed before the sets that use them
            Output:
                dict[str, int]  -- rows written per label set
            Raises:
                LakeError, SchemaError  -- a write fails or rows are malformed
                FileNotFoundError       -- a listed file is missing
        """
        dates = self.read_dates()
        anchors: dict[str, Anchors] = {}
        written: dict[str, int] = {}
        for source in sources:
            rows = self.build_rows(source, self.read_records(source), dates, anchors)
            self._store.write(source.label_set, rows, replace_source=source.path)
            own = anchors.setdefault(source.label_set, {})
            for r in rows.itertuples():
                own[(str(r.ts_code), str(r.period))] = (
                    str(r.doc_key), self._to_text(r.doc_type), self._to_text(r.known_on)
                )  # fmt: skip
            unique = len(rows.drop_duplicates(KEY)) if len(rows) else 0
            written[source.label_set] = written.get(source.label_set, 0) + unique
            logger.info("imported %s: %d rows", source.path, unique)
        return written

    def read_dates(self) -> dict[str, str]:
        """
        Purpose:
            Public date of every listed document id (CNINFO ann_id, Eastmoney info_code).

        Contract:
            Input:
                (none)
            Output:
                dict[str, str]  -- id -> YYYYMMDD (earliest when listed twice); lists not
                                   downloaded yet are skipped
            Raises:
                LakeError  -- the document lists cannot be read
        """
        out: dict[str, str] = {}
        views = set(self._query.sql(_VIEWS)["table_name"])
        for view, key, day in DATE_LISTS:
            if view not in views:
                continue
            frame = self._query.sql(_DATES.format(key=key, day=day, view=view))
            for doc, date in zip(frame["id"], frame["d"], strict=True):
                if doc and date and (str(doc) not in out or str(date) < out[str(doc)]):
                    out[str(doc)] = str(date)
        return out

    def read_records(self, source: LabelSource) -> list[dict[str, Any]]:
        """
        Purpose:
            The records of one label file.

        Contract:
            Input:
                source: LabelSource
            Output:
                list[dict]  -- one per jsonl line or parquet row, in file order, without the
                               records whose key is listed in the source's exclude_file
            Raises:
                FileNotFoundError  -- the file is missing
        """
        path = self._root / source.path
        if source.is_parquet:
            frame = pd.read_parquet(path)
            records = [
                {str(k): (None if self._is_missing(v) else v) for k, v in r.items()}
                for r in frame.to_dict("records")
            ]
        else:
            with path.open(encoding="utf-8") as handle:
                records = [json.loads(line) for line in handle if line.strip()]
        if source.exclude_file is None or source.key_field is None:
            return records
        excluded = set(pd.read_csv(self._root / source.exclude_file, dtype=str)["key"])
        kept = [r for r in records if str(r.get(source.key_field)) not in excluded]
        logger.info("%s: %d records excluded", source.path, len(records) - len(kept))
        return kept

    def build_rows(
        self,
        source: LabelSource,
        records: list[dict[str, Any]],
        dates: dict[str, str],
        anchors: dict[str, Anchors],
    ) -> pd.DataFrame:
        """
        Purpose:
            LabelStore rows of one source's records.

        Contract:
            Input:
                source; records (read_records); dates (read_dates);
                anchors: label_set -> {(ts_code, period): (doc_key, doc_type, known_on)}
            Output:
                DataFrame  -- LabelStore columns; one row per importable record
            Raises:
                (none)
        """
        out: list[dict[str, Any]] = []
        skipped = early = 0
        for record in records:
            try:
                ts_code = self._normalizer.normalize(str(record.get("code") or ""))
            except ValueError:
                skipped += 1
                continue
            row = self._build_row(source, record, ts_code, dates, anchors)
            if row["known_on"] is not None and row["known_on"] < row["period"]:
                early += 1  # published before the period ended: the wrong document was read
                logger.warning("%s: %s %s public %s < period %s, skipped", source.path,
                               ts_code, row["doc_key"], row["known_on"], row["period"])  # fmt: skip
                continue
            out.append(row)
        if skipped or early:
            logger.warning(
                "%s: skipped %d bad codes, %d early documents", source.path, skipped, early
            )
        return pd.DataFrame(out)

    def _build_row(
        self,
        source: LabelSource,
        record: dict[str, Any],
        ts_code: str,
        dates: dict[str, str],
        anchors: dict[str, Anchors],
    ) -> dict[str, Any]:
        stated = self._to_text(record.get(source.date_field)) if source.date_field else None
        period = source.period or self._to_period(record.get("period")) or stated
        doc_key, doc_type, known_on = self._find_document(source, record, ts_code, period, anchors)
        if doc_key and known_on is None:
            known_on = dates.get(doc_key.split(":", 1)[-1])
        known_on = stated or known_on
        return {
            "ts_code": ts_code,
            "doc_key": doc_key or f"{source.label_set}:{period}",
            "doc_type": source.doc_type or self._to_text(record.get("doc_type")) or doc_type,
            "taxonomy_version": source.taxonomy_version,
            "period": period or known_on,
            "known_on": known_on,
            "event_date": None,
            "source": source.path,
            "payload": json.dumps(record, ensure_ascii=False, default=self._to_json),
        }

    def _find_document(
        self,
        source: LabelSource,
        record: dict[str, Any],
        ts_code: str,
        period: str | None,
        anchors: dict[str, Anchors],
    ) -> tuple[str | None, str | None, str | None]:
        if source.key_field and record.get(source.key_field) is not None:
            key = str(record[source.key_field])
            if ":" not in key and source.key_prefix:
                key = f"{source.key_prefix}:{key}"
            prefix = key.split(":", 1)[0] if ":" in key else None
            return key, prefix, None
        if source.anchor_set and period is not None:
            hit = anchors.get(source.anchor_set, {}).get((ts_code, period))
            if hit is not None:
                return hit
        return None, None, None

    @staticmethod
    def _to_period(value: Any) -> str | None:
        text = LegacyLabelImporter._to_text(value)
        if text is None:
            return None
        if len(text) == _QUARTER_LEN and text[4:] in QUARTER_END:
            return text[:4] + QUARTER_END[text[4:]]
        return text

    @staticmethod
    def _to_text(value: Any) -> str | None:
        if value is None or LegacyLabelImporter._is_missing(value):
            return None
        text = str(value)
        return text or None

    @staticmethod
    def _is_missing(value: Any) -> bool:
        return not isinstance(value, (list, dict, np.ndarray)) and bool(pd.isna(value))

    @staticmethod
    def _to_json(value: Any) -> Any:
        return value.tolist() if hasattr(value, "tolist") else str(value)
