"""Contract tests for portfolio.PositionReviewer (plan 15 ph7f)."""

from __future__ import annotations

from typing import Any, cast

import pandas as pd

from quant_cn.core.positions_book import PositionsBook
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.lake.fundamental_signal_reader import FundamentalSignalReader
from quant_cn.portfolio.condition_evaluator import ConditionEvaluator
from quant_cn.portfolio.position_reviewer import PositionReviewer

AS_OF = "20261112"


class FakeChips:
    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        return pd.DataFrame(
            {"holders_chg_q": 0.05, "lg_weeks_pos_4w": 1.0}, index=pd.Index(codes, name="ts_code")
        )


class FakeFundamentals:
    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        return pd.DataFrame(
            {"period": "20260930", "gm_q": 0.21}, index=pd.Index(codes, name="ts_code")
        )

    def read_series(self, ids: list[str], as_of: str) -> dict[str, float]:
        return {}


def _build_book(**rules: Any) -> PositionsBook:
    note = {
        "thesis": "t",
        "stop": 10.0,
        "target": 20.0,
        "reviewed": "20261101",
        "conditions": [
            {"label": "GM", "kind": "statement", "metric": "gm_q", "op": ">=", "value": 0.22}
        ],
    }
    return PositionsBook(
        cash=0,
        positions=[{"code": c, "shares": 100, "cost": 10} for c in ("A", "B", "C")],  # type: ignore[list-item]
        notes={"A": note, "B": note | {"reviewed": ""}},  # type: ignore[dict-item]
        rules={"max_weight": 0.2, "weight_exceptions": ["B"], "review_every_days": 30, **rules},  # type: ignore[arg-type]
    )


def _build_review(
    book: PositionsBook, closes: dict[str, float], weights: dict[str, float], as_of: str = AS_OF
) -> dict[str, Any]:
    evaluator = ConditionEvaluator(
        cast(ChipStructureReader, FakeChips()), cast(FundamentalSignalReader, FakeFundamentals())
    )
    held = pd.DataFrame(
        {
            "code": list(closes),
            "close": list(closes.values()),
            "weight": [weights[c] for c in closes],
        }
    )
    return PositionReviewer(book, evaluator).build(held, as_of)


def _list_kinds(review: dict[str, Any], code: str) -> list[str]:
    return [f["kind"] for f in review[code]["flags"]]


def test_tc_prv_001_stop_target_edges() -> None:
    """TC-PRV-001"""
    book = _build_book()
    assert _list_kinds(_build_review(book, {"A": 10.0}, {"A": 0.1}), "A") == ["stop"]
    assert _list_kinds(_build_review(book, {"A": 10.01}, {"A": 0.1}), "A") == []
    assert _list_kinds(_build_review(book, {"A": 20.0}, {"A": 0.1}), "A") == ["target"]
    assert _list_kinds(_build_review(book, {"A": 19.99}, {"A": 0.1}), "A") == []


def test_tc_prv_002_weight_review_and_missing_note() -> None:
    """TC-PRV-002"""
    book = _build_book()
    out = _build_review(book, {"A": 15.0, "B": 15.0, "C": 15.0}, {"A": 0.21, "B": 0.3, "C": 0.2})
    assert _list_kinds(out, "A") == ["weight"]
    assert _list_kinds(out, "B") == ["review"]  # excepted from the cap, never reviewed
    assert _list_kinds(out, "C") == ["note"] and out["C"]["note"] is None
    late = _build_review(book, {"A": 15.0}, {"A": 0.1}, as_of="20261202")
    assert late["A"]["flags"][0]["message"] == "笔记 31 天未复盘"
    assert _list_kinds(_build_review(book, {"A": 15.0}, {"A": 0.1}, as_of="20261201"), "A") == []


def test_tc_prv_003_chips_and_conditions() -> None:
    """TC-PRV-003"""
    out = _build_review(_build_book(), {"A": 15.0}, {"A": 0.1})["A"]
    assert out["chips"]["holders_chg_q"] == 0.05 and out["period"] == "20260930"
    assert out["chips"]["retail_gauge"] is None
    assert [(c["label"], c["state"], c["actual"]) for c in out["conditions"]] == [
        ("GM", "unmet", 0.21)
    ]
    assert out["note"]["stop"] == 10.0 and out["note"]["thesis"] == "t"
