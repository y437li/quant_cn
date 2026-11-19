"""The daily opportunity list: RetailGauge, order flow, earnings, valuation, fit (plan 21 ph4)."""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

import pandas as pd

from quant_cn.calculation.company_cycle_panel import CompanyCyclePanel
from quant_cn.core.exceptions import LakeError
from quant_cn.core.opportunity_settings import OpportunitySettings
from quant_cn.core.positions_book import PositionsBook
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.lake.dated_table_store import DatedTableStore
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.statement_version_reader import StatementVersionReader
from quant_cn.lake.valuation_history_reader import ValuationHistoryReader
from quant_cn.portfolio.opportunity_rules import HIT_COLUMNS, LIST_COLUMNS, OpportunityRules
from quant_cn.portfolio.style_fit_checker import StyleFitChecker
from quant_cn.risk.base_risk_model import BaseRiskModel

logger = logging.getLogger(__name__)

TABLE = "opportunity_list"
GAUGE_VIEW = "derived.retail_gauge"
SIGNAL_COLUMNS = [
    "lg_weeks_pos_4w", "lg_net_4w", "sm_weeks_neg_4w", "sm_net_4w", "margin_chg_60d",
    "winner_rate", "cost_lo_gap", "cost_hi_gap",
]  # fmt: skip
OUTPUT_COLUMNS = [
    "as_of", "ts_code", "name", *LIST_COLUMNS, "pct", "exp_change", "lo_streak", "gauge_as_of",
    "circ_mv", *SIGNAL_COLUMNS, "period", "np_yoy", "np_qoq", "val_value", "val_median",
    "fit_styles", "fit_delta", *HIT_COLUMNS,
]  # fmt: skip
_SESSION = "SELECT max(trade_date) FROM curated.daily_basic WHERE trade_date <= ?"
_UNIVERSE = """
SELECT b.ts_code, s.name, b.circ_mv / 1e4 AS circ_mv
FROM curated.daily_basic b LEFT JOIN curated.stock_basic s USING (ts_code)
WHERE b.trade_date = ? AND b.circ_mv >= ?
"""
_GAUGE = f"""
SELECT ts_code, arg_max(pct, as_of) AS pct, arg_max(exp_change, as_of) AS exp_change,
       arg_max(avoid, as_of) AS avoid, arg_max(retail_leaving, as_of) AS retail_leaving,
       arg_max(lo_streak, as_of) AS lo_streak, max(as_of) AS gauge_as_of
FROM {GAUGE_VIEW} WHERE as_of <= ? AND as_of >= ? GROUP BY 1
"""
_RISK_SESSION = "SELECT max(trade_date) FROM derived.risk_specific_risk WHERE trade_date <= ?"
_CLOSES = (
    "SELECT ts_code, close FROM curated.daily WHERE trade_date = ? AND list_contains(?, ts_code)"
)
_WAN = 1e4  # circ_mv is in 万元; settings in 亿


class OpportunityScreen:
    """
    Purpose:
        Build the daily opportunity list (plan 21 ph4). Universe: stocks with free-float cap
        >= min_circ_mv on the session, ST names dropped (exclude_st), the user's holdings
        dropped (their gauge flips are flagged separately), and only names with a RetailGauge
        reading within gauge_max_age_days (the latest one: a quarter's first 14 sessions
        have none). When `retail_leaving` is a required rule only leaving names are scored.
        Each candidate gets its signal row (ChipStructureReader: large / small order weekly
        streaks, margin trend, winner rate, cost band), the latest quarter's profit YoY / QoQ
        (CompanyCyclePanel on the versions known on the session), its valuation against its
        own `valuation_years` median (ValuationHistoryReader) and the factor fit against the
        book (StyleFitChecker on the latest risk-model snapshot; NaN without one). The rules
        and the ranking are OpportunityRules'; `is_new` compares with the last stored list.

    Contract:
        Input:
            settings: OpportunitySettings; query: LakeQuery (curated daily_basic, stock_basic,
            daily; derived retail_gauge, risk_specific_risk); chips: ChipStructureReader;
            valuations: ValuationHistoryReader; versions: StatementVersionReader;
            cycle: CompanyCyclePanel; model: BaseRiskModel; rules: OpportunityRules;
            fit: StyleFitChecker; tables: DatedTableStore
        Output:
            instance; `build(as_of, book) -> DataFrame` with OUTPUT_COLUMNS (listed names
            first, then near-misses; empty with those columns when nothing qualifies);
            `write(frame) -> list[Path]` into derived/opportunity_list (by as_of);
            `read_previous(session)` -> the last stored list before the session
        Raises:
            LakeError  -- no daily_basic session on or before as_of, RetailGauge table
                          missing, a query failure

    Used by:
        cli.GaugeCommands  -- `opportunity-list`

    Test cases:
        TC-OSC-001  fixture lake: the leaving, inflowing, improving, cheap name that fits is
                    listed; an avoid name and a held name never appear; a name missing one
                    rule is a near-miss naming it; is_new against a stored previous list
        TC-OSC-002  no daily_basic session or no retail_gauge view -> LakeError
    """

    def __init__(
        self,
        settings: OpportunitySettings,
        query: LakeQuery,
        chips: ChipStructureReader,
        valuations: ValuationHistoryReader,
        versions: StatementVersionReader,
        cycle: CompanyCyclePanel,
        model: BaseRiskModel,
        rules: OpportunityRules,
        fit: StyleFitChecker,
        tables: DatedTableStore,
    ) -> None:
        self._settings = settings
        self._query = query
        self._chips = chips
        self._valuations = valuations
        self._versions = versions
        self._cycle = cycle
        self._model = model
        self._rules = rules
        self._fit = fit
        self._tables = tables

    def build(self, as_of: str, book: PositionsBook) -> pd.DataFrame:
        """
        Purpose:
            The opportunity list on the last daily_basic session on or before `as_of`.

        Contract:
            Input:
                as_of: str YYYYMMDD; book: PositionsBook (held codes are excluded; weights
                for the fit rule)
            Output:
                DataFrame  -- OUTPUT_COLUMNS, as_of = the session
            Raises:
                LakeError  -- see the class contract
        """
        session = self._query.sql(_SESSION, [as_of]).iloc[0, 0]
        if not isinstance(session, str):
            raise LakeError(f"no daily_basic session on or before {as_of}")
        pool = self._read_pool(session, {p.code for p in book.positions})
        codes = list(pool.index)
        if not codes:
            return pd.DataFrame(columns=OUTPUT_COLUMNS)
        metrics = pool.join(self._chips.read(codes, session)[SIGNAL_COLUMNS])
        metrics = metrics.join(self._read_cycle(codes, session))
        metrics = metrics.join(self._read_valuation(codes, session))
        metrics = metrics.join(self._compute_fit(codes, session, book))
        previous = set(self.read_previous(session)["ts_code"])
        listed = self._rules.build_list(metrics, previous)
        out = listed.reset_index().assign(as_of=session)
        logger.info("opportunity list %s: %d of %d candidates", session, len(out), len(codes))
        return out.reindex(columns=OUTPUT_COLUMNS)

    def write(self, frame: pd.DataFrame) -> list[Path]:
        """
        Purpose:
            Store the list in derived/opportunity_list, replacing its session.

        Contract:
            Input:
                frame: DataFrame  -- `build` output
            Output:
                list[Path]  -- year files written (none for an empty list)
            Raises:
                LakeError  -- write failure
        """
        if frame.empty:
            return []
        return self._tables.write(TABLE, frame, "as_of")

    def _read_pool(self, session: str, held: set[str]) -> pd.DataFrame:
        if not self._query.has_view(GAUGE_VIEW):
            raise LakeError(f"{GAUGE_VIEW} missing: run retail-gauge")
        floor = self._settings.min_circ_mv * _WAN
        universe = self._query.sql(_UNIVERSE, [session, floor]).set_index("ts_code")
        if self._settings.exclude_st:
            universe = universe[~universe["name"].fillna("").str.contains("ST")]
        day = dt.datetime.strptime(session, "%Y%m%d").date()
        oldest = (day - dt.timedelta(days=self._settings.gauge_max_age_days)).strftime("%Y%m%d")
        gauge = self._query.sql(_GAUGE, [session, oldest]).set_index("ts_code")
        pool = universe.join(gauge, how="inner")
        pool = pool[~pool.index.isin(list(held))]
        pool["avoid"] = pool["avoid"].fillna(False).astype(bool)
        pool["retail_leaving"] = pool["retail_leaving"].fillna(False).astype(bool)
        if "retail_leaving" in self._settings.required:
            pool = pool[pool["retail_leaving"]]
        return pool[~pool["avoid"]].sort_index()

    def _read_cycle(self, codes: list[str], session: str) -> pd.DataFrame:
        start = self._cycle.compute_start(session)
        versions = self._versions.read_versions(self._cycle.list_fields(), session, start)
        panel = self._cycle.build(versions[versions["ts_code"].isin(codes)], session)
        return panel.set_index("ts_code")[["period", "np_yoy", "np_qoq"]]

    def _read_valuation(self, codes: list[str], session: str) -> pd.DataFrame:
        years = self._settings.valuation_years
        start = f"{int(session[:4]) - years}{session[4:]}"
        frame = self._valuations.read(codes, self._settings.valuation_field, start, session)
        return frame.rename(columns={"value": "val_value", "median": "val_median"})[
            ["val_value", "val_median"]
        ]

    def _compute_fit(self, codes: list[str], session: str, book: PositionsBook) -> pd.DataFrame:
        risk_session = self._query.sql(_RISK_SESSION, [session]).iloc[0, 0]
        if not isinstance(risk_session, str):
            logger.warning("no risk-model session on or before %s: fit rule unknown", session)
            return pd.DataFrame(index=pd.Index(codes, name="ts_code"), columns=["fit"])
        snap = self._model.load_snapshot(risk_session)
        return self._fit.compute(snap, self._read_weights(book, session), codes)

    def _read_weights(self, book: PositionsBook, session: str) -> pd.Series:
        if not book.positions:
            return pd.Series(dtype=float)
        shares = pd.Series({p.code: p.shares for p in book.positions}, dtype=float)
        closes = self._query.sql(_CLOSES, [session, list(shares.index)])
        value = shares * closes.set_index("ts_code")["close"].reindex(shares.index)
        return (value / (float(value.sum()) + book.cash)).dropna()

    def read_previous(self, session: str) -> pd.DataFrame:
        """
        Purpose:
            The last stored list before `session` (listed and near rows).

        Contract:
            Input:
                session: str YYYYMMDD
            Output:
                DataFrame  -- stored OUTPUT_COLUMNS rows of the latest earlier as_of; empty
                              when none
            Raises:
                LakeError  -- unreadable table
        """
        years = [session[:4], str(int(session[:4]) - 1)]
        stored = self._tables.read(TABLE, years)
        if stored.empty:
            return pd.DataFrame(columns=OUTPUT_COLUMNS)
        earlier = stored[stored["as_of"] < session]
        if earlier.empty:
            return pd.DataFrame(columns=OUTPUT_COLUMNS)
        last: pd.DataFrame = earlier[earlier["as_of"] == earlier["as_of"].max()]
        return last.reset_index(drop=True)
