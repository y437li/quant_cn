from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.frames import PRICE_PANEL
from quant_cn.statistic.ic_calculator import IcCalculator

DAYS = ["20260105", "20260106", "20260107", "20260108"]


def build_prices(opens: list[float], closes: list[float], code: str = "A") -> pd.DataFrame:
    rows = [
        {c: np.nan for c in PRICE_PANEL.columns}
        | {
            "trade_date": d,
            "ts_code": code,
            "open": o,
            "close": c,
            "adj_factor": 2.0,
            "close_adj": c * 2,
        }
        for d, o, c in zip(DAYS, opens, closes, strict=True)
    ]
    return PRICE_PANEL.normalize(pd.DataFrame(rows), strict=True)


# TC-ICC-001
def test_tc_icc_001_open_entry() -> None:
    fwd = IcCalculator().build_forward_returns(
        build_prices([10, 11, 12, 13], [10, 12, 13, 15]), [2]
    )
    r = fwd.set_index("trade_date")["fwd_return"]
    assert r[DAYS[0]] == pytest.approx(13 / 11 - 1)  # buy open t+1 = 11, sell close t+2 = 13
    assert r[DAYS[1]] == pytest.approx(15 / 12 - 1)
    assert math.isnan(r[DAYS[2]]) and math.isnan(r[DAYS[3]])
    close = IcCalculator().build_forward_returns(
        build_prices([10, 11, 12, 13], [10, 12, 13, 15]), [1], "close"
    )
    assert close.set_index("trade_date")["fwd_return"][DAYS[0]] == pytest.approx(12 / 10 - 1)


# TC-ICC-002
def test_tc_icc_002_suspension() -> None:
    fwd = IcCalculator().build_forward_returns(
        build_prices([10, np.nan, 12, 13], [10, np.nan, 13, 15]), [1]
    )
    r = fwd.set_index("trade_date")["fwd_return"]
    assert math.isnan(r[DAYS[0]])  # cannot buy at the suspended open of t+1
    assert r[DAYS[1]] == pytest.approx(13 / 12 - 1)


def build_panels(n: int, sign: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    codes = [f"{i:06d}.SH" for i in range(n)]
    factors = pd.DataFrame(
        {
            "trade_date": DAYS[0],
            "ts_code": codes,
            "factor": "f",
            "value": np.arange(n, dtype=float),
            "value_raw": np.nan,
        }
    )
    returns = pd.DataFrame(
        {
            "trade_date": DAYS[0],
            "ts_code": codes,
            "horizon": 5.0,
            "fwd_return": sign * np.exp(np.arange(n) / 10),
        }
    )  # monotone, not linear
    return factors, returns


# TC-ICC-003
def test_tc_icc_003_spearman() -> None:
    up = IcCalculator().compute(*build_panels(40, 1.0))
    down = IcCalculator().compute(*build_panels(40, -1.0))
    assert up["ic"].iloc[0] == pytest.approx(1.0) and up["n"].iloc[0] == 40
    assert down["ic"].iloc[0] == pytest.approx(-1.0)
    assert IcCalculator(method="pearson").compute(*build_panels(40, 1.0))["ic"].iloc[0] < 1.0


# TC-ICC-004
def test_tc_icc_004_min_names() -> None:
    assert IcCalculator(min_names=30).compute(*build_panels(20, 1.0)).empty
    with pytest.raises(ValueError):
        IcCalculator(min_names=2)
