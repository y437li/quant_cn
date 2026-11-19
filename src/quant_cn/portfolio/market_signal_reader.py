"""Valuation, analyst revisions and institutional surveys of a sector (plan 33)."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from quant_cn.calculation.realized_vol_calculator import RealizedVolCalculator
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.sector_monitor_settings import SectorMonitorSettings
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.sector_metric_reader import LINE_COLUMNS, SectorMetricReader

INDEX_FIELD = {"pb": "pb", "pe_ttm": "pe"}  # daily_basic field -> sw_daily field
FY1_FROM_MONTH = 5  # from May the as-of year is FY1 (annual reports are out)
_VALUATION = """
    SELECT ts_code, trade_date, {field} AS v FROM curated.{table}
    WHERE ts_code IN (SELECT UNNEST(?)) AND trade_date <= ?"""
_FORECASTS = """
    SELECT ts_code, report_date, org_name, quarter, np FROM curated.report_rc
    WHERE ts_code IN (SELECT UNNEST(?)) AND report_date > ? AND report_date <= ?
      AND np IS NOT NULL AND quarter LIKE '%Q4'"""
_SURVEYS = """
    SELECT ts_code, substr(surv_date, 1, 6) AS month, count(DISTINCT surv_date) AS n
    FROM curated.stk_surv WHERE ts_code IN (SELECT UNNEST(?)) AND surv_date <= ?
    GROUP BY 1, 2"""


class MarketSignalReader:
    """
    Purpose:
        Market-side signals of a monitored sector (plan 33, D-170), as LINE_COLUMNS lines
        (label = company or index name):
        - `read_valuation(names, index, field, as_of)`: (percentile lines, levels). The field
          is daily_basic "pb" or "pe_ttm" for companies and the matching sw_daily field for
          the index (INDEX_FIELD); values <= 0 are dropped (no PE for a loss-maker). The
          percentile (%, 0-100) is the share of the trailing `val_window` sessions at or below
          each day (RealizedVolCalculator.compute_rank_pct), over the last history_sessions;
          levels hold each label's latest value.
        - `read_revisions(names, as_of)`: per month end (and as_of for the current month) the
          % change of the FY1 median net-profit forecast (report_rc, trailing revision_days;
          one value per broker, its latest report in the window, so repeated notes of one
          broker do not outweigh the rest); none when either median is <= 0 (a loss)
          against the window ending revision_days earlier, only when both windows target
          the same FY1 (the as-of year from May, else the year before).
        - `read_surveys(names, as_of)`: (survey days per month over history_months, survey
          days in the trailing survey_days) from stk_surv.
        Missing views give empty frames.

    Contract:
        Input:
            settings: SectorMonitorSettings (val_window via ranks, revision_days, survey_days,
            history_sessions, history_months); query: LakeQuery; ranks: RealizedVolCalculator
            (the valuation percentile window); codec: DateCodec
        Output:
            instance; the read_* methods above
        Raises:
            LakeError  -- a lake query fails

    Used by:
        portfolio.SectorMonitorBuilder  -- valuation, revision and surveys metrics
        cli.AppServiceBuilder  -- `build_sector_monitor`

    Test cases:
        TC-MKS-001  valuation: company and index percentile lines and latest levels; values
                    <= 0 dropped; no view gives empty frames
        TC-MKS-002  revisions: median FY1 forecast change between two 90-day windows, one
                    (latest) value per broker; no value across an FY1 change or when a median
                    is a loss
        TC-MKS-003  surveys: distinct survey days per month and in the trailing window
    """

    def __init__(
        self,
        settings: SectorMonitorSettings,
        query: LakeQuery,
        ranks: RealizedVolCalculator,
        codec: DateCodec,
    ) -> None:
        self._s = settings
        self._query = query
        self._ranks = ranks
        self._codec = codec

    def read_valuation(
        self, names: dict[str, str], index: tuple[str, str], field: str, as_of: str
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Purpose:
            Valuation percentile lines and latest levels of the companies and the index.

        Contract:
            Input:
                names: dict[str, str] (ts_code -> name); index: (code, name); field: "pb" |
                "pe_ttm"; as_of: str YYYYMMDD
            Output:
                (DataFrame, DataFrame)  -- LINE_COLUMNS percentile (%) lines, period trade
                date; LINE_COLUMNS latest level per label
            Raises:
                LakeError  -- a query fails
        """
        frames = []
        if self._query.has_view("curated.daily_basic"):
            frames.append(self._query.sql(_VALUATION.format(field=field, table="daily_basic"),
                                          [list(names), as_of]))  # fmt: skip
        if self._query.has_view("curated.sw_daily"):
            index_sql = _VALUATION.format(field=INDEX_FIELD[field], table="sw_daily")
            frames.append(self._query.sql(index_sql, [[index[0]], as_of]))
        empty = pd.DataFrame(columns=LINE_COLUMNS)
        if not frames:
            return empty, empty
        long = pd.concat(frames)
        long = long[long["v"] > 0]
        wide = long.pivot_table(index="trade_date", columns="ts_code", values="v").sort_index()
        labels = {**names, index[0]: index[1]}
        pct_rows, level_rows = [], []
        for code in wide.columns:
            series = wide[code].dropna()
            if series.empty:
                continue
            pct = (self._ranks.compute_rank_pct(series) * 100).dropna()
            tail = pct.tail(self._s.history_sessions)
            pct_rows += [{"label": labels[str(code)], "period": str(day), "value": float(v)}
                         for day, v in tail.items()]  # fmt: skip
            level_rows.append({"label": labels[str(code)], "period": str(series.index[-1]),
                               "value": float(series.iloc[-1])})  # fmt: skip
        return pd.DataFrame(pct_rows, columns=LINE_COLUMNS), pd.DataFrame(
            level_rows, columns=LINE_COLUMNS
        )

    def read_revisions(self, names: dict[str, str], as_of: str) -> pd.DataFrame:
        """
        Purpose:
            Monthly FY1 forecast revision (%) per company.

        Contract:
            Input:
                names: dict[str, str]; as_of: str YYYYMMDD
            Output:
                DataFrame  -- LINE_COLUMNS, period YYYY-MM, value %
            Raises:
                LakeError  -- the query fails
        """
        if not self._query.has_view("curated.report_rc"):
            return pd.DataFrame(columns=LINE_COLUMNS)
        ends = self._list_month_ends(as_of)
        days = dt.timedelta(days=self._s.revision_days)
        start = self._codec.to_str(self._codec.to_date(ends[0]) - 2 * days)
        rows = self._query.sql(_FORECASTS, [list(names), start, as_of])
        out = []
        for code, group in rows.groupby("ts_code"):
            for end in ends:
                before = self._codec.to_str(self._codec.to_date(end) - days)
                now, then = self._get_median(group, end), self._get_median(group, before)
                if now is None or then is None or min(now, then) <= 0:
                    continue  # a % change of a loss (or of nothing) means nothing
                if self._get_fy1(end) == self._get_fy1(before):
                    out.append({"label": names[str(code)], "period": f"{end[:4]}-{end[4:6]}",
                                "value": (now / then - 1) * 100})  # fmt: skip
        return pd.DataFrame(out, columns=LINE_COLUMNS)

    def read_surveys(self, names: dict[str, str], as_of: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Purpose:
            Institutional survey days per month, and in the trailing survey_days.

        Contract:
            Input:
                names: dict[str, str]; as_of: str YYYYMMDD
            Output:
                (DataFrame, DataFrame)  -- LINE_COLUMNS monthly counts (period YYYY-MM, last
                history_months); LINE_COLUMNS one row per company with surveys (period as_of)
            Raises:
                LakeError  -- a query fails
        """
        empty = pd.DataFrame(columns=LINE_COLUMNS)
        if not self._query.has_view("curated.stk_surv"):
            return empty, empty
        monthly = self._query.sql(_SURVEYS, [list(names), as_of])
        monthly["label"] = monthly["ts_code"].map(names)
        monthly["period"] = monthly["month"].str[:4] + "-" + monthly["month"].str[4:]
        monthly["value"] = monthly["n"].astype(float)
        lines = SectorMetricReader.get_recent(monthly[LINE_COLUMNS], self._s.history_months)
        since = self._codec.to_str(
            self._codec.to_date(as_of) - dt.timedelta(days=self._s.survey_days)
        )
        recent = self._query.sql(
            "SELECT ts_code, count(DISTINCT surv_date) AS n FROM curated.stk_surv "
            "WHERE ts_code IN (SELECT UNNEST(?)) AND surv_date > ? AND surv_date <= ? GROUP BY 1",
            [list(names), since, as_of],
        )
        latest = pd.DataFrame({"label": recent["ts_code"].map(names), "period": as_of,
                               "value": recent["n"].astype(float)})  # fmt: skip
        return lines, latest.reset_index(drop=True)

    def _list_month_ends(self, as_of: str) -> list[str]:
        """Month ends of the last history_months - 1 months before as_of's month, then as_of."""
        first = self._codec.to_date(as_of).replace(day=1)
        ends = []
        for _ in range(self._s.history_months - 1):
            first = (first - dt.timedelta(days=1)).replace(day=1)
            ends.append(self._codec.to_str(self._get_month_end(first)))
        return [*sorted(ends), as_of]

    @staticmethod
    def _get_month_end(first: dt.date) -> dt.date:
        nxt = (first.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        return nxt - dt.timedelta(days=1)

    def _get_median(self, rows: pd.DataFrame, end: str) -> float | None:
        """Median FY1 net-profit forecast in (end - revision_days, end], latest per broker."""
        start = self._codec.to_str(
            self._codec.to_date(end) - dt.timedelta(days=self._s.revision_days)
        )
        fy = f"{self._get_fy1(end)}Q4"
        hit = rows[(rows["report_date"] > start) & (rows["report_date"] <= end)
                   & (rows["quarter"] == fy)]  # fmt: skip
        latest = hit.sort_values("report_date").drop_duplicates("org_name", keep="last")["np"]
        return float(latest.median()) if not latest.empty else None

    @staticmethod
    def _get_fy1(day: str) -> int:
        year, month = int(day[:4]), int(day[4:6])
        return year if month >= FY1_FROM_MONTH else year - 1
