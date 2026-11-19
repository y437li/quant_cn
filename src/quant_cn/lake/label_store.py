"""Every label set as local parquet, keyed by company, document and period (plan 28 ph0, D-161)."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import SchemaError
from quant_cn.lake.parquet_writer import ParquetWriter

logger = logging.getLogger(__name__)

COLUMNS = [
    "ts_code",
    "doc_key",
    "doc_type",
    "taxonomy_version",
    "period",
    "known_on",
    "event_date",
    "source",
    "payload",
]
REQUIRED = ("ts_code", "doc_key", "period", "payload")
KEY = ["ts_code", "doc_key"]
ROOT = "labels"
_SET_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class LabelStore:
    """
    Purpose:
        Hold every label set (LLM or rule output about a company's documents) as parquet under
        `derived/labels/<label_set>/year=<YYYY>/part-0.parquet`, partitioned by the year of the
        period the label describes. One row per (company, document): `period` is what the label
        describes, `known_on` when its document became public, `event_date` an event's own date,
        `taxonomy_version` the node ids it used, `payload` the full record as JSON text.
        Writes upsert on (ts_code, doc_key), so re-importing or re-running a document replaces it.
        `replace_source` makes one source file authoritative: its earlier rows not in the new write
        (a document the re-run no longer chose) are removed from every partition.

    Contract:
        Input:
            writer:    ParquetWriter  -- atomic parquet writes into derived/
            lake_root: Path           -- where derived/labels lives
            dates:     DateCodec      -- YYYYMMDD checks
        Output:
            instance; `write(label_set, rows, replace_source) -> list[Path]`,
            `read(label_set, codes, as_of)`,
            `list_sets() -> list[str]`
        Raises:
            (none at construction)

    Used by:
        cli.AppServiceBuilder  -- `build_sector_monitor`
        portfolio.DeveloperSalesReader  -- operating_data (销售简报)
        industry_graph.CompanyPeriodBuilder  -- reads every label set
        industry_graph.GraphBuilder  -- reads label sets
        industry_graph.LegacyLabelImporter  -- writes imported rows
        cli.DocumentCommands                -- `import-labels`
        portfolio.BuybackMonitorBuilder     -- buyback_terms
        cli.ReportCommands                  -- wires it for the buyback monitor

    Test cases:
        TC-LBS-001  write lands rows under year partitions of the period; read returns them
                    sorted by known_on, ts_code, doc_key with string columns
        TC-LBS-002  writing the same (ts_code, doc_key) again replaces the row; other rows stay
        TC-LBS-003  read(as_of) keeps rows with known_on <= as_of only; codes filter; unknown
                    set gives an empty frame with COLUMNS
        TC-LBS-004  bad set name, missing required column, null key or bad period raise
                    SchemaError; duplicate keys inside one write keep the last
        TC-LBS-005  write(replace_source=s) drops the earlier rows of source s that the new rows do
                    not carry, also in other year partitions; rows of other sources stay
    """

    def __init__(self, writer: ParquetWriter, lake_root: Path, dates: DateCodec) -> None:
        self._writer = writer
        self._root = lake_root / "derived" / ROOT
        self._dates = dates

    def write(
        self, label_set: str, rows: pd.DataFrame, replace_source: str | None = None
    ) -> list[Path]:
        """
        Purpose:
            Upsert rows of one label set.

        Contract:
            Input:
                label_set:      str        -- lower snake case
                rows:           DataFrame  -- REQUIRED columns non-null; other COLUMNS optional
                replace_source: str | None -- a `source` value: its earlier rows are removed first
            Output:
                list[Path]  -- the partitions written (empty for an empty frame and no removal)
            Raises:
                SchemaError  -- bad name, missing column, null key, period not YYYYMMDD
                LakeError    -- a write failed
        """
        frame = self._to_frame(label_set, rows)
        years = set(frame["period"].str[:4].dropna())
        if replace_source is not None:
            years |= {f.parent.name.split("=", 1)[1] for f in self._list_files(label_set)}
        paths: list[Path] = []
        for year in sorted(years):
            path = self._get_path(label_set, str(year))
            part = frame[frame["period"].str[:4] == year]
            old = pd.read_parquet(path).astype("string") if path.exists() else frame.iloc[0:0]
            kept = old if replace_source is None else old[old["source"] != replace_source]
            if part.empty and len(kept) == len(old):
                continue
            merged = pd.concat([kept, part], ignore_index=True)
            merged = merged.drop_duplicates(KEY, keep="last").sort_values(["period", *KEY])
            rel = path.relative_to(self._root.parent)
            paths.append(
                self._writer.write_table("derived", str(rel), merged.reset_index(drop=True))
            )
        logger.info("labels %s: %d rows -> %d partitions", label_set, len(frame), len(paths))
        return paths

    def read(
        self, label_set: str, codes: list[str] | None = None, as_of: str | None = None
    ) -> pd.DataFrame:
        """
        Purpose:
            Rows of one label set, optionally as known on a date.

        Contract:
            Input:
                label_set: str; codes: ts_codes or None (all);
                as_of: YYYYMMDD or None -- keep known_on <= as_of (rows without known_on dropped)
            Output:
                DataFrame  -- COLUMNS, string dtype, sorted by known_on, ts_code, doc_key
            Raises:
                SchemaError  -- bad set name or as_of
        """
        self._check_name(label_set)
        files = self._list_files(label_set)
        if not files:
            return pd.DataFrame({c: pd.Series(dtype="string") for c in COLUMNS})
        out = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
        out = out.reindex(columns=COLUMNS).astype("string")
        if codes is not None:
            out = out[out["ts_code"].isin(codes)]
        if as_of is not None:
            self._check_date(as_of, "as_of")
            out = out[out["known_on"].notna() & (out["known_on"] <= as_of)]
        return out.sort_values(["known_on", *KEY], na_position="last").reset_index(drop=True)

    def list_sets(self) -> list[str]:
        """
        Purpose:
            Names of the label sets on disk.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- sorted; empty when nothing was written
            Raises:
                (none)
        """
        if not self._root.exists():
            return []
        return sorted(p.name for p in self._root.iterdir() if p.is_dir())

    def _to_frame(self, label_set: str, rows: pd.DataFrame) -> pd.DataFrame:
        self._check_name(label_set)
        missing = [c for c in REQUIRED if c not in rows.columns]
        if missing:
            raise SchemaError(f"labels {label_set}: missing columns {missing}")
        frame = rows.reindex(columns=COLUMNS).astype("string")
        if frame[list(REQUIRED)].isna().any().any():
            raise SchemaError(f"labels {label_set}: null in {list(REQUIRED)}")
        for column in ("period", "known_on", "event_date"):
            for value in frame[column].dropna().unique():
                self._check_date(str(value), column)
        return frame.drop_duplicates(KEY, keep="last")

    def _list_files(self, label_set: str) -> list[Path]:
        return sorted((self._root / label_set).glob("year=*/part-0.parquet"))

    def _get_path(self, label_set: str, year: str) -> Path:
        return self._root / label_set / f"year={year}" / "part-0.parquet"

    def _check_name(self, label_set: str) -> None:
        if not _SET_NAME.match(label_set):
            raise SchemaError(f"label set {label_set!r} must be lower snake case")

    def _check_date(self, value: str, column: str) -> None:
        try:
            self._dates.validate(value)
        except ValueError as exc:
            raise SchemaError(f"labels: {column} {value!r} is not YYYYMMDD") from exc
