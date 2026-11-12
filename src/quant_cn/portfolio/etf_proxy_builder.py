"""The national-team ETF proxy behind the app's 国家队 ETF panel (plan 15 phase 7b, D-126)."""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
import numbers
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.etf_proxy_settings import EtfProxySettings
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.etf_flow_calculator import EtfFlowCalculator

logger = logging.getLogger(__name__)

FILE_NAME = "etf_proxy.json"
_LOOKBACK_DAYS = 20  # calendar days loaded before `start` so the first day has a previous row
_FUNDS = "SELECT ts_code, name, benchmark FROM curated.fund_basic WHERE market = 'E'"
_SHARES = """
SELECT ts_code, trade_date, fd_share FROM curated.fund_share
WHERE list_contains(?, ts_code) AND trade_date >= ? ORDER BY ts_code, trade_date
"""
_PRICES = """
SELECT ts_code, trade_date, close, pre_close FROM curated.fund_daily
WHERE list_contains(?, ts_code) AND trade_date >= ? ORDER BY ts_code, trade_date
"""
_GROUPS = {True: "core", False: "other"}


class EtfProxyBuilder:
    """
    Purpose:
        Sum the broad-index ETFs into a proxy of national-team positioning: daily net
        subscriptions and the position at today's price, for the core ETFs the national team
        holds and for the other ETFs on the same indices, per index and in total.

    Contract:
        Input:
            config:     Config             -- `etf_proxy` settings (indices, start, window)
            query:      LakeQuery          -- reads curated.fund_basic, fund_share, fund_daily
            codec:      DateCodec
            calculator: EtfFlowCalculator  -- membership, flows and positions
        Output:
            instance; `build` -> dict, `write` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.ResearchCommands  -- `etf-proxy` command

    Test cases:
        TC-EP-001  build splits core / other, per index, weekly and recent; as_of = last share day
        TC-EP-002  no indices configured -> empty document without reading the lake
        TC-EP-003  write puts etf_proxy.json in the directory; a missing directory raises LakeError
        TC-EP-004  no fund_share rows from start raises LakeError
    """

    def __init__(
        self, config: Config, query: LakeQuery, codec: DateCodec, calculator: EtfFlowCalculator
    ) -> None:
        self._settings: EtfProxySettings = config.etf_proxy
        self._query = query
        self._codec = codec
        self._calculator = calculator

    def build(self) -> dict[str, Any]:
        """
        Purpose:
            The proxy document from `start` to the last day with share data.

        Contract:
            Input:
                (none)
            Output:
                dict  -- {as_of, price_as_of, start, n_members, totals: {core, other},
                         recent: [{date, core, other}], weekly: [{date, core_flow, other_flow,
                         core_position, other_position}], yearly: [{year, core, other}],
                         indices: [{name, reference, n_etf, aum, position, core_position,
                         flow_recent, flow_ytd, weekly: [{date, position, flow}]}]};
                         money in 亿元 rounded to 0.1; empty lists and "" dates when no indices
            Raises:
                LakeError  -- no share rows from start, or a query fails
        """
        s = self._settings
        if not s.indices:
            return self._build_empty()
        members = self._calculator.build_members(self._query.sql(_FUNDS))
        codes = members["ts_code"].tolist()
        since = self._codec.to_str(self._codec.to_date(s.start) - dt.timedelta(_LOOKBACK_DAYS))
        refs = [i.reference for i in s.indices]
        shares = self._query.sql(_SHARES, [codes, since])
        if shares.empty:
            raise LakeError(f"curated.fund_share has no rows since {since}: run make etf-proxy")
        prices = self._query.sql(_PRICES, [sorted(set(codes) | set(refs)), since])
        daily = self._calculator.compute_daily(prices, shares, members)
        daily = daily[daily["trade_date"] >= s.start]
        as_of = str(shares["trade_date"].max())
        return {
            "as_of": as_of,
            "price_as_of": str(prices["trade_date"].max()) if not prices.empty else "",
            "start": s.start,
            "n_members": len(members),
            **self._build_summary(daily, as_of),
        }

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build the document and write it as `etf_proxy.json` for the app's data directory.

        Contract:
            Input:
                out_dir: Path  -- existing directory (the chain app's data dir)
            Output:
                Path  -- the written file, UTF-8 JSON
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"etf proxy output directory missing: {out_dir}")
        path = out_dir / FILE_NAME
        doc = self.build()
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("etf proxy: %d members as of %s -> %s", doc["n_members"], doc["as_of"], path)
        return path

    def _build_summary(self, daily: pd.DataFrame, as_of: str) -> dict[str, Any]:
        grouped = daily.groupby(["trade_date", "is_core"])[["aum", "flow", "position"]]
        day = pd.DataFrame(grouped.sum(min_count=1).unstack("is_core")).sort_index()
        dates = day.index.tolist()
        recent = dates[-self._settings.recent_days :]
        year = as_of[:4]
        totals = {
            _GROUPS[c]: self._build_totals(pd.DataFrame(day.xs(c, axis=1, level=1)), recent, year)
            for c in (True, False)
            if c in day.columns.get_level_values(1)
        }
        return {
            "totals": totals,
            "recent": [
                {
                    "date": d,
                    **{
                        _GROUPS[c]: self._to_yi(day.at[d, ("flow", c)])
                        for c in (True, False)
                        if ("flow", c) in day
                    },
                }
                for d in recent
            ],
            "weekly": self._build_weekly(day),
            "yearly": self._build_yearly(day),
            "indices": [
                self._build_index(daily, i.name, i.reference, recent, year)
                for i in self._settings.indices
            ],
        }

    def _build_totals(self, part: pd.DataFrame, recent: list[str], year: str) -> dict[str, Any]:
        position = part["position"].dropna()
        peak_date = str(position.idxmax()) if not position.empty else ""
        after = position[position.index >= peak_date] if peak_date else position
        trough_date = str(after.idxmin()) if not after.empty else ""
        return {
            "aum": self._to_yi(part["aum"].iloc[-1]),
            "position": self._to_yi(position.iloc[-1]) if not position.empty else None,
            "flow_recent": self._to_yi(part.loc[recent, "flow"].sum()),
            "flow_ytd": self._to_yi(part.loc[part.index >= f"{year}0101", "flow"].sum()),
            "peak": {"date": peak_date, "position": self._to_yi(position.get(peak_date))},
            "trough_since_peak": {
                "date": trough_date,
                "position": self._to_yi(position.get(trough_date)),
            },
        }

    def _build_weekly(self, day: pd.DataFrame) -> list[dict[str, Any]]:
        week = pd.Series(day.index, index=day.index).map(self._to_week)
        rows = []
        for _, part in day.groupby(week, sort=True):
            last = part.index[-1]
            row: dict[str, Any] = {"date": last}
            for c in (True, False):
                if ("flow", c) in part:
                    row[f"{_GROUPS[c]}_flow"] = self._to_yi(part[("flow", c)].sum())
                    row[f"{_GROUPS[c]}_position"] = self._to_yi(part.at[last, ("position", c)])
            rows.append(row)
        return rows

    def _build_yearly(self, day: pd.DataFrame) -> list[dict[str, Any]]:
        flow = day["flow"]
        years = flow.groupby(flow.index.str[:4]).sum()
        return [
            {
                "year": y,
                **{_GROUPS[c]: self._to_yi(years.at[y, c]) for c in (True, False) if c in years},
            }
            for y in years.index
        ]

    def _build_index(
        self, daily: pd.DataFrame, name: str, reference: str, recent: list[str], year: str
    ) -> dict[str, Any]:
        part = daily[daily["index"] == name]
        day = part.groupby("trade_date")[["aum", "flow", "position"]].sum(min_count=1).sort_index()
        core = part[part["is_core"]].groupby("trade_date")["position"].sum(min_count=1)
        last = day.index[-1] if not day.empty else None
        week = pd.Series(day.index, index=day.index).map(self._to_week)
        weekly = [
            {
                "date": g.index[-1],
                "position": self._to_yi(g["position"].iloc[-1]),
                "flow": self._to_yi(g["flow"].sum()),
            }
            for _, g in day.groupby(week, sort=True)
        ]
        return {
            "name": name,
            "reference": reference,
            "n_etf": int(part.loc[part["trade_date"] == last, "ts_code"].nunique()) if last else 0,
            "aum": self._to_yi(day["aum"].iloc[-1]) if last else None,
            "position": self._to_yi(day["position"].iloc[-1]) if last else None,
            "core_position": self._to_yi(core.get(last)) if last else None,
            "flow_recent": self._to_yi(day.loc[day.index.isin(recent), "flow"].sum()),
            "flow_ytd": self._to_yi(day.loc[day.index >= f"{year}0101", "flow"].sum()),
            "weekly": weekly,
        }

    def _build_empty(self) -> dict[str, Any]:
        return {
            "as_of": "",
            "price_as_of": "",
            "start": self._settings.start,
            "n_members": 0,
            "totals": {},
            "recent": [],
            "weekly": [],
            "yearly": [],
            "indices": [],
        }

    def _to_week(self, day: str) -> str:
        iso = self._codec.to_date(day).isocalendar()
        return f"{iso[0]}-{iso[1]:02d}"

    @staticmethod
    def _to_yi(value: object) -> float | None:
        if not isinstance(value, numbers.Real):
            return None
        number = float(value)
        return None if math.isnan(number) else round(number, 1)
