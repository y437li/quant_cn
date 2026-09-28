"""The read API over the lake: SQL through the catalog connection (D-009)."""

from __future__ import annotations

from collections.abc import Sequence

import duckdb
import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.core.frames import PRICE_PANEL
from quant_cn.lake.lake_catalog import LakeCatalog


class LakeQuery:
    """
    Purpose:
        Run read queries against the catalog views; the only way code above the lake reads data.

    Contract:
        Input:
            catalog: LakeCatalog
        Output:
            instance; `sql`, `has_view`, `read_prices`
        Raises:
            (none at construction)

    Used by:
        lake.TradingCalendar     -- reads raw.trade_cal
        lake.Compactor.rebuild   -- reads raw files through DuckDB
        cli.QuantCnCli           -- composition root
        pipeline.CuratePipeline  -- injected type or call
        pipeline.DeriveStep      -- injected type or call
        lake.DerivedViews        -- injected type or call
        lake.PitAligner          -- injected type or call

    Test cases:
        TC-LQ-001  sql returns a DataFrame with parameters bound
        TC-LQ-002  bad SQL raises LakeError
        TC-LQ-003  has_view reflects which views exist
        TC-LQ-004  read_prices returns PRICE_PANEL rows in range, filtered and sorted
    """

    def __init__(self, catalog: LakeCatalog) -> None:
        self._catalog = catalog

    def sql(self, query: str, params: Sequence[object] | None = None) -> pd.DataFrame:
        """
        Purpose:
            Execute a query and return the result as a DataFrame.

        Contract:
            Input:
                query:  str                      -- DuckDB SQL, `?` placeholders
                params: Sequence[object] | None  -- bound in order
            Output:
                DataFrame  -- may be empty
            Raises:
                LakeError  -- DuckDB error (syntax, missing view, type)
        """
        try:
            return self._catalog.connection.execute(query, list(params or [])).df()
        except duckdb.Error as exc:
            raise LakeError(f"query failed: {exc}") from exc

    def has_view(self, name: str) -> bool:
        """
        Purpose:
            True if `schema.view` exists in the catalog.

        Contract:
            Input:
                name: str  -- "raw.trade_cal", "curated.daily", ...
            Output:
                bool
            Raises:
                LakeError  -- catalog unreadable
        """
        schema, _, view = name.partition(".")
        found = self.sql(
            "SELECT 1 FROM duckdb_views() WHERE schema_name = ? AND view_name = ?", [schema, view]
        )
        return not found.empty

    def read_prices(
        self, start: str, end: str, tickers: Sequence[str] | None = None
    ) -> pd.DataFrame:
        """
        Purpose:
            Adjusted daily prices from `derived.prices_adj` for a date range.

        Contract:
            Input:
                start, end: str                 -- YYYYMMDD, inclusive
                tickers:    Sequence[str] | None  -- ts_code filter; None = all
            Output:
                DataFrame  -- PRICE_PANEL, sorted by (trade_date, ts_code); suspended days absent
            Raises:
                LakeError    -- view missing (run curate) or query failure
                SchemaError  -- the view no longer matches PRICE_PANEL
        """
        codes = list(tickers) if tickers is not None else None
        raw = self.sql(
            "SELECT * FROM derived.prices_adj WHERE trade_date BETWEEN ? AND ? "
            "AND (? IS NULL OR list_contains(?, ts_code)) ORDER BY trade_date, ts_code",
            [start, end, codes, codes],
        )
        return PRICE_PANEL.validate(PRICE_PANEL.normalize(raw, strict=True))
