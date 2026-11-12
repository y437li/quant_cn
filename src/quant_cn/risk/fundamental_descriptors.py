"""CNE5 value, leverage and growth descriptors from point-in-time statements (plan 05, D-127)."""

from __future__ import annotations

import numpy as np
import pandas as pd

WAN = 1e4  # daily_basic total_mv is in 10k CNY; statements are in CNY

BALANCE_FIELDS = (
    "total_hldr_eqy_exc_min_int",
    "total_assets",
    "total_liab",
    "lt_borr",
    "bond_payable",
)
TTM_FIELDS = ("n_income_attr_p_ttm", "n_cashflow_act_ttm", "c_pay_acq_const_fiolta_ttm")
ANNUAL_FIELDS = ("eps", "revenue")


class FundamentalDescriptors:
    """
    Purpose:
        CNE5 descriptors from statements already aligned point in time (FUNDAMENTALS_PIT for
        balance and TTM fields; StatementVersionReader snapshots for annual history):
        BTOP = common equity / market cap; ETOP, CETOP = TTM net profit (parent) and operating
        cash flow / market cap; MLEV = (ME + LD) / ME, DTOA = total liabilities / total assets,
        FCFP = (TTM operating cash flow - TTM capex, c_pay_acq_const_fiolta) / market cap
        (D-131); BLEV = (BE + LD) / BE with LD = long-term borrowings + bonds payable
        (preferred equity is not reported separately and taken as 0); EGRO, SGRO = slope of the
        last up to `years` annual EPS / revenue on time divided by their mean absolute value
        (revenue instead of revenue per share: a constant share count cancels in slope / mean).

    Contract:
        Input:
            years:     int >= 2  -- annual reports in the growth regression (CNE5: 5)
            min_years: int in [2, years]  -- fewer known annual reports -> NaN
        Output:
            instance; `compute_value_leverage`, `compute_growth`
        Raises:
            ValueError  -- min_years outside [2, years]

    Used by:
        risk.DescriptorBuilder  -- fundamental descriptors
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-FD-001  btop, etop, cetop, mlev, dtoa, blev from hand-computed statements (10k CNY mv)
        TC-FD-002  negative book equity gives NaN blev and keeps btop negative; missing debt = 0
        TC-FD-003  growth = slope / mean |value| over the last `years` annuals; < min_years -> NaN
    """

    def __init__(self, years: int = 5, min_years: int = 3) -> None:
        if not 2 <= min_years <= years:  # noqa: PLR2004 -- a slope needs two points
            raise ValueError("min_years must be in [2, years]")
        self._years, self._min_years = years, min_years

    def compute_value_leverage(self, frame: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Value and leverage descriptors per (trade_date, ts_code).

        Contract:
            Input:
                frame: DataFrame  -- trade_date, ts_code, total_mv (10k CNY) and the columns of
                                     BALANCE_FIELDS + TTM_FIELDS (CNY, NaN allowed)
            Output:
                DataFrame  -- trade_date, ts_code, btop, etop, cetop, fcfp, mlev, dtoa, blev;
                              NaN where the inputs are missing or market cap <= 0
            Raises:
                KeyError  -- a required column is missing
        """
        mv = frame["total_mv"].where(frame["total_mv"] > 0) * WAN
        equity = frame["total_hldr_eqy_exc_min_int"]
        has_bs = frame["total_assets"].notna()
        debt = (frame["lt_borr"].fillna(0) + frame["bond_payable"].fillna(0)).where(has_bs)
        book = equity.where(equity > 0)
        assets = frame["total_assets"].where(frame["total_assets"] > 0)
        return pd.DataFrame(
            {
                "trade_date": frame["trade_date"],
                "ts_code": frame["ts_code"],
                "btop": equity / mv,
                "etop": frame["n_income_attr_p_ttm"] / mv,
                "cetop": frame["n_cashflow_act_ttm"] / mv,
                "fcfp": (frame["n_cashflow_act_ttm"] - frame["c_pay_acq_const_fiolta_ttm"]) / mv,
                "mlev": (mv + debt) / mv,
                "dtoa": frame["total_liab"] / assets,
                "blev": (book + debt) / book,
            }
        )

    def compute_growth(self, annual: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            EGRO and SGRO per (as_of, ts_code) from the annual reports known on each as_of.

        Contract:
            Input:
                annual: DataFrame  -- as_of, ts_code, end_date (YYYY1231), field in
                                      ANNUAL_FIELDS, value; one row per key (latest version)
            Output:
                DataFrame  -- as_of, ts_code, egro, sgro (NaN when fewer than min_years
                              consecutive-or-not annuals, or mean |value| = 0)
            Raises:
                KeyError  -- missing column
        """
        cols = ["as_of", "ts_code", "egro", "sgro"]
        rows = annual[annual["end_date"].str.endswith("1231") & annual["value"].notna()]
        if rows.empty:
            return pd.DataFrame(columns=cols)
        rows = rows.sort_values(["as_of", "ts_code", "field", "end_date"])
        rows = rows.groupby(["as_of", "ts_code", "field"]).tail(self._years).copy()
        rows["t"] = rows["end_date"].str[:4].astype(int).astype(float)
        keys = ["as_of", "ts_code", "field"]
        g = rows.groupby(keys)
        rows["dt"] = rows["t"] - g["t"].transform("mean")
        rows["dv"] = rows["value"] - g["value"].transform("mean")
        rows["abs"] = rows["value"].abs()
        stats = rows.assign(xy=rows["dt"] * rows["dv"], xx=rows["dt"] ** 2).groupby(keys)
        agg = stats.agg(xy=("xy", "sum"), xx=("xx", "sum"), mabs=("abs", "mean"), n=("t", "size"))
        with np.errstate(divide="ignore", invalid="ignore"):
            agg["growth"] = (agg["xy"] / agg["xx"]) / agg["mabs"].replace(0, np.nan)
        agg.loc[agg["n"] < self._min_years, "growth"] = np.nan
        wide = agg["growth"].unstack("field")
        out = pd.DataFrame(index=wide.index)
        out["egro"] = wide.get("eps", np.nan)
        out["sgro"] = wide.get("revenue", np.nan)
        return out.reset_index()[cols]
