"""The tradeable universe per session, materialised to derived/universe (plan 04 phase 3)."""

from __future__ import annotations

from quant_cn.core.base_step import BaseStep, ProgressHook
from quant_cn.core.config import UniverseConfig
from quant_cn.core.frames import UNIVERSE_PANEL
from quant_cn.core.step_report import StepReport
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter

TABLE = "universe"
INPUTS = ("curated.trade_cal", "curated.stock_basic", "curated.namechange", "curated.daily")
_SQL = """
WITH cal AS (SELECT cal_date AS trade_date, row_number() OVER (ORDER BY cal_date) AS idx
             FROM curated.trade_cal WHERE is_open = 1),
days AS (SELECT * FROM cal WHERE trade_date BETWEEN ? AND ?
           AND trade_date <= (SELECT max(trade_date) FROM curated.daily)),
stocks AS (SELECT ts_code, list_date, delist_date,
                  regexp_extract(ts_code, '\\.([A-Z]+)$', 1) AS exch
           FROM curated.stock_basic WHERE list_date IS NOT NULL),
listed AS (SELECT s.*, c.idx AS list_idx FROM stocks s
           ASOF LEFT JOIN cal c ON c.trade_date >= s.list_date),
grid AS (SELECT d.trade_date, d.idx, l.ts_code, l.exch, l.list_idx FROM days d
         JOIN listed l ON l.list_date <= d.trade_date
          AND (l.delist_date IS NULL OR d.trade_date < l.delist_date)),
named AS (SELECT g.*, n.name FROM grid g
          ASOF LEFT JOIN curated.namechange n
            ON n.ts_code = g.ts_code AND n.start_date <= g.trade_date),
flags AS (SELECT n.trade_date, n.ts_code,
                 NOT list_contains(?, n.exch) AS bad_exchange,
                 coalesce(n.name LIKE '%ST%' OR n.name LIKE 'PT%', FALSE) AS st,
                 coalesce(n.name LIKE '%退%', FALSE) AS delisting,
                 coalesce(n.idx - n.list_idx + 1 < ?, TRUE) AS new_listing,
                 b.ts_code IS NULL AS suspended
          FROM named n
          LEFT JOIN curated.daily b ON b.ts_code = n.ts_code AND b.trade_date = n.trade_date)
SELECT trade_date, ts_code,
       CAST(NOT (bad_exchange OR st OR delisting OR new_listing OR suspended) AS DOUBLE)
           AS in_universe,
       concat_ws(',', CASE WHEN bad_exchange THEN 'exchange' END, CASE WHEN st THEN 'st' END,
                 CASE WHEN delisting THEN 'delisting' END,
                 CASE WHEN new_listing THEN 'new_listing' END,
                 CASE WHEN suspended THEN 'suspended' END) AS reason
FROM flags ORDER BY trade_date, ts_code"""


class UniverseStep(BaseStep):
    """
    Purpose:
        Build UNIVERSE_PANEL: one row per stock listed on each session (list_date <= t <
        delist_date; retired alias codes are absent from stock_basic, D-053), in_universe = 1 when
        no rule excludes it, and every failing rule kept in `reason` (comma-joined): exchange (not
        in config, BJ by default, D-054), st (name in effect at t contains ST or starts with PT,
        from namechange start dates), delisting (name contains 退, 退市整理期), new_listing (fewer
        than min_sessions sessions since the first session on/after list_date), suspended (no
        daily bar at t). Delisted stocks stay in history (no survivorship). Point in time: the
        name at t is the namechange row with the latest start_date <= t (FACTOR_TESTING_DESIGN
        §11). One unit per calendar year, written to derived/universe/year=YYYY.

    Contract:
        Input:
            query:  LakeQuery
            writer: ParquetWriter  -- write_derived
            rules:  UniverseConfig
        Output:
            instance; BaseStep API
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-US-001  reasons: exchange, st, delisting, new_listing, suspended; clean rows are in
        TC-US-002  PIT: a stock leaves on its ST start date and returns when the ST name ends
        TC-US-003  rows only while listed (last row the session before delist_date); one file a year
        TC-US-004  missing input views -> no units, nothing written
    """

    def __init__(self, query: LakeQuery, writer: ParquetWriter, rules: UniverseConfig) -> None:
        self._query = query
        self._writer = writer
        self._rules = rules

    @property
    def name(self) -> str:
        """
        Purpose:
            Step name.

        Contract:
            Input:
                (none)
            Output:
                str  -- "universe"
            Raises:
                (none)
        """
        return TABLE

    def list_units(self) -> list[str]:
        """
        Purpose:
            Years to build: from rules.start to the last daily session.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- ["2010", ...]; empty when an input view is missing
            Raises:
                LakeError  -- query failure
        """
        if not all(self._query.has_view(v) for v in INPUTS):
            return []
        last = self._query.sql("SELECT max(trade_date) AS d FROM curated.daily")["d"].iloc[0]
        if not isinstance(last, str):
            return []
        return [str(y) for y in range(int(self._rules.start[:4]), int(last[:4]) + 1)]

    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        """
        Purpose:
            Build and write every year.

        Contract:
            Input:
                run_id: str; progress: ProgressHook | None
            Output:
                StepReport  -- keys_total = years, fetched = years written, rows = rows written
            Raises:
                LakeError, SchemaError
        """
        units = self.list_units()
        report = StepReport(self.name, keys_total=len(units))
        for year in units:
            start = max(self._rules.start, f"{year}0101")
            frame = self._query.sql(
                _SQL,
                [start, f"{year}1231", list(self._rules.exchanges), self._rules.min_sessions],
            )
            panel = UNIVERSE_PANEL.validate(UNIVERSE_PANEL.normalize(frame, strict=True))
            self._writer.write_derived(TABLE, int(year), panel)
            report.fetched += 1
            report.rows += len(panel)
            if progress:
                progress(year, "fetched")
        return report
