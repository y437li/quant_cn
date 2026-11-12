"""Stock-specific risk forecasts (plan 05 phase 4)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.core.frames import SPECIFIC_RISK
from quant_cn.core.risk_model_settings import RiskModelSettings
from quant_cn.risk.bayesian_shrinker import BayesianShrinker
from quant_cn.risk.ewm_window import EwmWindow
from quant_cn.risk.structural_specific_risk import StructuralSpecificRisk
from quant_cn.risk.volatility_regime_adjuster import VolatilityRegimeAdjuster


class SpecificRiskEstimator:
    """
    Purpose:
        Specific (idiosyncratic) volatility forecasts in three steps. (1) Time series: zero-mean
        EWMA of residual variance (specific_window, specific_half_life) with Newey-West lags
        (specific_nw_lags), and the residual count h in the window. (2) Per session: blend
        sigma = g sigma_ts + (1 - g) sigma_str with g = clip((h - min_obs) / (full_obs -
        min_obs), 0, 1) and sigma_str from StructuralSpecificRisk fitted on stocks with g = 1;
        then BayesianShrinker toward size-group means. (3) Volatility regime: lambda from the
        cap-weighted bias of residuals over the previous session's forecast; sigma = lambda x
        shrunk. method = ewma (g = 1), blended (0 < g < 1) or structural (g = 0).

    Contract:
        Input:
            settings: RiskModelSettings; structural: StructuralSpecificRisk
            shrinker: BayesianShrinker; regime: VolatilityRegimeAdjuster
        Output:
            instance; `compute_time_series`, `compute_session`, `compute_final`
        Raises:
            (none at construction)

    Used by:
        risk.RiskModel  -- specific risk step
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-SRE-001  time-series sigma equals the weighted residual sd for i.i.d. residuals;
                    counts equal valid residuals in the window
        TC-SRE-002  a thin history uses the structural forecast and the method label follows g
        TC-SRE-003  compute_final applies lambda from the previous session's forecasts and
                    validates SPECIFIC_RISK
    """

    def __init__(
        self,
        settings: RiskModelSettings,
        structural: StructuralSpecificRisk,
        shrinker: BayesianShrinker,
        regime: VolatilityRegimeAdjuster,
    ) -> None:
        self._s = settings
        self._structural = structural
        self._shrinker = shrinker
        self._regime = regime
        self._window = EwmWindow(settings.specific_window, settings.specific_half_life)

    def compute_time_series(self, resid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Purpose:
            EWMA + Newey-West residual vol and residual counts for every session and stock.

        Contract:
            Input:
                resid: DataFrame  -- sessions x stocks residuals (NaN = no regression row),
                                     index sorted
            Output:
                tuple[DataFrame, DataFrame]  -- sigma_ts (NaN where h < specific_min_obs) and h,
                                                both shaped like resid
            Raises:
                (none)
        """
        u = resid.to_numpy(float)
        valid = np.isfinite(u)
        x = np.where(valid, u, 0.0)
        s = self._window.compute_sum
        with np.errstate(divide="ignore", invalid="ignore"):
            var = s(x * x) / s(valid)
            lags = self._s.specific_nw_lags
            for lag in range(1, lags + 1):
                prod = np.zeros_like(x)
                both = np.zeros_like(x)
                prod[lag:] = x[lag:] * x[:-lag]
                both[lag:] = valid[lag:] & valid[:-lag]
                var = var + 2 * (1 - lag / (lags + 1)) * np.nan_to_num(s(prod) / s(both))
        h = self._window.compute_count(valid)
        sigma = np.where(h >= self._s.specific_min_obs, np.sqrt(np.clip(var, 0.0, None)), np.nan)
        return (
            pd.DataFrame(sigma, index=resid.index, columns=resid.columns),
            pd.DataFrame(h, index=resid.index, columns=resid.columns),
        )

    def compute_session(
        self, sigma_ts: np.ndarray, obs: np.ndarray, exposures: np.ndarray, cap: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Purpose:
            Blended and shrunk specific vol of one session (before the regime multiplier).

        Contract:
            Input:
                sigma_ts:  np.ndarray  -- (N,) time-series vol (NaN = too short)
                obs:       np.ndarray  -- (N,) residual counts h
                exposures: np.ndarray  -- (N, K) industry dummies and styles
                cap:       np.ndarray  -- (N,) market cap (weights, size groups)
            Output:
                tuple[np.ndarray, np.ndarray]  -- shrunk sigma (N,) and blend weight g (N,)
            Raises:
                (none)
        """
        lo, hi = self._s.specific_min_obs, self._s.specific_full_obs
        g = np.clip((np.nan_to_num(obs) - lo) / (hi - lo), 0.0, 1.0)
        g = np.where(np.isfinite(sigma_ts), g, 0.0)
        weights = np.sqrt(np.clip(np.nan_to_num(cap), 0.0, None))
        structural = self._structural.compute(sigma_ts, exposures, weights, g >= 1.0)
        blended = np.where(g >= 1.0, sigma_ts, g * np.nan_to_num(sigma_ts) + (1 - g) * structural)
        return self._shrinker.compute(blended, cap), g

    def compute_final(
        self, pre: pd.DataFrame, resid: pd.DataFrame, start: str | None = None
    ) -> pd.DataFrame:
        """
        Purpose:
            Apply the specific volatility regime multiplier and build SPECIFIC_RISK.

        Contract:
            Input:
                pre:   DataFrame  -- trade_date, ts_code, sigma (pre-regime), sigma_raw, g,
                                     cap; every session of the history
                resid: DataFrame  -- sessions x stocks residuals (as compute_time_series)
                start: str | None  -- first session to output
            Output:
                DataFrame  -- SPECIFIC_RISK sorted by key; sigma = lambda_t x pre sigma
            Raises:
                SchemaError  -- invalid output
        """
        wide = pre.pivot(index="trade_date", columns="ts_code", values="sigma")
        wide = wide.reindex(index=resid.index, columns=resid.columns)
        caps = pre.pivot(index="trade_date", columns="ts_code", values="cap")
        caps = caps.reindex(index=resid.index, columns=resid.columns)
        prev = wide.shift(1).to_numpy(float)
        bias = self._regime.compute_bias(resid.to_numpy(float), prev, caps.shift(1).to_numpy(float))
        lam = self._regime.compute_lambda(pd.Series(bias, index=resid.index))
        out = pre.assign(sigma=pre["sigma"] * pre["trade_date"].map(lam).fillna(1.0))
        out["method"] = np.select(
            [out["g"] >= 1.0, out["g"] <= 0.0], ["ewma", "structural"], "blended"
        )
        if start is not None:
            out = out[out["trade_date"] >= start]
        out = out.dropna(subset=["sigma"])[SPECIFIC_RISK.columns]
        out = out.sort_values(["trade_date", "ts_code"]).reset_index(drop=True)
        return SPECIFIC_RISK.validate(SPECIFIC_RISK.normalize(out, strict=True))
