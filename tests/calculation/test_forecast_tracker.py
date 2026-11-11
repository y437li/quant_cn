"""Contract tests for calculation.ForecastTracker (plan 18 phase 1, D-124)."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
import pytest

from quant_cn.calculation.forecast_tracker import (
    ACTUAL_COLUMNS,
    EXPRESS_COLUMNS,
    FORECAST_COLUMNS,
    OUTCOME_COLUMNS,
    PROFIT_FIELD,
    TRACK_COLUMNS,
    ForecastTracker,
)
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.guidance_settings import GuidanceSettings

H1 = "20260630"
AS_OF = "20261101"
NAN = float("nan")


def _build_tracker(**settings: Any) -> ForecastTracker:
    return ForecastTracker(DateCodec(), GuidanceSettings(**settings))


def _build_forecast(code: str, ann: str, lo: float, hi: float, **extra: Any) -> dict[str, Any]:
    row = dict.fromkeys(FORECAST_COLUMNS, NAN)
    row |= {"ts_code": code, "ann_date": ann, "end_date": H1, "type": "预增", "update_flag": "1"}
    return row | {"net_profit_min": lo, "net_profit_max": hi} | extra


def _build_actual(
    code: str, value: float, known_on: str = "20260820", end: str = H1
) -> dict[str, Any]:
    return {"ts_code": code, "end_date": end, "field": PROFIT_FIELD, "value": value,
            "known_on": known_on}  # fmt: skip


def _build_frames(
    forecasts: list[dict[str, Any]],
    actuals: list[dict[str, Any]],
    express: list[dict[str, Any]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Text columns as pandas `string`, as the lake readers return them (comparisons give <NA>)."""
    text = {"ts_code", "ann_date", "end_date", "type", "update_flag", "field", "known_on"}

    def build(rows: list[dict[str, Any]], columns: list[str]) -> pd.DataFrame:
        frame = pd.DataFrame(rows, columns=columns)
        for col in text & set(columns):
            frame[col] = frame[col].astype("string")
        return frame

    return (
        build(forecasts, FORECAST_COLUMNS),
        build(actuals, ACTUAL_COLUMNS),
        build(express or [], EXPRESS_COLUMNS),
    )


def _find_row(out: pd.DataFrame, code: str, ann: str | None = None) -> pd.Series:
    hit = out[out["ts_code"] == code]
    if ann is not None:
        hit = hit[hit["ann_date"] == ann]
    assert len(hit) == 1
    return hit.iloc[0]


# TC-FT-001
def test_tc_ft_001_range_and_outcome() -> None:
    forecasts = [
        _build_forecast("A", "20260710", 800.0, 1000.0),
        _build_forecast("B", "20260710", 1000.0, 800.0),  # bounds given in reverse order
        _build_forecast("C", "20260710", 800.0, 1000.0),
    ]
    actuals = [_build_actual("A", 9e6), _build_actual("B", 1.2e7), _build_actual("C", 7e6)]
    out = _build_tracker().build(*_build_frames(forecasts, actuals), AS_OF)
    assert list(out.columns) == OUTCOME_COLUMNS
    a, b, c = _find_row(out, "A"), _find_row(out, "B"), _find_row(out, "C")
    assert (a["low"], a["high"], a["mid"]) == (
        pytest.approx(8e6),
        pytest.approx(1e7),
        pytest.approx(9e6),
    )
    assert (a["outcome"], a["position"], a["surprise"]) == (
        "in",
        pytest.approx(0.5),
        pytest.approx(0.0),
    )
    assert b["low"] == pytest.approx(8e6) and b["outcome"] == "above"
    assert b["surprise"] == pytest.approx(3 / 9) and b["position"] == pytest.approx(2.0)
    assert c["outcome"] == "below" and c["surprise"] == pytest.approx(-2 / 9)
    assert a["actual_known_on"] == "20260820"


# TC-FT-002
def test_tc_ft_002_range_from_change_and_no_range() -> None:
    from_change = {"p_change_min": 10.0, "p_change_max": 30.0, "last_parent_net": 100.0}
    negative_base = {"p_change_min": 10.0, "p_change_max": 30.0, "last_parent_net": -100.0}
    forecasts = [
        _build_forecast("D", "20260710", NAN, NAN, **from_change),
        _build_forecast("E", "20260710", NAN, NAN),
        _build_forecast("F", "20260710", NAN, NAN, **negative_base),
    ]
    actuals = [_build_actual(c, 1.2e6) for c in "DEF"]
    out = _build_tracker().build(*_build_frames(forecasts, actuals), AS_OF)
    d = _find_row(out, "D")
    assert (d["low"], d["high"], d["outcome"]) == (pytest.approx(1.1e6), pytest.approx(1.3e6), "in")
    assert _find_row(out, "E")["outcome"] == "no_range"
    assert _find_row(out, "F")["outcome"] == "no_range"


# TC-FT-003
def test_tc_ft_003_one_sided_ranges() -> None:
    forecasts = [
        _build_forecast("F1", "20260710", 500.0, NAN),
        _build_forecast("F2", "20260710", 500.0, NAN),
        _build_forecast("C1", "20260710", NAN, 500.0),
        _build_forecast("C2", "20260710", NAN, 500.0),
    ]
    actuals = [
        _build_actual("F1", 6e6),
        _build_actual("F2", 4e6),
        _build_actual("C1", 4e6),
        _build_actual("C2", 6e6),
    ]
    out = _build_tracker().build(*_build_frames(forecasts, actuals), AS_OF)
    assert [_find_row(out, c)["outcome"] for c in ("F1", "F2", "C1", "C2")] == [
        "in", "below", "in", "above",
    ]  # fmt: skip
    f1 = _find_row(out, "F1")
    assert math.isnan(f1["high"]) and math.isnan(f1["mid"])
    assert math.isnan(f1["position"]) and math.isnan(f1["surprise"])


# TC-FT-004
def test_tc_ft_004_revisions() -> None:
    forecasts = [
        _build_forecast("H", "20260710", 800.0, 1000.0),
        _build_forecast("H", "20260801", 900.0, 1100.0, update_flag="0"),
        _build_forecast("H", "20260801", 1000.0, 1200.0, update_flag="1"),
        _build_forecast("H", "20260805", 1000.0, 1200.0),
    ]
    out = _build_tracker().build(*_build_frames(forecasts, [_build_actual("H", 1.1e7)]), AS_OF)
    assert list(out["ann_date"]) == ["20260710", "20260801", "20260805"]
    assert list(out["version"]) == [1, 2, 3] and set(out["n_versions"]) == {3}
    assert list(out["is_last"]) == [False, False, True]
    assert _find_row(out, "H", "20260801")["mid"] == pytest.approx(1.1e7)  # flag 1 kept
    assert pd.isna(out["revision"].iloc[0]) and list(out["revision"].iloc[1:]) == ["up", "none"]


# TC-FT-005
def test_tc_ft_005_point_in_time() -> None:
    forecasts = [
        _build_forecast("P", "20260710", 800.0, 1000.0),
        _build_forecast("P", "20260901", 850.0, 950.0),  # announced after the actual
        _build_forecast("Q", "20261201", 800.0, 1000.0),  # announced after as_of
    ]
    frames = _build_frames(forecasts, [_build_actual("P", 9e6, known_on="20260820")])
    early = _build_tracker().build(*frames, "20260815")
    assert list(early["outcome"]) == ["pending"] and "Q" not in set(early["ts_code"])
    late = _build_tracker().build(*frames, AS_OF)
    assert list(late["outcome"]) == ["in", "after_actual"]
    assert "Q" not in set(late["ts_code"])


# TC-FT-006
def test_tc_ft_006_express_and_history_start() -> None:
    old = _build_forecast("A", "20180110", 800.0, 1000.0) | {"end_date": "20171231"}
    flash = {"ts_code": "A", "end_date": H1, "update_flag": "1"}
    express = [
        flash | {"ann_date": "20260720", "n_income": 9.1e6},
        flash | {"ann_date": "20260725", "n_income": 9.2e6},
    ]
    forecasts = [_build_forecast("A", "20260710", 800.0, 1000.0), old]
    actuals = [_build_actual("A", 9e6), _build_actual("A", 9e6, "20180320", "20171231")]
    out = _build_tracker().build(*_build_frames(forecasts, actuals, express), AS_OF)
    assert list(out["end_date"]) == [H1]
    row = _find_row(out, "A")
    assert (row["express_profit"], row["express_known_on"]) == (pytest.approx(9.1e6), "20260720")
    before = _build_tracker().build(*_build_frames(forecasts, actuals, express), "20260715")
    assert pd.isna(_find_row(before, "A")["express_profit"])


def _build_outcome(
    code: str,
    end: str,
    version: int,
    is_last: bool,
    outcome: str,
    surprise: float,
    ex_ante: bool = False,
) -> dict[str, Any]:
    row = dict.fromkeys(OUTCOME_COLUMNS, NAN)
    return row | {"ts_code": code, "end_date": end, "ann_date": end, "version": version,
                  "is_last": is_last, "outcome": outcome, "surprise": surprise,
                  "ex_ante": ex_ante}  # fmt: skip


# TC-FT-007
def test_tc_ft_007_track_record() -> None:
    rows = [
        _build_outcome("A", "20230630", 1, True, "below", -0.5),  # before the 3-year window
        _build_outcome("A", "20240630", 1, False, "below", -0.2),
        _build_outcome("A", "20240630", 2, True, "in", 0.0),
        _build_outcome("A", "20250630", 1, True, "above", 0.2),
        _build_outcome("A", "20260630", 1, True, "in", 0.1),
        _build_outcome("A", "20260930", 1, True, "pending", NAN),  # not scored
        _build_outcome("B", "20260630", 1, True, "below", -0.4),
    ]
    out = _build_tracker().build_track_record(pd.DataFrame(rows, columns=OUTCOME_COLUMNS), AS_OF)
    assert list(out.columns) == TRACK_COLUMNS and list(out["ts_code"]) == ["A", "B"]
    a = out.iloc[0]
    assert a["n"] == 3 and a["hit_rate"] == pytest.approx(2 / 3)
    assert (a["above_rate"], a["below_rate"]) == (pytest.approx(1 / 3), pytest.approx(0.0))
    assert a["mean_surprise"] == pytest.approx(0.1) and a["median_abs_surprise"] == pytest.approx(
        0.1
    )
    assert a["first_hit_rate"] == pytest.approx(1 / 3)  # v1: below, above, in
    assert a["last_period"] == "20260630" and bool(a["sufficient"]) is True
    assert bool(out.iloc[1]["sufficient"]) is False


# TC-FT-008
def test_tc_ft_008_empty_and_errors() -> None:
    tracker = _build_tracker()
    out = tracker.build(*_build_frames([], []), AS_OF)
    assert out.empty and list(out.columns) == OUTCOME_COLUMNS
    record = tracker.build_track_record(out, AS_OF)
    assert record.empty and list(record.columns) == TRACK_COLUMNS
    with pytest.raises(ValueError):
        tracker.build(*_build_frames([], []), "2026-11-01")
    with pytest.raises(ValueError):
        tracker.build(pd.DataFrame({"ts_code": []}), *_build_frames([], [])[1:], AS_OF)
    with pytest.raises(ValueError):
        tracker.build_track_record(pd.DataFrame({"ts_code": []}), AS_OF)
    assert ForecastTracker.list_fields() == [PROFIT_FIELD]


# TC-FT-009
def test_tc_ft_009_days_after_end_and_ex_ante() -> None:
    forecasts = [
        _build_forecast("A", "20260620", 800.0, 1000.0),
        _build_forecast("A", "20260630", 800.0, 1000.0),
        _build_forecast("A", "20260715", 800.0, 1000.0),
    ]
    out = _build_tracker().build(*_build_frames(forecasts, [_build_actual("A", 9e6)]), AS_OF)
    assert list(out["days_after_end"]) == [-10, 0, 15]
    assert list(out["ex_ante"]) == [True, True, False]


# TC-FT-010
def test_tc_ft_010_ex_ante_record() -> None:
    rows = [
        _build_outcome("A", "20240630", 1, False, "below", -0.3, ex_ante=True),
        _build_outcome("A", "20240630", 2, False, "above", 0.2, ex_ante=True),  # last ex-ante
        _build_outcome("A", "20240630", 3, True, "in", 0.0),
        _build_outcome("A", "20250630", 1, True, "in", 0.1, ex_ante=True),
        _build_outcome("A", "20260630", 1, True, "in", 0.0),
        _build_outcome("B", "20260630", 1, True, "in", 0.0),
    ]
    out = _build_tracker().build_track_record(pd.DataFrame(rows, columns=OUTCOME_COLUMNS), AS_OF)
    a, b = out.iloc[0], out.iloc[1]
    assert a["n_ex_ante"] == 2 and a["ex_ante_hit_rate"] == pytest.approx(0.5)
    assert a["ex_ante_mean_surprise"] == pytest.approx(0.15)
    assert bool(a["ex_ante_sufficient"]) is False
    assert b["n_ex_ante"] == 0 and math.isnan(b["ex_ante_hit_rate"])
