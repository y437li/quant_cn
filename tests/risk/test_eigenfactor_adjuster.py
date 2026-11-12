"""Tests of eigenfactor_adjuster (plan 05)."""

from __future__ import annotations

import numpy as np
import pytest

from quant_cn.risk.eigenfactor_adjuster import EigenfactorAdjuster


def build_cov(k: int = 8, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((200, k)) * np.linspace(0.002, 0.02, k)
    return np.asarray(np.cov(a.T))


# TC-EFA-001
def test_tc_efa_001_gamma_rises_at_small_eigenvalues() -> None:
    cov = build_cov()
    weights = np.full(60, 1 / 60)
    gamma = EigenfactorAdjuster(sims=300, scale=1.2).compute_gamma(cov, weights, seed=1)
    assert gamma[0] > 1.05  # smallest eigenvalue is under-estimated in short samples
    assert gamma[0] > gamma[-1]


# TC-EFA-002
def test_tc_efa_002_apply_keeps_vectors_and_psd() -> None:
    cov = build_cov()
    gamma = np.linspace(1.5, 1.0, cov.shape[0])
    out = EigenfactorAdjuster.compute_adjusted(cov, gamma)
    np.testing.assert_allclose(out, out.T)
    vals, vecs = np.linalg.eigh(cov)
    new_vals = np.linalg.eigvalsh(out)
    np.testing.assert_allclose(np.sort(new_vals), np.sort(vals * gamma**2), rtol=1e-8)
    np.testing.assert_allclose(vecs.T @ out @ vecs, np.diag(vals * gamma**2), atol=1e-12)
    with pytest.raises(ValueError):
        EigenfactorAdjuster.compute_adjusted(cov, gamma[:-1])


# TC-EFA-003
def test_tc_efa_003_seeded_and_disabled() -> None:
    cov, w = build_cov(), np.full(40, 1 / 40)
    adj = EigenfactorAdjuster(sims=50)
    np.testing.assert_array_equal(adj.compute_gamma(cov, w, 3), adj.compute_gamma(cov, w, 3))
    np.testing.assert_array_equal(EigenfactorAdjuster(sims=0).compute_gamma(cov, w, 3), 1.0)
