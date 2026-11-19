"""Crowding of style ETF flows (银行, 红利) for the ETF page and alerts (plan 15 ph7g)."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from quant_cn.core.etf_proxy_settings import EtfProxySettings
from quant_cn.portfolio.etf_flow_calculator import EtfFlowCalculator

HISTORY_STEP = 5  # sessions between points of the z history (weekly)


class EtfStyleHeat:
    """
    Purpose:
        Per style group (银行, 红利): pick its ETFs, and from their daily flows compute the
        `style_window`-day net flow, that flow as a share of today's AUM, and its z-score
        against the previous `style_z_days` sessions (today excluded, so z uses only the past).
        Status: 过热 (hot) at z ≥ style_hot_z; after a hot day it stays hot until z ≤ 0, which
        is the 降温 (cooled) day; normal otherwise. Style ETFs are a separate member set and
        never enter the national-team core / other totals.

    Contract:
        Input:
            settings: EtfProxySettings  -- styles, style_window, style_z_days, style_hot_z and
                                           the member name rules
        Output:
            instance; `build_members(funds)` -> members, `build(prices, shares, members)` ->
            list of style dicts
        Raises:
            (none at construction)

    Used by:
        portfolio.EtfProxyBuilder  -- `styles` part of etf_proxy.json

    Test cases:
        TC-ESH-001  members: bank / dividend patterns, excluded benchmarks skipped, core empty
        TC-ESH-002  flow sum, share of AUM and z from hand flows; z ignores today
        TC-ESH-003  hot fires at the z bound and not just below; stays hot until z ≤ 0 (cooled)
    """

    def __init__(self, settings: EtfProxySettings) -> None:
        self._s = settings
        styled = settings.model_copy(update={"indices": list(settings.styles), "core": []})
        self._calculator = EtfFlowCalculator(styled)

    def build_members(self, funds: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            The ETFs of each style group.

        Contract:
            Input:
                funds: DataFrame  -- ts_code, name, benchmark (curated.fund_basic, market E)
            Output:
                DataFrame  -- ts_code, index (style name), is_core (always False)
            Raises:
                (none)
        """
        return self._calculator.build_members(funds)

    def build(
        self, prices: pd.DataFrame, shares: pd.DataFrame, members: pd.DataFrame
    ) -> list[dict[str, Any]]:
        """
        Purpose:
            One summary per style with data.

        Contract:
            Input:
                prices, shares: as EtfFlowCalculator.compute_daily; members: from build_members
            Output:
                list[dict]  -- {key, name, metric, as_of, n_etf, aum, flow_1d, flow_window,
                               flow_pct, z, status (hot | cooled | normal), hot_since,
                               history: [{d, z, flow_pct}]}; money in 亿元, pct as fraction
            Raises:
                (none)
        """
        if members.empty:
            return []
        daily = self._calculator.compute_daily(prices, shares, members)
        out = []
        for style in self._s.styles:
            part = daily[daily["index"] == style.name]
            if part.empty:
                continue
            day = part.groupby("trade_date")[["aum", "flow"]].sum(min_count=1).sort_index()
            out.append(self._build_style(style.key, style.name, day, part["ts_code"].nunique()))
        return out

    def _build_style(self, key: str, name: str, day: pd.DataFrame, n_etf: int) -> dict[str, Any]:
        s = self._s
        flow = day["flow"].fillna(0.0).rolling(s.style_window, min_periods=s.style_window).sum()
        pct = flow / day["aum"]
        past = pct.shift(1).rolling(s.style_z_days, min_periods=s.style_z_days // 2)
        z = (pct - past.mean()) / past.std()
        status, since = self._compute_status(z)
        last = day.index[-1]
        hist = pd.DataFrame({"z": z, "pct": pct}).dropna().iloc[::-1].iloc[::HISTORY_STEP]
        return {
            "key": key,
            "name": name,
            "metric": f"{key}_etf_z",
            "as_of": str(last),
            "n_etf": int(n_etf),
            "aum": self._to_number(day["aum"].iloc[-1], 1),
            "flow_1d": self._to_number(day["flow"].iloc[-1], 1),
            "flow_window": self._to_number(flow.iloc[-1], 1),
            "flow_pct": self._to_number(pct.iloc[-1], 4),
            "z": self._to_number(z.iloc[-1], 2),
            "status": status,
            "hot_since": since,
            "history": [
                {"d": str(d), "z": round(float(r.z), 2), "flow_pct": round(float(r.pct), 4)}
                for d, r in hist.iloc[::-1].iterrows()
            ],
        }

    def _compute_status(self, z: pd.Series) -> tuple[str, str]:
        state, since = "normal", ""
        for d, v in z.items():
            if pd.isna(v):
                continue
            if v >= self._s.style_hot_z:
                since = since if state == "hot" else str(d)
                state = "hot"
            elif state == "hot" and v <= 0:
                state = "cooled"
            elif state == "cooled":
                state, since = "normal", ""
        return state, since

    @staticmethod
    def _to_number(v: Any, digits: int) -> float | None:
        if v is None or (isinstance(v, float) and math.isnan(v)) or pd.isna(v):
            return None
        return round(float(v), digits)
