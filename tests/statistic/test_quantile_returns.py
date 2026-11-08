from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.statistic.quantile_returns import QuantileReturns


def build_inputs(n: int = 50) -> tuple[pd.DataFrame, pd.DataFrame]:
    codes = [f"{i:06d}.SH" for i in range(n)]
    factors = pd.DataFrame(
        {
            "trade_date": "d1",
            "ts_code": codes,
            "factor": "f",
            "value": np.arange(n, dtype=float),
            "value_raw": np.nan,
        }
    )
    returns = pd.DataFrame(
        {
            "trade_date": "d1",
            "ts_code": codes,
            "horizon": 5.0,
            "fwd_return": np.arange(n, dtype=float) / 100,
        }
    )
    return factors, returns


# TC-QR-001
def test_tc_qr_001_ladder() -> None:
    out = QuantileReturns(5).compute(*build_inputs())
    ladder = out[out["quantile"] > 0]["ret"].to_numpy()
    assert np.all(np.diff(ladder) > 0)
    assert out[out["quantile"] == 0]["ret"].iloc[0] == pytest.approx(ladder[-1] - ladder[0])
    with pytest.raises(ValueError):
        QuantileReturns(1)


# TC-QR-002
def test_tc_qr_002_counts() -> None:
    out = QuantileReturns(5).compute(*build_inputs())
    assert (
        out[out["quantile"] > 0]["n"].sum() == 50 and out[out["quantile"] == 0]["n"].iloc[0] == 20
    )
