"""The lake read API above raw SQL (D-041, D-089): panels, prices, PIT fundamentals, reference."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping, Sequence

import pandas as pd

from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.exceptions import LakeError
from quant_cn.core.frames import FUNDAMENTALS_PIT, PRICE_PANEL, UNIVERSE_PANEL
from quant_cn.core.schema import Schema
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.panel_cache import PanelCache
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar

REFERENCE_PREFIX = "reference/"


class LakeReader:
    """
    Purpose:
        The read API factors, the universe step and notebooks use (SRC_DESIGN §2.2b, D-089): one
        curated dataset as a panel, dense or sparse prices, point-in-time fundamentals, reference
        tables (in-memory frames and view discovery: LakeQuery). Retired codes are mapped to
        their surviving codes on every per-stock read (TickerAliasMap, new code wins); every
        output is validated with its schema; an optional PanelCache serves repeated reads.
        LakeQuery stays the raw SQL layer underneath.

    Contract:
        Input:
            catalog:   LakeCatalog                 -- connection (register_frame)
            query:     LakeQuery                   -- SQL
            datasets:  Mapping[str, DatasetSpec]   -- Config.datasets
            aligner:   PitAligner                  -- PIT fundamentals
            alias_map: TickerAliasMap              -- retired -> surviving codes
            calendar:  TradingCalendar             -- sessions for dense prices
            cache:     PanelCache | None           -- on in notebooks, off in pipelines
        Output:
            instance; `read_panel`, `read_prices`, `read_fundamentals_pit`, `read_universe`,
            `read_reference` (register_frame / list_views are on LakeQuery)
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder    -- build_reader
        (none yet)            -- UniverseStep, factors (plan 04 phases 3-4), notebooks
        factor.FactorFactory  -- injected type or call

    Test cases:
        TC-LRD-001  read_panel filters dates and tickers, validates, maps old-code rows (new wins)
        TC-LRD-002  read_prices dense adds NaN rows for missing sessions inside each stock's span
        TC-LRD-003  read_fundamentals_pit attaches statements filed under the old code to the new
        TC-LRD-004  read_reference returns reference tables only; unknown or dated names raise
        TC-LRD-006  a second identical read is a cache hit
        TC-LRD-007  read_universe filters dates and, with members_only, excluded rows
    """

    def __init__(
        self,
        catalog: LakeCatalog,
        query: LakeQuery,
        datasets: Mapping[str, DatasetSpec],
        aligner: PitAligner,
        alias_map: TickerAliasMap,
        calendar: TradingCalendar,
        cache: PanelCache | None = None,
    ) -> None:
        self._catalog = catalog
        self._query = query
        self._datasets = dict(datasets)
        self._aligner = aligner
        self._alias = alias_map
        self._calendar = calendar
        self._cache = cache

    def read_panel(
        self,
        dataset: str,
        start: str,
        end: str,
        tickers: Sequence[str] | None = None,
        columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            One curated dataset over a date range as a long panel, sorted by primary key.

        Contract:
            Input:
                dataset:    str                   -- a dated curated dataset
                start, end: str                   -- YYYYMMDD, inclusive, on its date column
                tickers:    Sequence[str] | None  -- ts_code filter (old codes follow automatically)
                columns:    Sequence[str] | None  -- subset; the primary key is always included
            Output:
                DataFrame  -- the dataset's curated columns (or the subset), key unique
            Raises:
                LakeError   -- unknown dataset, undated dataset, or query failure
                SchemaError -- the curated view no longer matches the spec
        """
        spec = self._get_spec(dataset)
        date_col = spec.curated.partition_by or spec.known_on
        if not date_col:
            raise LakeError(f"{dataset} has no date column; use read_reference")
        cols = list(dict.fromkeys([*spec.primary_key, *(columns or spec.fields)]))
        key: Hashable = ("read_panel", dataset, start, end, self._to_key(tickers), tuple(cols))
        return self._read_cached(
            key, lambda: self._load_panel(spec, date_col, start, end, tickers, cols)
        )

    def read_prices(
        self, start: str, end: str, tickers: Sequence[str] | None = None, dense: bool = False
    ) -> pd.DataFrame:
        """
        Purpose:
            Daily prices (raw and backward-adjusted close) for a date range.

        Contract:
            Input:
                start, end: str                   -- YYYYMMDD, inclusive
                tickers:    Sequence[str] | None  -- ts_code filter
                dense:      bool                  -- True: every session between a stock's first
                                                     and last bar in range, suspended days as NaN
            Output:
                DataFrame  -- PRICE_PANEL sorted by (trade_date, ts_code)
            Raises:
                LakeError   -- derived.prices_adj or trade_cal missing
                SchemaError -- the view no longer matches PRICE_PANEL
        """
        key: Hashable = ("read_prices", start, end, self._to_key(tickers), dense)
        return self._read_cached(key, lambda: self._load_prices(start, end, tickers, dense))

    def read_fundamentals_pit(
        self,
        fields: Sequence[str] | None,
        start: str,
        end: str,
        tickers: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            Point-in-time fundamentals per session (PitAligner), statements filed under a retired
            code attached to the surviving code (the new code's value wins on the same day).

        Contract:
            Input:
                fields:     Sequence[str] | None  -- fundamentals_long field names; None = all
                start, end: str                   -- YYYYMMDD, inclusive
                tickers:    Sequence[str] | None
            Output:
                DataFrame  -- FUNDAMENTALS_PIT sorted by key
            Raises:
                ValueError  -- malformed dates or start > end
                LakeError   -- states view missing or query failure
        """
        key: Hashable = (
            "read_fundamentals_pit",
            self._to_key(fields),
            start,
            end,
            self._to_key(tickers),
        )
        return self._read_cached(key, lambda: self._load_fundamentals(fields, start, end, tickers))

    def read_universe(self, start: str, end: str, members_only: bool = False) -> pd.DataFrame:
        """
        Purpose:
            The tradeable universe per session (UniverseStep output).

        Contract:
            Input:
                start, end:   str   -- YYYYMMDD, inclusive
                members_only: bool  -- True: only rows with in_universe = 1
            Output:
                DataFrame  -- UNIVERSE_PANEL sorted by (trade_date, ts_code)
            Raises:
                LakeError  -- derived.universe missing (run curate) or query failure
        """
        key: Hashable = ("read_universe", start, end, members_only)
        member = "AND in_universe = 1" if members_only else ""
        sql = (
            "SELECT trade_date, ts_code, in_universe, reason FROM derived.universe "
            f"WHERE trade_date BETWEEN ? AND ? {member} ORDER BY trade_date, ts_code"
        )
        return self._read_cached(
            key,
            lambda: UNIVERSE_PANEL.validate(
                UNIVERSE_PANEL.normalize(self._query.sql(sql, [start, end]), strict=True)
            ),
        )

    def read_reference(self, name: str) -> pd.DataFrame:
        """
        Purpose:
            A whole reference table (curated under reference/: stock_basic, namechange, trade_cal,
            index_daily, index_classify, fund_basic, fut_basic, ...).

        Contract:
            Input:
                name: str  -- dataset name
            Output:
                DataFrame  -- the dataset's curated columns, sorted by primary key
            Raises:
                LakeError  -- unknown dataset or not a reference table
        """
        spec = self._get_spec(name)
        if not spec.curated.path.startswith(REFERENCE_PREFIX):
            raise LakeError(f"{name} is not a reference table; use read_panel")
        order = ", ".join(spec.primary_key) or "1"
        return self._read_cached(
            ("read_reference", name),
            lambda: self._validate(
                spec, self._query.sql(f"SELECT * FROM curated.{name} ORDER BY {order}"), spec.fields
            ),
        )

    def _load_panel(
        self,
        spec: DatasetSpec,
        date_col: str,
        start: str,
        end: str,
        tickers: Sequence[str] | None,
        cols: list[str],
    ) -> pd.DataFrame:
        coded = "ts_code" in spec.fields
        codes = self._alias.list_codes(tickers) if tickers is not None and coded else None
        where = "(? IS NULL OR list_contains(?, ts_code))" if coded else "? IS NULL AND ? IS NULL"
        order = ", ".join(spec.primary_key) or "1"
        raw = self._query.sql(
            f"SELECT {', '.join(cols)} FROM curated.{spec.name} "
            f"WHERE {date_col} BETWEEN ? AND ? AND {where} ORDER BY {order}",
            [start, end, codes, codes],
        )
        frame = (
            self._alias.normalize_codes(raw, spec.primary_key)
            if coded and spec.primary_key
            else raw
        )
        if tickers is not None and coded:
            frame = frame[frame["ts_code"].isin(list(tickers))].reset_index(drop=True)
        return self._validate(spec, frame, cols)

    def _load_prices(
        self, start: str, end: str, tickers: Sequence[str] | None, dense: bool
    ) -> pd.DataFrame:
        sparse = self._query.read_prices(start, end, tickers)
        if not dense or sparse.empty:
            return sparse
        sessions = pd.DataFrame({"trade_date": self._calendar.list_sessions(start, end)})
        spans = sparse.groupby("ts_code")["trade_date"].agg(["min", "max"]).reset_index()
        grid = spans.merge(sessions, how="cross")
        grid = grid[(grid["trade_date"] >= grid["min"]) & (grid["trade_date"] <= grid["max"])]
        dense_frame = grid[["trade_date", "ts_code"]].merge(
            sparse, on=["trade_date", "ts_code"], how="left"
        )
        dense_frame = dense_frame.sort_values(["trade_date", "ts_code"]).reset_index(drop=True)
        return PRICE_PANEL.validate(PRICE_PANEL.normalize(dense_frame, strict=True))

    def _load_fundamentals(
        self,
        fields: Sequence[str] | None,
        start: str,
        end: str,
        tickers: Sequence[str] | None,
    ) -> pd.DataFrame:
        codes = self._alias.list_codes(tickers) if tickers is not None else None
        aligned = self._aligner.read_aligned(start, end, codes, fields)
        frame = self._alias.normalize_codes(aligned, FUNDAMENTALS_PIT.primary_key)
        if tickers is not None:
            frame = frame[frame["ts_code"].isin(list(tickers))].reset_index(drop=True)
        return FUNDAMENTALS_PIT.validate(FUNDAMENTALS_PIT.normalize(frame, strict=True))

    def _read_cached(self, key: Hashable, load: Callable[[], pd.DataFrame]) -> pd.DataFrame:
        if self._cache is not None:
            hit = self._cache.find(key)
            if hit is not None:
                return hit
        frame = load()
        if self._cache is not None:
            self._cache.add(key, frame)
        return frame

    def _get_spec(self, name: str) -> DatasetSpec:
        spec = self._datasets.get(name)
        if spec is None:
            raise LakeError(f"unknown dataset {name!r}")
        return spec

    @staticmethod
    def _validate(spec: DatasetSpec, frame: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
        schema = Schema(
            spec.name,
            list(cols),
            [c for c in spec.text_fields if c in cols],
            spec.primary_key,
        )
        return schema.validate(schema.normalize(frame, strict=True))

    @staticmethod
    def _to_key(values: Sequence[str] | None) -> tuple[str, ...] | None:
        return tuple(values) if values is not None else None
