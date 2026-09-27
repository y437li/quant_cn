"""The read API over the lake: SQL through the catalog connection (D-009)."""

from __future__ import annotations

from collections.abc import Sequence

import duckdb
import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_catalog import LakeCatalog


class LakeQuery:
    """
    Purpose:
        Run read queries against the catalog views; the only way code above the lake reads data.

    Contract:
        Input:
            catalog: LakeCatalog
        Output:
            instance; `sql`, `has_view`
        Raises:
            (none at construction)

    Used by:
        lake.TradingCalendar             -- reads raw.trade_cal
        lake.Compactor.compact           -- reads raw files through DuckDB
        cli.QuantCnCli                   -- composition root

    Test cases:
        TC-LQ-001  sql returns a DataFrame with parameters bound
        TC-LQ-002  bad SQL raises LakeError
        TC-LQ-003  has_view reflects which views exist
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
