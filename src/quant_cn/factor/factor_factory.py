"""Factors from config/factors.yaml and the panels they need (SRC_DESIGN §2.5)."""

from __future__ import annotations

import datetime as dt
import importlib
import pkgutil
from collections.abc import Sequence

import pandas as pd

from quant_cn.calculation.consensus_panel_builder import ConsensusPanelBuilder
from quant_cn.core.config import FactorSpec
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError
from quant_cn.factor import library
from quant_cn.factor.base_factor import BaseFactor, FactorInputs
from quant_cn.lake.dated_table_store import DatedTableStore
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.trading_calendar import TradingCalendar

CALENDAR_DAYS_PER_SESSION = 1.6  # generous: covers Golden Week and Spring Festival gaps
EXTRA_DAYS = 30
CONSENSUS_LEAD_DAYS = 40  # month ends from before the start: the first output has a reading
GAUGE_LEAD_DAYS = 60  # a quarter's first 14 sessions have no reading: read from before start
GAUGE_TABLE = "retail_gauge"
GAUGE_FIELDS = ["as_of", "ts_code", "pct"]


class FactorFactory:
    """
    Purpose:
        Resolve config/factors.yaml entries to BaseFactor instances (every module under
        factor/library/ is imported so its classes register themselves; adding a factor needs one
        module, one registry block and one YAML line) and load, once, the panels the chosen factors
        declare: dense prices from `lookback` sessions before the start, PIT fundamentals for the
        union of fields, daily_basic columns, and the analyst consensus on month-end sessions
        (from CONSENSUS_LEAD_DAYS before the start) and the last session (plan 36), and the
        RetailGauge readings from GAUGE_LEAD_DAYS before the start (plan 21 ph6).

    Contract:
        Input:
            specs:    Sequence[FactorSpec]  -- Config.factors
            calendar: TradingCalendar       -- sessions for the lookback
            codec:    DateCodec
            consensus: ConsensusPanelBuilder | None  -- needed only by `consensus` factors
            gauge:     DatedTableStore | None        -- derived/retail_gauge; needed only by
                                                        `retail_gauge` factors
        Output:
            instance; `build_all`, `build_inputs`
        Raises:
            (none at construction)

    Used by:
        notebooks             -- factor campaign
        pipeline.FeatureStep  -- injected type or call
        cli.ServiceBuilder    -- injected type or call

    Test cases:
        TC-FAF-001  build_all returns the configured classes with names and params
        TC-FAF-002  an unknown class name raises ConfigError
        TC-FAF-003  build_inputs loads prices from lookback sessions before start, the union of
                    fundamentals fields and the needed daily_basic columns only
        TC-FAF-004  a consensus factor gets the consensus on month-end sessions and the last
                    session, with the longest declared window; without one the panel is empty;
                    a consensus factor without a builder raises ConfigError
        TC-FAF-005  a retail_gauge factor gets the readings from GAUGE_LEAD_DAYS before start;
                    without one the panel is empty; without the store it raises ConfigError
    """

    def __init__(
        self,
        specs: Sequence[FactorSpec],
        calendar: TradingCalendar,
        codec: DateCodec,
        consensus: ConsensusPanelBuilder | None = None,
        gauge: DatedTableStore | None = None,
    ) -> None:
        self._specs = list(specs)
        self._calendar = calendar
        self._codec = codec
        self._consensus = consensus
        self._gauge = gauge

    def build_all(self) -> list[BaseFactor]:
        """
        Purpose:
            One instance per configured factor.

        Contract:
            Input:
                (none)
            Output:
                list[BaseFactor]  -- in config order
            Raises:
                ConfigError  -- unknown class or bad params
        """
        for module in pkgutil.iter_modules(library.__path__):
            importlib.import_module(f"{library.__name__}.{module.name}")
        out = []
        for spec in self._specs:
            cls = BaseFactor.registry.get(spec.class_name)
            if cls is None:
                raise ConfigError(f"factor {spec.name}: unknown class {spec.class_name!r}")
            try:
                out.append(cls(spec.name, **spec.params))
            except (TypeError, ValueError) as exc:
                raise ConfigError(f"factor {spec.name}: {exc}") from exc
        return out

    def build_inputs(
        self, reader: LakeReader, factors: Sequence[BaseFactor], start: str, end: str
    ) -> FactorInputs:
        """
        Purpose:
            The panels the factors need for outputs in [start, end].

        Contract:
            Input:
                reader: LakeReader; factors: Sequence[BaseFactor]; start, end: str (YYYYMMDD)
            Output:
                FactorInputs  -- prices dense from the session `max(lookback)` before start (always
                                 loaded: the session grid); fundamentals for the union of `fields`
                                 in [start, end]; daily_basic with the union of `basic_columns`
                                 from the same history start; consensus (see the class)
            Raises:
                LakeError  -- views missing
                ConfigError  -- a consensus factor without a ConsensusPanelBuilder, a
                                retail_gauge factor without the DatedTableStore
        """
        history = self._get_history_start(start, max((f.lookback for f in factors), default=0))
        prices = reader.read_prices(history, end, dense=True)
        fields = sorted({f_ for f in factors for f_ in f.fields})
        fundamentals = (
            reader.read_fundamentals_pit(fields, start, end) if fields else pd.DataFrame()
        )
        columns = sorted({c for f in factors for c in f.basic_columns})
        basic = (
            reader.read_panel("daily_basic", history, end, columns=columns)
            if columns
            else pd.DataFrame()
        )
        consensus = self._build_consensus(factors, start, end)
        gauge = self._read_gauge(factors, start, end)
        return FactorInputs(
            prices=prices,
            fundamentals=fundamentals,
            daily_basic=basic,
            consensus=consensus,
            retail_gauge=gauge,
        )

    def _read_gauge(self, factors: Sequence[BaseFactor], start: str, end: str) -> pd.DataFrame:
        if not any("retail_gauge" in f.inputs for f in factors):
            return pd.DataFrame()
        if self._gauge is None:
            raise ConfigError("a retail_gauge factor needs the DatedTableStore")
        lead = dt.timedelta(days=GAUGE_LEAD_DAYS)
        earlier = self._codec.to_str(self._codec.to_date(start) - lead)
        years = [str(y) for y in range(int(earlier[:4]), int(end[:4]) + 1)]
        rows = self._gauge.read(GAUGE_TABLE, years)
        if rows.empty:
            return pd.DataFrame(columns=GAUGE_FIELDS)
        inside = (rows["as_of"] >= earlier) & (rows["as_of"] <= end)
        out: pd.DataFrame = rows.loc[inside, GAUGE_FIELDS].reset_index(drop=True)
        return out

    def _build_consensus(self, factors: Sequence[BaseFactor], start: str, end: str) -> pd.DataFrame:
        days = max((f.consensus_days for f in factors if "consensus" in f.inputs), default=0)
        if days == 0:
            return pd.DataFrame()
        if self._consensus is None:
            raise ConfigError("a consensus factor needs a ConsensusPanelBuilder")
        lead = dt.timedelta(days=CONSENSUS_LEAD_DAYS)
        earlier = self._codec.to_str(self._codec.to_date(start) - lead)
        sessions = self._calendar.list_sessions(earlier, end)
        month_ends = [
            s for s, n in zip(sessions, [*sessions[1:], ""], strict=True) if s[:6] != n[:6]
        ]
        return self._consensus.build(month_ends, days)

    def _get_history_start(self, start: str, lookback: int) -> str:
        if lookback == 0:
            return start
        days = int(lookback * CALENDAR_DAYS_PER_SESSION) + EXTRA_DAYS
        earlier = self._codec.to_str(self._codec.to_date(start) - dt.timedelta(days=days))
        sessions = [s for s in self._calendar.list_sessions(earlier, start) if s < start]
        return sessions[-lookback] if len(sessions) >= lookback else earlier
