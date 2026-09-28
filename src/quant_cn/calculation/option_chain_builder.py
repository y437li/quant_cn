"""Tidy option chains from opt_basic + opt_daily, and per-term strike quote tables."""

from __future__ import annotations

import pandas as pd

CHAIN_COLUMNS = [
    "trade_date",
    "opt_code",
    "ts_code",
    "call_put",
    "strike",
    "maturity_date",
    "days",
    "close",
    "settle",
    "vol",
    "oi",
    "adjusted",
]


class OptionChainBuilder:
    """
    Purpose:
        Join the option master (opt_basic) with daily prices (opt_daily) into one tidy chain per
        underlying, and turn one expiry of it into a strike x (call, put) quote table.

    Contract:
        Input:
            exclude_adjusted: bool  -- drop strike-adjusted ETF contracts (name ending "A"), D-048
        Output:
            instance; `build_chain`, `build_quotes`
        Raises:
            (none at construction)

    Used by:
        calculation.VixCalculator  -- quotes per term

    Test cases:
        TC-OCB-001  join keeps only contracts with a master row; days = maturity - trade date
        TC-OCB-002  adjusted contracts excluded by default and kept when asked
        TC-OCB-003  quotes use close, fall back to settle when close is 0 or missing, and report it
    """

    def __init__(self, exclude_adjusted: bool = True) -> None:
        self.exclude_adjusted = exclude_adjusted

    def build_chain(self, basic: pd.DataFrame, daily: pd.DataFrame, opt_code: str) -> pd.DataFrame:
        """
        Purpose:
            The chain of one underlying over the dates present in `daily`.

        Contract:
            Input:
                basic:    DataFrame  -- opt_basic columns (ts_code, opt_code, name, call_put,
                                        exercise_price, maturity_date)
                daily:    DataFrame  -- opt_daily (ts_code, trade_date, close, settle, vol, oi)
                opt_code: str        -- e.g. "OP510300.SH"
            Output:
                DataFrame  -- CHAIN_COLUMNS, sorted by trade_date, maturity_date, strike, call_put
            Raises:
                KeyError  -- required columns missing
        """
        master = basic[basic["opt_code"] == opt_code]
        master = master.assign(adjusted=master["name"].astype(str).str.endswith("A"))
        if self.exclude_adjusted:
            master = master[~master["adjusted"]]
        master = master.rename(columns={"exercise_price": "strike"})
        cols = ["ts_code", "opt_code", "call_put", "strike", "maturity_date", "adjusted"]
        chain = daily.merge(master[cols], on="ts_code", how="inner")
        days = pd.to_datetime(chain["maturity_date"]) - pd.to_datetime(chain["trade_date"])
        chain = chain.assign(days=days.dt.days)
        order = ["trade_date", "maturity_date", "strike", "call_put"]
        return chain[CHAIN_COLUMNS].sort_values(order).reset_index(drop=True)

    def build_quotes(self, term: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
        """
        Purpose:
            Strike x side table of prices and volumes for one expiry on one day.

        Contract:
            Input:
                term: DataFrame  -- chain rows of one trade_date and one maturity_date
            Output:
                (DataFrame, bool)  -- columns MultiIndex (price|vol, C|P) indexed by strike,
                                      ascending; True if any settle replaced a close
            Raises:
                KeyError  -- required columns missing
        """
        replace = ~(term["close"] > 0) & term["settle"].notna()
        price = term["close"].where(~replace, term["settle"])
        used_settle = bool(replace.any())
        table = term.assign(price=price).pivot_table(
            index="strike", columns="call_put", values=["price", "vol"]
        )
        return table.sort_index(), used_settle
