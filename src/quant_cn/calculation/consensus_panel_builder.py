"""Analyst consensus FY1-FY3 net profit per stock on given dates, point in time (plan 36)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.lake.lake_query import LakeQuery

CONSENSUS_COLUMNS = ("trade_date", "ts_code", "fy1", "np1", "np2", "np3", "n_brokers")
FY1_FROM_MONTH = 5  # from May the as-of year is FY1 (annual reports are out)
_CONSENSUS = """
WITH w AS (
  SELECT ts_code, org_name, quarter, np, report_date FROM curated.report_rc
  WHERE report_date > ? AND report_date < ? AND np IS NOT NULL AND quarter LIKE '%Q4'),
l AS (SELECT ts_code, org_name, quarter, arg_max(np, report_date) AS np FROM w GROUP BY 1, 2, 3)
SELECT ts_code, CAST(substr(quarter, 1, 4) AS INTEGER) AS fy, median(np) AS np,
       count(*) AS n
FROM l GROUP BY 1, 2
"""


class ConsensusPanelBuilder:
    """
    Purpose:
        The analyst consensus known on each given date (plan 36, D-173): from report_rc notes
        with report_date in (date - window_days, date) (a note is visible from the session
        after its report_date: known_on_rule next_session), one value per broker and fiscal
        year (its latest note), the median net-profit forecast for FY1, FY2 and FY3 per
        stock. FY1 = the date's year from May, else the year before. np in 10k CNY (as report_rc and
        daily_basic.total_mv). Nothing after a date is read.

    Contract:
        Input:
            query: LakeQuery  -- curated.report_rc
            codec: DateCodec
        Output:
            instance; `build(dates, window_days) -> DataFrame` (CONSENSUS_COLUMNS: fy1 int,
            np1 / np2 / np3 float or NaN, n_brokers = brokers behind np1; one row per date and
            stock with an FY1 or FY2 forecast); empty without report_rc
        Raises:
            (none at construction)

    Used by:
        factor.FactorFactory  -- the `consensus` input of FactorInputs
        risk.RiskInputLoader  -- analyst descriptors of the risk model (plan 37)
        cli.ServiceBuilder    -- injected into FactorFactory

    Test cases:
        TC-CNS-001  medians of the latest note per broker inside the window; a note dated on the
                    date or later does not count (PIT), one window_days earlier does not
        TC-CNS-002  FY1 rolls in May: April uses the previous year as FY1, May the current one
        TC-CNS-003  no report_rc view or no dates -> empty frame with CONSENSUS_COLUMNS
    """

    def __init__(self, query: LakeQuery, codec: DateCodec) -> None:
        self._query = query
        self._codec = codec

    def build(self, dates: Sequence[str], window_days: int) -> pd.DataFrame:
        """
        Purpose:
            Consensus FY1-FY3 per stock on each date.

        Contract:
            Input:
                dates: Sequence[str] YYYYMMDD; window_days: int > 0
            Output:
                DataFrame  -- CONSENSUS_COLUMNS, sorted by trade_date, ts_code
            Raises:
                LakeError  -- the query fails
        """
        empty = pd.DataFrame(columns=list(CONSENSUS_COLUMNS))
        if not dates or not self._query.has_view("curated.report_rc"):
            return empty
        frames = [self._build_one(d, window_days) for d in sorted(set(dates))]
        kept = [f for f in frames if not f.empty]
        out = pd.concat(kept, ignore_index=True) if kept else empty
        return out.sort_values(["trade_date", "ts_code"]).reset_index(drop=True)

    def _build_one(self, day: str, window_days: int) -> pd.DataFrame:
        start = self._codec.to_str(self._codec.to_date(day) - dt.timedelta(days=window_days))
        rows = self._query.sql(_CONSENSUS, [start, day])
        fy1 = self.get_fy1(day)
        wide = rows.pivot_table(index="ts_code", columns="fy", values="np", aggfunc="first")
        counts = rows[rows["fy"] == fy1].set_index("ts_code")["n"]
        out = pd.DataFrame(
            {
                f"np{k}": wide[fy1 + k - 1] if fy1 + k - 1 in wide.columns else float("nan")
                for k in (1, 2, 3)
            },
            index=wide.index,
        )
        out = out[out["np1"].notna() | out["np2"].notna()]
        out["n_brokers"] = counts.reindex(out.index).fillna(0).astype(int)
        return out.reset_index().assign(trade_date=day, fy1=fy1)[list(CONSENSUS_COLUMNS)]

    @staticmethod
    def get_fy1(day: str) -> int:
        """
        Purpose:
            The first unreported fiscal year on a date.

        Contract:
            Input:
                day: str YYYYMMDD
            Output:
                int  -- the year from May, else the year before
            Raises:
                (none)
        """
        year, month = int(day[:4]), int(day[4:6])
        return year if month >= FY1_FROM_MONTH else year - 1
