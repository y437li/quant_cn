"""Retired codes mapped to their surviving codes (D-053, D-089): one company, one history."""

from __future__ import annotations

from collections.abc import Sequence

import duckdb
import pandas as pd

from quant_cn.core.config import TickerAlias
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

ALIAS_VIEW = "derived.ticker_alias"
MIN_SHARED_DAYS = 20
MIN_EQUAL_RATE = 0.99
_ALIAS_SQL = f"""
CREATE OR REPLACE VIEW {ALIAS_VIEW} AS
WITH cfg(old_code, new_code) AS ({{config_rows}}),
listed AS (SELECT ts_code FROM curated.stock_basic),
old AS (SELECT ts_code, trade_date, close FROM curated.daily
        WHERE ts_code NOT IN (SELECT ts_code FROM listed)),
new AS (SELECT ts_code, trade_date, close FROM curated.daily
        WHERE ts_code IN (SELECT ts_code FROM listed)),
hits AS (SELECT o.ts_code AS old_code, n.ts_code AS new_code, count(*) AS equal_days
         FROM old o JOIN new n ON n.trade_date = o.trade_date AND n.close = o.close
         GROUP BY 1, 2 HAVING count(*) >= {MIN_SHARED_DAYS}),
stats AS (SELECT h.old_code, h.new_code, count(*) AS shared_days,
                 max(h.equal_days) / count(*) AS equal_rate
          FROM hits h JOIN old o ON o.ts_code = h.old_code
          JOIN new n ON n.ts_code = h.new_code AND n.trade_date = o.trade_date
          GROUP BY 1, 2),
detected AS (SELECT *, count(*) OVER (PARTITION BY old_code) AS candidates
             FROM stats WHERE equal_rate >= {MIN_EQUAL_RATE}),
ranges AS (SELECT ts_code, min(trade_date) AS first_date, max(trade_date) AS last_date
           FROM old GROUP BY 1)
SELECT coalesce(c.old_code, d.old_code) AS old_code, coalesce(c.new_code, d.new_code) AS new_code,
       r.first_date, r.last_date, d.shared_days, d.equal_rate,
       coalesce(d.candidates, 0) AS candidates,
       CASE WHEN c.old_code IS NOT NULL AND d.old_code IS NOT NULL THEN 'config+detected'
            WHEN c.old_code IS NOT NULL THEN 'config' ELSE 'detected' END AS source,
       c.old_code IS NOT NULL
           OR (d.candidates = 1 AND d.old_code NOT IN (SELECT old_code FROM cfg)) AS accepted
FROM detected d FULL JOIN cfg c ON c.old_code = d.old_code AND c.new_code = d.new_code
LEFT JOIN ranges r ON r.ts_code = coalesce(c.old_code, d.old_code)"""


class TickerAliasMap:
    """
    Purpose:
        Map retired codes to their surviving codes so a company has one history. Tushare keeps a
        retired code's rows and back-fills the same history under the new code, but some datasets
        (stk_limit, moneyflow, margin_detail) exist only under the old code before the change.
        `refresh` builds `derived.ticker_alias`: pairs detected from the data (a code missing from
        stock_basic whose closes equal a listed code's on >= 20 shared dates, >= 99% equal) plus
        the config pairs; every candidate keeps its match statistics, and an old code matching
        more than one listed code is kept but not accepted. `normalize_codes` renames accepted
        old codes and, where both codes have a row for the same key, keeps the new code's row.

    Contract:
        Input:
            catalog: LakeCatalog             -- connection for the view
            query:   LakeQuery               -- reads
            aliases: Sequence[TickerAlias]   -- Config.ticker_aliases (the floor)
        Output:
            instance; `refresh`, `get_pairs`, `normalize_codes`, `list_codes`
        Raises:
            (none at construction)

    Used by:
        lake.DerivedViews   -- refresh during curate
        lake.LakeReader     -- apply to panels and PIT fundamentals
        cli.ServiceBuilder  -- injected type or call
        lake.StatementVersionReader  -- retired codes on statement versions

    Test cases:
        TC-TAM-001  detection finds the equal-close pair with its statistics; config pairs kept
        TC-TAM-002  an old code matching two listed codes is recorded but not accepted
        TC-TAM-003  normalize_codes renames old codes; the new code's row wins on a duplicate key
        TC-TAM-004  list_codes adds the old codes of requested new codes (filters see both)
    """

    def __init__(
        self, catalog: LakeCatalog, query: LakeQuery, aliases: Sequence[TickerAlias] = ()
    ) -> None:
        self._catalog = catalog
        self._query = query
        self._aliases = list(aliases)
        self._pairs: dict[str, str] | None = None

    def refresh(self) -> str | None:
        """
        Purpose:
            (Re)create `derived.ticker_alias`.

        Contract:
            Input:
                (none)
            Output:
                str | None  -- the view name, or None when curated daily / stock_basic are missing
            Raises:
                LakeError  -- DuckDB rejects the view
        """
        self._pairs = None
        if not all(self._query.has_view(v) for v in ("curated.daily", "curated.stock_basic")):
            self._execute(f"DROP VIEW IF EXISTS {ALIAS_VIEW}")
            return None
        rows = ", ".join(
            f"('{self._format(a.old_code)}', '{self._format(a.new_code)}')" for a in self._aliases
        )
        config_rows = f"VALUES {rows}" if rows else "SELECT NULL, NULL WHERE FALSE"
        self._execute("CREATE SCHEMA IF NOT EXISTS derived")
        self._execute(_ALIAS_SQL.format(config_rows=config_rows))
        return ALIAS_VIEW

    def get_pairs(self) -> dict[str, str]:
        """
        Purpose:
            Accepted old -> new pairs (read once per refresh).

        Contract:
            Input:
                (none)
            Output:
                dict[str, str]  -- empty when the view does not exist
            Raises:
                LakeError  -- query failure
        """
        if self._pairs is None:
            if not self._query.has_view(ALIAS_VIEW):
                return {}
            frame = self._query.sql(f"SELECT old_code, new_code FROM {ALIAS_VIEW} WHERE accepted")
            self._pairs = dict(zip(frame["old_code"], frame["new_code"], strict=True))
        return dict(self._pairs)

    def normalize_codes(self, frame: pd.DataFrame, key: Sequence[str]) -> pd.DataFrame:
        """
        Purpose:
            Rename accepted old codes to new codes; on a duplicate key the new code's row wins.

        Contract:
            Input:
                frame: DataFrame      -- with a ts_code column (returned unchanged otherwise)
                key:   Sequence[str]  -- primary key including ts_code
            Output:
                DataFrame  -- same columns, key unique, sorted by key
            Raises:
                LakeError  -- alias view unreadable
        """
        pairs = self.get_pairs()
        if "ts_code" not in frame.columns or not pairs or frame.empty:
            return frame
        is_alias = frame["ts_code"].isin(list(pairs))
        if not is_alias.any():
            return frame
        out = frame.assign(ts_code=frame["ts_code"].replace(pairs), _alias=is_alias)
        out = out.sort_values("_alias", kind="stable").drop_duplicates(list(key), keep="first")
        return out.drop(columns="_alias").sort_values(list(key)).reset_index(drop=True)

    def list_codes(self, codes: Sequence[str]) -> list[str]:
        """
        Purpose:
            `codes` plus the old codes of any requested new code, so a filter sees both.

        Contract:
            Input:
                codes: Sequence[str]
            Output:
                list[str]  -- deduplicated, input order first
            Raises:
                LakeError  -- alias view unreadable
        """
        wanted = set(codes)
        extra = [old for old, new in self.get_pairs().items() if new in wanted]
        return list(dict.fromkeys([*codes, *extra]))

    def _execute(self, sql: str) -> None:
        try:
            self._catalog.connection.execute(sql)
        except duckdb.Error as exc:
            raise LakeError(f"ticker alias view failed: {exc}") from exc

    @staticmethod
    def _format(value: str) -> str:
        return value.replace("'", "''")
