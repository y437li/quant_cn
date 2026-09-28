"""The only point-in-time join (D-006): fundamentals visible the trading day after announcement."""

from __future__ import annotations

from collections.abc import Sequence

import duckdb
import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.core.frames import FUNDAMENTALS_PIT
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

STATES_VIEW = "derived.fundamentals_states"
_STATES_SQL = f"""
CREATE OR REPLACE VIEW {STATES_VIEW} AS
WITH cal AS (
    SELECT cal_date FROM curated.trade_cal WHERE is_open = 1
),
effective AS (
    SELECT f.*, c.cal_date AS effective_date
    FROM derived.fundamentals_long f
    ASOF JOIN cal c ON c.cal_date > f.known_on
),
versions AS (
    SELECT * FROM effective
    QUALIFY row_number() OVER (
        PARTITION BY ts_code, field, end_date, effective_date
        ORDER BY known_on DESC, ann_date DESC, update_flag DESC NULLS LAST
    ) = 1
),
running AS (
    SELECT ts_code, field, effective_date, end_date,
           arg_max(value, end_date || effective_date) OVER w AS best_value,
           arg_max(end_date, end_date || effective_date) OVER w AS best_end_date,
           arg_max(ann_date, end_date || effective_date) OVER w AS best_ann_date
    FROM versions
    WINDOW w AS (PARTITION BY ts_code, field ORDER BY effective_date, end_date
                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
)
SELECT ts_code, field, effective_date, best_value AS value, best_end_date AS end_date,
       best_ann_date AS ann_date
FROM running
QUALIFY row_number() OVER (
    PARTITION BY ts_code, field, effective_date ORDER BY end_date DESC
) = 1
"""


class PitAligner:
    """
    Purpose:
        Align fundamentals to trading days without look-ahead. A version announced on `known_on`
        (f_ann_date / ann_date) becomes effective on the first trading day strictly after it;
        on each day the visible value of a field is the latest report period effective so far,
        in its latest effective restatement. Older-period restatements never replace a newer
        period. Built as the DuckDB view `derived.fundamentals_states` (one row per change)
        and read with an ASOF JOIN from trading days.

    Contract:
        Input:
            catalog: LakeCatalog  -- connection for the states view
            query:   LakeQuery    -- reads
            codec:   DateCodec    -- validates date arguments
        Output:
            instance; `refresh`, `read_aligned`
        Raises:
            (none at construction)

    Used by:
        pipeline.CuratePipeline    -- refresh after derived views
        research_space/main.ipynb  -- aligned fundamentals
        pipeline.DeriveStep        -- injected type or call
        cli.QuantCnCli             -- composition root
        cli.QuantCnCli             -- composition root

    Test cases:
        TC-PA-001  nothing is visible on or before the announcement date; visible the next session
        TC-PA-002  a restatement of the latest period replaces the value from its effective day
        TC-PA-003  a later restatement of an older period never replaces a newer period
        TC-PA-004  output satisfies FUNDAMENTALS_PIT; ticker and field filters apply
        TC-PA-005  missing inputs raise LakeError; start after end raises ValueError
    """

    def __init__(self, catalog: LakeCatalog, query: LakeQuery, codec: DateCodec) -> None:
        self._catalog = catalog
        self._query = query
        self._codec = codec

    def refresh(self) -> str:
        """
        Purpose:
            (Re)create `derived.fundamentals_states` from derived.fundamentals_long and the
            curated trading calendar.

        Contract:
            Input:
                (none)
            Output:
                str  -- the view name
            Raises:
                LakeError  -- inputs missing or DuckDB rejects the view
        """
        for view in ("derived.fundamentals_long", "curated.trade_cal"):
            if not self._query.has_view(view):
                raise LakeError(f"{view} is missing; compact and refresh derived views first")
        try:
            self._catalog.connection.execute(_STATES_SQL)
        except duckdb.Error as exc:
            raise LakeError(f"cannot create {STATES_VIEW}: {exc}") from exc
        return STATES_VIEW

    def read_aligned(
        self,
        start: str,
        end: str,
        tickers: Sequence[str] | None = None,
        fields: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            Point-in-time values for every trading day in [start, end] and every (ticker, field)
            that has become visible by that day.

        Contract:
            Input:
                start, end: str               -- YYYYMMDD, inclusive, start <= end
                tickers:    Sequence[str] | None  -- ts_code filter; None = all
                fields:     Sequence[str] | None  -- field filter; None = all
            Output:
                DataFrame  -- FUNDAMENTALS_PIT (trade_date, ts_code, field, value, end_date,
                              ann_date), sorted by key; days before first visibility absent
            Raises:
                ValueError  -- malformed dates or start > end
                LakeError   -- states view missing (call refresh) or query failure
        """
        self._codec.validate(start)
        self._codec.validate(end)
        if start > end:
            raise ValueError(f"start {start} is after end {end}")
        if not self._query.has_view(STATES_VIEW):
            raise LakeError(f"{STATES_VIEW} is missing; call refresh() first")
        sql = f"""
            WITH days AS (
                SELECT cal_date AS trade_date FROM curated.trade_cal
                WHERE is_open = 1 AND cal_date BETWEEN ? AND ?
            ),
            keys AS (
                SELECT DISTINCT ts_code, field FROM {STATES_VIEW}
                WHERE (? IS NULL OR list_contains(?, ts_code))
                  AND (? IS NULL OR list_contains(?, field))
            )
            SELECT d.trade_date, k.ts_code, k.field, s.value, s.end_date, s.ann_date
            FROM days d CROSS JOIN keys k
            ASOF JOIN {STATES_VIEW} s
              ON s.ts_code = k.ts_code AND s.field = k.field AND s.effective_date <= d.trade_date
            ORDER BY d.trade_date, k.ts_code, k.field
        """
        tick = list(tickers) if tickers is not None else None
        flds = list(fields) if fields is not None else None
        raw = self._query.sql(sql, [start, end, tick, tick, flds, flds])
        return FUNDAMENTALS_PIT.validate(FUNDAMENTALS_PIT.normalize(raw, strict=True))
