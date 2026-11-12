"""Factor covariance forecasts: EWMA + Newey-West, eigenfactor and regime adjusted (plan 05 ph4)."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from quant_cn.core.frames import FACTOR_COV, FACTOR_RETURN
from quant_cn.core.risk_model_settings import RiskModelSettings
from quant_cn.risk.eigenfactor_adjuster import EigenfactorAdjuster
from quant_cn.risk.ewm_window import EwmWindow
from quant_cn.risk.volatility_regime_adjuster import VolatilityRegimeAdjuster

logger = logging.getLogger(__name__)

MIN_EIGEN = 1e-12


class FactorCovarianceEstimator:
    """
    Purpose:
        For every session t, the factor covariance forecast for t+1 from factor returns up to t
        over the last `cov_window` sessions: zero-mean exponentially weighted covariances with
        pairwise missing-data normalisation and Newey-West autocorrelation terms
        (Bartlett weights, `cov_nw_lags`), volatilities with `vol_half_life` and correlations
        with `corr_half_life` (CNE5 90 / 480), combined as D C D and made PSD (cov_raw); then
        the eigenfactor adjustment (gamma profile refitted every `eigen_refit_days` sessions or
        when the factor set changes) and the volatility regime multiplier lambda^2 (cov).
        Units: daily variance; horizon_days records the NW horizon. A factor enters a session's
        matrix only with >= min_factor_obs observations in its window.

    Contract:
        Input:
            settings: RiskModelSettings; eigen: EigenfactorAdjuster
            regime: VolatilityRegimeAdjuster
        Output:
            instance; `compute(factor_returns) -> DataFrame (FACTOR_COV)`,
            `compute_raw(window_returns) -> np.ndarray`
        Raises:
            (none at construction)

    Used by:
        risk.RiskModel  -- covariance step
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-FCE-001  compute_raw on i.i.d. returns matches the weighted sample covariance; NW
                    lags raise variance of autocorrelated returns
        TC-FCE-002  every session's matrix is symmetric PSD; cov_raw <= cov on the smallest
                    eigen direction after the eigen adjustment
        TC-FCE-003  factors with too few observations are left out; output validates FACTOR_COV
    """

    def __init__(
        self,
        settings: RiskModelSettings,
        eigen: EigenfactorAdjuster,
        regime: VolatilityRegimeAdjuster,
    ) -> None:
        self._s = settings
        self._eigen = eigen
        self._regime = regime
        self._vol = EwmWindow(settings.cov_window, settings.vol_half_life)
        self._corr = EwmWindow(settings.cov_window, settings.corr_half_life)

    def compute(self, factor_returns: pd.DataFrame, start: str | None = None) -> pd.DataFrame:
        """
        Purpose:
            FACTOR_COV for every session of the factor-return history (from `start` if given).

        Contract:
            Input:
                factor_returns: DataFrame  -- FACTOR_RETURN (the full history up to the last
                                              session; earlier sessions feed the windows)
                start: str | None          -- first session to output (YYYYMMDD)
            Output:
                DataFrame  -- FACTOR_COV sorted by key; both triangles stored
            Raises:
                SchemaError  -- invalid input frame
        """
        FACTOR_RETURN.validate(factor_returns)
        wide = factor_returns.pivot(index="trade_date", columns="factor", values="ret").sort_index()
        dates, names, values = list(wide.index), list(wide.columns), wide.to_numpy(float)
        raw_list: list[tuple[int, list[int], np.ndarray, np.ndarray]] = []
        gamma: np.ndarray | None = None
        last_cols: list[int] = []
        for t in range(len(dates)):
            lo = max(0, t + 1 - self._s.cov_window)
            window = values[lo : t + 1]
            cols = self._list_columns(window)
            if len(cols) == 0:
                continue
            raw = self.compute_raw(window[:, cols])
            if gamma is None or cols != last_cols or t % self._s.eigen_refit_days == 0:
                weights = self._corr.weights[: len(window)][::-1]
                gamma = self._eigen.compute_gamma(raw, weights / weights.sum(), self._s.seed + t)
                last_cols = cols
            raw_list.append((t, cols, raw, self._eigen.compute_adjusted(raw, gamma)))
        lam = self._compute_lambda(values, raw_list, len(dates))
        return self._to_frame(raw_list, lam, dates, names, start)

    def compute_raw(self, window: np.ndarray) -> np.ndarray:
        """
        Purpose:
            EWMA + Newey-West covariance of one window (last row = most recent).

        Contract:
            Input:
                window: np.ndarray  -- (T, K) factor returns, NaN = missing
            Output:
                np.ndarray  -- (K, K) symmetric PSD (eigenvalues floored at 1e-12 x largest)
            Raises:
                (none)
        """
        vol = np.sqrt(np.diag(self._compute_nw(window, self._vol)))
        cov = self._compute_nw(window, self._corr)
        d = np.sqrt(np.clip(np.diag(cov), MIN_EIGEN, None))
        corr = np.clip(cov / np.outer(d, d), -1.0, 1.0)
        np.fill_diagonal(corr, 1.0)
        out = corr * np.outer(vol, vol)
        vals, vecs = np.linalg.eigh((out + out.T) / 2)
        vals = np.clip(vals, MIN_EIGEN * max(vals.max(), MIN_EIGEN), None)
        return (vecs * vals) @ vecs.T

    def _compute_nw(self, window: np.ndarray, kernel: EwmWindow) -> np.ndarray:
        n = len(window)
        w = kernel.weights[:n][::-1]  # oldest first, aligned with the window rows
        mask = np.isfinite(window).astype(float)
        x = np.nan_to_num(window)
        cov = self._compute_lagged(x, mask, w, 0)
        for lag in range(1, self._s.cov_nw_lags + 1):
            if lag >= n:
                break
            g = self._compute_lagged(x, mask, w, lag)
            cov += (1 - lag / (self._s.cov_nw_lags + 1)) * (g + g.T)
        return cov

    @staticmethod
    def _compute_lagged(x: np.ndarray, mask: np.ndarray, w: np.ndarray, lag: int) -> np.ndarray:
        a, b, m_a, m_b, ww = x[lag:], x[: len(x) - lag], mask[lag:], mask[: len(x) - lag], w[lag:]
        num = (a * ww[:, None]).T @ b
        den = (m_a * ww[:, None]).T @ m_b
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(den > 0, num / den, 0.0)

    def _list_columns(self, window: np.ndarray) -> list[int]:
        counts = np.isfinite(window).sum(axis=0)
        return [int(i) for i in np.flatnonzero(counts >= self._s.min_factor_obs)]

    def _compute_lambda(
        self,
        values: np.ndarray,
        raw_list: list[tuple[int, list[int], np.ndarray, np.ndarray]],
        n: int,
    ) -> pd.Series:
        sigma_prev = np.full_like(values, np.nan)
        for t, cols, _, adj in raw_list:
            if t + 1 < n:
                sigma_prev[t + 1, cols] = np.sqrt(np.diag(adj))
        bias = self._regime.compute_bias(values, sigma_prev)
        return self._regime.compute_lambda(pd.Series(bias))

    def _to_frame(
        self,
        raw_list: list[tuple[int, list[int], np.ndarray, np.ndarray]],
        lam: pd.Series,
        dates: list[str],
        names: list[str],
        start: str | None,
    ) -> pd.DataFrame:
        parts = []
        for t, cols, raw, adj in raw_list:
            if start is not None and dates[t] < start:
                continue
            labels = np.array(names)[cols]
            k = len(cols)
            parts.append(
                pd.DataFrame(
                    {
                        "trade_date": dates[t],
                        "factor_i": np.repeat(labels, k),
                        "factor_j": np.tile(labels, k),
                        "cov": (adj * lam.iloc[t] ** 2).ravel(),
                        "cov_raw": raw.ravel(),
                        "horizon_days": float(self._s.horizon_days),
                    }
                )
            )
        if not parts:
            return FACTOR_COV.normalize(pd.DataFrame(columns=FACTOR_COV.columns), strict=True)
        out = pd.concat(parts, ignore_index=True).sort_values(
            ["trade_date", "factor_i", "factor_j"]
        )
        return FACTOR_COV.validate(FACTOR_COV.normalize(out.reset_index(drop=True), strict=True))
