"""Point-in-time panels the risk model reads for one fitting window (plan 05)."""

from __future__ import annotations

import datetime as dt
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field

import pandas as pd

from quant_cn.calculation.consensus_panel_builder import ConsensusPanelBuilder
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.risk_model_settings import ExternalSeriesSpec, ThemeBasketSpec
from quant_cn.lake.exposure_reader import ExposureReader
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.statement_version_reader import StatementVersionReader
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.risk.fundamental_descriptors import ANNUAL_FIELDS, BALANCE_FIELDS, TTM_FIELDS

logger = logging.getLogger(__name__)

PRICE_HISTORY = 530  # sessions: RSTR 504 + lag 21 + slack
BASIC_COLUMNS = ("total_mv", "circ_mv", "turnover_rate_f", "dv_ttm")
CALENDAR_DAYS_PER_SESSION = 1.5
EXTRA_DAYS = 30
GROWTH_YEARS = 6  # annual reports read back per snapshot (5 used + one restated)
SERIES_SLACK_DAYS = 10  # calendar days of external series before the price history


@dataclass(frozen=True)
class RiskInputs:
    """
    Purpose:
        Everything the descriptors need for exposures on [start, end], all point in time:
        dense prices and daily_basic from PRICE_HISTORY sessions before start (descriptor
        windows), universe members with their Shenwan L1 group (EXPOSURE_PANEL), balance and TTM
        fields (FUNDAMENTALS_PIT) and month-end snapshots of annual EPS and revenue.

    Contract:
        Input:
            start, end:   str        -- YYYYMMDD exposure window
            prices:       DataFrame  -- PRICE_PANEL, dense
            basic:        DataFrame  -- trade_date, ts_code, total_mv, circ_mv, turnover_rate_f,
                                        dv_ttm (trailing dividend yield, percent)
            members:      DataFrame  -- EXPOSURE_PANEL rows in [start, end]
            fundamentals: DataFrame  -- FUNDAMENTALS_PIT for BALANCE_FIELDS + TTM_FIELDS
            annual:       DataFrame  -- as_of, ts_code, end_date, field, value
            external:     dict[str, DataFrame]  -- descriptor -> trade_date (vendor date plus
                                                   the spec's shift), pct_chg (percent)
            themes:       dict[str, tuple[tuple[str, ...], str]]  -- descriptor -> (member codes,
                                                                     first session) (D-130)
            consensus:    DataFrame  -- CONSENSUS_COLUMNS on month-end sessions from the month
                                        before start, and end (plan 37); empty when not loaded
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        risk.RiskInputLoader    -- built by load
        risk.DescriptorBuilder  -- descriptor input
        risk.RiskModel  -- injected type or call

    Test cases:
        TC-RIL-001  load reads every panel for the window with the price history before start
    """

    start: str
    end: str
    prices: pd.DataFrame
    basic: pd.DataFrame
    members: pd.DataFrame
    fundamentals: pd.DataFrame
    annual: pd.DataFrame
    external: dict[str, pd.DataFrame] = field(default_factory=dict)
    themes: dict[str, tuple[tuple[str, ...], str]] = field(default_factory=dict)
    consensus: pd.DataFrame = field(default_factory=pd.DataFrame)


class RiskInputLoader:
    """
    Purpose:
        Read RiskInputs for one exposure window through the lake readers only (no parquet
        paths): LakeReader for prices, daily_basic and FUNDAMENTALS_PIT, ExposureReader for
        universe members with Shenwan L1 (D-093), StatementVersionReader for the annual reports
        known on each month-end session (growth descriptors refresh monthly, PIT at the
        snapshot date; D-127).

    Contract:
        Input:
            reader:   LakeReader; exposures: ExposureReader; versions: StatementVersionReader
            calendar: TradingCalendar; codec: DateCodec
            query: LakeQuery  -- theme members (curated.ths_member, a current snapshot)
            external: Sequence[ExternalSeriesSpec]; themes: Sequence[ThemeBasketSpec]
            consensus: ConsensusPanelBuilder | None; consensus_days: int >= 0  -- the analyst
                       consensus is read only with a builder and consensus_days > 0 (plan 37)
        Output:
            instance; `load(start, end) -> RiskInputs`
        Raises:
            (none at construction)

    Used by:
        pipeline.RiskModelStep  -- yearly inputs
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-RIL-001  load reads every panel for the window with the price history before start
        TC-RIL-002  annual snapshots are taken on the last session of each month, starting with
                    the month before start
        TC-RIL-003  external series are read from before the price history, prices turned into
                    percent changes and dates shifted; theme members come from ths_member
        TC-RIL-004  the consensus is read on the snapshot dates and end with consensus_days, and
                    not read without a builder or with consensus_days 0
    """

    def __init__(
        self,
        reader: LakeReader,
        exposures: ExposureReader,
        versions: StatementVersionReader,
        calendar: TradingCalendar,
        codec: DateCodec,
        query: LakeQuery,
        external: Sequence[ExternalSeriesSpec] = (),
        themes: Sequence[ThemeBasketSpec] = (),
        consensus: ConsensusPanelBuilder | None = None,
        consensus_days: int = 0,
    ) -> None:
        self._reader = reader
        self._exposures = exposures
        self._versions = versions
        self._calendar = calendar
        self._codec = codec
        self._query = query
        self._external = list(external)
        self._themes = list(themes)
        self._consensus = consensus
        self._consensus_days = consensus_days

    def load(self, start: str, end: str) -> RiskInputs:
        """
        Purpose:
            All panels for exposures on [start, end].

        Contract:
            Input:
                start, end: str  -- YYYYMMDD, start <= end
            Output:
                RiskInputs
            Raises:
                ValueError  -- start > end
                LakeError   -- a view is missing
        """
        if start > end:
            raise ValueError(f"start {start} after end {end}")
        history = self._get_history_start(start, PRICE_HISTORY)
        prices = self._reader.read_prices(history, end, dense=True)
        basic = self._reader.read_panel("daily_basic", history, end, columns=list(BASIC_COLUMNS))
        members = self._exposures.read_exposures(start, end)
        fields = [*BALANCE_FIELDS, *TTM_FIELDS]
        fundamentals = self._reader.read_fundamentals_pit(fields, start, end)
        annual = self._read_annual(start, end)
        external = {s.descriptor: self._read_external(s, history, end) for s in self._external}
        themes = {t.descriptor: (self._read_members(t.concept), t.start) for t in self._themes}
        logger.info(
            "risk inputs %s..%s: %d members, %d prices", start, end, len(members), len(prices)
        )
        consensus = pd.DataFrame()
        if self._consensus is not None and self._consensus_days > 0:
            dates = sorted({*self.list_snapshot_dates(start, end), end})
            consensus = self._consensus.build(dates, self._consensus_days)
        return RiskInputs(
            start, end, prices, basic, members, fundamentals, annual, external, themes, consensus
        )

    def _read_external(self, spec: ExternalSeriesSpec, start: str, end: str) -> pd.DataFrame:
        first = self._get_shifted(start, -SERIES_SLACK_DAYS)
        frame = self._reader.read_panel(
            spec.dataset, first, end, tickers=[spec.code], columns=[spec.column]
        ).sort_values("trade_date")
        values = frame[spec.column].astype(float)
        pct = values if spec.kind == "pct" else (values / values.shift(1) - 1.0) * 100.0
        dates = frame["trade_date"].astype(str)
        if spec.date_shift_days:
            dates = dates.map(lambda d: self._get_shifted(d, spec.date_shift_days))
        out = pd.DataFrame({"trade_date": dates.to_numpy(), "pct_chg": pct.to_numpy()})
        return out.dropna().reset_index(drop=True)

    def _read_members(self, concept: str) -> tuple[str, ...]:
        rows = self._query.sql(
            "SELECT DISTINCT con_code FROM curated.ths_member WHERE ts_code = ? ORDER BY 1",
            [concept],
        )
        return tuple(rows["con_code"].astype(str))

    def list_snapshot_dates(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            Month-end sessions used as growth snapshots: the last session of each month in
            [start, end] plus the last session before start.

        Contract:
            Input:
                start, end: str  -- YYYYMMDD
            Output:
                list[str]  -- ascending, unique
            Raises:
                (none)
        """
        earlier = self._get_shifted(start, -45)
        sessions = self._calendar.list_sessions(earlier, end)
        before = [s for s in sessions if s < start]
        inside = [s for s in sessions if s >= start]
        month_ends = [
            s for i, s in enumerate(inside) if i + 1 == len(inside) or inside[i + 1][:6] != s[:6]
        ]
        return ([before[-1]] if before else []) + month_ends

    def _read_annual(self, start: str, end: str) -> pd.DataFrame:
        parts = []
        for as_of in self.list_snapshot_dates(start, end):
            first = f"{int(as_of[:4]) - GROWTH_YEARS}1231"
            snap = self._versions.read_versions(list(ANNUAL_FIELDS), as_of, first)
            parts.append(snap[snap["end_date"].str.endswith("1231")].assign(as_of=as_of))
        if not parts:
            return pd.DataFrame(columns=["as_of", "ts_code", "end_date", "field", "value"])
        return pd.concat(parts, ignore_index=True)

    def _get_history_start(self, start: str, lookback: int) -> str:
        earlier = self._get_shifted(start, -int(lookback * CALENDAR_DAYS_PER_SESSION) - EXTRA_DAYS)
        sessions = [s for s in self._calendar.list_sessions(earlier, start) if s < start]
        return sessions[-lookback] if len(sessions) >= lookback else earlier

    def _get_shifted(self, date: str, days: int) -> str:
        return self._codec.to_str(self._codec.to_date(date) + dt.timedelta(days=days))
