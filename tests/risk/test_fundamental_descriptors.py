"""Tests of FundamentalDescriptors."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.risk.fundamental_descriptors import FundamentalDescriptors


def build_frame(**overrides: float) -> pd.DataFrame:
    row: dict[str, object] = {
        "trade_date": "20250102",
        "ts_code": "000001.SZ",
        "total_mv": 100.0,  # 10k CNY -> 1e6 CNY
        "total_hldr_eqy_exc_min_int": 5e5,
        "total_assets": 2e6,
        "total_liab": 1.2e6,
        "lt_borr": 2e5,
        "bond_payable": 1e5,
        "n_income_attr_p_ttm": 5e4,
        "n_cashflow_act_ttm": 8e4,
        "c_pay_acq_const_fiolta_ttm": 3e4,
    }
    return pd.DataFrame([row | overrides])


# TC-FD-001
def test_tc_fd_001_value_and_leverage() -> None:
    out = FundamentalDescriptors().compute_value_leverage(build_frame()).iloc[0]
    assert out["btop"] == pytest.approx(0.5)
    assert out["etop"] == pytest.approx(0.05)
    assert out["cetop"] == pytest.approx(0.08)
    assert out["fcfp"] == pytest.approx(0.05)
    assert out["mlev"] == pytest.approx(1.3)
    assert out["dtoa"] == pytest.approx(0.6)
    assert out["blev"] == pytest.approx(1.6)


# TC-FD-002
def test_tc_fd_002_negative_equity_and_missing_debt() -> None:
    frame = build_frame(total_hldr_eqy_exc_min_int=-1e5, lt_borr=np.nan, bond_payable=np.nan)
    out = FundamentalDescriptors().compute_value_leverage(frame).iloc[0]
    assert np.isnan(out["blev"])
    assert out["btop"] == pytest.approx(-0.1)
    assert out["mlev"] == pytest.approx(1.0)
    no_bs = FundamentalDescriptors().compute_value_leverage(build_frame(total_assets=np.nan))
    assert np.isnan(no_bs.iloc[0]["mlev"])


# TC-FD-003
def test_tc_fd_003_growth_slope_over_mean() -> None:
    rows = [
        {"as_of": "20250430", "ts_code": "A", "end_date": f"{y}1231", "field": f, "value": v}
        for y, v in zip(range(2018, 2025), [1, 2, 3, 4, 5, 6, 7], strict=True)
        for f in ("eps", "revenue")
    ]
    rows += [
        {"as_of": "20250430", "ts_code": "B", "end_date": "20231231", "field": "eps", "value": 1.0},
        {"as_of": "20250430", "ts_code": "B", "end_date": "20241231", "field": "eps", "value": 2.0},
    ]
    out = FundamentalDescriptors(years=5, min_years=3).compute_growth(pd.DataFrame(rows))
    a = out[out["ts_code"] == "A"].iloc[0]
    assert a["egro"] == pytest.approx(1.0 / 5.0)  # last 5: 3..7, slope 1, mean 5
    assert a["sgro"] == pytest.approx(0.2)
    assert np.isnan(out[out["ts_code"] == "B"].iloc[0]["egro"])
    with pytest.raises(ValueError):
        FundamentalDescriptors(years=3, min_years=4)
