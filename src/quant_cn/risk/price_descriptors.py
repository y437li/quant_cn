"""CNE5 price and turnover descriptors on date x stock matrices (RISK_FACTOR_LIST §1, plan 05)."""

from __future__ import annotations

import numpy as np

from quant_cn.risk.ewm_window import EwmWindow

MONTH = 21  # sessions per month in CNE5 descriptor definitions
SINGULAR = 1e-8  # det / (var_m var_x) below this = collinear regressors


class PriceDescriptors:
    """
    Purpose:
        The CNE5 descriptors that need only daily returns and turnover, computed for every
        session and stock at once on wide matrices (rows = sessions in order, columns = stocks):
        BETA and HSIGMA (exponentially weighted regression on the cap-weighted market, 252 d,
        half-life 63), RSTR (weighted sum of log returns over 504 d, half-life 126, lag 21),
        DASTD (weighted sd of returns, 252 d, half-life 42), CMRA (range of cumulative log
        returns over the last 12 months), STOM / STOQ / STOA (log share turnover over 1 / 3 / 12
        months). Values at row t use rows <= t only.

    Contract:
        Input:
            beta_window, beta_half_life, rstr_window, rstr_half_life, rstr_lag, vol_window,
            vol_half_life: int  -- CNE5 defaults 252 / 63 / 504 / 126 / 21 / 252 / 42
            min_obs:       int  -- valid returns a regression / volatility window needs (63)
        Output:
            instance; `compute_beta`, `compute_partial_beta`, `compute_rstr`, `compute_dastd`,
            `compute_cmra`, `compute_liquidity`
        Raises:
            ValueError  -- non-positive windows

    Used by:
        risk.DescriptorBuilder  -- price descriptors
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-PD-001  beta and hsigma recover a planted beta and residual sd on simulated returns
        TC-PD-002  rstr skips the last `lag` sessions; too few observations give NaN
        TC-PD-003  dastd equals the weighted sd; cmra equals max - min cumulative monthly log return
        TC-PD-004  liquidity: stom = ln(21-day turnover sum), stoq / stoa monthly means; 0 -> NaN
        TC-PD-005  partial beta recovers a planted external slope with the market controlled;
                   an external series equal to the market gives NaN (singular)
    """

    def __init__(
        self,
        beta_window: int = 252,
        beta_half_life: int = 63,
        rstr_window: int = 504,
        rstr_half_life: int = 126,
        rstr_lag: int = 21,
        vol_window: int = 252,
        vol_half_life: int = 42,
        min_obs: int = 63,
    ) -> None:
        self._beta = EwmWindow(beta_window, beta_half_life)
        self._rstr = EwmWindow(rstr_window, rstr_half_life, lag=rstr_lag)
        self._vol = EwmWindow(vol_window, vol_half_life)
        self._min_obs = min_obs

    def compute_beta(
        self, returns: np.ndarray, market: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Purpose:
            BETA (slope) and HSIGMA (residual sd) of the weighted regression r = a + b m + e.

        Contract:
            Input:
                returns: np.ndarray  -- (T, N) daily simple returns, NaN = no trade
                market:  np.ndarray  -- (T,) cap-weighted market return
            Output:
                tuple[np.ndarray, np.ndarray]  -- beta, hsigma, each (T, N); NaN where the
                                                  window holds < min_obs valid returns
            Raises:
                (none)
        """
        valid = np.isfinite(returns) & np.isfinite(market)[:, None]
        r = np.where(valid, returns, 0.0)
        m = np.where(valid, market[:, None], 0.0)
        s = self._beta.compute_sum
        w = s(valid)
        with np.errstate(divide="ignore", invalid="ignore"):
            mx, my = s(m) / w, s(r) / w
            var_m = s(m * m) / w - mx * mx
            cov = s(r * m) / w - mx * my
            var_r = s(r * r) / w - my * my
            beta = cov / var_m
            resid = np.clip(var_r - beta * cov, 0.0, None)
        enough = self._beta.compute_count(valid) >= self._min_obs
        return np.where(enough, beta, np.nan), np.where(enough, np.sqrt(resid), np.nan)

    def compute_partial_beta(
        self, returns: np.ndarray, market: np.ndarray, external: np.ndarray
    ) -> np.ndarray:
        """
        Purpose:
            Slope on an external return in the weighted regression r = a + b m + c x + e (same
            window and half-life as BETA): the sensitivity to x beyond the home market m, e.g.
            the S&P 500 overnight return (D-128).

        Contract:
            Input:
                returns:  np.ndarray  -- (T, N) daily simple returns, NaN = no trade
                market:   np.ndarray  -- (T,) home cap-weighted market return
                external: np.ndarray  -- (T,) external return aligned to the same sessions, or
                                         (T, N) one series per stock (theme basket without the
                                         stock); NaN = unknown
            Output:
                np.ndarray  -- (T, N) coefficient c; NaN with < min_obs valid rows or a singular
                               window
            Raises:
                (none)
        """
        ext = external if external.ndim == 2 else external[:, None]  # noqa: PLR2004 -- matrix
        valid = np.isfinite(returns) & np.isfinite(market)[:, None] & np.isfinite(ext)
        r = np.where(valid, returns, 0.0)
        m = np.where(valid, market[:, None], 0.0)
        x = np.where(valid, ext, 0.0)
        s = self._beta.compute_sum
        w = s(valid)
        with np.errstate(divide="ignore", invalid="ignore"):
            mm, mx, mr = s(m) / w, s(x) / w, s(r) / w
            c_mm = s(m * m) / w - mm * mm
            c_xx = s(x * x) / w - mx * mx
            c_mx = s(m * x) / w - mm * mx
            c_mr = s(m * r) / w - mm * mr
            c_xr = s(x * r) / w - mx * mr
            det = c_mm * c_xx - c_mx * c_mx
            ok = np.abs(det) > SINGULAR * c_mm * c_xx  # relative: collinear m and x
            coef = (c_mm * c_xr - c_mx * c_mr) / np.where(ok, det, np.nan)
        enough = self._beta.compute_count(valid) >= self._min_obs
        return np.where(enough, coef, np.nan)

    def compute_rstr(self, returns: np.ndarray) -> np.ndarray:
        """
        Purpose:
            RSTR: weighted sum of ln(1 + r) over the window, skipping the most recent `lag`.

        Contract:
            Input:
                returns: np.ndarray  -- (T, N) simple returns, NaN = no trade (contributes 0)
            Output:
                np.ndarray  -- (T, N); NaN with fewer than half the window's sessions valid
            Raises:
                (none)
        """
        valid = np.isfinite(returns)
        logs = np.log1p(np.where(valid, np.clip(returns, -0.99, None), 0.0))
        enough = self._rstr.compute_count(valid) >= len(self._rstr.weights) / 2
        return np.where(enough, self._rstr.compute_sum(logs), np.nan)

    def compute_dastd(self, returns: np.ndarray) -> np.ndarray:
        """
        Purpose:
            DASTD: exponentially weighted standard deviation of daily returns.

        Contract:
            Input:
                returns: np.ndarray  -- (T, N), NaN = no trade (excluded, weights renormalised)
            Output:
                np.ndarray  -- (T, N) >= 0; NaN with < min_obs valid returns
            Raises:
                (none)
        """
        valid = np.isfinite(returns)
        r = np.where(valid, returns, 0.0)
        s = self._vol.compute_sum
        w = s(valid)
        with np.errstate(divide="ignore", invalid="ignore"):
            mean = s(r) / w
            var = np.clip(s(r * r) / w - mean * mean, 0.0, None)
        enough = self._vol.compute_count(valid) >= self._min_obs
        return np.where(enough, np.sqrt(var), np.nan)

    def compute_cmra(self, returns: np.ndarray, months: int = 12) -> np.ndarray:
        """
        Purpose:
            CMRA: max minus min over T = 1..months of the cumulative log return of the last
            T months (Z(T) = sum of ln(1 + r) over the last 21 T sessions), i.e.
            ln(1 + R_max) - ln(1 + R_min) for cumulative simple returns R.

        Contract:
            Input:
                returns: np.ndarray  -- (T, N); NaN contributes 0
                months:  int >= 1
            Output:
                np.ndarray  -- (T, N) >= 0; NaN until 21 * months rows of history, or with fewer
                               than half of those sessions valid
            Raises:
                (none)
        """
        valid = np.isfinite(returns)
        logs = np.log1p(np.where(valid, np.clip(returns, -0.99, None), 0.0))
        cum = np.vstack([np.zeros((1, logs.shape[1])), np.cumsum(logs, axis=0)])
        n_rows, span = logs.shape[0], MONTH * months
        out = np.full(logs.shape, np.nan)
        if n_rows < span:
            return out
        end = cum[span:]  # cum after row t, t = span-1 .. n_rows-1
        z = np.stack(
            [end - cum[span - MONTH * k : n_rows + 1 - MONTH * k] for k in range(1, months + 1)]
        )
        out[span - 1 :] = z.max(axis=0) - z.min(axis=0)
        counts = EwmWindow(span, np.inf).compute_count(valid)
        return np.where(counts >= span / 2, out, np.nan)

    def compute_liquidity(self, turnover: np.ndarray) -> dict[str, np.ndarray]:
        """
        Purpose:
            STOM, STOQ, STOA from daily share turnover (a fraction of free-float shares).

        Contract:
            Input:
                turnover: np.ndarray  -- (T, N) daily turnover fraction; NaN = no row (counts 0)
            Output:
                dict[str, np.ndarray]  -- "stom" = ln(sum 21 d), "stoq" = ln(sum 63 d / 3),
                                          "stoa" = ln(sum 252 d / 12); NaN when the sum is 0 or
                                          fewer than half of the window's rows exist
            Raises:
                (none)
        """
        has_row = np.isfinite(turnover)
        out: dict[str, np.ndarray] = {}
        for name, months in (("stom", 1), ("stoq", 3), ("stoa", 12)):
            window = EwmWindow(MONTH * months, np.inf)
            total = window.compute_sum(turnover) * (MONTH * months) / months
            enough = window.compute_count(has_row) >= MONTH * months / 2
            with np.errstate(divide="ignore"):
                out[name] = np.where(enough & (total > 0), np.log(total), np.nan)
        return out
