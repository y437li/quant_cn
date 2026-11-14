from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.frames import PRICE_PANEL
from quant_cn.factor.base_factor import FactorInputs
from quant_cn.factor.library.intraday_reversal_factor import IntradayReversalFactor

N = 60
DAYS = pd.bdate_range("2025-01-01", periods=N).strftime("%Y%m%d").tolist()
RNG = np.random.default_rng(7)
OPENS = 10 + RNG.random(N)
CLOSES = OPENS * np.exp(RNG.normal(0, 0.02, N))
TURNOVER = RNG.permutation(N).astype(float) + 1.0  # distinct


def build_inputs(opens: np.ndarray, closes: np.ndarray, turnover: np.ndarray) -> FactorInputs:
    rows = pd.DataFrame({c: np.nan for c in PRICE_PANEL.columns}, index=range(N))
    rows = rows.assign(
        trade_date=DAYS, ts_code="A", open=opens, close=closes, adj_factor=1.0, close_adj=closes
    )
    basic = pd.DataFrame({"trade_date": DAYS, "ts_code": "A", "turnover_rate_f": turnover})
    return FactorInputs(prices=PRICE_PANEL.normalize(rows, strict=True), daily_basic=basic)


def compute_values(
    factor: IntradayReversalFactor,
    opens: np.ndarray = OPENS,
    closes: np.ndarray = CLOSES,
    turnover: np.ndarray = TURNOVER,
) -> pd.Series:
    out = factor.compute(build_inputs(opens, closes, turnover), DAYS[0], DAYS[-1])
    return out.set_index("trade_date")["value"]


def find_expected(t: int, turnover: np.ndarray, window: int = 21, top_k: int = 10) -> float:
    days = range(t - window + 1, t + 1)
    busiest = sorted(days, key=lambda i: (turnover[i], i))[-top_k:]
    return -sum(np.log(CLOSES[i] / OPENS[i]) for i in busiest)


# TC-IRV-001
def test_tc_irv_001_known_answer() -> None:
    values = compute_values(IntradayReversalFactor("irv"))
    assert values.index.min() == DAYS[20]  # needs a full window of 21 sessions
    for t in (20, 33, N - 1):
        assert values[DAYS[t]] == pytest.approx(find_expected(t, TURNOVER))


# TC-IRV-002
def test_tc_irv_002_tie_takes_later_session() -> None:
    turnover = np.ones(N)
    values = compute_values(
        IntradayReversalFactor("irv", window=21, top_k=1, min_obs=15), turnover=turnover
    )
    assert values[DAYS[40]] == pytest.approx(-np.log(CLOSES[40] / OPENS[40]))


# TC-IRV-003
def test_tc_irv_003_untraded_sessions_and_min_obs() -> None:
    factor = IntradayReversalFactor("irv", window=21, top_k=10, min_obs=15)
    opens, turnover = OPENS.copy(), TURNOVER.copy()
    busiest = int(np.argmax(TURNOVER[20:41])) + 20
    opens[busiest] = np.nan  # suspended: skipped even though its turnover is the highest
    values = compute_values(factor, opens=opens)
    masked = TURNOVER.copy()
    masked[busiest] = -np.inf
    assert values[DAYS[40]] == pytest.approx(find_expected(40, masked))
    turnover[24:30] = np.nan  # window 20..40 keeps exactly 15 traded sessions
    assert DAYS[40] in compute_values(factor, turnover=turnover).index
    turnover[30] = np.nan  # 14 traded sessions < min_obs
    assert DAYS[40] not in compute_values(factor, turnover=turnover).index


# TC-IRV-004
def test_tc_irv_004_point_in_time() -> None:
    factor = IntradayReversalFactor("irv")
    base = compute_values(factor)[DAYS[40]]
    closes, turnover = CLOSES.copy(), TURNOVER.copy()
    closes[41:] *= 3
    turnover[41:] = 1e6
    assert compute_values(factor, closes=closes, turnover=turnover)[DAYS[40]] == base


# TC-IRV-005
@pytest.mark.parametrize(
    ("window", "top_k", "min_obs"), [(0, 1, 1), (21, 0, 15), (21, 16, 15), (21, 10, 22)]
)
def test_tc_irv_005_invalid_params(window: int, top_k: int, min_obs: int) -> None:
    with pytest.raises(ValueError):
        IntradayReversalFactor("irv", window=window, top_k=top_k, min_obs=min_obs)
