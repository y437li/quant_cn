"""Statement and manual-series signals per stock as known on a date (plan 15 ph7f conditions)."""

from __future__ import annotations

import datetime as dt
import math

import pandas as pd

from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.statement_version_reader import StatementVersionReader

COLUMNS = ["period", "gm_q", "dedt_yoy_q", "ocf_to_np"]
FIELDS = ["revenue", "oper_cost", "profit_dedt", "n_cashflow_act_ttm", "n_income_attr_p_ttm"]
_SERIES = """
SELECT series, arg_max(value, date) AS value FROM curated.manual_series
WHERE list_contains(?, series) AND published <= ? GROUP BY 1
"""


class FundamentalSignalReader:
    """
    Purpose:
        Read statement signals of a set of stocks as known on `as_of` (latest announced
        version, D-092): single-quarter gross margin and deducted-profit YoY of the latest
        reported quarter, and TTM operating cash flow over TTM net profit. Also the latest
        published value of manual series (plan 20) for `series` conditions.

    Contract:
        Input:
            versions: StatementVersionReader  -- derived.fundamentals_long versions
            query:    LakeQuery               -- curated.manual_series
        Output:
            instance; `read(codes, as_of) -> DataFrame[COLUMNS]` indexed by ts_code;
            `read_series(ids, as_of) -> dict[str, float]` keyed "series:<id>"
        Raises:
            (none at construction)

    Used by:
        portfolio.ConditionEvaluator  -- statement and series metrics
        cli.AppServiceBuilder  -- wires it

    Test cases:
        TC-FSR-001  single-quarter GM and deducted-profit YoY from YTD versions (Q3 - H1)
        TC-FSR-002  Q1 is its own single quarter; a loss base gives YoY on |base|; no data -> NaN
        TC-FSR-003  ocf_to_np from TTM fields; series value is the latest published by as_of
    """

    def __init__(self, versions: StatementVersionReader, query: LakeQuery) -> None:
        self._versions = versions
        self._query = query

    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        """
        Purpose:
            Statement signals for `codes` on `as_of`.

        Contract:
            Input:
                codes: list[str]  -- ts_codes
                as_of: str        -- YYYYMMDD
            Output:
                DataFrame  -- index = codes, columns = COLUMNS; period = latest reported
                              end_date; NaN when unknown
            Raises:
                LakeError  -- view missing or query failure
        """
        out = pd.DataFrame(index=pd.Index(codes, name="ts_code"), columns=COLUMNS, dtype=object)
        if not codes:
            return out
        start = (dt.datetime.strptime(as_of, "%Y%m%d") - dt.timedelta(days=760)).strftime("%Y%m%d")
        raw = self._versions.read_versions(FIELDS, as_of, start)
        raw = raw[raw["ts_code"].isin(codes)]
        wide = raw.pivot_table(index=["ts_code", "end_date"], columns="field", values="value")
        rows = {
            code: self._compute_one(pd.DataFrame(wide.xs(code, level=0)).sort_index())
            for code in codes
            if code in wide.index.get_level_values(0)
        }
        found = pd.DataFrame.from_dict(rows, orient="index", columns=COLUMNS)
        return found.reindex(out.index)

    def read_series(self, ids: list[str], as_of: str) -> dict[str, float]:
        """
        Purpose:
            Latest published value of each manual series by `as_of`.

        Contract:
            Input:
                ids:   list[str]  -- series ids
                as_of: str        -- YYYYMMDD; only rows published on or before it
            Output:
                dict[str, float]  -- "series:<id>" -> value; ids without data are left out
            Raises:
                LakeError  -- query failure
        """
        if not ids or not self._query.has_view("curated.manual_series"):
            return {}
        frame = self._query.sql(_SERIES, [ids, as_of])
        return {
            f"series:{s}": float(v) for s, v in zip(frame["series"], frame["value"], strict=True)
        }

    def _compute_one(self, frame: pd.DataFrame) -> list[object]:
        revenue = frame.get("revenue", pd.Series(dtype=float)).dropna()
        if revenue.empty:
            return [None, float("nan"), float("nan"), float("nan")]
        period = str(revenue.index[-1])
        rev = self._get_quarter(frame, "revenue", period)
        cost = self._get_quarter(frame, "oper_cost", period)
        gm = (rev - cost) / rev if self._is_number(rev) and rev != 0 else float("nan")
        now = self._get_quarter(frame, "profit_dedt", period)
        base = self._get_quarter(frame, "profit_dedt", str(int(period[:4]) - 1) + period[4:])
        yoy = (now - base) / abs(base) if self._is_number(base) and base != 0 else float("nan")
        ocf = self._get_value(frame, "n_cashflow_act_ttm", period)
        npr = self._get_value(frame, "n_income_attr_p_ttm", period)
        ratio = ocf / npr if self._is_number(npr) and npr > 0 else float("nan")
        return [period, gm, yoy, ratio]

    @staticmethod
    def _get_value(frame: pd.DataFrame, field: str, period: str) -> float:
        if field not in frame.columns or period not in frame.index:
            return float("nan")
        return float(pd.to_numeric(frame.at[period, field]))

    @staticmethod
    def _is_number(value: float) -> bool:
        return not math.isnan(value)

    def _get_quarter(self, frame: pd.DataFrame, field: str, period: str) -> float:
        ytd = self._get_value(frame, field, period)
        if period.endswith("0331"):
            return ytd
        prior = {"0630": "0331", "0930": "0630", "1231": "0930"}[period[4:]]
        return ytd - self._get_value(frame, field, period[:4] + prior)
