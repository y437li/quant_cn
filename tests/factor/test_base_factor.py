from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.factor.base_factor import BaseFactor, FactorInputs


class ConstantFactor(BaseFactor):
    """Test double: value_raw = 1 on every price row, NaN on the first."""

    inputs = ("prices",)

    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        out = inputs.prices[["trade_date", "ts_code"]].assign(value_raw=1.0)
        out.loc[out.index[0], "value_raw"] = np.nan
        return out


PRICES = pd.DataFrame({"trade_date": ["20260105", "20260106", "20260107"], "ts_code": "A"})


# TC-FIN-001
def test_tc_fin_001_compute_field() -> None:
    fundamentals = pd.DataFrame(
        {
            "trade_date": ["d1", "d1"],
            "ts_code": ["A", "A"],
            "field": ["x", "y"],
            "value": [1.0, 2.0],
            "end_date": "e",
            "ann_date": "a",
        }
    )
    out = FactorInputs(prices=PRICES, fundamentals=fundamentals).compute_field("y")
    assert out.to_dict("records") == [{"trade_date": "d1", "ts_code": "A", "y": 2.0}]
    assert list(FactorInputs(prices=PRICES).compute_field("y").columns) == [
        "trade_date",
        "ts_code",
        "y",
    ]


# TC-BFA-001
def test_tc_bfa_001_compute() -> None:
    out = ConstantFactor("const").compute(FactorInputs(prices=PRICES), "20260105", "20260106")
    assert out["trade_date"].tolist() == ["20260106"]  # NaN dropped, range kept
    assert out[["factor", "value", "value_raw"]].values.tolist() == [["const", 1.0, 1.0]]


# TC-BFA-002
def test_tc_bfa_002_registry() -> None:
    assert BaseFactor.registry["ConstantFactor"] is ConstantFactor
    with pytest.raises(TypeError):
        BaseFactor("x")  # type: ignore[abstract]
