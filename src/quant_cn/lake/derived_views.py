"""Derived DuckDB views over curated/ (D-015c): prices, fundamentals, futures, industry."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence

import duckdb

from quant_cn.core.config import FuturesCategory
from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)
SCHEMA = "derived"
PRICES_VIEW = f"{SCHEMA}.prices_adj"
FUNDAMENTALS_VIEW = f"{SCHEMA}.fundamentals_long"
HOLDING_VIEW = f"{SCHEMA}.fut_holding_brokers"
ONE_SIDED_VIEW = f"{SCHEMA}.fut_daily_one_sided"
INDUSTRY_VIEW = f"{SCHEMA}.industry_l1"
# statements only: event datasets are period-swept too (forecast_vip, disclosure_date; D-081)
FUNDAMENTALS_PREFIX = "fundamentals/"
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
# D-079: contract rows only, member-category totals dropped, the one-day "ZCE" label normalised.
_HOLDING_SQL = f"""
CREATE OR REPLACE VIEW {HOLDING_VIEW} AS
SELECT h.trade_date, h.exchange, h.symbol, h.broker, h.vol, h.vol_chg, h.long_hld, h.long_chg,
       h.short_hld, h.short_chg
FROM (SELECT * REPLACE (CASE WHEN exchange = 'ZCE' THEN 'CZCE' ELSE exchange END AS exchange)
      FROM curated.fut_holding) h
WHERE regexp_matches(h.symbol, '^[A-Za-z]+[0-9]{{{{3,4}}}}$'){{category_filter}}"""
# D-079: SHFE/DCE/CZCE/INE reported vol, amount and oi two-sided (long + short) until 2019-12-31.
_ONE_SIDED_SQL = f"""
CREATE OR REPLACE VIEW {ONE_SIDED_VIEW} AS
SELECT ts_code, trade_date, pre_close, pre_settle, open, high, low, close, settle, change1, change2,
       CASE WHEN two_sided THEN vol / 2 ELSE vol END AS vol,
       CASE WHEN two_sided THEN amount / 2 ELSE amount END AS amount,
       CASE WHEN two_sided THEN oi / 2 ELSE oi END AS oi,
       CASE WHEN two_sided THEN oi_chg / 2 ELSE oi_chg END AS oi_chg,
       two_sided AS two_sided_adjusted
FROM (SELECT *, trade_date < '20200102'
             AND regexp_extract(ts_code, '\\.([A-Z]+)$', 1) IN ('SHF', 'DCE', 'ZCE', 'INE')
             AS two_sided
      FROM curated.fut_daily)"""
# D-071: Shenwan L1 per stock as validity intervals (valid_from / valid_to inclusive, NULL = open).
# PIT rows come from index_member_all; the time before a stock's first record and gaps between
# records carry its first-known L1 with industry_backfilled = TRUE (usable for grouping, not PIT).
_NEXT_DAY = "strftime(strptime({0}, '%Y%m%d') + INTERVAL 1 DAY, '%Y%m%d')"
_PREV_DAY = "strftime(strptime({0}, '%Y%m%d') - INTERVAL 1 DAY, '%Y%m%d')"
_INDUSTRY_SQL = f"""
CREATE OR REPLACE VIEW {INDUSTRY_VIEW} AS
WITH m AS (SELECT ts_code, l1_code, l1_name, in_date, out_date
           FROM curated.index_member_all WHERE in_date IS NOT NULL),
first_l1 AS (SELECT ts_code, arg_min(l1_code, in_date) AS l1_code,
                    arg_min(l1_name, in_date) AS l1_name, min(in_date) AS first_in
             FROM m GROUP BY ts_code),
ordered AS (SELECT ts_code, out_date,
                   lead(in_date) OVER (PARTITION BY ts_code ORDER BY in_date) AS next_in
            FROM m)
SELECT ts_code, l1_code, l1_name, in_date AS valid_from, out_date AS valid_to,
       FALSE AS industry_backfilled
FROM m
UNION ALL
SELECT ts_code, l1_code, l1_name, NULL AS valid_from, {_PREV_DAY.format("first_in")} AS valid_to,
       TRUE AS industry_backfilled
FROM first_l1
UNION ALL
SELECT o.ts_code, f.l1_code, f.l1_name, {_NEXT_DAY.format("o.out_date")} AS valid_from,
       {_PREV_DAY.format("o.next_in")} AS valid_to, TRUE AS industry_backfilled
FROM ordered o JOIN first_l1 f USING (ts_code)
WHERE o.out_date IS NOT NULL AND o.next_in > {_NEXT_DAY.format("o.out_date")}"""


class DerivedViews:
    """
    Purpose:
        Create the `derived` schema views built only from curated/:
        `derived.prices_adj` (daily bars joined to adj_factor, close_adj = close * adj_factor;
        PRICE_PANEL columns; retired alias codes absent from stock_basic dropped);
        `derived.fundamentals_long` (every period-swept dataset unpivoted to one row per numeric
        field and announced version; statements under curated/fundamentals/ only, filtered to
        report_type = '1');
        `derived.fut_holding_brokers` (contract rows of fut_holding without member-category
        totals, exchange "ZCE" -> "CZCE"; D-079);
        `derived.fut_daily_one_sided` (fut_daily with vol, amount, oi, oi_chg halved for
        SHFE/DCE/CZCE/INE before 2020-01-02, flagged two_sided_adjusted; D-079);
        `derived.industry_l1` (Shenwan L1 validity intervals per stock, PIT rows plus back-filled
        rows flagged industry_backfilled; l1_pit = rows not back-filled, l1_grouping = any; D-071).

    Contract:
        Input:
            catalog:    LakeCatalog                  -- connection
            query:      LakeQuery                    -- which curated views exist
            datasets:   Mapping[str, DatasetSpec]    -- Config.datasets; sources = sweep "period"
            categories: Sequence[FuturesCategory]    -- Config.futures_categories
        Output:
            instance; `refresh() -> list[str]` views created
        Raises:
            (none at construction)

    Used by:
        pipeline.CuratePipeline  -- after compaction
        pipeline.DeriveStep      -- injected type or call
        cli.ServiceBuilder       -- injected type or call

    Test cases:
        TC-DV-001  prices_adj joins daily and adj_factor with close_adj = close * adj_factor
        TC-DV-002  fundamentals_long keeps report_type 1 only, every version, no null values
        TC-DV-003  views are skipped when their curated inputs are missing
        TC-DV-004  prices_adj drops codes missing from stock_basic (retired aliases)
        TC-DV-005  fut_holding_brokers drops category rows and product symbols, maps ZCE to CZCE
        TC-DV-006  fut_daily_one_sided halves two-sided commodity rows before 2020 only
        TC-DV-007  industry_l1 gives PIT intervals plus back-filled rows before and between them
    """

    def __init__(
        self,
        catalog: LakeCatalog,
        query: LakeQuery,
        datasets: Mapping[str, DatasetSpec],
        categories: Sequence[FuturesCategory] = (),
    ) -> None:
        self._catalog = catalog
        self._query = query
        self._datasets = dict(datasets)
        self._categories = list(categories)

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
        self._execute(con, f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        aliases = _ALIAS_FILTER if self._query.has_view("curated.stock_basic") else ""
        parts = [self._build_unpivot(s) for s in self._list_sources()]
        fundamentals = (
            f"CREATE OR REPLACE VIEW {FUNDAMENTALS_VIEW} AS\n" + "\nUNION ALL\n".join(parts)
            if parts
            else ""
        )
        plan: list[tuple[str, list[str], str]] = [
            (PRICES_VIEW, ["daily", "adj_factor"], _PRICE_SQL.format(alias_filter=aliases)),
            (FUNDAMENTALS_VIEW, [], fundamentals),
            (
                HOLDING_VIEW,
                ["fut_holding"],
                _HOLDING_SQL.format(category_filter=self._build_category_filter()),
            ),
            (ONE_SIDED_VIEW, ["fut_daily"], _ONE_SIDED_SQL),
            (INDUSTRY_VIEW, ["index_member_all"], _INDUSTRY_SQL),
        ]
        created: list[str] = []
        for view, inputs, sql in plan:
            if sql and all(self._query.has_view(f"curated.{name}") for name in inputs):
                self._execute(con, sql)
                created.append(view)
            else:
                self._execute(con, f"DROP VIEW IF EXISTS {view}")
        logger.info("derived views: %s", created)
        return created

    def _build_category_filter(self) -> str:
        if not self._categories:
            return ""
        pairs = ", ".join(
            f"('{self._format_literal(c.exchange)}', '{self._format_literal(c.broker)}')"
            for c in self._categories
        )
        return (
            f"\n  AND NOT EXISTS (SELECT 1 FROM (VALUES {pairs}) c(exchange, broker)"
            " WHERE c.exchange = h.exchange AND c.broker = h.broker)"
        )

    @staticmethod
    def _format_literal(value: str) -> str:
        return value.replace("'", "''")

    def _list_sources(self) -> list[DatasetSpec]:
        return [
            spec
            for spec in self._datasets.values()
            if spec.sweep.kind == "period"
            and spec.curated.path.startswith(FUNDAMENTALS_PREFIX)
            and self._query.has_view(f"curated.{spec.name}")
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
