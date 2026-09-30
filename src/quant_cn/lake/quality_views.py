"""Cross-source quality views (schema `quality`): verification never overwrites primary data."""

from __future__ import annotations

import logging

import duckdb

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)
SCHEMA = "quality"
AGREEMENT_VIEW = f"{SCHEMA}.margin_targets_agreement"
MISMATCH_VIEW = f"{SCHEMA}.price_mismatches"
CROSSCHECK_VIEW = f"{SCHEMA}.price_crosscheck"
ADJ_VIEW = f"{SCHEMA}.adj_crosscheck"
TOLERANCE = 1e-6  # relative (D-085)
# D-084: month-end agreement of the SSE eligibility proxy with Tushare margin_secs (2024-04+).
_AGREEMENT_SQL = f"""
CREATE OR REPLACE VIEW {AGREEMENT_VIEW} AS
WITH month_end AS (SELECT max(trade_date) AS trade_date FROM curated.margin_secs
                   WHERE trade_date >= '20240401' GROUP BY substr(trade_date, 1, 6)),
proxy AS (SELECT trade_date, ts_code FROM derived.margin_targets
          WHERE source = 'sse_margin_detail_proxy'
            AND trade_date IN (SELECT trade_date FROM month_end)),
listed AS (SELECT trade_date, ts_code FROM curated.margin_secs
           WHERE exchange = 'SSE' AND trade_date IN (SELECT trade_date FROM month_end))
SELECT coalesce(p.trade_date, l.trade_date) AS trade_date,
       count(*) FILTER (WHERE p.ts_code IS NOT NULL AND l.ts_code IS NOT NULL) AS both_lists,
       count(*) FILTER (WHERE l.ts_code IS NULL) AS proxy_only,
       count(*) FILTER (WHERE p.ts_code IS NULL) AS margin_secs_only,
       count(*) FILTER (WHERE p.ts_code IS NOT NULL AND l.ts_code IS NOT NULL) / count(*)
           AS agreement
FROM proxy p FULL JOIN listed l ON l.trade_date = p.trade_date AND l.ts_code = p.ts_code
GROUP BY 1"""
# D-085: Tushare unadjusted closes vs BaoStock (adjustflag 3) on traded days; recent rows win.
_MISMATCH_SQL = f"""
CREATE OR REPLACE VIEW {MISMATCH_VIEW} AS
WITH bs AS ({{baostock}}),
joined AS (SELECT d.ts_code, d.trade_date, d.close AS tushare_close, b.close AS baostock_close
           FROM curated.daily d JOIN bs b USING (ts_code, trade_date)
           WHERE b.tradestatus = 1)
SELECT *, abs(tushare_close - baostock_close) / abs(tushare_close) AS rel_diff,
       abs(tushare_close - baostock_close) > {TOLERANCE} * abs(tushare_close) AS mismatch
FROM joined"""
_CROSSCHECK_SQL = f"""
CREATE OR REPLACE VIEW {CROSSCHECK_VIEW} AS
SELECT trade_date, count(*) AS compared, count(*) FILTER (WHERE mismatch) AS mismatches,
       count(*) FILTER (WHERE mismatch) / count(*) AS mismatch_rate
FROM {MISMATCH_VIEW} GROUP BY trade_date"""
# D-085: at each BaoStock dividend date, the step of Tushare's adj_factor vs BaoStock's back factor.
_ADJ_SQL = f"""
CREATE OR REPLACE VIEW {ADJ_VIEW} AS
WITH ev AS (SELECT ts_code, trade_date, back_adjust_factor,
                   lag(back_adjust_factor) OVER (PARTITION BY ts_code ORDER BY trade_date)
                       AS prev_back
            FROM curated.baostock_adj_factor),
ts AS (SELECT ts_code, trade_date, adj_factor,
              lag(adj_factor) OVER (PARTITION BY ts_code ORDER BY trade_date) AS prev_adj
       FROM curated.adj_factor)
SELECT ev.ts_code, ev.trade_date, ev.back_adjust_factor / ev.prev_back AS baostock_step,
       ts.adj_factor / ts.prev_adj AS tushare_step,
       abs(ev.back_adjust_factor / ev.prev_back - ts.adj_factor / ts.prev_adj)
           / (ts.adj_factor / ts.prev_adj) AS rel_diff
FROM ev JOIN ts USING (ts_code, trade_date)
WHERE ev.prev_back IS NOT NULL AND ts.prev_adj IS NOT NULL"""


class QualityViews:
    """
    Purpose:
        Create the `quality` schema: cross-source comparisons that report, never overwrite (D-065).
        `quality.margin_targets_agreement` (SSE eligibility proxy vs margin_secs, D-084);
        `quality.price_mismatches` / `quality.price_crosscheck` (Tushare daily close vs BaoStock,
        relative tolerance 1e-6, per row / per day, D-085); `quality.adj_crosscheck` (adjustment
        step at each BaoStock dividend date vs Tushare adj_factor).

    Contract:
        Input:
            catalog: LakeCatalog  -- connection
            query:   LakeQuery    -- which curated / derived views exist
        Output:
            instance; `refresh() -> list[str]` views created
        Raises:
            (none at construction)

    Used by:
        lake.DerivedViews.refresh  -- after the derived views

    Test cases:
        TC-QV-001  price_crosscheck counts closes beyond tolerance; recent rows override backfill
        TC-QV-002  adj_crosscheck compares factor steps at BaoStock dividend dates
        TC-QV-003  views whose inputs are missing are dropped, not created
    """

    def __init__(self, catalog: LakeCatalog, query: LakeQuery) -> None:
        self._catalog = catalog
        self._query = query

    def refresh(self) -> list[str]:
        """
        Purpose:
            (Re)create every quality view whose inputs exist; drop the others.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- quality views created
            Raises:
                LakeError  -- DuckDB rejects a view
        """
        con = self._catalog.connection
        self._execute(con, f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        baostock = self._build_baostock_source()
        margin = ["derived.margin_targets", "curated.margin_secs"]
        plan: list[tuple[str, list[str], str]] = [
            (AGREEMENT_VIEW, margin, _AGREEMENT_SQL),
            (
                MISMATCH_VIEW,
                ["curated.daily"],
                _MISMATCH_SQL.format(baostock=baostock) if baostock else "",
            ),
            (CROSSCHECK_VIEW, ["curated.daily"], _CROSSCHECK_SQL if baostock else ""),
            (ADJ_VIEW, ["curated.baostock_adj_factor", "curated.adj_factor"], _ADJ_SQL),
        ]
        created: list[str] = []
        for view, inputs, sql in plan:
            if sql and all(self._query.has_view(name) for name in inputs):
                self._execute(con, sql)
                created.append(view)
            else:
                self._execute(con, f"DROP VIEW IF EXISTS {view}")
        logger.info("quality views: %s", created)
        return created

    def _build_baostock_source(self) -> str:
        cols = "ts_code, trade_date, close, tradestatus"
        recent = self._query.has_view("curated.baostock_daily_recent")
        backfill = self._query.has_view("curated.baostock_daily")
        if recent and backfill:
            return (
                f"SELECT {cols} FROM curated.baostock_daily_recent UNION ALL "
                f"SELECT {cols} FROM curated.baostock_daily b WHERE NOT EXISTS (SELECT 1 FROM "
                "curated.baostock_daily_recent r WHERE r.ts_code = b.ts_code "
                "AND r.trade_date = b.trade_date)"
            )
        if recent or backfill:
            name = "baostock_daily_recent" if recent else "baostock_daily"
            return f"SELECT {cols} FROM curated.{name}"
        return ""

    @staticmethod
    def _execute(con: duckdb.DuckDBPyConnection, sql: str) -> None:
        try:
            con.execute(sql)
        except duckdb.Error as exc:
            raise LakeError(f"quality view failed: {exc}") from exc
