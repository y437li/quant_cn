"""Tests of base_risk_model (plan 05)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.risk.base_risk_model import BaseRiskModel
from quant_cn.risk.risk_snapshot import RiskSnapshot

FACTORS = ["country", "size"]


def build_snapshot() -> RiskSnapshot:
    x = pd.DataFrame([[1.0, 1.0], [1.0, -1.0], [1.0, 0.0]], index=["A", "B", "C"], columns=FACTORS)
    cov = pd.DataFrame([[4e-4, 1e-4], [1e-4, 1e-4]], index=FACTORS, columns=FACTORS)
    spec = pd.Series([0.02, 0.03, 0.01], index=["A", "B", "C"])
    return RiskSnapshot("20250102", x, cov, spec)


class FixedModel(BaseRiskModel):
    def load_snapshot(self, trade_date: str) -> RiskSnapshot:
        return build_snapshot()


# TC-BRM-001
def test_tc_brm_001_compute_portfolio_risk() -> None:
    h = pd.Series({"A": 0.5, "B": 0.5})
    factor, spec = build_snapshot().compute_variance(h)
    assert FixedModel("m").compute_portfolio_risk(h, "20250102") == pytest.approx(
        np.sqrt(factor + spec)
    )
    with pytest.raises(TypeError):
        BaseRiskModel("m")  # type: ignore[abstract]  # TC-BRM-001: the base is abstract
