"""Single-factor significance tests on an IC series (FACTOR_TESTING_DESIGN §2, §10)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import stats

from quant_cn.core.frames import IC_SERIES, IC_TEST
from quant_cn.statistic.block_bootstrap import BlockBootstrap
from quant_cn.statistic.hac_variance import HacVariance

SUBPERIODS: dict[str, tuple[str, str]] = {
    "2019-2021": ("20190101", "20211231"),
    "2022-2024": ("20220101", "20241231"),
    "2025-": ("20250101", "99991231"),
}
TRIM = 0.15
ANDREWS_5PCT = 8.68  # Andrews (1993) sup-F critical value, one parameter, 15% trimming, 5%
Values = Sequence[float] | np.ndarray


class IcSignificance:
    """
    Purpose:
        The §2 tests for one factor at one horizon: Newey-West t on mean IC (Newey & West 1987,
        1994, prewhitened per D-090), stationary block-bootstrap CI of mean IC and ICIR (Politis &
        Romano 1994), Fisher-z / Stouffer screen, sign consistency per sub-period, single break in
        mean (Bai & Perron 1998; sup-F critical values of Andrews 1993), plus Pesaran-Timmermann
        directional accuracy (1992, 2009) and an exponential decay fit across horizons.

    Contract:
        Input:
            hac:       HacVariance
            bootstrap: BlockBootstrap
            subperiods: Mapping[str, tuple[str, str]]  -- window name -> (start, end)
        Output:
            instance; `compute`, `compute_break`, `compute_pesaran_timmermann`, `compute_decay`
        Raises:
            (none at construction)

    Used by:
        factor.FactorEvaluator  -- injected type or call

    Test cases:
        TC-ICS-001  compute returns ic_mean (NW t, bootstrap CI), icir, fisher_z and one row per
                    sub-period, as IC_TEST
        TC-ICS-002  compute_break finds a planted mean shift near its date (sup-F above the 5%
                    value); a stable series stays below it in most samples
        TC-ICS-003  known answer: Pesaran-Timmermann p is uniform on independent signs (KS) and
                    rejects near 5% at the 5% level; a skilled signal is detected
        TC-ICS-004  compute_decay recovers the half-life of an exponential IC profile
    """

    def __init__(
        self,
        hac: HacVariance,
        bootstrap: BlockBootstrap,
        subperiods: Mapping[str, tuple[str, str]] = SUBPERIODS,
    ) -> None:
        self._hac = hac
        self._boot = bootstrap
        self._subperiods = dict(subperiods)

    def compute(self, ic_series: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            IC_TEST rows for one factor and horizon.

        Contract:
            Input:
                ic_series: DataFrame  -- IC_SERIES rows of one factor and one horizon
            Output:
                DataFrame  -- IC_TEST (window "full" and one per sub-period):
                              ic_mean: mu = mean(IC_t), se = sqrt(Omega / T), t = mu / se, p
                                       Student-t (T - 1 df), CI = bootstrap percentile of mu;
                              icir:    mu / sd(IC_t), CI and p from the block bootstrap;
                              fisher_z: Z = sum_t atanh(IC_t) sqrt(n_t - 3) / sqrt(T), p normal
                              (Stouffer; screen only)
            Raises:
                SchemaError -- not IC_SERIES
                ValueError  -- more than one factor or horizon, or fewer than 3 dates
        """
        frame = IC_SERIES.validate(ic_series).sort_values("trade_date")
        if frame["factor"].nunique() != 1 or frame["horizon"].nunique() != 1:
            raise ValueError("pass one factor and one horizon")
        factor, horizon = str(frame["factor"].iloc[0]), int(frame["horizon"].iloc[0])
        ic = frame["ic"].to_numpy(float)
        block = self._boot.compute_block(horizon)
        rows = [self._build_mean_row(factor, horizon, ic, "full", block)]
        rows += self._build_full_rows(frame, factor, horizon, block)
        for name, (lo, hi) in self._subperiods.items():
            part = frame[(frame["trade_date"] >= lo) & (frame["trade_date"] <= hi)]["ic"]
            if len(part) >= 3:  # noqa: PLR2004 -- HAC needs three points
                rows.append(self._build_mean_row(factor, horizon, part.to_numpy(float), name, None))
        return IC_TEST.validate(IC_TEST.normalize(pd.DataFrame(rows), strict=True))

    def compute_break(self, ic_series: pd.DataFrame, horizon: int = 1) -> dict[str, object]:
        """
        Purpose:
            Single structural break in mean IC.

        Contract:
            Input:
                ic_series: DataFrame  -- IC_SERIES of one factor and horizon
                horizon:   int >= 1   -- for the HAC lag
            Output:
                dict  -- sup_f = max_{tau in [0.15T, 0.85T]} F(tau), F(tau) = (mu_2 - mu_1)^2 /
                         (Omega_e (1/T_1 + 1/T_2)) with Omega_e the HAC variance of the residuals
                         from the two segment means; break_date (first date of segment 2);
                         critical_5pct = 8.68 (Andrews 1993); significant (sup_f > critical)
            Raises:
                ValueError  -- fewer than 20 dates
        """
        frame = IC_SERIES.validate(ic_series).sort_values("trade_date")
        x, dates = frame["ic"].to_numpy(float), frame["trade_date"].tolist()
        n = len(x)
        if n < 20:  # noqa: PLR2004 -- trimming needs a minimal sample
            raise ValueError("need at least 20 dates")
        best, best_tau = -1.0, 0
        for tau in range(int(TRIM * n), int((1 - TRIM) * n) + 1):
            left, right = x[:tau], x[tau:]
            resid = np.concatenate([left - left.mean(), right - right.mean()])
            omega = self._hac.compute_hac_variance(resid, horizon)
            f_stat = (right.mean() - left.mean()) ** 2 / (omega * (1 / len(left) + 1 / len(right)))
            if f_stat > best:
                best, best_tau = float(f_stat), tau
        return {
            "sup_f": best,
            "break_date": dates[best_tau],
            "critical_5pct": ANDREWS_5PCT,
            "significant": best > ANDREWS_5PCT,
        }

    def compute_pesaran_timmermann(self, signal: Values, outcome: Values) -> dict[str, float]:
        """
        Purpose:
            Directional accuracy of sign(signal) for sign(outcome) beyond chance.

        Contract:
            Input:
                signal, outcome: Values  -- aligned (pooled stock-dates or a return series)
            Output:
                dict  -- pt_2009: y_t = 1{r_t > 0}, x_t = 1{f_t > 0}; OLS y = a + beta x;
                         PT = beta / se_HAC(beta), p_2009 two-sided normal (Pesaran & Timmermann
                         2009); pt_1992 = (P - P*) / sqrt(V(P) - V(P*)), P* = Py Px + (1-Py)(1-Px),
                         p_1992 normal (Pesaran & Timmermann 1992); hit_rate P
            Raises:
                ValueError  -- lengths differ or fewer than 3 observations
        """
        f, r = np.asarray(signal, float), np.asarray(outcome, float)
        if f.shape != r.shape:
            raise ValueError("signal and outcome differ in length")
        keep = ~(np.isnan(f) | np.isnan(r))
        x, y = (f[keep] > 0).astype(float), (r[keep] > 0).astype(float)
        n = len(x)
        var_x = float(((x - x.mean()) ** 2).mean())
        beta = float(((x - x.mean()) * (y - y.mean())).mean() / var_x) if var_x > 0 else 0.0
        resid = (y - y.mean()) - beta * (x - x.mean())
        score = (x - x.mean()) * resid
        se = math.sqrt(self._hac.compute_hac_variance(score) / n) / var_x if var_x > 0 else math.inf
        pt_2009 = beta / se if se > 0 else 0.0
        p_hat, py, px = float((x == y).mean()), float(y.mean()), float(x.mean())
        p_star = py * px + (1 - py) * (1 - px)
        v_p = p_star * (1 - p_star) / n
        v_star = ((2 * py - 1) ** 2 * px * (1 - px) + (2 * px - 1) ** 2 * py * (1 - py)) / n
        v_star += 4 * py * px * (1 - py) * (1 - px) / n**2
        denom = math.sqrt(max(v_p - v_star, 1e-300))
        pt_1992 = (p_hat - p_star) / denom
        return {
            "pt_2009": pt_2009,
            "p_2009": float(2 * stats.norm.sf(abs(pt_2009))),
            "pt_1992": pt_1992,
            "p_1992": float(2 * stats.norm.sf(abs(pt_1992))),
            "hit_rate": p_hat,
            "n": float(n),
        }

    @staticmethod
    def compute_decay(mean_ic: Mapping[int, float]) -> dict[str, float]:
        """
        Purpose:
            Exponential decay of mean IC over horizons.

        Contract:
            Input:
                mean_ic: Mapping[int, float]  -- horizon h -> mean IC (same sign expected)
            Output:
                dict  -- fit ln|IC_h| = ln a - (ln 2 / H) h by OLS; half_life H (inf if not
                         decaying), r2 of the log fit, n horizons
            Raises:
                ValueError  -- fewer than 2 horizons with non-zero IC
        """
        pairs = [(h, abs(v)) for h, v in sorted(mean_ic.items()) if v]
        if len(pairs) < 2:  # noqa: PLR2004 -- a slope needs two points
            raise ValueError("need at least two horizons with non-zero IC")
        h = np.array([p[0] for p in pairs], float)
        y = np.log([p[1] for p in pairs])
        slope, intercept = np.polyfit(h, y, 1)
        fitted = intercept + slope * h
        total = float(((y - y.mean()) ** 2).sum())
        r2 = 1 - float(((y - fitted) ** 2).sum()) / total if total > 0 else 1.0
        half_life = math.log(2) / -slope if slope < 0 else math.inf
        return {"half_life": float(half_life), "r2": r2, "n": float(len(h))}

    def _build_full_rows(
        self, frame: pd.DataFrame, factor: str, horizon: int, block: int
    ) -> list[dict[str, object]]:
        ic = frame["ic"].to_numpy(float)
        icir = self._boot.compute_interval(ic, self._compute_icir, block)
        z = np.arctanh(np.clip(ic, -0.999999, 0.999999)) * np.sqrt(np.maximum(frame["n"] - 3, 0))
        stouffer = float(z.sum() / math.sqrt(len(z)))
        return [
            self._build_row(
                factor,
                horizon,
                "icir",
                "full",
                icir["estimate"],
                ci=(icir["ci_lo"], icir["ci_hi"]),
                p=icir["p"],
            ),
            self._build_row(
                factor,
                horizon,
                "fisher_z",
                "full",
                stouffer,
                t=stouffer,
                p=float(2 * stats.norm.sf(abs(stouffer))),
            ),
        ]

    def _build_mean_row(
        self, factor: str, horizon: int, ic: np.ndarray, window: str, block: int | None
    ) -> dict[str, object]:
        nw = self._hac.compute_t(ic, horizon)
        ci: tuple[float, float] | None = None
        if block is not None:
            boot = self._boot.compute_interval(ic, np.mean, block)
            ci = (boot["ci_lo"], boot["ci_hi"])
        return self._build_row(
            factor, horizon, "ic_mean", window, nw["mean"], se=nw["se"], t=nw["t"], p=nw["p"], ci=ci
        )

    @staticmethod
    def _build_row(
        factor: str,
        horizon: int,
        metric: str,
        window: str,
        value: float,
        se: float | None = None,
        t: float | None = None,
        p: float | None = None,
        ci: tuple[float, float] | None = None,
    ) -> dict[str, object]:
        return {
            "factor": factor,
            "horizon": float(horizon),
            "metric": metric,
            "value": value,
            "se": se,
            "t": t,
            "p": p,
            "ci_lo": ci[0] if ci else None,
            "ci_hi": ci[1] if ci else None,
            "window": window,
            "p_adj_holm": None,
            "p_adj_bhy": None,
            "p_adj_romano_wolf": None,
            "hlz_pass": None,
        }

    @staticmethod
    def _compute_icir(values: np.ndarray) -> float:
        sd = float(np.std(values, ddof=1))
        return float(np.mean(values) / sd) if sd > 0 else 0.0
