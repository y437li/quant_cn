"""Bias statistics and fit quality of a risk model (RISK_MODEL_DESIGN §6, plan 05 phase 5)."""

from __future__ import annotations

import itertools
import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd

from quant_cn.core.frames import FACTOR_COV, FACTOR_RETURN, RISK_VALIDATION
from quant_cn.risk.base_risk_model import BaseRiskModel
from quant_cn.risk.risk_snapshot import RiskSnapshot

logger = logging.getLogger(__name__)


class RiskModelValidator:
    """
    Purpose:
        Test whether forecasts match realised risk. Bias statistic of a series of forecasts:
        B = sd(z) with z_t = r_{t+1} / sigma_t (forecast at the close of t, return over t+1);
        B ~ 1 when unbiased, with a 95% band of about 1 +- sqrt(2 / T). Applied to every factor
        (FACTOR_COV diagonal vs FACTOR_RETURN), to random long-only portfolios (snapshots of
        the model vs realised stock returns) and to any named portfolio (e.g. CSI 300 weights).
        Also reports the cross-sectional fit (median / mean R^2) and the q-statistic
        mean(z^2 - ln z^2) when asked.

    Contract:
        Input:
            model: BaseRiskModel  -- snapshots for portfolio forecasts
            seed:  int            -- random portfolio RNG seed
        Output:
            instance; `compute_bias`, `compute_factor_bias`, `build_random_portfolios`,
            `compute_portfolio_forecasts`, `compute_fit`
        Raises:
            (none at construction)

    Used by:
        research_space/notebooks/20261111_risk_model_validation.ipynb  -- acceptance tests
        pipeline.RiskValidationWriter  -- injected type or call
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-RMV-001  compute_bias ~ 1 for returns drawn with the forecast vol, ~ k when the
                    forecast is k times too low; window and count reported
        TC-RMV-002  factor bias pairs the covariance at t with the return at t+1 (no overlap)
        TC-RMV-003  random portfolios are long-only, sum to 1, reproducible by seed
        TC-RMV-004  portfolio forecasts come from the model snapshots and pair with next-session
                    returns; compute_fit reports median and mean R^2; frames validate
    """

    def __init__(self, model: BaseRiskModel, seed: int = 20260928) -> None:
        self._model = model
        self._seed = seed

    @staticmethod
    def compute_bias(paired: pd.DataFrame, scope_column: str = "scope") -> pd.DataFrame:
        """
        Purpose:
            Bias statistic and q-statistic per scope.

        Contract:
            Input:
                paired: DataFrame  -- trade_date (forecast session), <scope_column>, sigma
                                      (forecast vol), ret (realised next-session return)
                scope_column: str
            Output:
                DataFrame  -- RISK_VALIDATION: metrics bias (sd of z), q_stat, n_obs per scope;
                              trade_date = last forecast session; window = "first-last"
            Raises:
                KeyError  -- missing column
        """
        ok = paired[(paired["sigma"] > 0) & paired["ret"].notna()]
        z = ok["ret"] / ok["sigma"]
        work = ok.assign(z=z, q=z**2 - np.log(np.clip(z**2, 1e-12, None)))
        rows = []
        for scope, part in work.groupby(scope_column):
            window = f"{part['trade_date'].min()}-{part['trade_date'].max()}"
            last = part["trade_date"].max()
            for metric, value in (
                ("bias", float(part["z"].std(ddof=1))),
                ("q_stat", float(part["q"].mean())),
                ("n_obs", float(len(part))),
            ):
                rows.append(
                    {
                        "trade_date": last,
                        "metric": metric,
                        "scope": str(scope),
                        "value": value,
                        "window": window,
                        "notes": "",
                    }
                )
        out = pd.DataFrame(rows, columns=RISK_VALIDATION.columns)
        return RISK_VALIDATION.validate(RISK_VALIDATION.normalize(out, strict=True))

    def compute_factor_bias(
        self, factor_returns: pd.DataFrame, factor_cov: pd.DataFrame, start: str, end: str
    ) -> pd.DataFrame:
        """
        Purpose:
            Bias statistic of every factor's variance forecast over forecasts made in [start, end].

        Contract:
            Input:
                factor_returns: DataFrame  -- FACTOR_RETURN
                factor_cov:     DataFrame  -- FACTOR_COV (diagonal used)
                start, end:     str        -- forecast sessions, YYYYMMDD
            Output:
                DataFrame  -- RISK_VALIDATION, scope "factor:<name>"
            Raises:
                SchemaError  -- invalid inputs
        """
        FACTOR_RETURN.validate(factor_returns)
        FACTOR_COV.validate(factor_cov)
        diag = factor_cov[factor_cov["factor_i"] == factor_cov["factor_j"]]
        sigma = diag.assign(sigma=np.sqrt(diag["cov"]))[["trade_date", "factor_i", "sigma"]]
        sessions = sorted(factor_returns["trade_date"].unique())
        nxt = dict(itertools.pairwise(sessions))
        sigma = sigma.assign(next_date=sigma["trade_date"].map(nxt)).rename(
            columns={"factor_i": "factor"}
        )
        paired = sigma.merge(
            factor_returns[["trade_date", "factor", "ret"]].rename(
                columns={"trade_date": "next_date"}
            ),
            on=["next_date", "factor"],
        )
        paired = paired[(paired["trade_date"] >= start) & (paired["trade_date"] <= end)]
        return self.compute_bias(paired.assign(scope="factor:" + paired["factor"]))

    def build_random_portfolios(self, names: Sequence[str], count: int, size: int) -> pd.DataFrame:
        """
        Purpose:
            Random long-only portfolios: `size` names drawn without replacement, Dirichlet(1)
            weights.

        Contract:
            Input:
                names: Sequence[str]  -- candidate ts_codes (e.g. the estimation universe)
                count: int >= 1; size: int >= 1 (capped at len(names))
            Output:
                DataFrame  -- portfolio ("rp_000"...), ts_code, weight; weights > 0 sum to 1
            Raises:
                ValueError  -- empty names
        """
        if not names:
            raise ValueError("no names to draw from")
        rng = np.random.default_rng(self._seed)
        k = min(size, len(names))
        rows = []
        for i in range(count):
            picks = rng.choice(np.array(sorted(names)), size=k, replace=False)
            weights = rng.dirichlet(np.ones(k))
            rows.append(
                pd.DataFrame({"portfolio": f"rp_{i:03d}", "ts_code": picks, "weight": weights})
            )
        return pd.concat(rows, ignore_index=True)

    def compute_portfolio_forecasts(
        self, portfolios: pd.DataFrame, sessions: Sequence[str], returns: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Purpose:
            Forecast vol at each session and the realised return over the next session for
            each portfolio (fixed weights, renormalised over names with a return).

        Contract:
            Input:
                portfolios: DataFrame  -- portfolio, ts_code, weight
                sessions:   Sequence[str]  -- forecast sessions in order (each needs stored frames)
                returns:    DataFrame  -- trade_date, ts_code, ret (simple daily returns)
            Output:
                DataFrame  -- trade_date, scope (portfolio), sigma, ret
            Raises:
                LakeError  -- frames missing for a session
        """
        nxt = dict(itertools.pairwise(sessions))
        wide = returns.pivot(index="trade_date", columns="ts_code", values="ret")
        weights = portfolios.pivot_table(
            index="ts_code", columns="portfolio", values="weight", aggfunc="sum"
        ).fillna(0.0)
        parts = []
        for date in sessions[:-1]:
            sigma = self._compute_sigmas(self._model.load_snapshot(date), weights)
            realized = self._get_row(wide, nxt[date]).reindex(weights.index).to_numpy(float)
            held = np.isfinite(realized)
            w = weights.to_numpy(float)
            total = w[held].sum(axis=0)
            with np.errstate(divide="ignore", invalid="ignore"):
                ret = np.where(
                    total > 0, (w[held] * realized[held, None]).sum(axis=0) / total, np.nan
                )
            parts.append(
                pd.DataFrame(
                    {
                        "trade_date": date,
                        "scope": weights.columns.astype(str),
                        "sigma": sigma,
                        "ret": ret,
                    }
                )
            )
        return (
            pd.concat(parts, ignore_index=True)
            if parts
            else pd.DataFrame(columns=["trade_date", "scope", "sigma", "ret"])
        )

    @staticmethod
    def _compute_sigmas(snap: RiskSnapshot, weights: pd.DataFrame) -> np.ndarray:
        """Forecast vol of every portfolio column at once (uncovered names ignored)."""
        covered = snap.exposures.index.intersection(snap.specific.dropna().index)
        w = weights.reindex(covered).fillna(0.0).to_numpy(float)
        x = snap.exposures.loc[covered].to_numpy(float)
        b = x.T @ w
        factor = np.einsum("kp,kl,lp->p", b, snap.cov.to_numpy(float), b)
        spec = (w**2).T @ (snap.specific.loc[covered].to_numpy(float) ** 2)
        return np.asarray(np.sqrt(np.clip(factor, 0.0, None) + spec), dtype=float)

    @staticmethod
    def _get_row(wide: pd.DataFrame, date: str) -> pd.Series:
        if date not in wide.index:
            return pd.Series(dtype=float)
        row = wide.loc[date]
        return row if isinstance(row, pd.Series) else row.iloc[0]

    @staticmethod
    def compute_fit(factor_returns: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
        """
        Purpose:
            Cross-sectional fit summary: median and mean R^2 and median adjusted R^2 of the daily
            regressions (adjusted R^2 compares models with different factor counts).

        Contract:
            Input:
                factor_returns: DataFrame  -- FACTOR_RETURN
                start, end: str            -- sessions, YYYYMMDD
            Output:
                DataFrame  -- RISK_VALIDATION rows median_r2, mean_r2 and median_adj_r2
                              (1 - (1 - R2)(n - 1)/(n - p), p = factors - 1; scope "model")
            Raises:
                KeyError  -- missing column
        """
        per_date = factor_returns.groupby("trade_date").agg(
            r2=("r2", "first"), n=("n_obs", "first"), k=("factor", "size")
        )
        per_date = per_date[(per_date.index >= start) & (per_date.index <= end)]
        r2 = per_date["r2"]
        free = per_date["k"] - 1  # one industry is fixed by the cap-weighted constraint
        adj = 1 - (1 - r2) * (per_date["n"] - 1) / (per_date["n"] - free).clip(lower=1)
        window = f"{start}-{end}"
        rows = [
            {
                "trade_date": end,
                "metric": m,
                "scope": "model",
                "value": float(v),
                "window": window,
                "notes": "",
            }
            for m, v in (
                ("median_r2", r2.median()),
                ("mean_r2", r2.mean()),
                ("median_adj_r2", adj.median()),
            )
        ]
        return RISK_VALIDATION.validate(RISK_VALIDATION.normalize(pd.DataFrame(rows), strict=True))
