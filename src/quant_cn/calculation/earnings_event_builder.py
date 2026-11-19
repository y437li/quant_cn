"""Earnings events: first disclosure, surprise (SUE) and excess returns around it (plan 35)."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.sector_earnings_signal_settings import SectorEarningsSignalSettings
from quant_cn.lake.lake_query import LakeQuery

EVENT_COLUMNS = ("ts_code", "end_date", "first_ann", "day0", "sue", "dec", "pre", "react", "post")
QUARTERS = 4
DECILES = 10
POST_SESSIONS = 20  # post = the POST_SESSIONS sessions after the reaction window
PRICE_LEAD_DAYS = 400  # calendar days of prices loaded before `start` (pre window + slack)
_PROFIT = """
SELECT ts_code, end_date, arg_min(n_income_attr_p, ann_date) AS cum, min(ann_date) AS ann
FROM curated.income_vip
WHERE report_type = '1' AND n_income_attr_p IS NOT NULL AND ann_date <= ?
GROUP BY 1, 2
"""
_FIRST = """
SELECT ts_code, end_date, min(ann_date) AS first_ann FROM (
  SELECT ts_code, end_date, ann_date FROM curated.forecast_vip WHERE ann_date <= ?
  UNION ALL SELECT ts_code, end_date, ann_date FROM curated.express_vip WHERE ann_date <= ?
  UNION ALL SELECT ts_code, end_date, ann_date FROM curated.income_vip
            WHERE report_type = '1' AND ann_date <= ?)
GROUP BY 1, 2
"""
_PRICES = """
SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS px
FROM curated.daily d JOIN curated.adj_factor a USING (ts_code, trade_date)
WHERE d.trade_date >= ? AND d.trade_date <= ?
"""


class EarningsEventBuilder:
    """
    Purpose:
        One event per (company, fiscal quarter), dated at its first disclosure: the earliest
        ann_date of the 业绩预告 (forecast_vip), 快报 (express_vip) or report (income_vip,
        report_type 1) (plan 35, D-172); a preview may come before the quarter end (the H1
        preview inside the Q1 report). Surprise SUE = (single-quarter parent net profit
        minus the same quarter a year earlier) / std of the prior sue_window such changes
        (at least sue_min), first reported versions only; SUE deciles 0..9 within each
        end_date among the events out by as_of that have a SUE and a pre window (a stock
        without pre_window sessions of history gets no decile). Excess = daily log return
        minus the equal-weight mean of all stocks (|log return| > max_abs_log_return dropped);
        windows in sessions from day 0 (first session on or after first_ann): pre
        [-pre_window, -1], react [0, react_window], post [react_window + 1,
        react_window + POST_SESSIONS], in %. A window not complete by as_of is NaN; pre is NaN
        when the stock has no price pre_window + 1 sessions before day 0. Nothing after as_of
        is read (point in time).

    Contract:
        Input:
            settings: SectorEarningsSignalSettings  -- start, sue_window, sue_min, windows,
                                                       max_abs_log_return, exclude_exchanges
            query:    LakeQuery  -- curated income_vip, forecast_vip, express_vip, daily,
                                    adj_factor
            codec:    DateCodec
        Output:
            instance; `build(as_of) -> DataFrame` (EVENT_COLUMNS, events with first_ann from
            `start` to as_of; sue / dec NaN without enough history); `compute_sue`,
            `compute_windows` (pure)
        Raises:
            (none at construction)

    Used by:
        portfolio.SectorEarningsSignalBuilder  -- events per sector and quarter
        cli.AppServiceBuilder                  -- `build_sector_earnings_signal`

    Test cases:
        TC-EEB-001  compute_sue: single quarters from YTD values, yoy change over the prior
                    std; fewer than sue_min prior changes or a missing quarter -> NaN
        TC-EEB-002  compute_windows: pre / react / post sums of excess from day 0; a window
                    past the last session or a stock without the pre history -> NaN
        TC-EEB-003  build on a mini lake: first disclosure is the earliest of preview / flash /
                    report (a preview before the quarter end counts); as_of cuts
                    announcements and prices (PIT); no decile without SUE
    """

    def __init__(
        self, settings: SectorEarningsSignalSettings, query: LakeQuery, codec: DateCodec
    ) -> None:
        self._s = settings
        self._query = query
        self._codec = codec

    def build(self, as_of: str) -> pd.DataFrame:
        """
        Purpose:
            All events with first disclosure in [start, as_of], with SUE, decile and windows.

        Contract:
            Input:
                as_of: str YYYYMMDD
            Output:
                DataFrame  -- EVENT_COLUMNS; empty when the lake has no statements
            Raises:
                LakeError  -- a query fails
        """
        if not self._query.has_view("curated.income_vip"):
            return pd.DataFrame(columns=EVENT_COLUMNS)
        profit = self._query.sql(_PROFIT, [as_of])
        sue = self.compute_sue(profit, self._s.sue_window, self._s.sue_min)
        first = self._read_first(as_of)
        events = first.merge(sue, on=["ts_code", "end_date"], how="left")
        events = events[(events["first_ann"] >= self._s.start) & self._is_kept(events["ts_code"])]
        events = events.reset_index(drop=True)
        cum = self._read_excess(as_of)
        out = self.compute_windows(events, cum, self._s.pre_window, self._s.react_window)
        ranked = out["sue"].where(out["pre"].notna())
        out["dec"] = ranked.groupby(out["end_date"]).transform(self._compute_decile)
        return out[list(EVENT_COLUMNS)].sort_values(["end_date", "ts_code"]).reset_index(drop=True)

    @staticmethod
    def compute_sue(profit: pd.DataFrame, window: int, min_obs: int) -> pd.DataFrame:
        """
        Purpose:
            Standardised unexpected earnings per (ts_code, end_date) from YTD profit.

        Contract:
            Input:
                profit: DataFrame  -- ts_code, end_date (quarter ends YYYYMMDD), cum (YTD
                                      parent net profit, first reported version)
                window, min_obs: int  -- prior yoy changes for the std, and the minimum
            Output:
                DataFrame  -- ts_code, end_date, sue (NaN without enough history or a zero std)
            Raises:
                (none)
        """
        f = profit[["ts_code", "end_date", "cum"]].copy()
        f["end_date"] = f["end_date"].astype(str)
        f = f[f["end_date"].str[4:].isin(["0331", "0630", "0930", "1231"])]
        f["year"] = f["end_date"].str[:4].astype(int)
        f["q"] = f["end_date"].str[4:6].astype(int) // 3
        f["key"] = f["year"] * QUARTERS + f["q"]
        f = f.sort_values(["ts_code", "key"])
        prev = f.groupby("ts_code")[["key", "cum"]].shift()
        follows = (prev["key"] == f["key"] - 1) & (f["q"] > 1)
        f["sq"] = np.where(f["q"] == 1, f["cum"], np.where(follows, f["cum"] - prev["cum"], np.nan))
        last = f[["ts_code", "key", "sq"]].assign(key=f["key"] + QUARTERS)
        f = f.merge(last.rename(columns={"sq": "sq_ly"}), on=["ts_code", "key"], how="left")
        f["d"] = f["sq"] - f["sq_ly"]
        sd = f.groupby("ts_code")["d"].transform(
            lambda s: s.shift().rolling(window, min_periods=min_obs).std()
        )
        f["sue"] = f["d"] / sd.where(sd > 0)
        return f[["ts_code", "end_date", "sue"]]

    @staticmethod
    def compute_windows(
        events: pd.DataFrame, cum: pd.DataFrame, pre_window: int, react_window: int
    ) -> pd.DataFrame:
        """
        Purpose:
            Day 0 and the pre / react / post excess sums (%) of each event.

        Contract:
            Input:
                events: DataFrame  -- ts_code, first_ann (YYYYMMDD)
                cum:    DataFrame  -- cumulative excess log return, index sessions (sorted
                                      YYYYMMDD), columns ts_code, NaN before a stock's first
                                      price
                pre_window, react_window: int
            Output:
                DataFrame  -- events plus day0 (NA past the last session), pre, react, post
            Raises:
                (none)
        """
        out = events.copy()
        n = len(cum.index)
        if n == 0 or out.empty:
            return out.assign(day0=None, pre=np.nan, react=np.nan, post=np.nan)
        dates = cum.index.to_numpy()
        d0 = np.searchsorted(dates, out["first_ann"].astype(str).to_numpy())
        cols = {c: i for i, c in enumerate(cum.columns)}
        ci = out["ts_code"].map(cols).fillna(-1).astype(int).to_numpy()
        values = cum.to_numpy()
        spans = {
            "pre": (-pre_window, -1),
            "react": (0, react_window),
            "post": (react_window + 1, react_window + POST_SESSIONS),
        }
        for name, (a, b) in spans.items():
            lo, hi = d0 + a - 1, d0 + b
            ok = (ci >= 0) & (lo >= 0) & (hi < n)
            res = np.full(len(out), np.nan)
            res[ok] = (values[hi[ok], ci[ok]] - values[lo[ok], ci[ok]]) * 100
            out[name] = res
        out["day0"] = [str(dates[i]) if i < n else None for i in d0]
        return out

    def _read_first(self, as_of: str) -> pd.DataFrame:
        first = self._query.sql(_FIRST, [as_of, as_of, as_of])
        first["end_date"] = first["end_date"].astype(str)
        first["first_ann"] = first["first_ann"].astype(str)
        return first

    def _read_excess(self, as_of: str) -> pd.DataFrame:
        lead = dt.timedelta(days=PRICE_LEAD_DAYS)
        start = self._codec.to_str(self._codec.to_date(self._s.start) - lead)
        px = self._query.sql(_PRICES, [start, as_of])
        px = px[self._is_kept(px["ts_code"])]
        close = px.pivot_table(index="trade_date", columns="ts_code", values="px").sort_index()
        close.index = close.index.astype(str)
        logs = pd.DataFrame(
            np.log(close.to_numpy(dtype=float)), index=close.index, columns=close.columns
        )
        lr = logs.diff()
        lr = lr.where(lr.abs() < self._s.max_abs_log_return)
        ar = lr.sub(lr.mean(axis=1), axis=0)
        cum: pd.DataFrame = ar.fillna(0).cumsum().where(close.notna().cummax())
        return cum

    def _is_kept(self, codes: pd.Series) -> pd.Series:
        suffix = codes.astype(str).str.split(".").str[-1]
        return ~suffix.isin(self._s.exclude_exchanges)

    @staticmethod
    def _compute_decile(s: pd.Series) -> pd.Series:
        valid = s.dropna()
        out = pd.Series(np.nan, index=s.index)
        if len(valid) >= DECILES:
            ranks = valid.rank(method="first")
            out[valid.index] = pd.qcut(ranks, DECILES, labels=False).astype(float)
        return out
