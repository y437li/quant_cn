"""CBOE-method volatility index for one option underlying over a date range (plan 03)."""

from __future__ import annotations

import pandas as pd

from quant_cn.calculation.expiry_clock import ExpiryClock
from quant_cn.calculation.forward_price_estimator import ForwardPriceEstimator
from quant_cn.calculation.option_chain_builder import OptionChainBuilder
from quant_cn.calculation.risk_free_curve import RiskFreeCurve
from quant_cn.calculation.term_interpolator import TermInterpolator
from quant_cn.calculation.term_selector import TermSelector
from quant_cn.calculation.variance_strip_calculator import VarianceStripCalculator
from quant_cn.core.frames import VIX_PANEL

_FAILURES = (ValueError, KeyError, ZeroDivisionError, IndexError)


class VixCalculator:
    """
    Purpose:
        Orchestrate the white-paper steps per trading day: select near/next terms, rate per term,
        forward and K0, variance strip, interpolation on the chosen clock; one VIX_PANEL row per
        (trade_date, underlying). A day that cannot be computed gets vix NaN and a
        "failed: <reason>" quality_flag instead of stopping the run.

    Contract:
        Input:
            curve:        RiskFreeCurve
            chains:       OptionChainBuilder
            selector:     TermSelector
            forward:      ForwardPriceEstimator
            strip:        VarianceStripCalculator
            interpolator: TermInterpolator
            clock:        ExpiryClock  -- "calendar" (CBOE) or "trading"
        Output:
            instance; `compute`
        Raises:
            (none at construction)

    Used by:
        research_space/notebooks/20260927_vix_calculation.ipynb  -- every underlying, both clocks

    Test cases:
        TC-VC-001  flat 20% synthetic chain returns vix within 0.3 of 20 on both clocks
        TC-VC-002  output validates as VIX_PANEL with one row per day and quality flags
        TC-VC-003  a day with one expiry yields vix NaN and a failed quality_flag, others computed
    """

    def __init__(
        self,
        curve: RiskFreeCurve,
        chains: OptionChainBuilder,
        selector: TermSelector,
        forward: ForwardPriceEstimator,
        strip: VarianceStripCalculator,
        interpolator: TermInterpolator,
        clock: ExpiryClock,
    ) -> None:
        self._curve = curve
        self._chains = chains
        self._selector = selector
        self._forward = forward
        self._strip = strip
        self._interpolator = interpolator
        self._clock = clock

    def compute(self, chain: pd.DataFrame, underlying: str) -> pd.DataFrame:
        """
        Purpose:
            The index for every trading day in `chain`.

        Contract:
            Input:
                chain:      DataFrame  -- OptionChainBuilder.build_chain output for one underlying
                underlying: str        -- label stored in the `underlying` column
            Output:
                DataFrame  -- VIX_PANEL, sorted by trade_date
            Raises:
                SchemaError  -- output does not satisfy VIX_PANEL (a bug, not a data problem)
        """
        rows = []
        for trade_date, day in chain.groupby("trade_date"):
            try:
                rows.append(self._compute_day(day, str(trade_date), underlying))
            except _FAILURES as exc:
                reason = f"failed: {type(exc).__name__}: {exc}"[:120]
                rows.append(
                    {
                        "trade_date": str(trade_date),
                        "underlying": underlying,
                        "clock": self._clock.mode,
                        "quality_flag": reason,
                    }
                )
        frame = pd.DataFrame(rows, columns=VIX_PANEL.columns)
        return VIX_PANEL.validate(VIX_PANEL.normalize(frame, strict=True))

    def _compute_day(
        self, day: pd.DataFrame, trade_date: str, underlying: str
    ) -> dict[str, object]:
        near, nxt = self._selector.list_terms(day)
        row: dict[str, object] = {
            "trade_date": trade_date,
            "underlying": underlying,
            "clock": self._clock.mode,
        }
        flags: set[str] = set()
        units = {}
        variances = {}
        for label, expiry in (("near", near), ("next", nxt)):
            term = day[day["maturity_date"] == expiry]
            days = int(term["days"].iloc[0])
            t = days / 365
            rate = self._curve.get_rate(trade_date, days)
            quotes, used_settle = self._chains.build_quotes(term)
            f, k0 = self._forward.compute(quotes, rate, t)
            var, n = self._strip.compute(quotes, f, k0, rate, t)
            units[label] = self._clock.get_units(trade_date, expiry, days)
            # re-express the term's total variance on the chosen clock
            variances[label] = var * t / (units[label] / self._clock.get_year())
            flags |= {"used_settle"} if used_settle else set()
            row |= {
                f"days_{label}": days,
                f"t_{label}": t,
                f"rate_{label}": rate,
                f"f_{label}": f,
                f"k0_{label}": k0,
                f"var_{label}": var,
                f"n_options_{label}": n,
            }
        row["vix"] = self._interpolator.compute(
            variances["near"],
            units["near"],
            variances["next"],
            units["next"],
            self._clock.get_target(),
            self._clock.get_year(),
        )
        row["quality_flag"] = ",".join(sorted(flags)) or "ok"
        return row
