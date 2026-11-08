"""Margin-financing liquidation ladder from per-stock margin data (plan 09)."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from typing import Any, cast

import pandas as pd

from quant_cn.core.frames import MARGIN_LADDER, MARGIN_VINTAGES

EMPTY = 1e-6
LADDER_COLUMNS = MARGIN_VINTAGES.columns


class MarginLadderEstimator:
    """
    Purpose:
        Estimate where margin-financed positions face forced selling. Per stock, financing debt is
        split into first-in-first-out vintages: each day's financed buying (rzmre) opens a vintage
        at that day's close; repayments (rzche) retire the oldest first; the balance before the
        window is one "seeded" vintage at the first close. A vintage is force-sold when
        collateral/debt falls below `maintenance_ratio`; with own capital = initial_margin_ratio
        x debt at entry, that happens at price entry x maintenance_ratio / (1 +
        initial_margin_ratio). Pooled
        per-stock data and cross-collateral make this an estimate of concentration, not prices.

    Contract:
        Input:
            maintenance_ratio:    float > 1   -- regulatory maintenance line (1.3)
            initial_margin_ratio: float > 0   -- own capital / debt at entry (1.0 = 100%)
        Output:
            instance; `compute_ladder`, `compute_curve`
        Raises:
            ValueError  -- ratios out of range

    Used by:
        research_space/notebooks/20260929_positioning_flows.ipynb  -- market liquidation curve

    Test cases:
        TC-MLE-001  FIFO: repayments retire the oldest vintage first; balance reconciles to rzye
        TC-MLE-002  liquidation price = entry * maintenance / (1 + initial margin)
        TC-MLE-003  compute_curve counts debt forced at each drawdown, monotone non-decreasing
        TC-MLE-004  invalid ratios raise ValueError
    """

    def __init__(self, maintenance_ratio: float = 1.3, initial_margin_ratio: float = 1.0) -> None:
        if maintenance_ratio <= 1 or initial_margin_ratio <= 0:
            raise ValueError("maintenance_ratio must be > 1 and initial_margin_ratio > 0")
        self.maintenance_ratio = maintenance_ratio
        self.initial_margin_ratio = initial_margin_ratio

    def compute_ladder(
        self, detail: pd.DataFrame, closes: pd.DataFrame, as_of: str
    ) -> pd.DataFrame:
        """
        Purpose:
            Outstanding financing vintages per stock on `as_of` with liquidation prices.

        Contract:
            Input:
                detail: DataFrame  -- margin_detail rows (ts_code, trade_date, rzye, rzmre, rzche)
                closes: DataFrame  -- unadjusted closes (ts_code, trade_date, close)
                as_of:  str        -- YYYYMMDD, last date used
            Output:
                DataFrame  -- MARGIN_VINTAGES; distance_pct = liquidation / price - 1 (< 0: below);
                              seeded 1.0 for the pre-window balance
            Raises:
                KeyError  -- required columns missing
        """
        merged = detail[detail["trade_date"] <= as_of].merge(
            closes, on=["ts_code", "trade_date"], how="inner"
        )
        merged = merged.sort_values(["ts_code", "trade_date"])
        rows: list[dict[str, object]] = []
        factor = self.maintenance_ratio / (1 + self.initial_margin_ratio)
        for ts_code, stock in merged.groupby("ts_code", sort=False):
            vintages = self._build_vintages(stock)
            price = float(stock["close"].iloc[-1])
            for entry_date, entry_price, debt, seeded in vintages:
                liq = entry_price * factor
                rows.append(
                    {
                        "ts_code": ts_code,
                        "entry_date": entry_date,
                        "entry_price": entry_price,
                        "debt": debt,
                        "liquidation_price": liq,
                        "price": price,
                        "distance_pct": (liq / price - 1) * 100,
                        "seeded": seeded,
                    }
                )
        frame = pd.DataFrame(rows, columns=MARGIN_VINTAGES.columns)
        return MARGIN_VINTAGES.validate(MARGIN_VINTAGES.normalize(frame, strict=True))

    def compute_curve(self, ladder: pd.DataFrame, drawdowns: Sequence[float]) -> pd.DataFrame:
        """
        Purpose:
            Financing debt whose liquidation price is reached if every stock falls by each drawdown.

        Contract:
            Input:
                ladder:    DataFrame        -- compute_ladder output
                drawdowns: Sequence[float]  -- percent falls, e.g. [0, 5, 10, 20]
            Output:
                DataFrame  -- MARGIN_LADDER: drawdown_pct, debt_forced (CNY), share_of_debt
            Raises:
                (none)
        """
        total = float(ladder["debt"].sum()) or 1.0
        out = []
        for dd in drawdowns:
            hit = ladder["liquidation_price"] >= ladder["price"] * (1 - dd / 100)
            forced = float(ladder.loc[hit, "debt"].sum())
            out.append(
                {"drawdown_pct": float(dd), "debt_forced": forced, "share_of_debt": forced / total}
            )
        frame = pd.DataFrame(out, columns=MARGIN_LADDER.columns)
        return MARGIN_LADDER.validate(MARGIN_LADDER.normalize(frame, strict=True))

    @staticmethod
    def _build_vintages(stock: pd.DataFrame) -> list[tuple[str, float, float, bool]]:
        records = cast(list[dict[str, Any]], stock.to_dict("records"))
        first = records[0]
        buy0, repay0 = float(first["rzmre"] or 0), float(first["rzche"] or 0)
        seed = float(first["rzye"]) - buy0 + repay0
        dates: deque[str] = deque()
        prices: deque[float] = deque()
        debts: deque[float] = deque()
        seeded: deque[bool] = deque()
        if seed > 0:
            dates.append(str(first["trade_date"]))
            prices.append(float(first["close"]))
            debts.append(seed)
            seeded.append(True)
        for row in records:
            buy, repay = float(row["rzmre"] or 0), float(row["rzche"] or 0)
            if buy > 0:
                dates.append(str(row["trade_date"]))
                prices.append(float(row["close"]))
                debts.append(buy)
                seeded.append(False)
            while repay > 0 and debts:
                take = min(repay, debts[0])
                debts[0] -= take
                repay -= take
                if debts[0] <= EMPTY:
                    dates.popleft()
                    prices.popleft()
                    debts.popleft()
                    seeded.popleft()
        return [
            (d, p, v, s) for d, p, v, s in zip(dates, prices, debts, seeded, strict=True) if v > 0
        ]
