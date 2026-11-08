"""Dealer gamma exposure by strike and across spot levels (plan 09): hedging-flow map."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

import numpy as np
import pandas as pd

from quant_cn.calculation.black76_model import Black76Model, Side
from quant_cn.calculation.forward_price_estimator import ForwardPriceEstimator
from quant_cn.calculation.option_chain_builder import OptionChainBuilder
from quant_cn.calculation.risk_free_curve import RiskFreeCurve
from quant_cn.core.frames import GEX_PANEL

DEFAULT_DEALER_SIGN: dict[str, float] = {"C": 1.0, "P": -1.0}
EXPOSURE_COLUMNS = GEX_PANEL.columns


class GammaExposureCalculator:
    """
    Purpose:
        Estimate the gamma dealers carry per option and strike, in CNY of underlying they must trade
        for a 1% move: GEX = sign * Gamma_F * OI * multiplier * F^2 * 1%, with Gamma from Black-76
        at each option's own implied volatility. `sign` is an ASSUMPTION about who is short: the
        default (+1 calls, -1 puts) means dealers are long calls and short puts (customers write
        calls and buy puts). Negative total GEX = dealers sell into falls (moves amplify).

    Contract:
        Input:
            curve:       RiskFreeCurve
            chains:      OptionChainBuilder
            forward:     ForwardPriceEstimator
            model:       Black76Model
            dealer_sign: Mapping[str, float]  -- {"C": +1 or -1, "P": +1 or -1}
            max_days:    int > 0              -- ignore expiries further out
        Output:
            instance; `compute`, `compute_profile`, `find_flip`
        Raises:
            ValueError  -- dealer_sign missing a side

    Used by:
        research_space/notebooks/20260929_positioning_flows.ipynb  -- CSI 300 gamma map

    Test cases:
        TC-GEC-001  per-option GEX equals sign * gamma * oi * multiplier * F^2 * 1%
        TC-GEC-002  default signs: puts-only chain gives negative total GEX, calls-only positive
        TC-GEC-003  profile is continuous and find_flip returns the zero crossing (None if none)
        TC-GEC-004  expiries < 1 day or > max_days and options without a solvable IV are skipped
    """

    def __init__(
        self,
        curve: RiskFreeCurve,
        chains: OptionChainBuilder,
        forward: ForwardPriceEstimator,
        model: Black76Model,
        dealer_sign: Mapping[str, float] = DEFAULT_DEALER_SIGN,
        max_days: int = 90,
    ) -> None:
        if set(dealer_sign) != {"C", "P"}:
            raise ValueError("dealer_sign needs exactly the keys C and P")
        self._curve = curve
        self._chains = chains
        self._forward = forward
        self._model = model
        self._sign = dict(dealer_sign)
        self._max_days = max_days

    def compute(self, day_chain: pd.DataFrame, trade_date: str, multiplier: float) -> pd.DataFrame:
        """
        Purpose:
            Exposure of every option of one day with 1 <= days <= max_days.

        Contract:
            Input:
                day_chain:  DataFrame  -- OptionChainBuilder.build_chain rows of one trade_date
                trade_date: str        -- YYYYMMDD
                multiplier: float > 0  -- contract multiplier (IO 100, ETF options 10000)
            Output:
                DataFrame  -- GEX_PANEL, one row per option
            Raises:
                ValueError  -- no SHIBOR fixing for the date
        """
        rows: list[dict[str, object]] = []
        terms = day_chain[(day_chain["days"] >= 1) & (day_chain["days"] <= self._max_days)]
        for expiry, term in terms.groupby("maturity_date"):
            days = int(term["days"].iloc[0])
            t = days / 365
            rate = self._curve.get_rate(trade_date, days)
            quotes, _ = self._chains.build_quotes(term)
            try:
                forward, _ = self._forward.compute(quotes, rate, t)
            except ValueError:
                continue
            for option in cast(list[dict[str, Any]], term.to_dict("records")):
                rows += self._build_row(option, str(expiry), days, forward, rate, t, multiplier)
        frame = pd.DataFrame(rows, columns=GEX_PANEL.columns)
        return GEX_PANEL.validate(GEX_PANEL.normalize(frame, strict=True))

    def compute_profile(self, exposures: pd.DataFrame, forwards: Sequence[float]) -> pd.DataFrame:
        """
        Purpose:
            Total dealer GEX if every term's forward moved to each level (IVs held fixed).

        Contract:
            Input:
                exposures: DataFrame        -- compute() output of one day
                forwards:  Sequence[float]  -- levels of the (near-term) forward to evaluate
            Output:
                DataFrame  -- columns level, gex (CNY per 1% move), one row per level
            Raises:
                (none)
        """
        base = exposures.groupby("maturity_date")["forward"].first().to_numpy(dtype=float)
        ref = float(base[0]) if len(base) else 1.0
        records = cast(list[dict[str, Any]], exposures.to_dict("records"))
        out = []
        for level in forwards:
            total = 0.0
            for row in records:
                f = float(row["forward"]) * level / ref
                gamma = self._model.compute_gamma(
                    f, float(row["strike"]), float(row["t"]), float(row["rate"]), float(row["iv"])
                )
                scale = float(row["oi"]) * float(row["multiplier"]) * f**2 * 0.01
                total += float(row["sign"]) * gamma * scale
            out.append({"level": float(level), "gex": total})
        return pd.DataFrame(out, columns=["level", "gex"])

    def find_flip(self, profile: pd.DataFrame) -> float | None:
        """
        Purpose:
            Level where total GEX changes sign (linear interpolation), the "gamma flip".

        Contract:
            Input:
                profile: DataFrame  -- compute_profile output, levels ascending
            Output:
                float | None  -- None when GEX keeps one sign over the grid
            Raises:
                (none)
        """
        levels, gex = profile["level"].to_numpy(dtype=float), profile["gex"].to_numpy(dtype=float)
        for i in range(1, len(levels)):
            if gex[i - 1] == 0:
                return float(levels[i - 1])
            if np.sign(gex[i - 1]) != np.sign(gex[i]):
                w = gex[i - 1] / (gex[i - 1] - gex[i])
                return float(levels[i - 1] + w * (levels[i] - levels[i - 1]))
        return None

    def _build_row(
        self,
        option: dict[str, Any],
        expiry: str,
        days: int,
        forward: float,
        rate: float,
        t: float,
        multiplier: float,
    ) -> list[dict[str, object]]:
        side, strike = str(option["call_put"]), float(option["strike"])
        close, settle = option["close"], option["settle"]
        price = float(close) if pd.notna(close) and close > 0 else float(settle)
        oi = float(option["oi"]) if pd.notna(option["oi"]) else 0.0
        if oi <= 0 or not price > 0:
            return []
        try:
            kind: Side = "C" if side == "C" else "P"
            iv = self._model.compute_implied_vol(price, forward, strike, t, rate, kind)
        except ValueError:
            return []
        gamma = self._model.compute_gamma(forward, strike, t, rate, iv)
        sign = self._sign[side]
        gex = sign * gamma * oi * multiplier * forward**2 * 0.01
        return [
            {
                "trade_date": option["trade_date"],
                "maturity_date": expiry,
                "days": days,
                "strike": strike,
                "call_put": side,
                "oi": oi,
                "price": price,
                "forward": forward,
                "rate": rate,
                "t": t,
                "iv": iv,
                "gamma": gamma,
                "sign": sign,
                "multiplier": multiplier,
                "gex": gex,
            }
        ]
