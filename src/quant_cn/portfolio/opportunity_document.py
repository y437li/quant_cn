"""opportunities.json for the app's #opportunities page and the morning report (plan 21 ph5)."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.core.opportunity_settings import OpportunitySettings

logger = logging.getLogger(__name__)

FILE_NAME = "opportunities.json"
BIG = 1e15  # larger whole numbers stay floats
ROW_FIELDS = (
    "rank", "status", "pct", "exp_change", "lo_streak", "circ_mv", "lg_weeks_pos_4w",
    "lg_net_4w", "sm_weeks_neg_4w", "sm_net_4w", "margin_chg_60d", "winner_rate",
    "cost_lo_gap", "cost_hi_gap", "period", "np_yoy", "np_qoq", "val_value", "val_median",
    "fit_styles", "fit_delta",
)  # fmt: skip


class OpportunityDocument:
    """
    Purpose:
        Turn one session's opportunity list (OpportunityScreen.build) and the previous stored
        list into the app document: listed names that are new first, then listed names that
        stayed, then near-misses (each with the rules hit and the missing one), and the names
        that dropped off since the previous list; the rule thresholds for the page's legend.

    Contract:
        Input:
            settings: OpportunitySettings
        Output:
            instance; `build(frame, previous, as_of) -> dict`; `write(doc, out_dir) -> Path`
        Raises:
            (none at construction)

    Used by:
        cli.GaugeCommands  -- `opportunity-list --out`

    Test cases:
        TC-OPD-001  order new listed, stayed listed, near; rules split into lists; NaN -> None;
                    dropped = previous codes not on today's list; empty list -> rows []
        TC-OPD-002  write puts opportunities.json in the directory; a missing directory raises
                    LakeError
    """

    def __init__(self, settings: OpportunitySettings) -> None:
        self._settings = settings

    def build(self, frame: pd.DataFrame, previous: pd.DataFrame, as_of: str) -> dict[str, Any]:
        """
        Purpose:
            The document (see the class contract).

        Contract:
            Input:
                frame: DataFrame     -- OpportunityScreen.build output (may be empty)
                previous: DataFrame  -- OpportunityScreen.read_previous output (may be empty)
                as_of: str           -- the session asked for (used when frame is empty)
            Output:
                dict  -- {as_of, previous_as_of, rules: {...}, rows: [{code, name, is_new,
                         rules_hit: [str], missing: [str], ROW_FIELDS...}], dropped: [{code,
                         name, status}]}; fractions as shares; numbers None when unknown
            Raises:
                (none)
        """
        s = self._settings
        rows = []
        if not frame.empty:
            listed = frame["status"] == "listed"
            group = (~listed) * 2 + (listed & ~frame["is_new"].astype(bool)) * 1
            order = frame.assign(k=group).sort_values(["k", "rank"])
            rows = [
                self._build_row({str(k): v for k, v in r.items()}) for r in order.to_dict("records")
            ]
        today = set(frame["ts_code"]) if not frame.empty else set()
        dropped = [
            {"code": r["ts_code"], "name": r.get("name"), "status": r.get("status")}
            for r in previous.to_dict("records")
            if r["ts_code"] not in today
        ]
        return {
            "as_of": str(frame["as_of"].iloc[0]) if not frame.empty else as_of,
            "previous_as_of": str(previous["as_of"].iloc[0]) if not previous.empty else None,
            "rules": {
                "min_circ_mv": s.min_circ_mv,
                "inflow_weeks": s.inflow_weeks,
                "np_yoy_min": s.np_yoy_min,
                "np_qoq_min": s.np_qoq_min,
                "valuation_field": s.valuation_field,
                "valuation_years": s.valuation_years,
                "fit_weight": s.fit_weight,
                "fit_styles": s.fit_styles,
                "top_n": s.top_n,
                "near_n": s.near_n,
            },
            "rows": rows,
            "dropped": dropped,
        }

    def write(self, doc: dict[str, Any], out_dir: Path) -> Path:
        """
        Purpose:
            Write the document as opportunities.json.

        Contract:
            Input:
                doc: dict  -- `build` output; out_dir: Path (the app's data directory)
            Output:
                Path  -- the file written
            Raises:
                LakeError  -- out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"opportunity output directory missing: {out_dir}")
        path = out_dir / FILE_NAME
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("opportunities %s: %d rows -> %s", doc["as_of"], len(doc["rows"]), path)
        return path

    def _build_row(self, r: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {
            "code": r["ts_code"],
            "name": r.get("name"),
            "is_new": bool(r["is_new"]),
            "rules_hit": [x for x in str(r.get("rules_hit") or "").split(",") if x],
            "missing": [x for x in str(r.get("missing") or "").split(",") if x],
        }
        for key in ROW_FIELDS:
            out[key] = self._to_value(r.get(key))
        return out

    @staticmethod
    def _to_value(value: object) -> object:
        if value is None or isinstance(value, str | bool):
            return value
        if not isinstance(value, int | float | np.number):
            return None
        number = float(value)
        if math.isnan(number):
            return None
        return int(number) if number.is_integer() and abs(number) < BIG else round(number, 6)
