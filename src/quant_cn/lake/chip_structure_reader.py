"""Chip-structure and order-flow signals per stock, as known on a date (plan 15 ph7f, 筹码结构)."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from quant_cn.lake.lake_query import LakeQuery

GAUGE_VIEW = "derived.retail_gauge"
# latest RetailGauge reading (D-155 avoid, D-167 streaks); booleans as 1.0 / 0.0
GAUGE_EXTRA = [
    "gauge_exp_change",
    "gauge_avoid",
    "gauge_avoid_strong",
    "gauge_leaving",
    "gauge_lo_streak",
    "gauge_hi_streak",
]
GAUGE_KEYS = ["retail_gauge", *GAUGE_EXTRA]  # the reading as shown in the app and report
COLUMNS = [
    "holders_chg_q",
    "inst_top10_dq_pp",
    "north_chg_pp",
    "margin_chg_60d",
    "lg_weeks_pos_4w",
    "lg_net_4w",
    "lg_net_20d",
    "sm_weeks_neg_4w",
    "sm_net_4w",
    "unlock_6m_pct",
    "insider_sell_6m_pct",
    "holder_sell_90d_pct",
    "retail_gauge",
    "winner_rate",
    "cost_lo_gap",
    "cost_hi_gap",
    *GAUGE_EXTRA,
]
_INST = "基金|社保|保险|养老|香港中央结算"
_PAIR = 2  # a change needs the last two announced periods
_HOLDERS = """
SELECT ts_code, end_date, arg_min(holder_num, ann_date) AS n FROM curated.stk_holdernumber
WHERE list_contains(?, ts_code) AND ann_date <= ? GROUP BY 1, 2 ORDER BY 1, 2
"""
_INSTITUTIONS = """
SELECT ts_code, end_date, sum(hold_float_ratio) AS r FROM (
  SELECT DISTINCT ts_code, end_date, holder_name, hold_float_ratio FROM curated.top10_floatholders
  WHERE list_contains(?, ts_code) AND ann_date <= ? AND regexp_matches(holder_name, ?))
GROUP BY 1, 2 ORDER BY 1, 2
"""
_NORTH = """
SELECT ts_code, trade_date, ratio FROM curated.hk_hold
WHERE list_contains(?, ts_code) AND trade_date <= ? AND trade_date > ? ORDER BY 1, 2
"""
_CHANGE = """
SELECT ts_code, arg_min({col}, trade_date) AS first, arg_max({col}, trade_date) AS last
FROM curated.{table} WHERE list_contains(?, ts_code) AND trade_date > ? AND trade_date <= ?
GROUP BY 1
"""
_FLOWS = """
SELECT ts_code, trade_date, (buy_lg_amount - sell_lg_amount) / 1e4 AS lg,
       (buy_sm_amount - sell_sm_amount) / 1e4 AS sm
FROM curated.moneyflow WHERE list_contains(?, ts_code) AND trade_date > ? AND trade_date <= ?
"""
_UNLOCKS = """
SELECT ts_code, sum(float_ratio) AS r FROM (
  SELECT DISTINCT ts_code, float_date, holder_name, float_ratio FROM curated.share_float
  WHERE list_contains(?, ts_code) AND ann_date <= ? AND float_date > ? AND float_date <= ?)
GROUP BY 1
"""
_INSIDERS = """
SELECT ts_code, sum(change_ratio) AS r FROM (
  SELECT DISTINCT ts_code, ann_date, holder_name, change_vol, change_ratio
  FROM curated.stk_holdertrade
  WHERE list_contains(?, ts_code) AND in_de = 'DE' AND ann_date > ? AND ann_date <= ?) GROUP BY 1
"""
_WINNER = """
SELECT ts_code, arg_max(winner_rate, trade_date) AS winner_rate,
       arg_max(trade_date, trade_date) AS trade_date,
       arg_max(cost_15pct, trade_date) AS lo, arg_max(cost_85pct, trade_date) AS hi
FROM curated.cyq_perf
WHERE list_contains(?, ts_code) AND trade_date > ? AND trade_date <= ? GROUP BY 1
"""
_CLOSE = """
SELECT ts_code, trade_date, close FROM curated.daily
WHERE list_contains(?, ts_code) AND trade_date > ? AND trade_date <= ?
"""
_GAUGE = f"""
SELECT ts_code, arg_max(pct, as_of) AS retail_gauge, arg_max(exp_change, as_of) AS gauge_exp_change,
       arg_max(avoid::DOUBLE, as_of) AS gauge_avoid,
       arg_max(avoid_strong::DOUBLE, as_of) AS gauge_avoid_strong,
       arg_max(retail_leaving::DOUBLE, as_of) AS gauge_leaving,
       arg_max(lo_streak::DOUBLE, as_of) AS gauge_lo_streak,
       arg_max(hi_streak::DOUBLE, as_of) AS gauge_hi_streak
FROM {GAUGE_VIEW} WHERE list_contains(?, ts_code) AND as_of <= ? AND as_of >= ? GROUP BY 1
"""


class ChipStructureReader:
    """
    Purpose:
        Read the 筹码结构 signals of a set of stocks as known on `as_of` (only rows announced
        or traded on or before it): shareholder-count change, top-10 institutional change,
        northbound change between its last two disclosures (quarterly since 2024), margin
        trend, large / small order weekly flows, unlocks ahead and insider sales, and the
        latest RetailGauge reading from derived.retail_gauge (as_of on or before the date and
        at most `gauge_max_age_days` old, since a quarter's first 14 sessions have none: pct,
        expected change, avoid / avoid_strong / retail_leaving flags as 1.0 / 0.0 and the
        D-167 streaks; NaN without the table), and the winner rate and cost band from
        curated.cyq_perf (last session within 10 days; NaN without the dataset):
        cost_lo_gap / cost_hi_gap = that session's close / cost_15pct (cost_85pct) - 1, so > 0
        means the price is above the cheapest 15% (most expensive 15%) of holders' cost
        (plan 21 ph4). Holder sales are de-duplicated (vendor repeats rows, D-081).

    Contract:
        Input:
            query:      LakeQuery    -- curated stk_holdernumber, top10_floatholders, hk_hold,
                                        margin_detail, moneyflow, share_float, stk_holdertrade
            gauge_max_age_days: int  -- oldest RetailGauge reading used (default 45)
        Output:
            instance; `read(codes, as_of) -> DataFrame` indexed by ts_code with COLUMNS
        Raises:
            (none at construction)

    Used by:
        portfolio.OpportunityScreen  -- signal row
        cli.GaugeCommands  -- wires it
        cli.AppServiceBuilder  -- `build_sector_monitor`
        portfolio.SectorMonitorBuilder  -- RetailGauge per company
        portfolio.ConditionEvaluator  -- metrics for conditions and chip rows
        cli.AppServiceBuilder  -- wires it

    Test cases:
        TC-CSR-001  holders and institutional changes use only rows announced by as_of
        TC-CSR-002  weekly flows: positive-week count and 4-week sums in 亿 from fixture days
        TC-CSR-003  unlocks ahead and insider sales windows; no retail_gauge table -> NaN
                    columns; the latest fresh reading and its flags; a stale one is ignored
        TC-CSR-004  duplicate sale rows count once; 90-day window; winner rate from cyq_perf
        TC-CSR-005  cost band gaps from the last cyq_perf session's close and cost_15 / 85pct
    """

    def __init__(self, query: LakeQuery, gauge_max_age_days: int = 45) -> None:
        self._query = query
        self._gauge_age = gauge_max_age_days

    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        """
        Purpose:
            All chip signals for `codes` on `as_of`.

        Contract:
            Input:
                codes: list[str]  -- ts_codes
                as_of: str        -- YYYYMMDD
            Output:
                DataFrame  -- index = codes (order kept), columns = COLUMNS; NaN when unknown
            Raises:
                LakeError  -- a query fails
        """
        out = pd.DataFrame(index=pd.Index(codes, name="ts_code"), columns=COLUMNS, dtype=float)
        if not codes:
            return out
        day = dt.datetime.strptime(as_of, "%Y%m%d").date()
        back = (day - dt.timedelta(days=90)).strftime("%Y%m%d")
        half = (day - dt.timedelta(days=182)).strftime("%Y%m%d")
        ahead = (day + dt.timedelta(days=182)).strftime("%Y%m%d")
        out["holders_chg_q"] = self._compute_last_change(
            self._query.sql(_HOLDERS, [codes, as_of]), "n", ratio=True
        )
        inst = self._query.sql(_INSTITUTIONS, [codes, as_of, _INST])
        out["inst_top10_dq_pp"] = self._compute_last_change(inst, "r", ratio=False)
        year = (day - dt.timedelta(days=400)).strftime("%Y%m%d")  # disclosures are quarterly
        north = self._query.sql(_NORTH, [codes, as_of, year])
        out["north_chg_pp"] = self._compute_last_change(north, "ratio", ratio=False)
        out["margin_chg_60d"] = self._read_change(
            "margin_detail", "rzye", codes, back, as_of, ratio=True
        )
        out.update(self._compute_flows(codes, as_of))
        unlocks = self._query.sql(_UNLOCKS, [codes, as_of, as_of, ahead]).set_index("ts_code")["r"]
        out["unlock_6m_pct"] = unlocks.reindex(out.index).fillna(0.0)
        sells = self._query.sql(_INSIDERS, [codes, half, as_of]).set_index("ts_code")["r"]
        out["insider_sell_6m_pct"] = sells.reindex(out.index).fillna(0.0)
        recent = self._query.sql(_INSIDERS, [codes, back, as_of]).set_index("ts_code")["r"]
        out["holder_sell_90d_pct"] = recent.reindex(out.index).fillna(0.0)
        chips = self._read_winner(codes, day, as_of).reindex(out.index)
        out[chips.columns] = chips
        gauge = self._read_gauge(codes, day, as_of).reindex(out.index)
        out[gauge.columns] = gauge
        return out

    @staticmethod
    def _compute_last_change(frame: pd.DataFrame, col: str, ratio: bool) -> pd.Series:
        if frame.empty:
            return pd.Series(dtype=float)
        last = frame.groupby("ts_code")[col].agg(lambda s: list(s.tail(2)))
        return last.map(lambda pair: ChipStructureReader._compute_pair(pair, ratio)).astype(float)

    @staticmethod
    def _compute_pair(pair: list[float], ratio: bool) -> float:
        if len(pair) < _PAIR or pd.isna(pair[0]) or (ratio and pair[0] == 0):
            return float("nan")
        return pair[1] / pair[0] - 1 if ratio else pair[1] - pair[0]

    def _read_change(
        self, table: str, col: str, codes: list[str], start: str, end: str, ratio: bool
    ) -> pd.Series:
        frame = self._query.sql(_CHANGE.format(col=col, table=table), [codes, start, end])
        frame = frame.set_index("ts_code")
        if ratio:
            return (frame["last"] / frame["first"].where(frame["first"] != 0) - 1).astype(float)
        return (frame["last"] - frame["first"]).astype(float)

    def _compute_flows(self, codes: list[str], as_of: str) -> pd.DataFrame:
        start = (dt.datetime.strptime(as_of, "%Y%m%d") - dt.timedelta(days=40)).strftime("%Y%m%d")
        days = self._query.sql(_FLOWS, [codes, start, as_of])
        cols = ["lg_weeks_pos_4w", "lg_net_4w", "lg_net_20d", "sm_weeks_neg_4w", "sm_net_4w"]
        if days.empty:
            return pd.DataFrame(columns=cols, dtype=float)
        dates = pd.to_datetime(days["trade_date"], format="%Y%m%d")
        days["week"] = dates.dt.strftime("%G-%V")
        weeks = days.groupby(["ts_code", "week"])[["lg", "sm"]].sum().groupby(level=0).tail(4)
        by = weeks.groupby(level=0)
        last20 = days.sort_values("trade_date").groupby("ts_code").tail(20)
        return pd.DataFrame(
            {
                "lg_weeks_pos_4w": by["lg"].apply(lambda s: float((s > 0).sum())),
                "lg_net_4w": by["lg"].sum(),
                "lg_net_20d": last20.groupby("ts_code")["lg"].sum(),
                "sm_weeks_neg_4w": by["sm"].apply(lambda s: float((s < 0).sum())),
                "sm_net_4w": by["sm"].sum(),
            }
        )

    def _read_winner(self, codes: list[str], day: dt.date, as_of: str) -> pd.DataFrame:
        cols = ["winner_rate", "cost_lo_gap", "cost_hi_gap"]
        if not self._query.has_view("curated.cyq_perf"):
            return pd.DataFrame(columns=cols, dtype=float)
        week = (day - dt.timedelta(days=10)).strftime("%Y%m%d")
        frame = self._query.sql(_WINNER, [codes, week, as_of])
        if self._query.has_view("curated.daily"):
            closes = self._query.sql(_CLOSE, [codes, week, as_of])
            frame = frame.merge(closes, on=["ts_code", "trade_date"], how="left")
        else:
            frame["close"] = float("nan")
        close = frame["close"].astype(float)
        frame["cost_lo_gap"] = close / frame["lo"].astype(float).where(frame["lo"] > 0) - 1
        frame["cost_hi_gap"] = close / frame["hi"].astype(float).where(frame["hi"] > 0) - 1
        return frame.set_index("ts_code")[cols].astype(float)

    def _read_gauge(self, codes: list[str], day: dt.date, as_of: str) -> pd.DataFrame:
        cols = GAUGE_KEYS
        if not self._query.has_view(GAUGE_VIEW):
            return pd.DataFrame(columns=cols, dtype=float)
        oldest = (day - dt.timedelta(days=self._gauge_age)).strftime("%Y%m%d")
        frame = self._query.sql(_GAUGE, [codes, as_of, oldest]).set_index("ts_code")
        return frame[cols].astype(float)
