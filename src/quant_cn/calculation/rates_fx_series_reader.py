"""Dated series of the rates and RMB monitor lines, read from the lake (plan 34, D-171)."""

from __future__ import annotations

import logging

import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.core.rates_fx_monitor_settings import RatesFxLine, RatesFxMonitorSettings
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

_CURVE = """
SELECT trade_date, {field} AS v FROM curated.cn_bond_yield
WHERE curve_name = ? AND trade_date >= ? ORDER BY trade_date
"""
_US = "SELECT trade_date, {field} AS v FROM curated.us_treasury_yield WHERE trade_date >= ?"
_SHIBOR = 'SELECT date AS trade_date, "{field}" AS v FROM curated.shibor WHERE date >= ?'
_FX = """
SELECT trade_date, (bid_close + ask_close) / 2 AS v FROM curated.fx_daily
WHERE ts_code = ? AND trade_date >= ?
"""
_FIXING = "SELECT trade_date, {field} / 100 AS v FROM curated.cny_fixing WHERE trade_date >= ?"
_EP = """
WITH w AS (SELECT trade_date AS wd, con_code FROM curated.index_weight WHERE index_code = ?),
     wd AS (SELECT DISTINCT wd FROM w),
     d AS (SELECT ts_code, trade_date, total_mv, pe_ttm FROM curated.daily_basic
           WHERE trade_date >= ? AND total_mv > 0)
SELECT d.trade_date,
       100 * sum(CASE WHEN d.pe_ttm > 0 THEN d.total_mv / d.pe_ttm END) / sum(d.total_mv) AS v
FROM d ASOF JOIN wd ON d.trade_date >= wd.wd
JOIN w ON w.wd = wd.wd AND w.con_code = d.ts_code
GROUP BY d.trade_date
"""


class RatesFxSeriesReader:
    """
    Purpose:
        One dated series per configured line, from `start` on: 中债 curve points
        (cn_bond_yield), US Treasury yields, SHIBOR, FXCM mid closes (bid / ask average),
        the SAFE central parity (per 100 units in the file, per unit here), an index earnings
        yield (members of the latest index_weight date on or before each day; Σ total_mv /
        pe_ttm over Σ total_mv in percent, members with a loss or no pe_ttm count in the market
        value only), and combos of earlier lines: diff a - b, mul a * b, div a / b and gap
        a / b - 1, each on a's dates with b's last value on or before that date. A line whose
        table is missing or unreadable is returned empty, so the builder lists it as missing.

    Contract:
        Input:
            settings: RatesFxMonitorSettings
            query:    LakeQuery
        Output:
            instance; `read_series(start)` -> dict[str, pd.Series]
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands                 -- wires it
        calculation.RatesFxMonitorBuilder  -- its series

    Test cases:
        TC-RFR-001  curve, fixing (÷ 100) and fx (mid) lines read their tables from start on
        TC-RFR-002  combos: diff, mul, div and gap on a's dates with b carried forward
        TC-RFR-003  equity_ep: Σ mv / pe ÷ Σ mv of the members of the last weight date
        TC-RFR-004  an unreadable table gives an empty series, not an error
    """

    def __init__(self, settings: RatesFxMonitorSettings, query: LakeQuery) -> None:
        self._s = settings
        self._query = query

    def read_series(self, start: str) -> dict[str, pd.Series]:
        """
        Purpose:
            Every line's series from `start` (YYYYMMDD) on.

        Contract:
            Input:
                start: str  -- first date read
            Output:
                dict[str, pd.Series]  -- line key -> float values indexed by YYYYMMDD strings,
                                         ascending, NaN dropped; empty when no data
            Raises:
                (none)
        """
        out: dict[str, pd.Series] = {}
        for line in self._s.lines:
            if line.kind == "combo":
                out[line.key] = self._compute_combo(line, out)
            else:
                out[line.key] = self._read_line(line, start)
        return out

    def _read_line(self, line: RatesFxLine, start: str) -> pd.Series:
        sources: dict[str, tuple[str, list[object]]] = {
            "curve": (_CURVE.format(field=line.field), [line.curve, start]),
            "us": (_US.format(field=line.field), [start]),
            "shibor": (_SHIBOR.format(field=line.field), [start]),
            "fx": (_FX, [line.code, start]),
            "fixing": (_FIXING.format(field=line.field), [start]),
            "equity_ep": (_EP, [line.code, start]),
        }
        sql, params = sources[line.kind]
        try:
            frame = self._query.sql(sql, params)
        except LakeError as exc:
            logger.warning("rates-fx monitor: %s unreadable: %s", line.key, exc)
            return pd.Series(dtype=float)
        values = pd.to_numeric(frame["v"], errors="coerce")
        series = pd.Series(values.to_numpy(), index=frame["trade_date"].astype(str), dtype=float)
        return series[~series.index.duplicated(keep="last")].sort_index().dropna()

    @staticmethod
    def _compute_combo(line: RatesFxLine, done: dict[str, pd.Series]) -> pd.Series:
        a, b = done[str(line.a)], done[str(line.b)]
        if a.empty or b.empty:
            return pd.Series(dtype=float)
        b_on_a = b.reindex(b.index.union(a.index)).ffill().reindex(a.index)
        result = {"diff": a - b_on_a, "mul": a * b_on_a, "div": a / b_on_a,
                  "gap": a / b_on_a - 1}[str(line.op)]  # fmt: skip
        if line.op == "diff" and line.unit == "bp":
            result = result * 100
        return result.dropna()
