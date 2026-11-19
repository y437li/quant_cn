"""Contract tests for calculation.RetailGaugeEvaluator (plan 21 ph3, D-142, D-155)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.calculation.retail_gauge_evaluator import RetailGaugeEvaluator


# TC-RGE-001
def test_tc_rge_001_scores() -> None:
    codes = [f"{i:02d}" for i in range(10)]
    pct = [(i + 1) / 10 for i in range(10)]
    back = pd.DataFrame(
        {
            "ts_code": codes * 2,
            "q": ["q1"] * 10 + ["q2"] * 10,
            "as_of": ["d1"] * 10 + ["d2"] * 10,
            "y": pct + [float("nan")] * 10,
            "pct": pct + pct[::-1],
        }
    )
    fwd = pd.DataFrame({"ts_code": codes, "as_of": "d1", "fwd": [0.1] * 9 + [-0.2]})
    out = RetailGaugeEvaluator.compute_scores(back, fwd, 0.9).set_index("q")
    assert out.loc["q1", "ic"] == pytest.approx(1.0) and not out.loc["q1", "ic_low"]
    assert out.loc["q1", "hit_top"] == 1.0 and math.isnan(
        out.loc["q1", "hit_bottom"]
    )  # pct 0.1 is not < 0.1
    assert out.loc["q1", "avoid_n"] == 2
    assert out.loc["q1", "avoid_excess"] == pytest.approx(((0.1 - 0.2) / 2 - 0.07) * 100)
    assert math.isnan(out.loc["q2", "ic"]) and math.isnan(out.loc["q2", "avoid_excess"])
    low = back.assign(pct=pct[::-1] + pct)
    assert RetailGaugeEvaluator.compute_scores(low, fwd, 0.9).set_index("q").loc["q1", "ic_low"]
