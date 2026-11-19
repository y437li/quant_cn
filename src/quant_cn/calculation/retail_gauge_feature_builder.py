"""The 83 RetailGauge v5 features per (as_of, ts_code), point in time (plan 21 ph2, D-142)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.calculation.holder_count_panel import HolderCountPanel
from quant_cn.calculation.retail_gauge_matrices import RetailGaugeMatrices
from quant_cn.core.exceptions import LakeError
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings
from quant_cn.lake.dated_table_store import DatedTableStore
from quant_cn.lake.lake_query import LakeQuery

TABLE = "retail_gauge_features"
KEY_COLUMNS = ["ts_code", "q", "as_of"]
_MATRIX_SQL = {
    "px": "SELECT * FROM (SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS v "
    "FROM curated.daily d JOIN curated.adj_factor a USING (ts_code, trade_date))",
    "tov": "SELECT ts_code, trade_date, turnover_rate_f AS v FROM curated.daily_basic",
    "cmv": "SELECT ts_code, trade_date, circ_mv AS v FROM curated.daily_basic",
    "lg": "SELECT ts_code, trade_date, buy_lg_amount - sell_lg_amount AS v FROM curated.moneyflow",
    "elg": "SELECT ts_code, trade_date, buy_elg_amount - sell_elg_amount AS v "
    "FROM curated.moneyflow",
    "sm": "SELECT ts_code, trade_date, buy_sm_amount - sell_sm_amount AS v FROM curated.moneyflow",
    "rz": "SELECT ts_code, trade_date, rzye AS v FROM curated.margin_detail",
}
_CHIP = """
SELECT c.ts_code, c.winner_rate, c.cost_15pct, c.cost_50pct, c.cost_85pct, c.weight_avg, d.close
FROM curated.cyq_perf c JOIN curated.daily d USING (ts_code, trade_date)
WHERE c.trade_date = (SELECT max(trade_date) FROM curated.cyq_perf WHERE trade_date <= ?)
"""
_QUARTER_DAYS = ("0331", "0630", "0930", "1231")
ALL_ANNOUNCED = "99991231"  # holder counts: every announcement; rows filter by as_of


class RetailGaugeFeatureBuilder:
    """
    Purpose:
        Build the 83 v5 features of the 散户温度计 RetailGauge for any as-of session (plan 21
        ph2, D-142): the quarter window runs from the previous quarter end a to as_of; the row
        belongs to quarter q (the first quarter end on or after as_of). Features:
        - path and order-size features over (a, as_of] and multi-scale features as of as_of
          (RetailGaugeMatrices);
        - chips from curated.cyq_perf at the last snapshot on or before as_of and on or before
          a: winner rate, concentration (cost 85% - 15%) / cost 50%, log close / cost 50%,
          their changes since a, and the log change of the average cost;
        - prev / prev2 holder changes announced by as_of (HolderCountPanel), quarter number;
        - `<f>_lag1` for every `settings.lagged` feature: its value on the row of quarter a
          (as of a), and dtov_prev = dtov_lag1 when dtov is lagged.
        Only data on or before as_of is read for a row; rows are stocks with a turnover in the
        window. Rows are written to derived/retail_gauge_features (one file per year of as_of,
        reruns replace their as_of rows).

    Contract:
        Input:
            settings: RetailGaugeSettings
            query:    LakeQuery      -- curated daily, adj_factor, daily_basic, moneyflow,
                                        margin_detail, cyq_perf, stk_holdernumber
            holders:  HolderCountPanel
            tables:   DatedTableStore  -- derived/retail_gauge_features
        Output:
            instance; `load(end)`; `build(as_ofs)` -> DataFrame KEY_COLUMNS + features (the
            83 FEATURES order); `build_quarter_ends(end)`; `list_quarter_ends(end)`;
            `write(frame)` -> list[Path]; `sessions`
        Raises:
            LakeError  -- a view missing or a query failure

    Used by:
        calculation.RetailGaugeNowcaster  -- training and daily rows
        cli.GaugeCommands  -- wires it, loads the lake

    Test cases:
        TC-RGF-001  build on a fixture lake: chip features and their changes since a equal
                    hand values; lag1 = the quarter-a row; q / as_of keys; a stock without a
                    turnover in the window has no row
        TC-RGF-002  a price, flow, chip or holder count dated after as_of changes nothing
        TC-RGF-003  write replaces the rows of a rewritten as_of and keeps the others
    """

    def __init__(
        self,
        settings: RetailGaugeSettings,
        query: LakeQuery,
        holders: HolderCountPanel,
        tables: DatedTableStore,
    ) -> None:
        self._s = settings
        self._query = query
        self._holders = holders
        self._tables = tables
        self._m: RetailGaugeMatrices | None = None
        self._end = ""
        self._lag_cache: dict[str, pd.DataFrame] = {}

    @property
    def sessions(self) -> pd.Index:
        """
        Purpose:
            Sessions of the loaded matrices.

        Contract:
            Input:
                (none)
            Output:
                Index  -- YYYYMMDD, ascending; empty before load
            Raises:
                (none)
        """
        return self._m.sessions if self._m is not None else pd.Index([], dtype=str)

    def load(self, end: str) -> None:
        """
        Purpose:
            Read the daily matrices from settings.start to end and every announced holder
            count (lags and labels are filtered by announcement date per row).

        Contract:
            Input:
                end: str  -- YYYYMMDD
            Output:
                None (state)
            Raises:
                LakeError  -- a view missing or a query failure
        """
        frames = {}
        for name, sql in _MATRIX_SQL.items():
            long = self._query.sql(f"{sql} WHERE trade_date BETWEEN ? AND ?", [self._s.start, end])
            long["ts_code"] = long["ts_code"].astype(str)
            long["trade_date"] = long["trade_date"].astype(str)
            frames[name] = long.pivot(index="trade_date", columns="ts_code", values="v").astype(
                float
            )
        self._m = RetailGaugeMatrices(self._s, frames)
        self._holders.load(ALL_ANNOUNCED)  # PIT per row: lags need ann <= as_of
        self._end = end
        self._lag_cache = {}

    def build(self, as_ofs: Sequence[str]) -> pd.DataFrame:
        """
        Purpose:
            Feature rows for the given as-of dates (each mapped to the last session on or
            before it). Loads the lake up to the latest as_of first when `load` has not
            covered it.

        Contract:
            Input:
                as_ofs: Sequence[str]  -- YYYYMMDD, after settings.first_quarter's next
                                          quarter start
            Output:
                DataFrame  -- KEY_COLUMNS + features, sorted by (as_of, ts_code)
            Raises:
                LakeError  -- a view missing or a query failure
        """
        if as_ofs and (self._m is None or max(as_ofs) > self._end):
            self.load(max(as_ofs))
        m = self._get_matrices()
        parts = []
        for day in as_ofs:
            as_of = str(m.sessions[m.sessions <= day][-1])
            q = self._get_quarter(day)
            a = HolderCountPanel.get_quarter_before(q, 1)
            part = self._compute_row(a, as_of, q)
            if not part.empty:
                parts.append(part)
        if not parts:
            return pd.DataFrame(columns=KEY_COLUMNS)
        frame = pd.concat(parts, ignore_index=True)
        frame = pd.concat([frame, self._holders.compute_lags(frame)], axis=1)
        frame["qtr"] = frame["q"].str[4:6].map({"03": 1, "06": 2, "09": 3, "12": 4}).astype(float)
        frame = self._add_lag1(frame)
        return frame.sort_values(["as_of", "ts_code"]).reset_index(drop=True)

    def build_quarter_ends(self, end: str) -> pd.DataFrame:
        """
        Purpose:
            Feature rows at every quarter end after settings.first_quarter up to end (the
            model's training and evaluation rows).

        Contract:
            Input:
                end: str  -- YYYYMMDD
            Output:
                DataFrame  -- as `build`
            Raises:
                LakeError  -- a view missing or a query failure
        """
        return self.build(self.list_quarter_ends(end))

    def list_quarter_ends(self, end: str) -> list[str]:
        """
        Purpose:
            Quarter ends after settings.first_quarter, on or before end.

        Contract:
            Input:
                end: str  -- YYYYMMDD
            Output:
                list[str]  -- ascending YYYYMMDD
            Raises:
                (none)
        """
        out: list[str] = []
        q = self._s.first_quarter
        while True:
            q = HolderCountPanel.get_quarter_before(q, -1)
            if q > end:
                return out
            out.append(q)

    def write(self, frame: pd.DataFrame) -> list[Path]:
        """
        Purpose:
            Store rows in derived/retail_gauge_features, replacing the rows of their as_of
            dates and keeping the rest of each year.

        Contract:
            Input:
                frame: DataFrame  -- a `build` result
            Output:
                list[Path]  -- year files written
            Raises:
                LakeError  -- write failed
        """
        return self._tables.write(TABLE, frame, "as_of")

    def _compute_row(self, a: str, as_of: str, q: str) -> pd.DataFrame:
        m = self._get_matrices()
        path = m.compute_path(a, as_of)
        if path.empty:
            return path
        f = pd.concat([path, m.compute_scale(as_of), self._compute_chip(a, as_of)], axis=1)
        f = f[path["tov"].notna()]
        f.index.name = "ts_code"
        f = f.reset_index()
        f.insert(1, "q", q)
        f.insert(2, "as_of", as_of)
        return f

    def _compute_chip(self, a: str, b: str) -> pd.DataFrame:
        cb, ca = self._read_chip(b), self._read_chip(a)
        c = pd.DataFrame(index=cb.index)
        c["win_b"] = cb["winner_rate"]
        c["conc_b"] = cb["conc"]
        c["pc50_b"] = np.log(cb["close"] / cb["cost_50pct"])
        c["dwin"] = cb["winner_rate"] - ca["winner_rate"]
        c["dconc"] = cb["conc"] - ca["conc"]
        c["dpc50"] = c["pc50_b"] - np.log(ca["close"] / ca["cost_50pct"])
        c["wavg_gap"] = np.log(cb["weight_avg"] / ca["weight_avg"])
        return c.replace([np.inf, -np.inf], np.nan)

    def _read_chip(self, day: str) -> pd.DataFrame:
        c = self._query.sql(_CHIP, [day])
        c["ts_code"] = c["ts_code"].astype(str)
        c = c.set_index("ts_code").astype(float)
        c["conc"] = (c["cost_85pct"] - c["cost_15pct"]) / c["cost_50pct"]
        return c

    def _add_lag1(self, frame: pd.DataFrame) -> pd.DataFrame:
        lagged = self._s.lagged
        prev = []
        for q in sorted(frame["q"].unique()):
            a = HolderCountPanel.get_quarter_before(q, 1)
            cols = ["ts_code", *lagged]
            if a not in self._lag_cache:
                # the first quarter end opens the first window and has no row of its own
                first = a <= self._s.first_quarter
                row = (
                    pd.DataFrame()
                    if first
                    else self._compute_row(HolderCountPanel.get_quarter_before(a, 1), a, a)
                )
                self._lag_cache[a] = row[cols] if not row.empty else pd.DataFrame(columns=cols)
            part = self._lag_cache[a].copy()
            part["q"] = q
            prev.append(part)
        lags = pd.concat(prev, ignore_index=True).rename(columns={c: f"{c}_lag1" for c in lagged})
        frame = frame.merge(lags, on=["ts_code", "q"], how="left")
        if "dtov_lag1" in frame.columns:
            frame["dtov_prev"] = frame["dtov_lag1"]  # v3 name kept: the model has both columns
        return frame

    def _get_quarter(self, day: str) -> str:
        year = day[:4]
        return next(f"{year}{d}" for d in _QUARTER_DAYS if f"{year}{d}" >= day)

    def _get_matrices(self) -> RetailGaugeMatrices:
        if self._m is None:
            raise LakeError("RetailGaugeFeatureBuilder: no data loaded")
        return self._m
