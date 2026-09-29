"""Index-futures positioning: open interest regimes, top-20 broker nets, basis (plan 09)."""

from __future__ import annotations

import calendar
import datetime as dt
import re

import numpy as np
import pandas as pd

from quant_cn.core.frames import FUTURES_POSITIONING

_CONTRACT = re.compile(r"^([A-Z]+)(\d{2})(\d{2})")
DAILY_COLUMNS = FUTURES_POSITIONING.columns
FRIDAY = 4
THIRD_WEEK = 2


class FuturesPositioning:
    """
    Purpose:
        Per trading day for one CFFEX index-futures product (IF, IH, IC, IM): total open interest
        and its change, the main contract's price change, the OI x price regime (new shorts, long
        liquidation, short covering, new longs), top-20 broker gross long / short / net summed over
        the product's contracts, and the main contract's basis to the index, raw and annualised to
        its third-Friday expiry. Top-20 figures are gross broker aggregates, not client intent.

    Contract:
        Input:
            product: str  -- futures product code, e.g. "IF"
        Output:
            instance; `compute`, `list_brokers`, `get_expiry`
        Raises:
            ValueError  -- empty product code

    Used by:
        research_space/notebooks/20260929_positioning_flows.ipynb  -- IF/IM positioning

    Test cases:
        TC-FP-001  regimes classified from the signs of price and OI changes
        TC-FP-002  top-20 net sums long minus short over the product's contracts only
        TC-FP-003  basis uses the highest-OI contract; annualisation uses its third-Friday expiry
        TC-FP-004  list_brokers ranks brokers by net for one day
    """

    def __init__(self, product: str) -> None:
        if not product:
            raise ValueError("product code is empty")
        self.product = product

    def compute(self, daily: pd.DataFrame, holding: pd.DataFrame, spot: pd.Series) -> pd.DataFrame:
        """
        Purpose:
            One row per trading day for the product.

        Contract:
            Input:
                daily:   DataFrame  -- fut_daily rows (ts_code, trade_date, close, oi, ...)
                holding: DataFrame  -- fut_holding (trade_date, symbol, broker, long_hld, short_hld)
                spot:    Series     -- index close by trade_date (YYYYMMDD)
            Output:
                DataFrame  -- FUTURES_POSITIONING sorted by trade_date; first day has NaN changes
            Raises:
                KeyError  -- required columns missing
        """
        rows = daily[daily["ts_code"].str.match(rf"^{self.product}\d{{4}}")].copy()
        rows["contract"] = rows["ts_code"].str.split(".").str[0]
        out = []
        for trade_date, day in rows.groupby("trade_date"):
            main = day.sort_values("oi", ascending=False).iloc[0]
            out.append(
                {
                    "trade_date": trade_date,
                    "product": self.product,
                    "main_contract": main["contract"],
                    "price": float(main["close"]),
                    "oi_total": float(day["oi"].sum()),
                }
            )
        frame = pd.DataFrame(out).sort_values("trade_date").reset_index(drop=True)
        same_main = frame["main_contract"].eq(frame["main_contract"].shift())
        frame["price_change"] = frame["price"].diff().where(same_main)
        frame["oi_change"] = frame["oi_total"].diff()
        frame["regime"] = [
            self._parse_regime(p, o)
            for p, o in zip(frame["price_change"], frame["oi_change"], strict=True)
        ]
        frame = frame.merge(self._build_holding_sums(holding), on="trade_date", how="left")
        frame["spot"] = frame["trade_date"].map(spot)
        frame["basis_pct"] = (frame["price"] / frame["spot"] - 1) * 100
        years = [
            max((self.get_expiry(c) - dt.datetime.strptime(d, "%Y%m%d").date()).days, 1) / 365
            for c, d in zip(frame["main_contract"], frame["trade_date"], strict=True)
        ]
        frame["basis_annualised"] = frame["basis_pct"] / np.array(years)
        return FUTURES_POSITIONING.validate(
            FUTURES_POSITIONING.normalize(frame[DAILY_COLUMNS], strict=True)
        )

    def list_brokers(self, holding: pd.DataFrame, trade_date: str) -> pd.DataFrame:
        """
        Purpose:
            Brokers' gross long, short and net over the product's contracts on one day.

        Contract:
            Input:
                holding: DataFrame; trade_date: str
            Output:
                DataFrame  -- broker, long, short, net, long_chg, short_chg; sorted by net ascending
            Raises:
                KeyError  -- required columns missing
        """
        day = self._list_product_rows(holding)
        day = day[day["trade_date"] == trade_date]
        cols = {
            "long_hld": "long",
            "short_hld": "short",
            "long_chg": "long_chg",
            "short_chg": "short_chg",
        }
        brokers = day.groupby("broker")[list(cols)].sum().rename(columns=cols)
        brokers["net"] = brokers["long"] - brokers["short"]
        return brokers.reset_index()[
            ["broker", "long", "short", "net", "long_chg", "short_chg"]
        ].sort_values("net")

    def get_expiry(self, contract: str) -> dt.date:
        """
        Purpose:
            CFFEX index futures expire on the third Friday of the contract month.

        Contract:
            Input:
                contract: str  -- e.g. "IF2612"
            Output:
                datetime.date
            Raises:
                ValueError  -- not a product+YYMM code
        """
        match = _CONTRACT.match(contract)
        if not match:
            raise ValueError(f"not a futures contract code: {contract!r}")
        year, month = 2000 + int(match.group(2)), int(match.group(3))
        fridays = [
            d
            for d in calendar.Calendar().itermonthdates(year, month)
            if d.month == month and d.weekday() == FRIDAY
        ]
        return fridays[THIRD_WEEK]

    def _list_product_rows(self, holding: pd.DataFrame) -> pd.DataFrame:
        return holding[holding["symbol"].astype(str).str.match(rf"^{self.product}\d{{4}}$")]

    def _build_holding_sums(self, holding: pd.DataFrame) -> pd.DataFrame:
        sums = (
            self._list_product_rows(holding).groupby("trade_date")[["long_hld", "short_hld"]].sum()
        )
        sums = sums.rename(columns={"long_hld": "top20_long", "short_hld": "top20_short"})
        sums["top20_net"] = sums["top20_long"] - sums["top20_short"]
        return sums.reset_index()

    @staticmethod
    def _parse_regime(price_change: float, oi_change: float) -> str:
        if pd.isna(price_change) or pd.isna(oi_change) or price_change == 0 or oi_change == 0:
            return "unclear"
        if price_change < 0:
            return "new_shorts" if oi_change > 0 else "long_liquidation"
        return "new_longs" if oi_change > 0 else "short_covering"
