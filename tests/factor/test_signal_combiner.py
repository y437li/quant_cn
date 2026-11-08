from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.factor.signal_combiner import SignalCombiner
from quant_cn.statistic.standardizer import Standardizer


def build_rows() -> pd.DataFrame:
    values = {
        ("A", "x"): 1.0,
        ("A", "y"): 3.0,
        ("B", "x"): -1.0,
        ("B", "y"): 1.0,
        ("C", "x"): 2.0,
        ("D", "x"): 0.0,
        ("D", "y"): 0.0,
    }
    return pd.DataFrame(
        [
            {"trade_date": "d1", "ts_code": c, "factor": f, "value": v, "value_raw": v}
            for (c, f), v in values.items()
        ]
    )


# TC-SGC-001
def test_tc_sgc_001_blend() -> None:
    out = SignalCombiner({"x": 1.0, "y": 3.0}, Standardizer(), min_factors=2).compute(build_rows())
    raw = out.set_index("ts_code")["value_raw"]
    assert raw["A"] == pytest.approx((1 * 1 + 3 * 3) / 4) and raw["B"] == pytest.approx(
        (-1 + 3) / 4
    )
    assert set(out["factor"]) == {"score"} and out["value"].std() == pytest.approx(1.0)
    with pytest.raises(ValueError):
        SignalCombiner({}, Standardizer())


# TC-SGC-002
def test_tc_sgc_002_min_factors() -> None:
    out = SignalCombiner({"x": 1.0, "y": 1.0}, Standardizer(), min_factors=2).compute(build_rows())
    assert "C" not in set(out["ts_code"])  # only one factor
