"""Derived DuckDB views over curated/ (D-015c, views first): adjusted prices, fundamentals."""

from __future__ import annotations

import logging
from collections.abc import Mapping

import duckdb

from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)
SCHEMA = "derived"
PRICES_VIEW = f"{SCHEMA}.prices_adj"
FUNDAMENTALS_VIEW = f"{SCHEMA}.fundamentals_long"
_PRICE_SQL = f"""
CREATE OR REPLACE VIEW {PRICES_VIEW} AS
SELECT d.trade_date, d.ts_code, d.open, d.high, d.low, d.close, d.pre_close, d.vol, d.amount,
       a.adj_factor, d.close * a.adj_factor AS close_adj
FROM curated.daily d
JOIN curated.adj_factor a USING (ts_code, trade_date)
{{alias_filter}}"""
# Tushare keeps a retired code's bars AND back-fills that history under the new code (000043 ->
# 001914, 000022 -> 001872, 300114 -> 302132): codes missing from stock_basic (L + D + P) are
# retired aliases and are dropped so no company is counted twice (D-053).
_ALIAS_FILTER = "WHERE d.ts_code IN (SELECT ts_code FROM curated.stock_basic)"


class DerivedViews:
    """
    Purpose:
        Create the `derived` schema views built only from curated/: `derived.prices_adj`
        (daily bars joined to adj_factor, close_adj = close * adj_factor; PRICE_PANEL columns;
        retired alias codes absent from stock_basic dropped)
        and `derived.fundamentals_long` (every period-swept dataset unpivoted to one row per
        numeric field and announced version; statements filtered to report_type = '1').

    Contract:
        Input:
            catalog:  LakeCatalog                -- connection
            query:    LakeQuery                  -- which curated views exist
            datasets: Mapping[str, DatasetSpec]  -- Config.datasets; sources = sweep kind "period"
        Output:
            instance; `refresh() -> list[str]` views created
        Raises:
            (none at construction)

    Used by:
        pipeline.CuratePipeline  -- after compaction
        pipeline.DeriveStep      -- injected type or call
        cli.QuantCnCli           -- composition root
        cli.QuantCnCli           -- composition root

    Test cases:
        TC-DV-001  prices_adj joins daily and adj_factor with close_adj = close * adj_factor
        TC-DV-002  fundamentals_long keeps report_type 1 only, every version, no null values
        TC-DV-003  views are skipped when their curated inputs are missing
        TC-DV-004  prices_adj drops codes missing from stock_basic (retired aliases)
    """

    def __init__(
        self, catalog: LakeCatalog, query: LakeQuery, datasets: Mapping[str, DatasetSpec]
    ) -> None:
        self._catalog = catalog
        self._query = query
        self._datasets = dict(datasets)

    def refresh(self) -> list[str]:
        """
        Purpose:
            (Re)create every derived view whose curated inputs exist; drop the others.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- views created, e.g. ["derived.prices_adj", ...]
            Raises:
                LakeError  -- DuckDB rejects a view
        """
        con = self._catalog.connection
        created: list[str] = []
        self._execute(con, f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        if self._query.has_view("curated.daily") and self._query.has_view("curated.adj_factor"):
            aliases = _ALIAS_FILTER if self._query.has_view("curated.stock_basic") else ""
            self._execute(con, _PRICE_SQL.format(alias_filter=aliases))
            created.append(PRICES_VIEW)
        else:
            self._execute(con, f"DROP VIEW IF EXISTS {PRICES_VIEW}")
        parts = [self._build_unpivot(s) for s in self._list_sources()]
        if parts:
            sql = f"CREATE OR REPLACE VIEW {FUNDAMENTALS_VIEW} AS\n" + "\nUNION ALL\n".join(parts)
            self._execute(con, sql)
            created.append(FUNDAMENTALS_VIEW)
        else:
            self._execute(con, f"DROP VIEW IF EXISTS {FUNDAMENTALS_VIEW}")
        logger.info("derived views: %s", created)
        return created

    def _list_sources(self) -> list[DatasetSpec]:
        return [
            spec
            for spec in self._datasets.values()
            if spec.sweep.kind == "period" and self._query.has_view(f"curated.{spec.name}")
        ]

    def _build_unpivot(self, spec: DatasetSpec) -> str:
        numeric = [f for f in spec.fields if f not in spec.text_fields]
        flag = "update_flag" if "update_flag" in spec.fields else "NULL"
        where = f"{spec.known_on} IS NOT NULL"
        if "report_type" in spec.fields:
            where += " AND report_type = '1'"
        cols = ", ".join(numeric)
        return (
            f"SELECT ts_code, end_date, known_on, ann_date,"
            f" CAST(update_flag AS VARCHAR) AS update_flag, '{spec.name}' AS source, field, value"
            f" FROM (UNPIVOT (SELECT ts_code, end_date,"
            f" {spec.known_on} AS known_on, ann_date, {flag} AS update_flag, {cols}"
            f" FROM curated.{spec.name} WHERE {where}) ON {cols} INTO NAME field VALUE value)"
        )

    @staticmethod
    def _execute(con: duckdb.DuckDBPyConnection, sql: str) -> None:
        try:
            con.execute(sql)
        except duckdb.Error as exc:
            raise LakeError(f"derived view failed: {exc}") from exc
