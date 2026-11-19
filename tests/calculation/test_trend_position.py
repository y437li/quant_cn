"""Contract tests for calculation.TrendPosition (plan 24 rule, used by plan 27)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.calculation.trend_position import TrendPosition

IDX = pd.bdate_range("2026-01-01", periods=40)


def test_tc_tp_001_blend_counts_windows() -> None:
    """TC-TP-001"""
    p = pd.DataFrame({"a": np.r_[np.arange(30, 0, -1.0), np.arange(1.0, 11.0)]}, index=IDX)
    blend = TrendPosition([2, 20], None, 5).compute_blend(p)["a"]
    assert blend.iloc[:20].isna().all()
    assert blend.iloc[25] == pytest.approx(0.0)  # falling: below 2 and 20 sessions ago
    assert blend.iloc[-1] == pytest.approx(0.5)  # up on 2 sessions, still below 20 sessions ago


def test_tc_tp_002_size_caps_and_scales() -> None:
    """TC-TP-002"""
    rng = np.random.default_rng(1)
    calm = 100 * np.cumprod(1 + 0.001 + 0.001 * rng.standard_normal(40))
    r = 0.02 * np.where(np.arange(40) % 2 == 0, 1.0, -1.0) + 0.0005
    wild = 100 * np.cumprod(1 + r)
    p = pd.DataFrame({"calm": calm, "wild": wild}, index=IDX)
    tp = TrendPosition([1], 0.20, 10)
    pos, blend = tp.compute_position(p), tp.compute_blend(p)
    assert pos["calm"].iloc[-1] == pytest.approx(blend["calm"].iloc[-1])
    vol = p["wild"].pct_change().iloc[-10:].std() * np.sqrt(252)
    assert pos["wild"].iloc[-1] == pytest.approx(blend["wild"].iloc[-1] * min(1.0, 0.2 / vol))


def test_tc_tp_003_no_sizing_and_describe() -> None:
    """TC-TP-003"""
    p = pd.Series(np.arange(1.0, 41.0), index=IDX)
    tp = TrendPosition([5, 10], None, 5)
    assert tp.compute_position(p.to_frame("x"))["x"].iloc[-1] == pytest.approx(1.0)
    d = tp.build_summary(p)
    assert [w["n"] for w in d["windows"]] == [5, 10] and all(w["up"] for w in d["windows"])
    assert d["blend"] == 1.0 and d["size"] == 1.0 and d["position"] == 1.0


@pytest.mark.parametrize(
    ("windows", "target", "vol"), [([], 0.2, 5), ([0], 0.2, 5), ([5], 0.0, 5), ([5], 0.2, 1)]
)
def test_tc_tp_004_bad_arguments(windows: list[int], target: float, vol: int) -> None:
    """TC-TP-004"""
    with pytest.raises(ValueError):
        TrendPosition(windows, target, vol)
