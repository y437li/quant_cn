"""Tests of risk_snapshot (plan 05)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.risk.risk_snapshot import RiskSnapshot

FACTORS = ["country", "size"]


def build_snapshot() -> RiskSnapshot:
    x = pd.DataFrame([[1.0, 1.0], [1.0, -1.0], [1.0, 0.0]], index=["A", "B", "C"], columns=FACTORS)
    cov = pd.DataFrame([[4e-4, 1e-4], [1e-4, 1e-4]], index=FACTORS, columns=FACTORS)
    spec = pd.Series([0.02, 0.03, 0.01], index=["A", "B", "C"])
    return RiskSnapshot("20250102", x, cov, spec)


# TC-RSN-001
def test_tc_rsn_001_variance() -> None:
    h = pd.Series({"A": 0.5, "B": 0.5})
    factor, spec = build_snapshot().compute_variance(h)
    b = np.array([1.0, 0.0])
    assert factor == pytest.approx(b @ np.array([[4e-4, 1e-4], [1e-4, 1e-4]]) @ b)
    assert spec == pytest.approx(0.25 * 0.02**2 + 0.25 * 0.03**2)


# TC-RSN-002
def test_tc_rsn_002_build_covered_weights() -> None:
    kept, dropped = build_snapshot().build_covered_weights(pd.Series({"A": 0.4, "Z": 0.6}))
    assert dropped == pytest.approx(0.6)
    assert kept.to_dict() == {"A": 0.4, "B": 0.0, "C": 0.0}


# TC-RSN-003
def test_tc_rsn_003_exposure_vector_and_matrix() -> None:
    b = build_snapshot().compute_exposure_vector(pd.Series({"A": 1.0, "B": 1.0}))
    assert b.to_dict() == {"country": 2.0, "size": 0.0}
    rows = pd.DataFrame({"factor_i": ["a"], "factor_j": ["a"], "cov": [2.0]})
    np.testing.assert_array_equal(
        RiskSnapshot.build_matrix(rows, ["a", "b"]), [[2.0, 0.0], [0.0, 0.0]]
    )


# TC-RSN-004
def test_tc_rsn_004_stock_cov() -> None:
    snap = build_snapshot()
    codes = list(snap.specific.dropna().index)
    cov = snap.compute_stock_cov(codes)
    x = snap.exposures.loc[codes].to_numpy(float)
    want = x @ snap.cov.to_numpy(float) @ x.T + np.diag(
        snap.specific.loc[codes].to_numpy(float) ** 2
    )
    np.testing.assert_allclose(cov.to_numpy(), want)
    h = pd.Series(0.5, index=codes[:2]).reindex(codes).fillna(0.0)
    factor, spec = snap.compute_variance(h)
    assert float(h.to_numpy() @ cov.to_numpy() @ h.to_numpy()) == pytest.approx(factor + spec)
