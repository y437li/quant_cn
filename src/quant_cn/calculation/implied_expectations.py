"""What today's price already pays for: years of excess profit, implied growth (plan 16 ph2)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from quant_cn.core.discovery_settings import DiscoverySettings

MARKET_COLUMNS = ("ts_code", "total_mv")  # optional: pe_med, precycle_mv
PANEL_COLUMNS = ("ts_code", "np_ttm", "np_dedt_ttm", "np_med")
GROWTH_BOUNDS = (-0.5, 1.0)  # implied growth is searched in this range and clamped to it
BISECTION_STEPS = 80
MIN_QUARTERS = 8  # quarters needed to estimate a profit sensitivity to a commodity price
MIN_R2 = 0.3  # below this fit the sensitivity is not used (profit is not driven by that price)


class ImpliedExpectations:
    """
    Purpose:
        Turn a market cap into what it already pays for (D-121: "priced in", not "cheap").
        Years priced: the market cap above a normal value V0 is read as an annuity of excess
        profit E = TTM profit - 10-year median profit, discounted at `discount_rate`;
        n = -ln(1 - r*(MC - V0)/E) / ln(1 + r), 0 when MC ≤ V0, `max_years` when the market
        pays more than a perpetuity of E, NaN when E ≤ 0. Three bases, always shown side by
        side: V0 = median profit x `normal_pe` (primary), x the stock's own median PE, and the
        pre-cycle market cap. Each on net profit and on deducted net profit.
        Reverse DCF: the constant growth g of TTM profit over `dcf_years`, exiting at
        `normal_pe` x final profit, that makes the discounted value equal the market cap
        (bisection in GROWTH_BOUNDS, clamped). Pure: the caller loads market caps and PEs.

    Contract:
        Input:
            settings: DiscoverySettings  -- normal_pe, discount_rate, dcf_years, max_years
        Output:
            instance; `compute_years`, `compute_implied_growth`, `compute_sensitivity`,
            `compute_implied_price`, `build`
        Raises:
            (none at construction)

    Used by:
        plan 16 phase 3 IdeaScreener and phase 6 DiscoveryStep (to come); research checks

    Test cases:
        TC-IE-001  compute_years: annuity inversion; MC ≤ V0 -> 0; above a perpetuity -> cap;
                   E ≤ 0 or NaN -> NaN
        TC-IE-002  compute_implied_growth recovers the growth used to price a synthetic cap;
                   clamps at the bounds; profit ≤ 0 -> NaN
        TC-IE-003  build: three bases on net and deducted profit, premium to normal value;
                   missing pe_med / precycle_mv -> NaN for that base; companies without a
                   market cap dropped
        TC-IE-004  build raises ValueError on missing panel or market columns
        TC-IE-005  2026-11-06 check values (normal PE 12, 9%): 云铝 7.6, 中国铝业 10.8,
                   中远海控 4.5 years (from the plan-16 phase-1 panel)
        TC-IE-006  compute_sensitivity recovers a known slope from quarterly means; too few
                   quarters or a poor fit -> NaN
        TC-IE-007  compute_implied_price solves normal_pe x profit(p) = market cap; NaN for a
                   non-positive sensitivity
    """

    def __init__(self, settings: DiscoverySettings) -> None:
        self._s = settings

    def compute_years(self, market_cap: float, base_value: float, excess_profit: float) -> float:
        """
        Purpose:
            Years of excess profit the market cap pays for above a base value.

        Contract:
            Input:
                market_cap, base_value, excess_profit: float  -- CNY
            Output:
                float  -- years in [0, max_years]; NaN when any input is NaN or excess ≤ 0
            Raises:
                (none)
        """
        if (
            any(math.isnan(v) for v in (market_cap, base_value, excess_profit))
            or excess_profit <= 0
        ):
            return math.nan
        if market_cap <= base_value:
            return 0.0
        r = self._s.discount_rate
        x = r * (market_cap - base_value) / excess_profit
        if x >= 1:
            return self._s.max_years
        return min(-math.log(1 - x) / math.log(1 + r), self._s.max_years)

    def compute_implied_growth(self, market_cap: float, profit: float) -> float:
        """
        Purpose:
            Annual profit growth over dcf_years that justifies the market cap (reverse DCF).

        Contract:
            Input:
                market_cap, profit: float  -- CNY; profit = TTM profit
            Output:
                float  -- growth in GROWTH_BOUNDS (clamped); NaN when profit ≤ 0 or NaN
            Raises:
                (none)
        """
        if math.isnan(market_cap) or math.isnan(profit) or profit <= 0:
            return math.nan
        lo, hi = GROWTH_BOUNDS
        if self._compute_value(profit, lo) >= market_cap:
            return lo
        if self._compute_value(profit, hi) <= market_cap:
            return hi
        for _ in range(BISECTION_STEPS):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if self._compute_value(profit, mid) < market_cap else (lo, mid)
        return (lo + hi) / 2

    @staticmethod
    def compute_sensitivity(quarters: pd.DataFrame, prices: pd.DataFrame) -> dict[str, float]:
        """
        Purpose:
            Annual profit change per unit of a commodity price: OLS of single-quarter profit on
            the quarter's mean futures price, times 4.

        Contract:
            Input:
                quarters: DataFrame  -- period (YYYYMMDD quarter end), np_q (CNY); one company
                prices:   DataFrame  -- trade_date (YYYYMMDD), price (FuturesCurve
                                        .build_dominant_series)
            Output:
                dict  -- slope (CNY of annual profit per price unit), r2, n; slope NaN when
                         fewer than MIN_QUARTERS quarters overlap or r2 < MIN_R2
            Raises:
                (none)
        """
        q_of = (
            prices["trade_date"]
            .astype(str)
            .map(lambda d: d[:4] + ("0331", "0630", "0930", "1231")[(int(d[4:6]) - 1) // 3])
        )
        means = prices.assign(period=q_of).groupby("period")["price"].mean()
        pairs = quarters.assign(price=quarters["period"].astype(str).map(means)).dropna(
            subset=["price", "np_q"]
        )
        n = len(pairs)
        if n < MIN_QUARTERS or pairs["price"].std() == 0:
            return {"slope": math.nan, "r2": math.nan, "n": float(n)}
        x, y = pairs["price"].to_numpy(dtype=float), pairs["np_q"].to_numpy(dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        resid = y - (slope * x + intercept)
        r2 = (
            1 - float((resid**2).sum()) / float(((y - y.mean()) ** 2).sum())
            if y.std() > 0
            else math.nan
        )
        ok = not math.isnan(r2) and r2 >= MIN_R2
        return {"slope": float(slope) * 4 if ok else math.nan, "r2": r2, "n": float(n)}

    def compute_implied_price(
        self, market_cap: float, profit: float, price_now: float, sensitivity: float
    ) -> float:
        """
        Purpose:
            The commodity price at which normal_pe x profit equals the market cap, with profit
            linear in the price: profit(p) = profit + sensitivity x (p - price_now).

        Contract:
            Input:
                market_cap, profit (TTM), price_now, sensitivity (annual CNY per price unit): float
            Output:
                float  -- implied price; NaN when sensitivity <= 0 or any input is NaN
            Raises:
                (none)
        """
        values = (market_cap, profit, price_now, sensitivity)
        if any(math.isnan(v) for v in values) or sensitivity <= 0:
            return math.nan
        return price_now + (market_cap / self._s.normal_pe - profit) / sensitivity

    def _compute_value(self, profit: float, growth: float) -> float:
        r, n = self._s.discount_rate, self._s.dcf_years
        flows = sum(profit * (1 + growth) ** t / (1 + r) ** t for t in range(1, n + 1))
        exit_value = profit * (1 + growth) ** n * self._s.normal_pe / (1 + r) ** n
        return flows + exit_value

    def build(self, panel: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Years priced on three bases and implied growth for every company with a market cap.

        Contract:
            Input:
                panel: DataFrame   -- CompanyCyclePanel.build output (PANEL_COLUMNS used)
                market: DataFrame  -- ts_code, total_mv (CNY); optional pe_med (own 10-year
                                      median PE), precycle_mv (CNY)
            Output:
                DataFrame  -- ts_code, total_mv, excess, excess_dedt, base_normal, base_own_pe,
                              base_precycle, years_normal, years_normal_dedt, years_own_pe,
                              years_precycle, premium_normal, implied_growth
            Raises:
                ValueError  -- a required column is missing
        """
        for name, frame, cols in (
            ("panel", panel, PANEL_COLUMNS),
            ("market", market, MARKET_COLUMNS),
        ):
            missing = [c for c in cols if c not in frame.columns]
            if missing:
                raise ValueError(f"{name} frame missing columns {missing}")
        m = market.reindex(columns=[*MARKET_COLUMNS, "pe_med", "precycle_mv"])
        df = panel[list(PANEL_COLUMNS)].merge(m.dropna(subset=["total_mv"]), on="ts_code")
        df = df.assign(
            excess=df["np_ttm"] - df["np_med"],
            excess_dedt=df["np_dedt_ttm"] - df["np_med"],
            base_normal=df["np_med"] * self._s.normal_pe,
            base_own_pe=df["np_med"] * df["pe_med"],
            base_precycle=df["precycle_mv"],
        )
        years = np.vectorize(self.compute_years, otypes=[float])
        return df.assign(
            years_normal=years(df["total_mv"], df["base_normal"], df["excess"]),
            years_normal_dedt=years(df["total_mv"], df["base_normal"], df["excess_dedt"]),
            years_own_pe=years(df["total_mv"], df["base_own_pe"], df["excess"]),
            years_precycle=years(df["total_mv"], df["base_precycle"], df["excess"]),
            premium_normal=df["total_mv"] / df["base_normal"].where(df["base_normal"] > 0) - 1,
            implied_growth=np.vectorize(self.compute_implied_growth, otypes=[float])(
                df["total_mv"], df["np_ttm"]
            ),
        ).drop(columns=["np_ttm", "np_dedt_ttm", "np_med", "pe_med", "precycle_mv"])
