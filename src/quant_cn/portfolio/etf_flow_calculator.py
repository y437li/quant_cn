"""Membership, net flows and positions of the national-team ETF proxy (plan 15 ph7b, D-126)."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from quant_cn.core.etf_proxy_settings import EtfProxySettings

_SHARE_FILL_DAYS = 5  # trading days a missing share row is carried forward for positions


class EtfFlowCalculator:
    """
    Purpose:
        Pick the ETFs that track each configured index, and compute their daily AUM, net
        subscriptions (split- and gap-proof) and position at today's price.

    Contract:
        Input:
            settings: EtfProxySettings  -- indices (patterns, references), core list, name rules
        Output:
            instance; `build_members` -> members, `compute_daily` -> daily panel
        Raises:
            (none at construction)

    Used by:
        portfolio.EtfProxyBuilder  -- membership and the daily panel
        portfolio.EtfStyleHeat     -- the same rules over the style groups
        portfolio.SmallCapWatchBuilder  -- broad-ETF flow rows of the 小盘观察
        cli.ResearchCommands       -- wiring of `etf-proxy`
        cli.ReportCommands         -- wiring of `smallcap-watch`

    Test cases:
        TC-EFC-001  flow = AUM_t - AUM_{t-1} x g_t / g_{t-1}: 0 on a pure price move,
                    shares added x close on a subscription
        TC-EFC-002  a split day (shares x2, close and pre_close halved) gives flow 0
        TC-EFC-003  a missing share day compounds both returns: pure price moves still give
                    flow 0; the position carries the last shares forward
        TC-EFC-004  position at today's price does not move with the reference price
        TC-EFC-005  build_members: first matching index wins; feeder, enhanced, non-100% dropped
        TC-EFC-006  build_members: a benchmark matching the index's `exclude` is skipped
    """

    def __init__(self, settings: EtfProxySettings) -> None:
        self._settings = settings

    def build_members(self, funds: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Pick the ETFs that track one configured index 100% and tag them with it.

        Contract:
            Input:
                funds: DataFrame  -- ts_code, name, benchmark (curated.fund_basic, market E)
            Output:
                DataFrame  -- ts_code, index, is_core; one row per member, sorted by ts_code
            Raises:
                (none)
        """
        s = self._settings
        rows = []
        for code, raw_name, raw_bench in zip(
            funds["ts_code"], funds["name"], funds["benchmark"], strict=True
        ):
            name, bench = str(raw_name or ""), str(raw_bench or "")
            if s.name_contains not in name or s.benchmark_contains not in bench:
                continue
            if any(word in name for word in s.name_excludes):
                continue
            index = next(
                (
                    i.name
                    for i in s.indices
                    if re.search(i.benchmark, bench)
                    and not (i.exclude and re.search(i.exclude, bench))
                ),
                None,
            )
            if index is not None:
                rows.append((str(code), index, str(code) in s.core))
        frame = pd.DataFrame(rows, columns=["ts_code", "index", "is_core"])
        return frame.sort_values("ts_code", ignore_index=True)

    def compute_daily(
        self, prices: pd.DataFrame, shares: pd.DataFrame, members: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Purpose:
            Daily AUM, net flow and position at today's price for every member ETF.

        Contract:
            Input:
                prices:  DataFrame  -- ts_code, trade_date, close, pre_close (fund_daily), incl.
                                       the reference ETFs
                shares:  DataFrame  -- ts_code, trade_date, fd_share in 万份 (fund_share)
                members: DataFrame  -- ts_code, index, is_core (from build_members)
            Output:
                DataFrame  -- ts_code, index, is_core, trade_date, aum, flow, position (亿元);
                              one row per member and price day up to its last share day, shares
                              carried forward at most 5 trading days for aum and position; flow
                              only on days with a share row (NaN on the first); position NaN
                              when the reference has no price that day
            Raises:
                (none)
        """
        px = self._add_growth(prices)
        frame = px.merge(members, on="ts_code").merge(
            shares[["ts_code", "trade_date", "fd_share"]], on=["ts_code", "trade_date"], how="left"
        )
        frame = frame.sort_values(["ts_code", "trade_date"], ignore_index=True)
        frame["held"] = frame.groupby("ts_code")["fd_share"].ffill(limit=_SHARE_FILL_DAYS)
        last_share = shares.groupby("ts_code")["trade_date"].max().rename("last_share")
        frame = frame.merge(last_share, on="ts_code")
        frame = frame[frame["trade_date"] <= frame["last_share"]].dropna(subset=["held"])
        frame["aum"] = frame["held"] * frame["close"] / 1e4
        frame = frame.merge(self._compute_flow(frame), on=["ts_code", "trade_date"], how="left")
        frame = frame.merge(self._build_deflator(px), on=["index", "trade_date"], how="left")
        frame["position"] = frame["aum"] * frame["g_last"] / frame["g_ref"]
        cols = ["ts_code", "index", "is_core", "trade_date", "aum", "flow", "position"]
        return frame[cols].sort_values(["trade_date", "ts_code"], ignore_index=True)

    @staticmethod
    def _add_growth(prices: pd.DataFrame) -> pd.DataFrame:
        """Cumulative return factor g per ETF from close / pre_close (split-adjusted)."""
        px = prices.sort_values(["ts_code", "trade_date"], ignore_index=True).copy()
        ratio = (px["close"] / px["pre_close"]).where(px["pre_close"] > 0, 1.0).fillna(1.0)
        log_ratio = pd.Series(np.log(ratio.to_numpy(dtype=float)), index=px.index)
        px["g"] = np.exp(log_ratio.groupby(px["ts_code"]).cumsum())
        return px

    @staticmethod
    def _compute_flow(frame: pd.DataFrame) -> pd.DataFrame:
        """Flow on real share rows only, so a gap compounds every return in between."""
        real = frame.dropna(subset=["fd_share"]).copy()
        by_code = real.groupby("ts_code")
        real["flow"] = real["aum"] - by_code["aum"].shift() * real["g"] / by_code["g"].shift()
        return real[["ts_code", "trade_date", "flow"]]

    def _build_deflator(self, px: pd.DataFrame) -> pd.DataFrame:
        """Per index and day: the reference ETF's g and its last g (today's price level)."""
        refs = pd.DataFrame(
            [(i.name, i.reference) for i in self._settings.indices], columns=["index", "ts_code"]
        )
        ref = refs.merge(px[["ts_code", "trade_date", "g"]], on="ts_code").sort_values("trade_date")
        ref["g_last"] = ref.groupby("index")["g"].transform("last")
        return ref.rename(columns={"g": "g_ref"})[["index", "trade_date", "g_ref", "g_last"]]
