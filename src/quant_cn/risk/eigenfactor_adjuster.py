"""Eigenfactor risk adjustment (Menchero, Wang and Orr 2011; CNE5), plan 05 phase 4."""

from __future__ import annotations

import numpy as np

BATCH = 100


class EigenfactorAdjuster:
    """
    Purpose:
        Remove the systematic underestimation of risk of the smallest-variance eigenportfolios
        of a sample covariance. For the matrix F0 = U0 D0 U0^T: simulate `sims` histories of
        `n_obs` returns from N(0, F0), estimate each sample covariance F_m = U_m D_m U_m^T with
        the estimation weights, compare the true variance of the simulated eigenportfolios
        diag(U_m^T F0 U_m) with the estimated D_m, and form the bias v(k) = sqrt(mean_m ratio)
        per eigen rank k. The adjusted matrix is U0 diag(gamma^2 D0) U0^T with
        gamma = scale (v - 1) + 1. The bias profile (gamma by rank) can be reused across
        nearby dates (`compute_adjusted`): it depends on the spectrum shape and sample length.

    Contract:
        Input:
            sims:  int >= 0   -- simulations (0 disables: gamma = 1)
            scale: float > 0  -- the empirical a (USE4: 1.2)
        Output:
            instance; `compute_gamma`, `compute_adjusted`
        Raises:
            (none)

    Used by:
        risk.FactorCovarianceEstimator  -- eigen adjustment
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-EFA-001  gamma >= ~1 for the smallest eigenvalues and rises toward the small end
        TC-EFA-002  apply keeps the eigenvectors, scales eigenvalues by gamma^2, stays PSD and
                    symmetric
        TC-EFA-003  same seed -> identical gamma; sims 0 -> gamma 1
    """

    def __init__(self, sims: int = 1000, scale: float = 1.2) -> None:
        self._sims = sims
        self._scale = scale

    def compute_gamma(self, cov: np.ndarray, weights: np.ndarray, seed: int) -> np.ndarray:
        """
        Purpose:
            The eigen-rank scaling gamma for a covariance estimated with `weights`.

        Contract:
            Input:
                cov:     np.ndarray  -- (K, K) symmetric PSD
                weights: np.ndarray  -- (T,) observation weights of the estimator, sum 1
                seed:    int         -- RNG seed
            Output:
                np.ndarray  -- (K,) gamma by ascending eigenvalue rank, >= 0
            Raises:
                np.linalg.LinAlgError  -- non-finite matrix
        """
        k = cov.shape[0]
        if self._sims == 0 or k < 2:  # noqa: PLR2004 -- one factor has no spectrum to fix
            return np.ones(k)
        vals = np.clip(np.linalg.eigvalsh(cov), 0.0, None)
        rng = np.random.default_rng(seed)
        ratio_sum = np.zeros(k)
        done = 0
        while done < self._sims:
            m = min(BATCH, self._sims - done)
            draws = rng.standard_normal((m, len(weights), k)) * np.sqrt(vals)
            sample = (draws * weights[None, :, None]).transpose(0, 2, 1) @ draws
            d_m, u_m = np.linalg.eigh(sample)
            true = np.einsum("mik,i,mik->mk", u_m, vals, u_m)
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio_sum += np.nan_to_num(true / d_m, nan=1.0, posinf=1.0).sum(axis=0)
            done += m
        bias = np.sqrt(ratio_sum / self._sims)
        return np.clip(self._scale * (bias - 1.0) + 1.0, 0.0, None)

    @staticmethod
    def compute_adjusted(cov: np.ndarray, gamma: np.ndarray) -> np.ndarray:
        """
        Purpose:
            Scale the eigenvalues of `cov` by gamma^2 (ascending rank order).

        Contract:
            Input:
                cov:   np.ndarray  -- (K, K) symmetric
                gamma: np.ndarray  -- (K,) from compute_gamma (same K)
            Output:
                np.ndarray  -- (K, K) symmetric PSD
            Raises:
                ValueError  -- gamma length differs from K
        """
        if len(gamma) != cov.shape[0]:
            raise ValueError("gamma length must equal the matrix size")
        vals, vecs = np.linalg.eigh(cov)
        adjusted = (vecs * (np.clip(vals, 0.0, None) * gamma**2)) @ vecs.T
        return np.asarray((adjusted + adjusted.T) / 2, dtype=float)
