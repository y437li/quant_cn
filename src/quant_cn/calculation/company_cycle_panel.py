"""Point-in-time company cycle panel: quarters, TTM and the 10-year norm (plan 16 ph1, D-121)."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.discovery_settings import DiscoverySettings

logger = logging.getLogger(__name__)

FLOWS = ("revenue", "oper_cost", "n_income_attr_p", "profit_dedt")
STOCKS = ("total_hldr_eqy_exc_min_int", "total_assets")
QUARTER_COLUMNS = [
    "rev_q", "gm_q", "np_q", "np_dedt_q", "rev_yoy", "np_yoy", "np_qoq", "dgm_yoy", "dgm_qoq",
]  # fmt: skip
COLUMNS = [
    "ts_code", "period", *QUARTER_COLUMNS, "rev_ttm", "np_ttm", "np_dedt_ttm", "nm_ttm",
    "roe_ttm", "turnover_ttm", "np_med", "nm_max", "n_years", "ttm_vs_med", "margin_peak",
]  # fmt: skip
VERSION_COLUMNS = ["ts_code", "end_date", "field", "value"]
QUARTER_HISTORY_COLUMNS = ["ts_code", "period", "rev_q", "gm_q", "np_q", "np_dedt_q"]


class CompanyCyclePanel:
    """
    Purpose:
        For every company, as known on a date, place its latest quarter in its own cycle:
        single-quarter and TTM figures with YoY and QoQ changes, deducted profit, and the
        10-year norm (median annual profit, highest annual net margin) (plan 16 ph1, D-121).
        Pure: the statement versions known on as_of come in as a frame
        (lake.StatementVersionReader.read_versions with list_fields() and compute_start(as_of)).

    Contract:
        Input:
            codec:    DateCodec
            settings: DiscoverySettings  -- history_years, min_years
        Output:
            instance; `list_quarters(versions, as_of, count)` -> single-quarter history
            (QUARTER_HISTORY_COLUMNS); `build(versions, as_of) -> pd.DataFrame` with COLUMNS,
            one row per company whose latest period in `versions` has a revenue figure:
                period      YYYYMMDD of the latest quarter-end visible on as_of
                *_q         single quarter (YTD minus the previous YTD of the same year; Q1 = YTD)
                rev_yoy, np_yoy  single quarter vs the same quarter a year earlier (np: NaN when
                            the base is <= 0); np_qoq vs the previous quarter (NaN when base <= 0)
                dgm_yoy, dgm_qoq  gross-margin change in shares (0.05 = 5pp)
                *_ttm       YTD + prior FY - prior same-period YTD; roe / turnover use the
                            balance sheet at `period`
                np_med, nm_max  median annual profit and max annual net margin over the
                            history_years full years before `period`'s year; NaN below min_years
                ttm_vs_med  np_ttm / np_med (NaN when np_med <= 0)
                margin_peak nm_ttm >= nm_max (False when either is NaN)
            amounts in CNY; shares as fractions; `versions` must hold only what was known on
            as_of (the reader guarantees it), so the panel is point in time
        Raises:
            ValueError  -- as_of malformed or versions without VERSION_COLUMNS

    Used by:
        (none yet)  -- pipeline.DiscoveryStep (plan 16 ph6), portfolio.IdeaScreener (ph3)

    Test cases:
        TC-CCP-001  single quarter: Q3 = 9M - H1, Q1 = YTD
        TC-CCP-002  YoY and QoQ of the single quarter; NaN on a non-positive base
        TC-CCP-003  TTM = YTD + prior FY - prior same period; roe / turnover from the balance sheet
        TC-CCP-004  with versions read on an earlier as_of the earlier period / restatement is used
        TC-CCP-005  10-year median profit, max margin, ttm_vs_med and margin_peak
        TC-CCP-006  deducted profit: np_dedt_q and np_dedt_ttm from profit_dedt
        TC-CCP-007  fewer than min_years annual reports -> cycle columns NaN, margin_peak False
        TC-CCP-008  no visible statements -> empty frame with COLUMNS
        TC-CCP-009  malformed as_of or missing version columns raise ValueError;
                    list_fields and compute_start give the reader's arguments
        TC-CCP-010  list_quarters: last `count` single quarters per company, oldest first
    """

    def __init__(self, codec: DateCodec, settings: DiscoverySettings) -> None:
        self._codec = codec
        self._settings = settings

    @staticmethod
    def list_fields() -> list[str]:
        """
        Purpose:
            The fundamentals_long fields the panel needs (flows YTD, then balance-sheet stocks).

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- FLOWS + STOCKS
            Raises:
                (none)
        """
        return [*FLOWS, *STOCKS]

    def compute_start(self, as_of: str) -> str:
        """
        Purpose:
            The earliest period end the panel needs for `as_of` (history_years + 1 years back).

        Contract:
            Input:
                as_of: str  -- YYYYMMDD
            Output:
                str  -- YYYY0101
            Raises:
                ValueError  -- as_of malformed
        """
        self._codec.validate(as_of)
        return f"{int(as_of[:4]) - self._settings.history_years - 1}0101"

    def build(self, versions: pd.DataFrame, as_of: str) -> pd.DataFrame:
        """
        Purpose:
            The cycle panel as known on `as_of` (see the class contract for the columns).

        Contract:
            Input:
                versions: DataFrame  -- VERSION_COLUMNS, statement values known on as_of
                as_of:    str        -- YYYYMMDD
            Output:
                pd.DataFrame  -- COLUMNS, sorted by ts_code
            Raises:
                ValueError  -- see the class contract
        """
        wide = self._build_wide(versions, as_of)
        if wide.empty:
            return pd.DataFrame(columns=COLUMNS)
        groups = wide.groupby(level=0, sort=True)
        rows = [self._build_row(str(code), frame) for code, frame in groups]
        out = pd.DataFrame([r for r in rows if r is not None], columns=COLUMNS)
        logger.info("cycle panel %s: %d companies", as_of, len(out))
        return out.reset_index(drop=True)

    def list_quarters(self, versions: pd.DataFrame, as_of: str, count: int = 12) -> pd.DataFrame:
        """
        Purpose:
            Single-quarter history per company (same YTD -> quarter rule as build).

        Contract:
            Input:
                versions: DataFrame  -- VERSION_COLUMNS, statement values known on as_of
                as_of:    str        -- YYYYMMDD
                count:    int        -- >= 1, quarters kept per company (the latest ones)
            Output:
                pd.DataFrame  -- QUARTER_HISTORY_COLUMNS, sorted by (ts_code, period); amounts
                                 in CNY, gm_q a share; a quarter needs the previous YTD of its year
            Raises:
                ValueError  -- as build, or count < 1
        """
        if count < 1:
            raise ValueError(f"count must be >= 1: {count}")
        wide = self._build_wide(versions, as_of)
        rows: list[dict[str, object]] = []
        for code, frame in wide.groupby(level=0, sort=True):
            ytd = frame.droplevel(0).sort_index()
            quarters = self._compute_quarters(ytd[ytd["revenue"].notna()])
            for period in sorted(quarters)[-count:]:
                q = quarters[period]
                rows.append(
                    {"ts_code": str(code), "period": period, "rev_q": float(q["revenue"]),
                     "gm_q": self._compute_gm(q), "np_q": float(q["n_income_attr_p"]),
                     "np_dedt_q": float(q["profit_dedt"])}
                )  # fmt: skip
        return pd.DataFrame(rows, columns=QUARTER_HISTORY_COLUMNS)

    def _build_wide(self, versions: pd.DataFrame, as_of: str) -> pd.DataFrame:
        self._codec.validate(as_of)
        missing = set(VERSION_COLUMNS) - set(versions.columns)
        if missing:
            raise ValueError(f"versions lack columns {sorted(missing)}")
        long = versions[versions["field"].isin(self.list_fields())]
        if long.empty:
            return long
        return long.pivot_table(
            index=["ts_code", "end_date"], columns="field", values="value", aggfunc="first"
        ).reindex(columns=[*FLOWS, *STOCKS])

    def _build_row(self, code: str, frame: pd.DataFrame) -> dict[str, object] | None:
        ytd = frame.droplevel(0).sort_index()
        ytd = ytd[ytd["revenue"].notna()]
        if ytd.empty:
            return None
        period = str(ytd.index[-1])
        q = self._compute_quarters(ytd)
        cur = q.get(period)
        prev_q = q.get(self._compute_period(period, 0, 1))
        prev_y = q.get(self._compute_period(period, 1, 0))
        ttm = self._compute_ttm(ytd, period)
        cyc = self._compute_norm(ytd, period)
        np_ttm, rev_ttm = float(ttm["n_income_attr_p"]), float(ttm["revenue"])
        nm_ttm = self._compute_ratio(np_ttm, rev_ttm)
        peak = bool(np.isfinite(nm_ttm) and np.isfinite(cyc["nm_max"]) and nm_ttm >= cyc["nm_max"])
        row: dict[str, object] = {"ts_code": code, "period": period}
        row |= self._build_quarter(cur, prev_q, prev_y)
        row |= {
            "rev_ttm": rev_ttm,
            "np_ttm": np_ttm,
            "np_dedt_ttm": float(ttm["profit_dedt"]),
            "nm_ttm": nm_ttm,
            "roe_ttm": self._compute_ratio(
                np_ttm, float(self._get_row(ytd, period, STOCKS)[STOCKS[0]])
            ),
            "turnover_ttm": self._compute_ratio(
                rev_ttm, float(self._get_row(ytd, period, STOCKS)[STOCKS[1]])
            ),
            **cyc,
            "ttm_vs_med": self._compute_ratio(np_ttm, cyc["np_med"], positive=True),
            "margin_peak": peak,
        }
        return row

    def _build_quarter(
        self, cur: pd.Series | None, prev_q: pd.Series | None, prev_y: pd.Series | None
    ) -> dict[str, float]:
        nan = float("nan")
        if cur is None:
            return dict.fromkeys(QUARTER_COLUMNS, nan)
        gm = self._compute_gm(cur)
        return {
            "rev_q": float(cur["revenue"]),
            "gm_q": gm,
            "np_q": float(cur["n_income_attr_p"]),
            "np_dedt_q": float(cur["profit_dedt"]),
            "rev_yoy": self._compute_growth(cur, prev_y, "revenue"),
            "np_yoy": self._compute_growth(cur, prev_y, "n_income_attr_p"),
            "np_qoq": self._compute_growth(cur, prev_q, "n_income_attr_p"),
            "dgm_yoy": gm - self._compute_gm(prev_y) if prev_y is not None else nan,
            "dgm_qoq": gm - self._compute_gm(prev_q) if prev_q is not None else nan,
        }

    @staticmethod
    def _compute_quarters(ytd: pd.DataFrame) -> dict[str, pd.Series]:
        out: dict[str, pd.Series] = {}
        for key, values in ytd[list(FLOWS)].iterrows():
            end = str(key)
            if end[4:] == "0331":
                out[end] = values
                continue
            before = {"0630": "0331", "0930": "0630", "1231": "0930"}.get(end[4:])
            prior = f"{end[:4]}{before}"
            if before and prior in ytd.index:
                out[end] = values - CompanyCyclePanel._get_row(ytd, prior, FLOWS)
        return out

    @staticmethod
    def _compute_ttm(ytd: pd.DataFrame, period: str) -> pd.Series:
        cur = CompanyCyclePanel._get_row(ytd, period, FLOWS)
        if period[4:] == "1231":
            return cur
        fy, same = f"{int(period[:4]) - 1}1231", f"{int(period[:4]) - 1}{period[4:]}"
        if fy not in ytd.index or same not in ytd.index:
            return pd.Series(np.nan, index=list(FLOWS))
        fy_row = CompanyCyclePanel._get_row(ytd, fy, FLOWS)
        return cur + fy_row - CompanyCyclePanel._get_row(ytd, same, FLOWS)

    def _compute_norm(self, ytd: pd.DataFrame, period: str) -> dict[str, float]:
        last = int(period[:4]) - 1
        years = [f"{y}1231" for y in range(last - self._settings.history_years + 1, last + 1)]
        ann = ytd.reindex(years)[["revenue", "n_income_attr_p"]].dropna()
        ann = ann[ann["revenue"] > 0]
        if len(ann) < self._settings.min_years:
            return {"np_med": float("nan"), "nm_max": float("nan"), "n_years": float(len(ann))}
        margin = ann["n_income_attr_p"] / ann["revenue"]
        return {
            "np_med": float(ann["n_income_attr_p"].median()),
            "nm_max": float(margin.max()),
            "n_years": float(len(ann)),
        }

    @staticmethod
    def _get_row(ytd: pd.DataFrame, period: str, fields: tuple[str, ...]) -> pd.Series:
        values = ytd.loc[[period], list(fields)].to_numpy(dtype=float)[0]
        return pd.Series(values, index=list(fields))

    @staticmethod
    def _compute_period(period: str, years: int, quarters: int) -> str:
        ends = ["0331", "0630", "0930", "1231"]
        index = int(period[:4]) * 4 + ends.index(period[4:]) - years * 4 - quarters
        return f"{index // 4}{ends[index % 4]}"

    @classmethod
    def _compute_gm(cls, q: pd.Series) -> float:
        return 1.0 - cls._compute_ratio(float(q["oper_cost"]), float(q["revenue"]), positive=True)

    @classmethod
    def _compute_growth(cls, cur: pd.Series, base: pd.Series | None, field: str) -> float:
        if base is None:
            return float("nan")
        return cls._compute_ratio(float(cur[field]), float(base[field]), positive=True) - 1.0

    @staticmethod
    def _compute_ratio(a: float, b: float, positive: bool = False) -> float:
        if not (np.isfinite(a) and np.isfinite(b)) or b == 0 or (positive and b <= 0):
            return float("nan")
        return a / b
