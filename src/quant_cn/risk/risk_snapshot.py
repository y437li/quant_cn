"""One session of a fitted risk model: exposures, factor covariance, specific risk (plan 05)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from quant_cn.core.exceptions import QuantCnError


@dataclass(frozen=True)
class RiskSnapshot:
    """
    Purpose:
        The model as of one session's close, ready for portfolio arithmetic: X (stocks x
        factors, country column = 1), F (factors x factors, daily variance) and specific vol.
        Portfolio variance = h^T X F X^T h + sum h^2 sigma^2.

    Contract:
        Input:
            trade_date: str            -- YYYYMMDD
            exposures:  DataFrame      -- index ts_code, columns = factors of `cov` (0 = none)
            cov:        DataFrame      -- factors x factors, same labels both axes
            specific:   Series         -- index ts_code, specific vol (daily)
        Output:
            frozen dataclass; `compute_variance`, `build_covered_weights`,
                        `compute_exposure_vector`, `compute_stock_cov`, `build_matrix`
        Raises:
            (none)

    Used by:
        portfolio.StyleFitChecker  -- book and candidate exposures
        risk.RiskModel       -- built by load_snapshot
        risk.RiskDecomposer  -- decomposition input
        risk.BaseRiskModel  -- injected type or call
        risk.RiskModelValidator  -- injected type or call
        portfolio.HoldingsRiskBuilder  -- injected type or call

    Test cases:
        TC-RSN-001  compute_variance equals h'XFX'h + h'Dh on a hand example
        TC-RSN-002  build_covered_weights drops names without a forecast and reports their weight
        TC-RSN-003  compute_exposure_vector = X'h; build_matrix fills missing pairs with 0
        TC-RSN-004  compute_stock_cov = X F X' + diag(sigma^2); h' C h equals compute_variance
    """

    trade_date: str
    exposures: pd.DataFrame
    cov: pd.DataFrame
    specific: pd.Series

    def build_covered_weights(self, weights: pd.Series) -> tuple[pd.Series, float]:
        """
        Purpose:
            Restrict weights to stocks with exposures and specific risk.

        Contract:
            Input:
                weights: Series  -- index ts_code, portfolio weights (any sign)
            Output:
                tuple[Series, float]  -- weights on covered stocks (index order of exposures),
                                         and the absolute weight dropped
            Raises:
                (none)
        """
        covered = self.exposures.index.intersection(self.specific.dropna().index)
        kept = weights[weights.index.isin(covered)]
        dropped = float(weights[~weights.index.isin(covered)].abs().sum())
        return kept.reindex(covered).fillna(0.0), dropped

    def compute_variance(self, weights: pd.Series) -> tuple[float, float]:
        """
        Purpose:
            Factor and specific variance of a portfolio (daily).

        Contract:
            Input:
                weights: Series  -- index ts_code (uncovered names are ignored)
            Output:
                tuple[float, float]  -- (factor variance, specific variance), >= 0
            Raises:
                QuantCnError  -- exposures and covariance label mismatch
        """
        if list(self.exposures.columns) != list(self.cov.columns):
            raise QuantCnError(f"{self.trade_date}: exposure and covariance factors differ")
        h, _ = self.build_covered_weights(weights)
        x = self.exposures.loc[h.index].to_numpy(float)
        b = x.T @ h.to_numpy(float)
        factor = float(b @ self.cov.to_numpy(float) @ b)
        spec = float(
            (h.to_numpy(float) ** 2 * self.specific.loc[h.index].to_numpy(float) ** 2).sum()
        )
        return max(factor, 0.0), spec

    def compute_exposure_vector(self, weights: pd.Series) -> pd.Series:
        """
        Purpose:
            Portfolio factor exposures b = X^T h.

        Contract:
            Input:
                weights: Series  -- index ts_code
            Output:
                Series  -- index factors
            Raises:
                (none)
        """
        h, _ = self.build_covered_weights(weights)
        values = self.exposures.loc[h.index].to_numpy(float).T @ h.to_numpy(float)
        return pd.Series(values, index=self.exposures.columns)

    def compute_stock_cov(self, codes: list[str]) -> pd.DataFrame:
        """
        Purpose:
            Daily covariance between stocks implied by the model: X F X^T + diag(sigma^2).

        Contract:
            Input:
                codes: list[str]  -- covered ts_codes (exposures and specific risk present)
            Output:
                DataFrame  -- codes x codes, daily variance units
            Raises:
                KeyError  -- a code without exposures or specific risk
        """
        x = self.exposures.loc[codes].to_numpy(float)
        spec = self.specific.loc[codes].to_numpy(float)
        cov = x @ self.cov.to_numpy(float) @ x.T + np.diag(spec**2)
        return pd.DataFrame(cov, index=codes, columns=codes)

    @staticmethod
    def build_matrix(rows: pd.DataFrame, labels: list[str]) -> np.ndarray:
        """
        Purpose:
            Dense K x K matrix from FACTOR_COV rows of one session.

        Contract:
            Input:
                rows: DataFrame  -- factor_i, factor_j, cov
                labels: list[str]  -- factor order
            Output:
                np.ndarray  -- (K, K); missing pairs 0
            Raises:
                (none)
        """
        wide = rows.pivot(index="factor_i", columns="factor_j", values="cov")
        return wide.reindex(index=labels, columns=labels).fillna(0.0).to_numpy(float)
