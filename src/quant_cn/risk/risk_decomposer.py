"""Portfolio risk attribution from a risk snapshot (plan 05 phase 5)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.core.frames import RISK_DECOMP
from quant_cn.risk.risk_snapshot import RiskSnapshot


class RiskDecomposer:
    """
    Purpose:
        Euler decomposition of a portfolio's forecast volatility at one session: total, factor
        and specific risk, each factor's contribution b_k (F b)_k / sigma (contributions plus
        the specific part h' D h / sigma sum to sigma), and the portfolio's factor exposures.
        With a benchmark, the same for active weights h - h_b (tracking error). Daily units;
        annualise with sqrt(252) when presenting.

    Contract:
        Input:
            (none)
        Output:
            instance; `compute(snapshot, weights, portfolio, benchmark) -> DataFrame`
        Raises:
            (none)

    Used by:
        research_space/notebooks/20261111_risk_model_validation.ipynb  -- attribution
        portfolio.HoldingsRiskBuilder  -- injected type or call
        cli.AppServiceBuilder  -- wires it

    Test cases:
        TC-RD-001  factor contributions + specific = total; pct sums to 1; total matches
                   RiskSnapshot.compute_variance
        TC-RD-002  a benchmark adds active rows whose total is the tracking error of h - h_b;
                   output validates RISK_DECOMP
    """

    def compute(
        self,
        snapshot: RiskSnapshot,
        weights: pd.Series,
        portfolio: str,
        benchmark: pd.Series | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            RISK_DECOMP rows of one portfolio (and its active version against a benchmark).

        Contract:
            Input:
                snapshot:  RiskSnapshot
                weights:   Series  -- index ts_code, weights
                portfolio: str     -- RISK_DECOMP.portfolio label
                benchmark: Series | None  -- index ts_code, benchmark weights
            Output:
                DataFrame  -- RISK_DECOMP: components total / factor / specific (kind = total /
                              factor / specific), f:<factor> contributions (kind factor),
                              x:<factor> exposures (risk = exposure, pct NaN, kind exposure);
                              active rows prefixed "active_" with kind active
            Raises:
                QuantCnError  -- snapshot label mismatch
        """
        rows = self._build_rows(snapshot, weights, prefix="", active=False)
        if benchmark is not None:
            index = weights.index.union(benchmark.index)
            active = weights.reindex(index).fillna(0.0) - benchmark.reindex(index).fillna(0.0)
            rows += self._build_rows(snapshot, active, prefix="active_", active=True)
        out = pd.DataFrame(rows).assign(trade_date=snapshot.trade_date, portfolio=portfolio)
        out = out[RISK_DECOMP.columns].sort_values("component").reset_index(drop=True)
        return RISK_DECOMP.validate(RISK_DECOMP.normalize(out, strict=True))

    @staticmethod
    def _build_rows(
        snapshot: RiskSnapshot, weights: pd.Series, prefix: str, active: bool
    ) -> list[dict[str, object]]:
        factor_var, spec_var = snapshot.compute_variance(weights)
        total = float(np.sqrt(factor_var + spec_var))
        b = snapshot.compute_exposure_vector(weights)
        fb = snapshot.cov.to_numpy(float) @ b.to_numpy(float)
        contrib = b.to_numpy(float) * fb / total if total > 0 else np.zeros(len(b))

        def kind(name: str) -> str:
            return "active" if active else name

        rows: list[dict[str, object]] = [
            {"component": f"{prefix}total", "risk": total, "pct": 1.0, "kind": kind("total")},
            {
                "component": f"{prefix}factor",
                "risk": float(np.sqrt(factor_var)),
                "pct": factor_var / total**2 if total > 0 else np.nan,
                "kind": kind("factor"),
            },
            {
                "component": f"{prefix}specific",
                "risk": float(np.sqrt(spec_var)),
                "pct": spec_var / total**2 if total > 0 else np.nan,
                "kind": kind("specific"),
            },
        ]
        for name, c, x in zip(b.index, contrib, b.to_numpy(float), strict=True):
            pct = c / total if total > 0 else np.nan
            rows.append(
                {"component": f"{prefix}f:{name}", "risk": c, "pct": pct, "kind": kind("factor")}
            )
            rows.append(
                {
                    "component": f"{prefix}x:{name}",
                    "risk": x,
                    "pct": np.nan,
                    "kind": kind("exposure"),
                }
            )
        return rows
