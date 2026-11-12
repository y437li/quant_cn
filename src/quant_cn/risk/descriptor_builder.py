"""Raw CNE5 descriptors for every universe member and session of a window (plan 05 phase 2)."""

from __future__ import annotations

import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd

from quant_cn.risk.fundamental_descriptors import (
    BALANCE_FIELDS,
    TTM_FIELDS,
    FundamentalDescriptors,
)
from quant_cn.risk.price_descriptors import PriceDescriptors
from quant_cn.risk.risk_input_loader import RiskInputs
from quant_cn.statistic.standardizer import Standardizer

logger = logging.getLogger(__name__)

PERCENT = 100.0
BASE_COLUMNS = ["trade_date", "ts_code", "l1_code", "industry_backfilled", "circ_mv"]
PRICE_COLUMNS = ["beta", "hsigma", "rstr", "dastd", "cmra", "stom", "stoq", "stoa"]
MAX_STALE_SESSIONS = 3  # sessions after the last foreign close that still get a value (0 or sum)
DESCRIPTORS = [
    "lncap",
    "nlsize",
    *PRICE_COLUMNS,
    "btop",
    "etop",
    "cetop",
    "fcfp",
    "mlev",
    "dtoa",
    "blev",
    "egro",
    "sgro",
]


class DescriptorBuilder:
    """
    Purpose:
        One row per universe member and session in [start, end] with its Shenwan L1 group,
        circulating market cap (regression weight base, CNY) and every raw CNE5 descriptor:
        LNCAP = ln(total market cap in CNY), NLSIZE = cube of the cap-weighted standardised
        LNCAP, the price descriptors (PriceDescriptors on the dense return matrix; market =
        previous-day circ_mv weighted return of all stocks), the value / leverage descriptors and
        the growth descriptors from the latest monthly snapshot on or before the session, and
        one partial beta per configured external series (the foreign return that closed between
        the previous and the current China close, e.g. S&P 500 or USDCNH; D-128, D-134) and per
        theme basket (circ_mv-weighted return of the concept's members excluding the stock
        itself, from the concept's start; D-130), with the China market as control
        (FundamentalDescriptors). Stocks whose code ends with an excluded suffix are dropped.

    Contract:
        Input:
            prices: PriceDescriptors; fundamentals: FundamentalDescriptors
            standardizer: Standardizer; exclude_suffixes: Sequence[str]  -- e.g. (".BJ",)
        Output:
            instance; `compute(inputs) -> DataFrame`, `compute_overnight_return`,
            `compute_theme_return`
        Raises:
            (none at construction)

    Used by:
        risk.RiskModel  -- exposures step
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-DB-001  one row per member and session in the window with every descriptor column;
                   excluded suffixes dropped
        TC-DB-002  descriptors use only past rows: changing a later return leaves earlier rows
        TC-DB-003  growth comes from the latest snapshot on or before the session
        TC-DB-004  overnight foreign return sums the closes dated in [previous session, session);
                   none in the window = 0; missing foreign data = NaN
        TC-DB-005  theme basket excludes the stock itself, is NaN before the start, and the theme
                   descriptor column appears next to the core descriptors
    """

    def __init__(
        self,
        prices: PriceDescriptors,
        fundamentals: FundamentalDescriptors,
        standardizer: Standardizer,
        exclude_suffixes: Sequence[str] = (".BJ",),
    ) -> None:
        self._prices = prices
        self._fundamentals = fundamentals
        self._standardizer = standardizer
        self._exclude = tuple(exclude_suffixes)

    def compute(self, inputs: RiskInputs) -> pd.DataFrame:
        """
        Purpose:
            The descriptor table of the window.

        Contract:
            Input:
                inputs: RiskInputs
            Output:
                DataFrame  -- BASE_COLUMNS + DESCRIPTORS + one column per external series and
                              theme (descriptor names), key (trade_date, ts_code) unique and
                              sorted; descriptor NaN = not computable (filled later by
                              ExposureStandardizer); circ_mv in CNY
            Raises:
                KeyError  -- an input panel lacks a required column
        """
        members = inputs.members[~inputs.members["ts_code"].str.endswith(self._exclude)]
        members = members[["trade_date", "ts_code", "l1_code", "industry_backfilled", "log_mcap"]]
        out = members.merge(
            self._compute_price_frame(inputs, members), on=["trade_date", "ts_code"], how="left"
        )
        out = out.merge(
            self._compute_fundamental_frame(inputs, members),
            on=["trade_date", "ts_code"],
            how="left",
        )
        out = out.merge(
            self._compute_growth_frame(inputs, members), on=["trade_date", "ts_code"], how="left"
        )
        out = out.rename(columns={"log_mcap": "lncap"})
        out["nlsize"] = self._compute_nlsize(out)
        out = out.sort_values(["trade_date", "ts_code"]).reset_index(drop=True)
        logger.info("descriptors %s..%s: %d rows", inputs.start, inputs.end, len(out))
        extra = [*inputs.external, *inputs.themes]
        return out[BASE_COLUMNS + DESCRIPTORS + extra]

    def _compute_price_frame(self, inputs: RiskInputs, members: pd.DataFrame) -> pd.DataFrame:
        close = inputs.prices.pivot(index="trade_date", columns="ts_code", values="close_adj")
        close = close.sort_index()
        basic = inputs.basic.set_index(["trade_date", "ts_code"])
        circ = basic["circ_mv"].unstack().reindex(index=close.index, columns=close.columns)
        turnover = (
            basic["turnover_rate_f"].unstack().reindex(index=close.index, columns=close.columns)
        )
        returns = (close / close.shift(1) - 1.0).to_numpy()
        market = self._compute_market(returns, circ.shift(1).to_numpy())
        beta, hsigma = self._prices.compute_beta(returns, market)
        values = {"beta": beta, "hsigma": hsigma, "rstr": self._prices.compute_rstr(returns)}
        values["dastd"] = self._prices.compute_dastd(returns)
        values["cmra"] = self._prices.compute_cmra(returns)
        values |= self._prices.compute_liquidity(turnover.to_numpy() / PERCENT)
        sessions = list(close.index)
        for name, series in inputs.external.items():
            foreign = self.compute_overnight_return(sessions, series)
            values[name] = self._prices.compute_partial_beta(returns, market, foreign)
        weights = circ.shift(1).to_numpy()
        for name, (codes, start) in inputs.themes.items():
            member = close.columns.isin(codes)
            basket = self.compute_theme_return(returns, weights, member)
            basket[np.array(sessions) < start] = np.nan
            values[name] = self._prices.compute_partial_beta(returns, market, basket)
        values["circ_mv"] = circ.to_numpy() * 1e4
        rows = close.index.get_indexer(pd.Index(members["trade_date"]))
        cols = close.columns.get_indexer(pd.Index(members["ts_code"]))
        found = (rows >= 0) & (cols >= 0)
        frame = members[["trade_date", "ts_code"]].copy()
        for name, matrix in values.items():
            column = np.full(len(frame), np.nan)
            column[found] = matrix[rows[found], cols[found]]
            frame[name] = column
        return frame

    @staticmethod
    def compute_theme_return(
        returns: np.ndarray, weights: np.ndarray, member: np.ndarray
    ) -> np.ndarray:
        """
        Purpose:
            Weighted theme-basket return seen by every stock: members get the basket without
            themselves, non-members the whole basket.

        Contract:
            Input:
                returns: np.ndarray  -- (T, N) daily returns
                weights: np.ndarray  -- (T, N) basket weights (previous-day circ_mv)
                member:  np.ndarray  -- (N,) bool, theme members
            Output:
                np.ndarray  -- (T, N) basket returns; NaN where the basket has no other weight
            Raises:
                (none)
        """
        valid = np.isfinite(returns) & np.isfinite(weights) & (np.nan_to_num(weights) > 0)
        w = np.where(valid & member[None, :], weights, 0.0)
        wr = w * np.where(valid, returns, 0.0)
        total_w, total_wr = w.sum(axis=1, keepdims=True), wr.sum(axis=1, keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            out = (total_wr - wr) / (total_w - w)
        return np.where((total_w - w) > 0, out, np.nan)

    @staticmethod
    def compute_overnight_return(sessions: list[str], foreign: pd.DataFrame) -> np.ndarray:
        """
        Purpose:
            Foreign index return aligned to China sessions: for session t with previous session
            p, the compounded return of every foreign close dated d with p <= d < t (a US close
            dated d happens on the morning of d + 1 Beijing time, between the two China closes).

        Contract:
            Input:
                sessions: list[str]   -- China sessions, ascending YYYYMMDD
                foreign:  DataFrame   -- trade_date (foreign local date), pct_chg (percent)
            Output:
                np.ndarray  -- (len(sessions),) simple returns; 0 when no foreign close falls in
                               the window (foreign holiday); NaN for the first session, with no
                               foreign data, or more than 3 sessions after the last foreign close
            Raises:
                KeyError  -- missing column
        """
        out = np.full(len(sessions), np.nan)
        if "pct_chg" not in foreign:
            return out
        rows = foreign.dropna(subset=["pct_chg"]).sort_values("trade_date")
        if rows.empty or len(sessions) < 2:  # noqa: PLR2004 -- a window needs two sessions
            return out
        dates = rows["trade_date"].astype(str).to_numpy()
        cum = np.concatenate([[0.0], np.cumsum(np.log1p(rows["pct_chg"].to_numpy(float) / 100))])
        after_last = np.cumsum(np.array(sessions) > dates[-1])
        for i in range(1, len(sessions)):
            if after_last[i] > MAX_STALE_SESSIONS or sessions[i] <= dates[0]:
                continue
            hi = np.searchsorted(dates, sessions[i], side="left")
            lo = np.searchsorted(dates, sessions[i - 1], side="left")
            out[i] = np.expm1(cum[hi] - cum[lo])
        return out

    @staticmethod
    def _compute_market(returns: np.ndarray, weights: np.ndarray) -> np.ndarray:
        valid = np.isfinite(returns) & np.isfinite(weights) & (np.nan_to_num(weights) > 0)
        w = np.where(valid, weights, 0.0)
        total = w.sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            market = (w * np.where(valid, returns, 0.0)).sum(axis=1) / total
        return np.where(total > 0, market, np.nan)

    def _compute_fundamental_frame(self, inputs: RiskInputs, members: pd.DataFrame) -> pd.DataFrame:
        keys = ["trade_date", "ts_code"]
        fields = inputs.fundamentals.pivot_table(
            index=keys, columns="field", values="value", aggfunc="last"
        )
        frame = members[keys].merge(inputs.basic[[*keys, "total_mv"]], on=keys, how="left")
        frame = frame.merge(fields.reset_index(), on=keys, how="left")
        for name in (*BALANCE_FIELDS, *TTM_FIELDS):
            if name not in frame:
                frame[name] = np.nan
        return self._fundamentals.compute_value_leverage(frame)

    def _compute_growth_frame(self, inputs: RiskInputs, members: pd.DataFrame) -> pd.DataFrame:
        growth = self._fundamentals.compute_growth(inputs.annual)
        keys = members[["trade_date", "ts_code"]]
        if growth.empty:
            return keys.assign(egro=np.nan, sgro=np.nan)
        left = keys.assign(day=keys["trade_date"].astype(int), ts_code=keys["ts_code"].astype(str))
        right = growth.assign(
            day=growth["as_of"].astype(int), ts_code=growth["ts_code"].astype(str)
        )
        left, right = left.sort_values("day"), right.sort_values("day")
        out = pd.merge_asof(
            left, right.drop(columns="as_of"), on="day", by="ts_code", direction="backward"
        )
        return out[["trade_date", "ts_code", "egro", "sgro"]]

    def _compute_nlsize(self, frame: pd.DataFrame) -> pd.Series:
        z = self._standardizer.compute(
            frame[["trade_date", "lncap", "circ_mv"]], column="lncap", weight_column="circ_mv"
        )["lncap"]
        return z**3
