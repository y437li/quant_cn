"""Shareholder yield: cash dividends plus buybacks executed over 12 months (plan 23 ph3, D-154)."""

from __future__ import annotations

import pandas as pd

from quant_cn.lake.buyback_ledger import BuybackLedger
from quant_cn.lake.lake_query import LakeQuery

COLUMNS = ["dividend_yield", "buyback_yield", "shareholder_yield", "buyback_ttm", "total_mv"]
METRICS = ["shareholder_yield", "buyback_yield", "buyback_plan_pct", "buyback_done_pct"]
_BASIC = """
SELECT ts_code, dv_ttm, total_mv FROM curated.daily_basic
WHERE trade_date = (SELECT max(trade_date) FROM curated.daily_basic WHERE trade_date <= ?) {codes}
"""


class ShareholderYieldReader:
    """
    Purpose:
        Per stock on a date: dividend yield (daily_basic dv_ttm, trailing 12 months of cash
        dividends over market cap), buyback yield (money executed in the last 365 days from
        BuybackLedger over total market cap) and their sum, the shareholder yield. All three
        are fractions; point in time (dividends as the vendor's dv_ttm on that day, buybacks
        announced on or before the date).

    Contract:
        Input:
            query:  LakeQuery     -- curated.daily_basic
            ledger: BuybackLedger -- executed buybacks
        Output:
            instance; `read(as_of, codes)` -> DataFrame (index ts_code, COLUMNS);
            `read_metrics(codes, as_of)` -> condition metrics METRICS (plan 23 ph5)
        Raises:
            (none at construction)

    Used by:
        research_space/runs/20261113_buyback_yield  -- month-end yields (plan 23 ph4)
        portfolio.ConditionEvaluator  -- kind `capital` metrics (ph5)
        cli.AppServiceBuilder         -- wires it

    Test cases:
        TC-SYR-001  dividend-only stock: shareholder yield = dv_ttm / 100; buyback adds
                    executed money / total market cap; stocks without dv_ttm count 0 dividend
        TC-SYR-002  plan metrics: largest live plan as % of market cap and its done share;
                    expired or stopped plans do not count
    """

    def __init__(self, query: LakeQuery, ledger: BuybackLedger) -> None:
        self._query = query
        self._ledger = ledger

    def read(self, as_of: str, codes: list[str] | None = None) -> pd.DataFrame:
        """
        Purpose:
            Yields of `codes` (or every stock) on the last session on or before `as_of`.

        Contract:
            Input:
                as_of: str (YYYYMMDD); codes: list[str] | None
            Output:
                DataFrame  -- index ts_code; dividend_yield, buyback_yield, shareholder_yield
                              (fractions), buyback_ttm (元), total_mv (元)
            Raises:
                LakeError  -- a query fails
        """
        if codes is None:
            basic = self._query.sql(_BASIC.format(codes=""), [as_of])
        else:
            basic = self._query.sql(
                _BASIC.format(codes="AND list_contains(?, ts_code)"), [as_of, codes]
            )
        basic = basic.set_index("ts_code")
        executed = self._ledger.read_executed(as_of, codes)
        return self.compute(basic, executed)

    @staticmethod
    def compute(basic: pd.DataFrame, executed: pd.Series) -> pd.DataFrame:
        """
        Purpose:
            Combine dividend yield and executed buybacks into the yields.

        Contract:
            Input:
                basic: DataFrame  -- index ts_code; dv_ttm (percent), total_mv (万元)
                executed: Series  -- ts_code -> buyback money (元) over 12 months
            Output:
                DataFrame  -- COLUMNS (fractions; money in 元)
            Raises:
                (none)
        """
        mv = basic["total_mv"] * 1e4
        out = pd.DataFrame(index=basic.index)
        out["dividend_yield"] = basic["dv_ttm"].fillna(0.0) / 100
        out["buyback_ttm"] = executed.reindex(basic.index).fillna(0.0)
        out["total_mv"] = mv
        out["buyback_yield"] = out["buyback_ttm"] / mv
        out["shareholder_yield"] = out["dividend_yield"] + out["buyback_yield"]
        return out[COLUMNS]

    def read_metrics(self, codes: list[str], as_of: str) -> pd.DataFrame:
        """
        Purpose:
            Condition metrics of `codes` on `as_of` (plan 23 ph5): shareholder and buyback yield,
            the largest live buyback plan as % of total market cap (research: plans >= 2%
            predict +2% over 60 days, +4.6% since 2024) and the share of it already executed.

        Contract:
            Input:
                codes: list[str]; as_of: str (YYYYMMDD)
            Output:
                DataFrame  -- index = codes, METRICS; plan columns NaN without a live plan
            Raises:
                LakeError  -- a query fails
        """
        yields = self.read(as_of, codes)
        programmes = self._ledger.build_programmes(self._ledger.read_rows(as_of, codes), as_of)
        plans = self.compute_plans(programmes, yields["total_mv"])
        out = yields[["shareholder_yield", "buyback_yield"]].join(plans)
        return out.reindex(pd.Index(codes, name="ts_code"))[METRICS]

    @staticmethod
    def compute_plans(programmes: pd.DataFrame, total_mv: pd.Series) -> pd.DataFrame:
        """
        Purpose:
            Largest live plan per stock and how much of it is done.

        Contract:
            Input:
                programmes: BuybackLedger.build_programmes output; total_mv: ts_code -> 元
            Output:
                DataFrame  -- index ts_code; buyback_plan_pct (percent of market cap),
                              buyback_done_pct (fraction of the plan executed)
            Raises:
                (none)
        """
        live = programmes[(programmes["state"] == "open") & programmes["planned_amount"].notna()]
        live = live[live["planned_amount"] > 0]
        top = live.sort_values("planned_amount").groupby("ts_code").tail(1).set_index("ts_code")
        mv = total_mv.reindex(top.index)
        return pd.DataFrame(
            {
                "buyback_plan_pct": top["planned_amount"] / mv * 100,
                "buyback_done_pct": top["executed_amount"] / top["planned_amount"],
            }
        )
