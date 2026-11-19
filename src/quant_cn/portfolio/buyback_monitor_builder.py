"""Market-wide buyback and 增持 monitor document for the app (plan 32 ph3, D-169)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.buyback_ledger import BuybackLedger
from quant_cn.lake.label_store import LabelStore
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.buyback_plan_frame import START, BuybackPlanFrame

logger = logging.getLogger(__name__)

FILE_NAME = "buyback_monitor.json"
LABEL_SET = "buyback_terms"
LOAN = "专项贷款"
YI = 1e8
_RESTRICTED = """
SELECT DISTINCT sec_code, ann_date FROM curated.cninfo_keyword_announcements
WHERE title LIKE '%限制性%' AND ann_date >= ? AND ann_date <= ?
"""
_TRADES = """
SELECT DISTINCT h.ts_code, h.ann_date, h.holder_name, h.change_vol, h.avg_price, d.close
FROM curated.stk_holdertrade h
LEFT JOIN curated.daily d ON d.ts_code = h.ts_code AND d.trade_date = h.ann_date
WHERE h.in_de = 'IN' AND h.ann_date >= ? AND h.ann_date <= ?
"""
_MV = """
SELECT b.ts_code, b.total_mv, b.close, s.name FROM curated.daily_basic b
LEFT JOIN curated.stock_basic s USING (ts_code)
WHERE b.trade_date = (SELECT max(trade_date) FROM curated.daily_basic WHERE trade_date <= ?)
"""


class BuybackMonitorBuilder:
    """
    Purpose:
        The market-wide buyback and 增持 document, the two kinds kept apart. Per kind: the live
        programmes (open), each with planned low / high, executed, % done (executed ÷ low, else
        high), price cap vs close, % of market cap and its labels; the window's events (new,
        completed = executed first reached the low, stopped / expired / ended); totals over the
        live ones (all, by purpose or holder type, by funding, the 专项贷款 sum); and per month
        of announcement since START the count, high amount and loans. A programme with several
        purposes counts once under each, so `all` is the only total that sums the rows; a row
        with one bound counts it as both its low and its high in totals.

    Contract:
        Input:
            query:  LakeQuery       -- repurchase listing titles, stk_holdertrade, daily,
                                       daily_basic, stock_basic
            ledger: BuybackLedger   -- 回购 programmes, point in time
            labels: LabelStore      -- label set buyback_terms
            frame:  BuybackPlanFrame
            days:   int > 0         -- event window in calendar days (default 7)
        Output:
            instance; `build(as_of)` -> dict, `compute_section(rows, mv, as_of, start)` (pure),
            `write(out_dir, as_of)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `buyback-events` writes it beside buybacks.json

    Test cases:
        TC-BMB-001  section: live rows only open, % done and cap gap; events new / completed /
                    stopped / ended in the window only; totals.all equals the sum of live rows;
                    loan sum; a one-bound row counts in both total bounds; months count every
                    programme
        TC-BMB-002  build on hand frames keeps the kinds apart and nothing after as_of; write
                    puts buyback_monitor.json in the directory; a missing directory raises
    """

    def __init__(
        self,
        query: LakeQuery,
        ledger: BuybackLedger,
        labels: LabelStore,
        frame: BuybackPlanFrame,
        days: int = 7,
    ) -> None:
        self._query, self._ledger, self._labels, self._frame = query, ledger, labels, frame
        self._days = days

    def build(self, as_of: str) -> dict[str, Any]:
        """
        Purpose:
            The monitor document on as_of from the lake.

        Contract:
            Input:
                as_of: str (YYYYMMDD)
            Output:
                dict  -- {as_of, days, start, buyback: section, increase: section}
            Raises:
                LakeError  -- a query fails
        """
        start = self._compute_start(as_of)
        rows = self._ledger.read_rows(as_of)
        progs = self._ledger.build_programmes(rows, as_of)
        before = self._ledger.build_programmes(rows, start)
        items = self._frame.build_items(self._labels.read(LABEL_SET, None, as_of), as_of)
        restricted = self._query.sql(_RESTRICTED, ["20231201", as_of])
        trades = self._query.sql(_TRADES, [START, as_of])
        mv = self._query.sql(_MV, [as_of]).set_index("ts_code")
        bb = self._frame.build_buybacks(progs, before, items, restricted)
        inc = self._frame.build_increases(items, trades, as_of, start)
        return {
            "as_of": as_of, "days": self._days, "start": START,
            "buyback": self.compute_section(bb, mv, as_of, start),
            "increase": self.compute_section(inc, mv, as_of, start),
        }  # fmt: skip

    def compute_section(
        self, rows: pd.DataFrame, mv: pd.DataFrame, as_of: str, start: str
    ) -> dict[str, Any]:
        """
        Purpose:
            One kind's part of the document.

        Contract:
            Input:
                rows: BuybackPlanFrame rows of one kind; mv: index ts_code, total_mv (万元),
                close, name; as_of, start: str (YYYYMMDD; events are after start up to as_of)
            Output:
                dict  -- {live: [row], events: [row + event], totals: {all, by_tag,
                          by_funding, loan}, months: [{month, count, high_yi, loan_count,
                          loan_yi}]}
            Raises:
                (none)
        """
        live = rows[rows["state"] == "open"]
        events = []
        for r in rows.itertuples():
            ev = self._compute_event(r, as_of, start)
            if ev:
                events.append(self._build_row(r, mv) | {"event": ev})
        events.sort(key=lambda e: e["date"], reverse=True)
        return {
            "live": sorted((self._build_row(r, mv) for r in live.itertuples()),
                           key=lambda x: -(x["high_yi"] or 0.0)),
            "events": events,
            "totals": self._compute_totals(live),
            "months": self._compute_months(rows),
        }  # fmt: skip

    def write(self, out_dir: Path, as_of: str) -> Path:
        """
        Purpose:
            Build and write buyback_monitor.json.

        Contract:
            Input:
                out_dir: Path (existing); as_of: str (YYYYMMDD)
            Output:
                Path  -- the written file
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"buyback monitor output directory missing: {out_dir}")
        doc = self.build(as_of)
        path = out_dir / FILE_NAME
        path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), "utf-8")
        logger.info("buyback monitor: %d / %d live -> %s", len(doc["buyback"]["live"]),
                    len(doc["increase"]["live"]), path)  # fmt: skip
        return path

    def _compute_start(self, as_of: str) -> str:
        return (pd.Timestamp(as_of) - pd.Timedelta(days=self._days)).strftime("%Y%m%d")

    @staticmethod
    def _compute_event(r: Any, as_of: str, start: str) -> str | None:
        if start < r.date <= as_of:
            return "new"
        target = BuybackMonitorBuilder._compute_target(r)
        if target and r.executed >= target > r.executed_before:
            return "completed"
        if r.state in ("stopped", "expired", "ended") and start < r.end <= as_of:
            return str(r.state)
        return None

    @staticmethod
    def _build_row(r: Any, mv: pd.DataFrame) -> dict[str, Any]:
        m = mv.loc[r.code] if r.code in mv.index else None
        close = None if m is None or pd.isna(m["close"]) else float(m["close"])
        cap_mv = None if m is None or pd.isna(m["total_mv"]) else float(m["total_mv"]) * 1e4
        target = BuybackMonitorBuilder._compute_target(r)
        row = {
            "code": r.code, "name": None if m is None else m["name"], "date": r.date,
            "end": r.end, "state": r.state, "tags": r.tags, "holders": r.holders,
            "funding": r.funding, "loan_bank": r.loan_bank,
            "loan_yi": BuybackMonitorBuilder._to_yi(r.loan_amount),
            "low_yi": BuybackMonitorBuilder._to_yi(r.low),
            "high_yi": BuybackMonitorBuilder._to_yi(r.high),
            "executed_yi": BuybackMonitorBuilder._to_yi(r.executed),
            "done_pct": round(r.executed / target, 4) if target else None,
            "price_cap": r.price_cap, "close": close,
            "cap_gap": round(close / r.price_cap - 1, 4) if close and r.price_cap else None,
            "mv_pct": round(r.high / cap_mv, 5) if r.high and cap_mv else None,
            "labelled": bool(r.labelled),
        }  # fmt: skip
        return {k: None if isinstance(v, float) and pd.isna(v) else v for k, v in row.items()}

    @staticmethod
    def _compute_target(r: Any) -> float | None:
        for v in (r.low, r.high):
            if v is not None and not pd.isna(v) and v > 0:
                return float(v)
        return None

    @staticmethod
    def _compute_totals(live: pd.DataFrame) -> dict[str, Any]:
        def total(sub: pd.DataFrame) -> dict[str, Any]:
            return {"count": len(sub),
                    "low_yi": round(float(sub["low"].fillna(sub["high"]).fillna(0).sum()) / YI, 2),
                    "high_yi": round(float(sub["high"].fillna(sub["low"]).fillna(0).sum()) / YI, 2),
                    "executed_yi": round(float(sub["executed"].sum()) / YI, 2)}  # fmt: skip

        def group(col: str) -> list[dict[str, Any]]:
            keys = sorted({k for v in live[col] for k in v})
            parts = [{"label": k} | total(live.loc[BuybackMonitorBuilder._has(live[col], k)])
                     for k in keys]  # fmt: skip
            return sorted(parts, key=lambda p: -p["count"])

        loans = live.loc[BuybackMonitorBuilder._has(live["funding"], LOAN)]
        return {
            "all": total(live), "by_tag": group("tags"), "by_funding": group("funding"),
            "loan": {"count": len(loans),
                     "loan_yi": round(float(loans["loan_amount"].fillna(0).sum()) / YI, 2)},
        }  # fmt: skip

    @staticmethod
    def _compute_months(rows: pd.DataFrame) -> list[dict[str, Any]]:
        out = []
        for month, g in rows.groupby(rows["date"].str[:6]):
            loans = g.loc[BuybackMonitorBuilder._has(g["funding"], LOAN)]
            loan_yi = round(float(loans["loan_amount"].fillna(0).sum()) / YI, 2)
            out.append({"month": month, "count": len(g),
                        "high_yi": round(float(g["high"].fillna(0).sum()) / YI, 2),
                        "loan_count": len(loans), "loan_yi": loan_yi})  # fmt: skip
        return out

    @staticmethod
    def _has(lists: pd.Series, key: str) -> pd.Series:
        return pd.Series([key in v for v in lists], index=lists.index, dtype=bool)

    @staticmethod
    def _to_yi(v: Any) -> float | None:
        return None if v is None or pd.isna(v) else round(float(v) / YI, 4)
