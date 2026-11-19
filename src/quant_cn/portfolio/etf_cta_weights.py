"""Target weights of the ETF CTA book: risk groups, A股 trend position, bond switch (plan 27)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from quant_cn.calculation.trend_position import TrendPosition
from quant_cn.core.etf_cta_settings import EtfCtaSettings

YEAR = 252  # sessions per year
BOND = "债券"


class EtfCtaWeights:
    """
    Purpose:
        Turn daily ETF returns into the book's target weights on each decision date (the last
        session of every week): group returns from live ETFs at their inner weights; risk weights
        ∝ 1 / annualised group vol over vol_window (at least vol_min_obs returns), set on the first
        session of each month and held; scaled to risk_share; A股 (timed) ETFs times the trend
        position (TrendPosition with trend_windows and vol_target, 0 until known); the bond sleeve
        bond_share x the bond switch (blend of switch_windows on the sleeve NAV, 1 until known).
        What is not invested stays in cash.

    Contract:
        Input:
            settings: EtfCtaSettings
            trend:    TrendPosition | None  -- A股 rule; None = built from settings
            switch:   TrendPosition | None  -- bond rule (no sizing); None = built from settings
        Output:
            instance; `compute_targets(returns)` -> DataFrame (decision dates x codes, weights
            >= 0, row sum <= 1, cash excluded); `build_summary(returns)` -> dict for the last date
        Raises:
            (none at construction)

    Used by:
        portfolio.EtfCtaBook  -- targets and the signal summary

    Test cases:
        TC-ECW-001  equal-vol groups split risk_share equally; a group twice as volatile gets half
        TC-ECW-002  risk weights change only on the first session of a month
        TC-ECW-003  timed ETFs are 0 before the trend position is known and scaled after
        TC-ECW-004  the bond switch cuts the sleeve when the sleeve NAV falls on every window
        TC-ECW-005  decisions fall on the last session of each week; an unlisted ETF has 0
        TC-ECW-006  build_summary gives group vols, risk weights, A股 positions and the bond switch
    """

    def __init__(
        self,
        settings: EtfCtaSettings,
        trend: TrendPosition | None = None,
        switch: TrendPosition | None = None,
    ) -> None:
        self._s = settings
        self._trend = trend or TrendPosition(
            settings.trend_windows, settings.vol_target, settings.vol_window
        )
        self._switch = switch or TrendPosition(settings.switch_windows, None, settings.vol_window)

    def compute_targets(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Target weight per ETF on every decision date.

        Contract:
            Input:
                returns: DataFrame  -- sessions (DatetimeIndex, sorted) x ts_codes, NaN before
                                       listing; must hold every non-cash code of the settings
            Output:
                DataFrame  -- decision dates x non-cash codes, weights in [0, 1]
            Raises:
                KeyError  -- a configured code has no column
        """
        daily = self._compute_daily(returns)
        return daily.loc[self.list_decisions(pd.DatetimeIndex(returns.index))]

    @staticmethod
    def list_decisions(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
        """
        Purpose:
            The last session of each calendar week in the index.

        Contract:
            Input:
                index: DatetimeIndex  -- sessions, sorted
            Output:
                DatetimeIndex  -- subset of index, one date per week
            Raises:
                (none)
        """
        weeks = pd.Series(index, index=index).groupby(index.to_period("W")).max()
        return pd.DatetimeIndex(weeks.to_numpy())

    def build_summary(self, returns: pd.DataFrame) -> dict[str, Any]:
        """
        Purpose:
            The signals behind the last decision: per group vol and risk weight, per timed ETF
            the trend windows / blend / vol / size / position, and the bond switch.

        Contract:
            Input:
                returns: DataFrame  -- as compute_targets
            Output:
                dict  -- {groups: [{name, vol, risk_weight}], timed: [{code, windows, blend, vol,
                         size, position}], bond_switch: {windows, blend, position}}
            Raises:
                KeyError  -- as compute_targets
        """
        last = self.list_decisions(pd.DatetimeIndex(returns.index))[-1]
        r = returns.loc[:last]
        groups = self._compute_group_returns(r)
        vol = groups.rolling(self._s.vol_window, min_periods=self._s.vol_min_obs).std()
        risk = self._compute_risk_weights(r)
        prices = self._to_prices(r)
        timed = [{"code": c, **self._trend.build_summary(prices[c])} for c in self._s.timed]
        sleeve = self._compute_sleeve_nav(r)
        return {
            "groups": [
                {
                    "name": g.name,
                    "vol": self._to_number(vol[g.name].iloc[-1] * math.sqrt(YEAR)),
                    "risk_weight": self._to_number(risk[g.name].iloc[-1]),
                }
                for g in self._s.groups
            ],
            "timed": timed,
            "bond_switch": self._switch.build_summary(sleeve) if self._s.bonds else None,
        }

    def _compute_daily(self, returns: pd.DataFrame) -> pd.DataFrame:
        risk = self._compute_risk_weights(returns) * self._s.risk_share
        weights = pd.DataFrame(0.0, index=returns.index, columns=self._list_codes())
        for g in self._s.groups:
            share = self._compute_live_share(returns, g.members)
            weights[list(g.members)] = share.mul(risk[g.name].fillna(0.0), axis=0)
        if self._s.timed:
            pos = self._trend.compute_position(self._to_prices(returns)[self._s.timed])
            weights[self._s.timed] = weights[self._s.timed] * pos.fillna(0.0)
        if self._s.bonds:
            switch = self._switch.compute_position(self._compute_sleeve_nav(returns).to_frame("b"))
            sleeve = self._s.bond_share * switch["b"].fillna(1.0)
            share = self._compute_live_share(returns, self._s.bonds)
            weights[list(self._s.bonds)] = share.mul(sleeve, axis=0)
        return weights.fillna(0.0)

    def _compute_risk_weights(self, returns: pd.DataFrame) -> pd.DataFrame:
        groups = self._compute_group_returns(returns)
        vol = groups.rolling(self._s.vol_window, min_periods=self._s.vol_min_obs).std()
        inverse = 1.0 / vol.replace(0.0, np.nan)
        weights = inverse.div(inverse.sum(axis=1), axis=0)
        idx = pd.DatetimeIndex(returns.index)
        month = pd.Series(idx.to_period("M"), index=idx)
        first = (month != month.shift(1)).to_numpy(dtype=bool)
        return weights.loc[idx[first]].reindex(idx).ffill()

    def _compute_group_returns(self, returns: pd.DataFrame) -> pd.DataFrame:
        out = {}
        for g in self._s.groups:
            share = self._compute_live_share(returns, g.members)
            live = returns[list(g.members)].notna().any(axis=1)
            out[g.name] = (share * returns[list(g.members)].fillna(0.0)).sum(axis=1).where(live)
        return pd.DataFrame(out, index=returns.index)

    def _compute_sleeve_nav(self, returns: pd.DataFrame) -> pd.Series:
        share = self._compute_live_share(returns, self._s.bonds)
        sleeve = (share * returns[list(self._s.bonds)].fillna(0.0)).sum(axis=1)
        live = returns[list(self._s.bonds)].notna().any(axis=1)
        nav = (1.0 + sleeve).cumprod()
        return nav.where(live.cummax())

    @staticmethod
    def _compute_live_share(returns: pd.DataFrame, members: dict[str, float]) -> pd.DataFrame:
        cols = list(members)
        live = returns[cols].notna().astype(float) * pd.Series(members)
        return live.div(live.sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0)

    @staticmethod
    def _to_prices(returns: pd.DataFrame) -> pd.DataFrame:
        listed = returns.notna().cummax()
        return (1.0 + returns.fillna(0.0)).cumprod().where(listed)

    def _list_codes(self) -> list[str]:
        return [c for c in self._s.list_codes() if c != self._s.cash]

    @staticmethod
    def _to_number(value: float) -> float | None:
        return None if pd.isna(value) else round(float(value), 4)
