"""Recent buyback events for the morning report: large plans and the book's events (plan 23)."""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

FILE_NAME = "buybacks.json"
LARGE_PCT = 2.0  # plans of at least 2% of total market cap (research 20261113_buyback_yield)
_EVENTS = """
SELECT DISTINCT r.ts_code, r.ann_date, r.proc, r.amount, r.high_limit, r.exp_date, s.name
FROM curated.repurchase r LEFT JOIN curated.stock_basic s USING (ts_code)
WHERE r.ann_date > ? AND r.ann_date <= ?
"""
_MV = """
SELECT ts_code, total_mv, close FROM curated.daily_basic
WHERE trade_date = (SELECT max(trade_date) FROM curated.daily_basic WHERE trade_date <= ?)
"""


class BuybackEventsBuilder:
    """
    Purpose:
        Buyback announcements of the last `days` calendar days: every new plan (预案) of at least
        2% of total market cap across the market (since 2024 such plans were followed by +4.6%
        excess over 60 sessions on average), and every event (预案 / 股东大会通过 / 实施 / 完成 /
        停止) of the held and watched stocks.

    Contract:
        Input:
            query: LakeQuery  -- curated.repurchase, stock_basic, daily_basic
            days:  int > 0    -- look-back in calendar days (default 7)
        Output:
            instance; `build(as_of, book)` -> dict, `write(out_dir, as_of, book)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `buyback-events` command

    Test cases:
        TC-BEB-001  large plans: only 预案 at >= 2% of market cap, sorted by size; book events
                    for the given codes only, newest first; plan price cap vs close
        TC-BEB-002  write puts buybacks.json in the directory; a missing directory raises
    """

    def __init__(self, query: LakeQuery, days: int = 7) -> None:
        self._query = query
        self._days = days

    def build(self, as_of: str, book: list[str]) -> dict[str, Any]:
        """
        Purpose:
            The events document.

        Contract:
            Input:
                as_of: str (YYYYMMDD); book: ts_codes held or watched
            Output:
                dict  -- {as_of, days, large_plans: [{code, name, ann_date, amount_yi, pct,
                         high_limit, close}], book_events: [{code, name, ann_date, proc,
                         amount_yi}]}
            Raises:
                LakeError  -- a query fails
        """
        start = (dt.datetime.strptime(as_of, "%Y%m%d") - dt.timedelta(days=self._days)).strftime(
            "%Y%m%d"
        )
        ev = self._query.sql(_EVENTS, [start, as_of])
        mv = self._query.sql(_MV, [as_of]).set_index("ts_code")
        return self.compute(ev, mv, as_of, book)

    def compute(
        self, ev: pd.DataFrame, mv: pd.DataFrame, as_of: str, book: list[str]
    ) -> dict[str, Any]:
        """
        Purpose:
            The document from event rows and market caps.

        Contract:
            Input:
                ev: repurchase rows (+ name); mv: index ts_code, total_mv (万元), close;
                as_of: str; book: list[str]
            Output:
                dict  -- as build
            Raises:
                (none)
        """
        plans = ev[ev["proc"] == "预案"].join(mv, on="ts_code")
        plans = plans.assign(pct=plans["amount"] / (plans["total_mv"] * 1e4) * 100)
        large = plans[plans["pct"] >= LARGE_PCT].sort_values("pct", ascending=False)
        mine = ev[ev["ts_code"].isin(book)].sort_values("ann_date", ascending=False)
        return {
            "as_of": as_of,
            "days": self._days,
            "large_plans": [
                {"code": r.ts_code, "name": r.name, "ann_date": r.ann_date,
                 "amount_yi": self._to_yi(r.amount), "pct": self._to_number(r.pct),
                 "high_limit": self._to_number(r.high_limit), "close": self._to_number(r.close)}
                for r in large.itertuples()
            ],
            "book_events": [
                {"code": r.ts_code, "name": r.name, "ann_date": r.ann_date, "proc": r.proc,
                 "amount_yi": self._to_yi(r.amount)}
                for r in mine.itertuples()
            ],
        }  # fmt: skip

    def write(self, out_dir: Path, as_of: str, book: list[str]) -> Path:
        """
        Purpose:
            Build and write `buybacks.json`.

        Contract:
            Input:
                out_dir: Path (existing); as_of: str; book: list[str]
            Output:
                Path  -- the written file
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"buyback events output directory missing: {out_dir}")
        doc = self.build(as_of, book)
        path = out_dir / FILE_NAME
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("buyback events: %d large plans -> %s", len(doc["large_plans"]), path)
        return path

    @staticmethod
    def _to_number(v: Any) -> float | None:
        return None if v is None or pd.isna(v) else round(float(v), 2)

    @staticmethod
    def _to_yi(v: Any) -> float | None:
        return None if v is None or pd.isna(v) else round(float(v) / 1e8, 2)
