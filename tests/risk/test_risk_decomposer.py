"""Tests of risk_decomposer (plan 05)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.frames import RISK_DECOMP
from quant_cn.risk.risk_decomposer import RiskDecomposer
from quant_cn.risk.risk_snapshot import RiskSnapshot

FACTORS = ["country", "size"]


def build_snapshot() -> RiskSnapshot:
    x = pd.DataFrame([[1.0, 1.0], [1.0, -1.0], [1.0, 0.0]], index=["A", "B", "C"], columns=FACTORS)
    cov = pd.DataFrame([[4e-4, 1e-4], [1e-4, 1e-4]], index=FACTORS, columns=FACTORS)
    spec = pd.Series([0.02, 0.03, 0.01], index=["A", "B", "C"])
    return RiskSnapshot("20250102", x, cov, spec)


# TC-RD-001
def test_tc_rd_001_contributions_sum_to_total() -> None:
    h = pd.Series({"A": 0.6, "B": 0.3, "C": 0.1})
    out = RiskDecomposer().compute(build_snapshot(), h, "p")
    by = out.set_index("component")
    factor_c = by.loc[[c for c in by.index if c.startswith("f:")], "risk"].sum()
    spec_var = build_snapshot().compute_variance(h)[1]
    total = by.loc["total", "risk"]
    assert factor_c + spec_var / total == pytest.approx(total)
    assert by.loc[[c for c in by.index if c.startswith("f:")], "pct"].sum() + by.loc[
        "specific", "pct"
    ] == pytest.approx(1.0)
    assert total == pytest.approx(np.sqrt(sum(build_snapshot().compute_variance(h))))


# TC-RD-002
def test_tc_rd_002_active_rows() -> None:
    h = pd.Series({"A": 0.6, "B": 0.4})
    bench = pd.Series({"A": 0.5, "C": 0.5})
    out = RiskDecomposer().compute(build_snapshot(), h, "p", bench)
    active = pd.Series({"A": 0.1, "B": 0.4, "C": -0.5})
    te = np.sqrt(sum(build_snapshot().compute_variance(active)))
    assert out.set_index("component").loc["active_total", "risk"] == pytest.approx(te)
    assert set(out[out["component"].str.startswith("active_")]["kind"]) == {"active"}
    RISK_DECOMP.validate(out)
