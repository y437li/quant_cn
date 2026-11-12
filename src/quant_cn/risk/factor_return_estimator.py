"""Daily factor returns by constrained weighted least squares (plan 05 phase 3)."""

from __future__ import annotations

import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd

from quant_cn.core.frames import FACTOR_RETURN, SPECIFIC_RETURN

logger = logging.getLogger(__name__)

COUNTRY = "country"
INDUSTRY_PREFIX = "ind_"


class FactorReturnEstimator:
    """
    Purpose:
        For each return session t, regress stock returns from the close of t-1 to the close of
        t on exposures known at the close of t-1: r = f_c + sum_i X_i f_i + sum_s X_s f_s + u,
        weights sqrt(circ_mv at t-1) capped at the `weight_cap_quantile` cross-sectional
        quantile. Country and industry factors are identified by the constraint
        sum_i w_i f_i = 0 with w_i the industry's share of circ_mv, imposed by the restriction
        f = R g (the largest industry is expressed through the others), so the country factor is
        the cap-weighted market. Styles with no exposure on a session are left out of it.
        R^2 is the weighted uncentred R^2 1 - sum w u^2 / sum w r^2 (Barra convention).

    Contract:
        Input:
            styles: Sequence[str]  -- style columns in the panel, in model order
            weight_cap_quantile: float in (0, 1]
            min_names: int  -- sessions with fewer usable stocks are skipped (default 100)
        Output:
            instance; `compute(panel) -> tuple[DataFrame, DataFrame]`, `compute_monitor`,
            `compute_date`
        Raises:
            ValueError  -- weight_cap_quantile outside (0, 1]

    Used by:
        risk.RiskModel  -- factor returns step
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-FRE-001  recovers planted factor returns on a synthetic market (corr > 0.99)
        TC-FRE-002  cap-weighted industry returns sum to 0 (1e-10) every session
        TC-FRE-003  residuals are weighted-orthogonal to every factor; R^2 in [0, 1]; weights
                    capped at the quantile
        TC-FRE-004  a style missing on a session is dropped for that session only; a thin
                    session is skipped; outputs validate FACTOR_RETURN / SPECIFIC_RETURN
        TC-FRE-005  compute_monitor recovers a planted monitor return, leaves the model's own
                    estimate unchanged and reports a non-negative R^2 gain
    """

    def __init__(
        self, styles: Sequence[str], weight_cap_quantile: float = 0.95, min_names: int = 100
    ) -> None:
        if not 0 < weight_cap_quantile <= 1:
            raise ValueError("weight_cap_quantile must be in (0, 1]")
        self._styles = list(styles)
        self._cap_q = weight_cap_quantile
        self._min_names = min_names

    def compute(self, panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Purpose:
            Factor returns and residuals for every session of the panel.

        Contract:
            Input:
                panel: DataFrame  -- trade_date (return session), ts_code, ret (simple return),
                                     circ_mv (CNY, at t-1), l1_code and the style columns
                                     (exposures at t-1); NaN allowed
            Output:
                tuple[DataFrame, DataFrame]  -- FACTOR_RETURN (country, ind_<code>, styles; r2 and
                                                n_obs repeated per factor) and SPECIFIC_RETURN
                                                (resid of every regressed stock, weight = its
                                                regression weight), both sorted by key
            Raises:
                KeyError  -- missing column
        """
        factor_parts, resid_parts = [], []
        for date, part in panel.groupby("trade_date", sort=True):
            result = self.compute_date(part)
            if result is None:
                continue
            factors, resid = result
            factor_parts.append(factors.assign(trade_date=date))
            resid_parts.append(resid.assign(trade_date=date))
        factors = (
            pd.concat(factor_parts, ignore_index=True)
            if factor_parts
            else pd.DataFrame(columns=FACTOR_RETURN.columns)
        )
        resid = (
            pd.concat(resid_parts, ignore_index=True)
            if resid_parts
            else pd.DataFrame(columns=SPECIFIC_RETURN.columns)
        )
        factors = factors[FACTOR_RETURN.columns].sort_values(["trade_date", "factor"])
        resid = resid[SPECIFIC_RETURN.columns].sort_values(["trade_date", "ts_code"])
        return (
            FACTOR_RETURN.validate(
                FACTOR_RETURN.normalize(factors.reset_index(drop=True), strict=True)
            ),
            SPECIFIC_RETURN.validate(
                SPECIFIC_RETURN.normalize(resid.reset_index(drop=True), strict=True)
            ),
        )

    def compute_monitor(self, panel: pd.DataFrame, monitor: Sequence[str]) -> pd.DataFrame:
        """
        Purpose:
            Returns of monitor styles (D-130): per session the constrained WLS is rerun with one
            monitor style added to the model's styles, and only that style's coefficient,
            t-stat and the R^2 gain are kept, so the risk model itself is unchanged.

        Contract:
            Input:
                panel:   DataFrame       -- as compute, plus the monitor style columns
                monitor: Sequence[str]   -- monitor style columns
            Output:
                DataFrame  -- FACTOR_RETURN rows (factor = monitor style; r2 = R^2 with the
                              style minus R^2 without), sessions where both regressions ran
            Raises:
                KeyError  -- missing column
        """
        rows = []
        for date, part in panel.groupby("trade_date", sort=True):
            base = self.compute_date(part)
            for name in monitor:
                if name not in part or part[name].isna().all() or base is None:
                    continue
                result = self.compute_date(part, extra=(name,))
                if result is None:
                    continue
                row = result[0][result[0]["factor"] == name].iloc[0]
                gain = float(row["r2"]) - float(base[0]["r2"].iloc[0])
                rows.append(
                    {
                        "trade_date": date,
                        "factor": name,
                        "ret": row["ret"],
                        "t_stat": row["t_stat"],
                        "r2": gain,
                        "n_obs": row["n_obs"],
                    }
                )
        out = pd.DataFrame(rows, columns=FACTOR_RETURN.columns)
        return FACTOR_RETURN.validate(FACTOR_RETURN.normalize(out, strict=True))

    def compute_date(
        self, part: pd.DataFrame, extra: Sequence[str] = ()
    ) -> tuple[pd.DataFrame, pd.DataFrame] | None:
        """
        Purpose:
            The constrained WLS of one session.

        Contract:
            Input:
                part:  DataFrame      -- the panel rows of one session
                extra: Sequence[str]  -- additional style columns for this fit (monitor)
            Output:
                tuple[DataFrame, DataFrame] | None  -- (factor, ret, t_stat, r2, n_obs) and
                                                       (ts_code, resid, weight); None when fewer
                                                       than min_names usable rows
            Raises:
                KeyError  -- missing column
        """
        names = [*self._styles, *extra]
        styles = [s for s in names if s in part and part[s].notna().any()]
        use = part.dropna(subset=["ret", "circ_mv", "l1_code", *styles])
        use = use[use["circ_mv"] > 0]
        if len(use) < self._min_names:
            return None
        weight = np.sqrt(use["circ_mv"].to_numpy(float))
        weight = np.minimum(weight, np.quantile(weight, self._cap_q))
        industries = sorted(use["l1_code"].astype(str).unique())
        dummies = (use["l1_code"].astype(str).to_numpy()[:, None] == np.array(industries)).astype(
            float
        )
        x = np.hstack([np.ones((len(use), 1)), dummies, use[styles].to_numpy(float)])
        restrict = self._build_restriction(dummies, use["circ_mv"].to_numpy(float), len(styles))
        f, se, resid, r2 = self._compute_wls(x, restrict, use["ret"].to_numpy(float), weight)
        names = [COUNTRY, *[INDUSTRY_PREFIX + i for i in industries], *styles]
        factors = pd.DataFrame(
            {"factor": names, "ret": f, "t_stat": f / se, "r2": r2, "n_obs": float(len(use))}
        )
        return factors, pd.DataFrame(
            {"ts_code": use["ts_code"].to_numpy(), "resid": resid, "weight": weight}
        )

    @staticmethod
    def _build_restriction(dummies: np.ndarray, cap: np.ndarray, n_styles: int) -> np.ndarray:
        """K x (K-1) matrix R with f = R g; the largest industry is the dependent one."""
        share = (dummies * cap[:, None]).sum(axis=0)
        n_ind = dummies.shape[1]
        drop = int(np.argmax(share))
        k = 1 + n_ind + n_styles
        restrict = np.zeros((k, k - 1))
        free = [c for c in range(k) if c != 1 + drop]
        for j, c in enumerate(free):
            restrict[c, j] = 1.0
        for j, c in enumerate(free):
            if 1 <= c <= n_ind:
                restrict[1 + drop, j] = -share[c - 1] / share[drop]
        return restrict

    @staticmethod
    def _compute_wls(
        x: np.ndarray, restrict: np.ndarray, r: np.ndarray, w: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        b = x @ restrict
        bw = b * w[:, None]
        xtx = b.T @ bw
        inv = np.linalg.pinv(xtx)
        g = inv @ (bw.T @ r)
        f = restrict @ g
        resid = r - x @ f
        dof = max(len(r) - b.shape[1], 1)
        sigma2 = float((w * resid**2).sum() / dof)
        cov = restrict @ (sigma2 * inv) @ restrict.T
        se = np.sqrt(np.clip(np.diag(cov), 1e-30, None))
        total = float((w * r**2).sum())
        r2 = 1.0 - float((w * resid**2).sum()) / total if total > 0 else np.nan
        return f, se, resid, r2
