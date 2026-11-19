"""Margin-trading signals per stock as known on a date, for conditions (plan 15 ph7m)."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from quant_cn.lake.lake_query import LakeQuery

COLUMNS = ["rz_chg_20d", "rz_net_20d_pct", "rq_pct_float", "rq_max_ratio"]
WINDOW = 20  # sessions
_ROWS = """
SELECT m.ts_code, m.trade_date, m.rzye, m.rzmre, m.rzche, m.rqye, b.circ_mv
FROM curated.margin_detail m LEFT JOIN curated.daily_basic b USING (ts_code, trade_date)
WHERE list_contains(?, m.ts_code) AND m.trade_date > ? AND m.trade_date < ?
ORDER BY m.ts_code, m.trade_date
"""


class MarginSignalReader:
    """
    Purpose:
        Per stock, from the margin data published before `as_of` (exchanges publish day t's
        figures after the close, so they are used from t+1): financing balance change over 20
        sessions, net financing buying over 20 sessions as % of float market cap, short balance
        as % of float market cap, and the short balance over its maximum of the last year.
        Research 20261113_margin_signals: rising financing and a high short balance both carry a
        contrarian IC of -0.03 to -0.06 (weaker since 2024).

    Contract:
        Input:
            query: LakeQuery  -- curated.margin_detail, curated.daily_basic
        Output:
            instance; `read(codes, as_of)` -> DataFrame (index ts_code, COLUMNS); `compute(rows)`
        Raises:
            (none at construction)

    Used by:
        portfolio.ConditionEvaluator  -- kind `margin` metrics
        cli.AppServiceBuilder         -- wires it

    Test cases:
        TC-MSR-001  20-day change, net buying % of float, short % of float and max ratio from
                    hand rows; the as_of day itself is not used
    """

    def __init__(self, query: LakeQuery) -> None:
        self._query = query

    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        """
        Purpose:
            Signals of `codes` from rows dated before `as_of`.

        Contract:
            Input:
                codes: list[str]; as_of: str (YYYYMMDD)
            Output:
                DataFrame  -- index = codes, COLUMNS; NaN when a stock has no margin data
            Raises:
                LakeError  -- the query fails
        """
        start = (dt.datetime.strptime(as_of, "%Y%m%d") - dt.timedelta(days=380)).strftime("%Y%m%d")
        rows = self._query.sql(_ROWS, [codes, start, as_of])
        return self.compute(rows).reindex(pd.Index(codes, name="ts_code"))

    @staticmethod
    def compute(rows: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Signals from margin rows (one or more stocks, sorted by date).

        Contract:
            Input:
                rows: DataFrame  -- ts_code, trade_date, rzye, rzmre, rzche, rqye, circ_mv (万元)
            Output:
                DataFrame  -- index ts_code, COLUMNS (fractions; % columns in percent)
            Raises:
                (none)
        """
        out = {}
        for code, group in rows.groupby("ts_code"):
            s = group.sort_values("trade_date")
            last = s.iloc[-1]
            mv = float(last["circ_mv"]) * 1e4 if pd.notna(last["circ_mv"]) else float("nan")
            tail = s.iloc[-WINDOW:]
            prev = float(s["rzye"].iloc[-WINDOW - 1]) if len(s) > WINDOW else float("nan")
            rq_max = float(s["rqye"].max()) if s["rqye"].notna().any() else float("nan")
            out[code] = {
                "rz_chg_20d": float(last["rzye"]) / prev - 1 if prev else float("nan"),
                "rz_net_20d_pct": float((tail["rzmre"] - tail["rzche"]).sum()) / mv * 100,
                "rq_pct_float": float(last["rqye"] or 0) / mv * 100,
                "rq_max_ratio": float(last["rqye"] or 0) / rq_max if rq_max else float("nan"),
            }
        return pd.DataFrame.from_dict(out, orient="index", columns=COLUMNS).rename_axis("ts_code")
