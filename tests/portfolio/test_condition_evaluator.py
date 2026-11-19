"""Contract tests for portfolio.ConditionEvaluator (plan 15 ph7f)."""

from __future__ import annotations

import math
from typing import Any, cast

import pandas as pd

from quant_cn.core.condition import Condition
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.lake.fundamental_signal_reader import FundamentalSignalReader
from quant_cn.lake.margin_signal_reader import MarginSignalReader
from quant_cn.lake.shareholder_yield_reader import ShareholderYieldReader
from quant_cn.portfolio.condition_evaluator import ConditionEvaluator, ConditionResult


class FakeChips:
    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        return pd.DataFrame({"lg_weeks_pos_4w": [3.0]}, index=pd.Index(codes[:1], name="ts_code"))


class FakeFundamentals:
    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        return pd.DataFrame({"gm_q": [0.25]}, index=pd.Index(codes[:1], name="ts_code"))

    def read_series(self, ids: list[str], as_of: str) -> dict[str, float]:
        return {f"series:{i}": 7.0 for i in ids}


def _build_evaluator() -> ConditionEvaluator:
    chips = cast(ChipStructureReader, FakeChips())
    return ConditionEvaluator(chips, cast(FundamentalSignalReader, FakeFundamentals()))


def _build_condition(
    op: str, value: float, metric: str = "lg_weeks_pos_4w", kind: str = "flow"
) -> Condition:
    return Condition(label="c", kind=kind, metric=metric, op=op, value=value)  # type: ignore[arg-type]


def _build_result(state: str) -> ConditionResult:
    return ConditionResult("c", "flow", "m", ">=", 1.0, None, state)


def test_tc_ce_001_boundaries_and_unknown() -> None:
    """TC-CE-001"""
    ev = _build_evaluator()
    row: dict[str, Any] = {"lg_weeks_pos_4w": 3.0, "gm_q": math.nan}
    cases = [
        (">=", 3.0, "met"),
        (">=", 3.0001, "unmet"),
        ("<=", 3.0, "met"),
        ("<=", 2.9999, "unmet"),
        (">", 3.0, "unmet"),
        ("<", 3.0, "unmet"),
        ("==", 3.0, "met"),
    ]
    for op, value, state in cases:
        assert ev.compute_results([_build_condition(op, value)], row)[0].state == state, (op, value)
    gm = ev.compute_results([_build_condition(">=", 0.2, "gm_q", "statement")], row)[0]
    gone = ev.compute_results([_build_condition(">=", 0.0, "close", "price")], row)[0]
    assert (gm.state, gm.actual, gone.state) == ("unknown", None, "unknown")
    assert ev.compute_results([_build_condition(">=", 3.0)], row)[0].to_record()["actual"] == 3.0


def test_tc_ce_002_summarize() -> None:
    """TC-CE-002"""
    met, unmet, unknown = _build_result("met"), _build_result("unmet"), _build_result("unknown")
    assert ConditionEvaluator.compute_status([met, met], price_met=True) == "buy"
    assert ConditionEvaluator.compute_status([met, unknown], price_met=True) == "near"
    assert ConditionEvaluator.compute_status([met, met], price_met=False) == "wait"
    assert ConditionEvaluator.compute_status([met, met, unmet], True, needed=2) == "buy"
    assert ConditionEvaluator.compute_status([met, unknown, unmet], True, needed=2) == "near"
    assert ConditionEvaluator.compute_status([], price_met=True) == "buy"


def test_tc_ce_003_read_metrics() -> None:
    """TC-CE-003"""
    frame = _build_evaluator().read_metrics({"A": 10.0, "B": 5.0}, "20261112", ["tio2"])
    assert frame.loc["A", "close"] == 10.0 and frame.loc["A", "lg_weeks_pos_4w"] == 3.0
    assert math.isnan(frame.loc["B", "gm_q"]) and frame.loc["B", "series:tio2"] == 7.0


def test_tc_ce_004_heat() -> None:
    """TC-CE-004"""
    chips = cast(ChipStructureReader, FakeChips())
    evaluator = ConditionEvaluator(
        chips, cast(FundamentalSignalReader, FakeFundamentals()), {"bank_etf_z": 1.9}
    )
    frame = evaluator.read_metrics({"A": 10.0, "B": 5.0}, "20261112")
    assert frame["bank_etf_z"].tolist() == [1.9, 1.9]
    cond = _build_condition("<=", 0.5, "bank_etf_z", "heat")
    assert evaluator.compute_results([cond], frame.loc["A"])[0].state == "unmet"
    plain = _build_evaluator().read_metrics({"A": 10.0}, "20261112")
    assert _build_evaluator().compute_results([cond], plain.loc["A"])[0].state == "unknown"


def test_tc_ce_005_required() -> None:
    """TC-CE-005"""
    req = ConditionResult("g", "statement", "gm_q", ">=", 0.12, 0.09, "unmet", True)
    a, b = _build_result("met"), _build_result("unmet")
    assert ConditionEvaluator.compute_status([req, a, b], True, 1) == "near"
    ok = ConditionResult("g", "statement", "gm_q", ">=", 0.12, 0.13, "met", True)
    assert ConditionEvaluator.compute_status([ok, a, b], True, 1) == "buy"
    assert ConditionEvaluator.compute_status([ok, a, b], True, None) == "near"


class FakeMargin:
    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        return pd.DataFrame({"rz_chg_20d": [0.1]}, index=pd.Index(["A"], name="ts_code"))


def test_tc_ce_006_margin() -> None:
    """TC-CE-006"""
    chips = cast(ChipStructureReader, FakeChips())
    evaluator = ConditionEvaluator(
        chips,
        cast(FundamentalSignalReader, FakeFundamentals()),
        None,
        cast(MarginSignalReader, FakeMargin()),
    )
    frame = evaluator.read_metrics({"A": 10.0, "B": 5.0}, "20261112")
    assert frame.loc["A", "rz_chg_20d"] == 0.1 and math.isnan(frame.loc["B", "rz_chg_20d"])


class FakeCapital:
    def read_metrics(self, codes: list[str], as_of: str) -> pd.DataFrame:
        return pd.DataFrame({"buyback_plan_pct": [2.5]}, index=pd.Index(["A"], name="ts_code"))


def test_tc_ce_007_capital() -> None:
    """TC-CE-007"""
    evaluator = ConditionEvaluator(
        cast(ChipStructureReader, FakeChips()),
        cast(FundamentalSignalReader, FakeFundamentals()),
        capital=cast(ShareholderYieldReader, FakeCapital()),
    )
    frame = evaluator.read_metrics({"A": 10.0, "B": 5.0}, "20261112")
    assert frame.loc["A", "buyback_plan_pct"] == 2.5 and math.isnan(
        frame.loc["B", "buyback_plan_pct"]
    )


def test_tc_ce_008_gauge_needs_streak() -> None:
    """TC-CE-008"""
    ev = _build_evaluator()
    low = _build_condition("<=", 0.3, "retail_gauge", "retail")
    high = _build_condition(">=", 0.9, "retail_gauge", "retail")
    once = {"retail_gauge": 0.2, "gauge_leaving": 0.0}
    streak = {"retail_gauge": 0.2, "gauge_leaving": 1.0}
    assert ev.compute_results([low], once)[0].state == "unmet"
    assert ev.compute_results([low], streak)[0].state == "met"
    assert ev.compute_results([low], {"retail_gauge": 0.2})[0].state == "unmet"
    assert ev.compute_results([high], {"retail_gauge": 0.95})[0].state == "met"
