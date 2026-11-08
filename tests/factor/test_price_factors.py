from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.frames import PRICE_PANEL
from quant_cn.factor.base_factor import FactorInputs
from quant_cn.factor.library.momentum_factor import MomentumFactor
from quant_cn.factor.library.reversal_factor import ReversalFactor
from quant_cn.factor.library.turnover_factor import TurnoverFactor

DAYS = pd.bdate_range("2025-01-01", periods=300).strftime("%Y%m%d").tolist()


def build_inputs(closes: np.ndarray, turnover: np.ndarray | None = None) -> FactorInputs:
    rows = pd.DataFrame({c: np.nan for c in PRICE_PANEL.columns}, index=range(len(DAYS)))
    rows = rows.assign(trade_date=DAYS, ts_code="A", close=closes, adj_factor=1.0, close_adj=closes)
    basic = (
        pd.DataFrame({"trade_date": DAYS, "ts_code": "A", "turnover_rate_f": turnover})
        if turnover is not None
        else pd.DataFrame()
    )
    return FactorInputs(prices=PRICE_PANEL.normalize(rows, strict=True), daily_basic=basic)


def get_value(frame: pd.DataFrame, i: int) -> float:
    return float(frame.set_index("trade_date").loc[DAYS[i], "value"])


# TC-MOM-001
def test_tc_mom_001_momentum() -> None:
    closes = np.linspace(10, 40, len(DAYS))
    factor = MomentumFactor("mom", window=252, skip=21)
    out = factor.compute(build_inputs(closes), DAYS[0], DAYS[-1])
    assert out["trade_date"].min() == DAYS[252]  # needs a full window
    assert get_value(out, 280) == pytest.approx(closes[280 - 21] / closes[280 - 252] - 1)
    future = closes.copy()
    future[281:] *= 3  # prices after t change
    assert get_value(factor.compute(build_inputs(future), DAYS[0], DAYS[-1]), 280) == get_value(
        out, 280
    )
    with pytest.raises(ValueError):
        MomentumFactor("m", window=10, skip=10)


# TC-REV-001
def test_tc_rev_001_reversal() -> None:
    closes = np.linspace(10, 40, len(DAYS))
    closes[100] = np.nan  # suspended: carry the last close
    factor = ReversalFactor("rev", window=21)
    out = factor.compute(build_inputs(closes), DAYS[0], DAYS[-1])
    assert get_value(out, 150) == pytest.approx(-(closes[150] / closes[129] - 1))
    assert get_value(out, 100) == pytest.approx(-(closes[99] / closes[79] - 1))
    future = closes.copy()
    future[151:] = 1.0
    assert get_value(factor.compute(build_inputs(future), DAYS[0], DAYS[-1]), 150) == get_value(
        out, 150
    )


# TC-TRN-001
def test_tc_trn_001_turnover() -> None:
    closes = np.full(len(DAYS), 10.0)
    turnover = np.arange(len(DAYS), dtype=float)
    turnover[:10] = np.nan
    factor = TurnoverFactor("turn", window=60, min_obs=40)
    out = factor.compute(build_inputs(closes, turnover), DAYS[0], DAYS[-1])
    assert get_value(out, 200) == pytest.approx(-turnover[141:201].mean())
    assert DAYS[45] not in set(out["trade_date"])  # 36 traded sessions < min_obs
    changed = turnover.copy()
    changed[201:] = 1000.0
    assert get_value(
        factor.compute(build_inputs(closes, changed), DAYS[0], DAYS[-1]), 200
    ) == get_value(out, 200)
