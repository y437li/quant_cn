"""Per-position note, chip row, flags and conditions for the holdings page (plan 15 ph7f)."""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

import pandas as pd

from quant_cn.core.positions_book import PositionNote, PositionsBook
from quant_cn.lake.chip_structure_reader import GAUGE_EXTRA
from quant_cn.portfolio.condition_evaluator import ConditionEvaluator

CHIP_KEYS = (
    "holders_chg_q",
    "retail_gauge",
    "winner_rate",
    "inst_top10_dq_pp",
    "north_chg_pp",
    "margin_chg_60d",
    "lg_weeks_pos_4w",
    "lg_net_4w",
    "sm_net_4w",
    "unlock_6m_pct",
    "insider_sell_6m_pct",
    "gm_q",
    "dedt_yoy_q",
    "ocf_to_np",
    "shareholder_yield",
    "buyback_plan_pct",
    *GAUGE_EXTRA,
)
NOTE_KEYS = ("thesis", "falsifier", "stop", "target", "action", "watch", "reviewed")


class PositionReviewer:
    """
    Purpose:
        For every held stock: its note, its 筹码结构 / statement row, its condition results and
        flags the user must see — close at or below the stop, at or above the target, weight
        above the book's cap (unless excepted), note never reviewed or older than the review
        interval, and a position without a note (the before-buy checklist was skipped).

    Contract:
        Input:
            book:      PositionsBook       -- notes and rules
            evaluator: ConditionEvaluator  -- metrics and condition results
        Output:
            instance; `build(held, as_of) -> dict[str, dict]` keyed by ts_code
        Raises:
            (none at construction)

    Used by:
        portfolio.HoldingsRiskBuilder  -- `reviews` of holdings_risk.json
        cli.AppServiceBuilder  -- wires it

    Test cases:
        TC-PRV-001  stop and target flags at the boundary and not one tick inside
        TC-PRV-002  weight flag above max_weight unless excepted; review flag after the
                     interval or when never reviewed; a position without a note is flagged
        TC-PRV-003  chips and conditions come from the evaluator's metrics row
    """

    def __init__(self, book: PositionsBook, evaluator: ConditionEvaluator) -> None:
        self._book = book
        self._evaluator = evaluator

    def build(self, held: pd.DataFrame, as_of: str) -> dict[str, dict[str, Any]]:
        """
        Purpose:
            One review per held stock.

        Contract:
            Input:
                held:  DataFrame  -- columns code, close, weight (weight of the whole book)
                as_of: str        -- YYYYMMDD session of the closes
            Output:
                dict  -- ts_code -> {note: {..} | None, flags: [{kind, message}],
                         chips: {CHIP_KEYS: float | None}, period: latest statement end_date
                         | None, conditions: [ConditionResult records]}
            Raises:
                LakeError  -- a metrics query fails
        """
        closes = dict(zip(held["code"], held["close"], strict=True))
        notes = self._book.notes
        series = [c.metric for n in notes.values() for c in n.conditions if c.kind == "series"]
        metrics = self._evaluator.read_metrics(closes, as_of, series)
        out = {}
        for code, close, weight in zip(held["code"], held["close"], held["weight"], strict=True):
            note = notes.get(code)
            row = metrics.loc[code].to_dict() if code in metrics.index else {}
            results = self._evaluator.compute_results(note.conditions if note else [], row)
            out[code] = {
                "note": note.model_dump(include=set(NOTE_KEYS)) if note else None,
                "flags": self._build_flags(code, note, close, weight, as_of),
                "chips": {k: self._to_number(row.get(k)) for k in CHIP_KEYS},
                "period": row.get("period") if isinstance(row.get("period"), str) else None,
                "conditions": [r.to_record() for r in results],
            }
        return out

    def _build_flags(
        self, code: str, note: PositionNote | None, close: float, weight: float, as_of: str
    ) -> list[dict[str, str]]:
        rules, flags = self._book.rules, []
        if note is None:
            items = ", ".join(rules.before_buy) or "thesis, falsifier, stop"
            return [{"kind": "note", "message": f"缺少持仓笔记; 买前清单: {items}"}]
        if note.stop is not None and close <= note.stop:
            flags.append({"kind": "stop", "message": f"收盘 {close:.2f} ≤ 止损 {note.stop:.2f}"})
        if note.target is not None and close >= note.target:
            flags.append(
                {"kind": "target", "message": f"收盘 {close:.2f} ≥ 目标 {note.target:.2f}"}
            )
        if weight > rules.max_weight and code not in rules.weight_exceptions:
            msg = f"仓位 {weight:.1%} > 上限 {rules.max_weight:.0%}"
            flags.append({"kind": "weight", "message": msg})
        age = self._compute_age(note.reviewed, as_of)
        if age is None or age > rules.review_every_days:
            msg = "笔记从未复盘" if age is None else f"笔记 {age} 天未复盘"
            flags.append({"kind": "review", "message": msg})
        return flags

    @staticmethod
    def _compute_age(reviewed: str, as_of: str) -> int | None:
        if not reviewed:
            return None
        start = dt.datetime.strptime(reviewed, "%Y%m%d")
        return (dt.datetime.strptime(as_of, "%Y%m%d") - start).days

    @staticmethod
    def _to_number(value: object) -> float | None:
        if not isinstance(value, int | float):
            return None
        return None if math.isnan(value) or math.isinf(value) else round(float(value), 6)
