from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.calculation.margin_ladder_estimator import MarginLadderEstimator

DETAIL = pd.DataFrame(
    {
        "ts_code": ["A"] * 3,
        "trade_date": ["20260922", "20260923", "20260924"],
        "rzye": [150.0, 160.0, 130.0],
        "rzmre": [50.0, 30.0, 0.0],
        "rzche": [0.0, 20.0, 30.0],
    }
)
CLOSES = pd.DataFrame(
    {
        "ts_code": ["A"] * 3,
        "trade_date": ["20260922", "20260923", "20260924"],
        "close": [10.0, 12.0, 11.0],
    }
)


# TC-MLE-001
def test_tc_mle_001_fifo() -> None:
    ladder = MarginLadderEstimator().compute_ladder(DETAIL, CLOSES, "20260924")
    # seed 100 @10 (repaid 20 then 30 -> 50 left), 50 @10 day 1, 30 @12 day 2
    assert ladder[["entry_date", "debt", "seeded"]].values.tolist() == [
        ["20260922", 50.0, True],
        ["20260922", 50.0, False],
        ["20260923", 30.0, False],
    ]
    assert ladder["debt"].sum() == pytest.approx(DETAIL["rzye"].iloc[-1])


# TC-MLE-002
def test_tc_mle_002_liquidation_price() -> None:
    ladder = MarginLadderEstimator(1.3, 1.0).compute_ladder(DETAIL, CLOSES, "20260924")
    assert ladder["liquidation_price"].iloc[-1] == pytest.approx(12.0 * 1.3 / 2.0)
    assert ladder["distance_pct"].iloc[-1] == pytest.approx((12.0 * 0.65 / 11.0 - 1) * 100)


# TC-MLE-003
def test_tc_mle_003_curve() -> None:
    est = MarginLadderEstimator()
    curve = est.compute_curve(est.compute_ladder(DETAIL, CLOSES, "20260924"), [0, 20, 30, 50])
    forced = curve["debt_forced"].tolist()
    assert forced == sorted(forced) and forced[0] == 0.0
    assert forced[-1] == pytest.approx(130.0) and curve["share_of_debt"].iloc[-1] == pytest.approx(
        1.0
    )


# TC-MLE-004
def test_tc_mle_004_invalid() -> None:
    with pytest.raises(ValueError):
        MarginLadderEstimator(maintenance_ratio=1.0)
    with pytest.raises(ValueError):
        MarginLadderEstimator(initial_margin_ratio=0.0)
