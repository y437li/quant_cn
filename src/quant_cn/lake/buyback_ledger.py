"""Buyback programmes and executed amounts from Tushare `repurchase` rows (plan 23, D-154)."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pandas as pd

from quant_cn.lake.lake_query import LakeQuery

PROGRAMME_COLUMNS = [
    "ts_code",
    "programme",
    "plan_date",
    "planned_amount",
    "high_limit",
    "exp_date",
    "state",
    "last_date",
    "executed_amount",
    "executed_vol",
    "seeded",
]
OPEN, STOPPED, EXPIRED = "open", "stopped", "expired"
FIT = 1.05  # a progress row fits a programme when planned amount x FIT >= its cumulative amount
DEFAULT_LIFE = 365  # days a 预案 without an expiry date stays open
_CLOSING = {"停止": STOPPED}
_EXECUTED = {"实施", "完成"}
# same-day order: progress and stops of older programmes before a new 预案, approvals after it
_SAME_DAY = {"实施": 0, "完成": 0, "停止": 1, "预案": 2, "股东大会通过": 3}
_ROWS = """
SELECT DISTINCT ts_code, ann_date, end_date, proc, exp_date, vol, amount, high_limit
FROM curated.repurchase WHERE ann_date <= ? {codes}
ORDER BY ts_code, ann_date
"""


class BuybackLedger:
    """
    Purpose:
        Turn buyback announcements into programmes and executed amounts, point in time. Rows of
        one stock are read in announcement order; one day's rows in a fixed order (实施 / 完成
        and 停止 first, as they belong to older programmes; then 预案, larger first; then
        股东大会通过; ties by end_date and amount), so input row order does not matter. A 预案
        opens a programme (planned amount, price cap, expiry; one year when none is given);
        programmes can run side by side (e.g. a large
        buyback and a small 回购注销限制性股票). 实施 and 完成 both carry the cumulative executed
        amount and shares (the vendor labels most progress reports 完成: 36k of 61k rows); such a
        row goes to the newest open, unexpired programme whose planned amount x 1.05 covers its
        cumulative amount, else the newest open one; its executed amount is the running maximum,
        never a sum. 股东大会通过 / 停止 go to the newest open programme; 停止 closes it. A
        programme past its expiry is expired. A progress row with no open programme (a plan
        before the data starts) opens a "seeded" programme without a planned amount.

    Contract:
        Input:
            query: LakeQuery  -- reads curated.repurchase
        Output:
            instance; `build_programmes(rows, as_of)` (pure), `read_programmes(as_of, codes)`,
            `compute_executed(rows, as_of, days)` (pure), `read_executed(as_of, codes, days)`
        Raises:
            (none at construction)

    Used by:
        lake.ShareholderYieldReader  -- buybacks over the last 12 months, live plans
        portfolio.BuybackMonitorBuilder  -- market-wide programmes (plan 32)
        cli.ReportCommands           -- wires it for the buyback monitor
        cli.AppServiceBuilder        -- wires it

    Test cases:
        TC-BBL-001  cumulative 实施 / 完成 amounts are not double counted; a small later 预案
                    does not take the progress of a larger open programme
        TC-BBL-002  停止 closes; an expired 预案 without 实施 has executed 0 and state expired
        TC-BBL-003  rows announced after as_of are ignored; executed in a window = growth of
                    the cumulative amount inside the window
        TC-BBL-004  an 实施 without an open programme opens a seeded programme
        TC-BBL-005  same-day rows: a 完成 filed with a new 预案 stays with the older programme;
                    shuffled input rows give the same programmes
    """

    def __init__(self, query: LakeQuery) -> None:
        self._query = query

    def read_rows(self, as_of: str, codes: list[str] | None = None) -> pd.DataFrame:
        """
        Purpose:
            Repurchase rows announced on or before `as_of`.

        Contract:
            Input:
                as_of: str (YYYYMMDD); codes: list[str] | None  -- None = every stock
            Output:
                DataFrame  -- ts_code, ann_date, end_date, proc, exp_date, vol, amount,
                              high_limit; exact duplicates dropped
            Raises:
                LakeError  -- the query fails
        """
        if codes is None:
            return self._query.sql(_ROWS.format(codes=""), [as_of])
        return self._query.sql(_ROWS.format(codes="AND list_contains(?, ts_code)"), [as_of, codes])

    def build_programmes(self, rows: pd.DataFrame, as_of: str) -> pd.DataFrame:
        """
        Purpose:
            Programmes of every stock in `rows`, as known on `as_of`.

        Contract:
            Input:
                rows: DataFrame  -- as read_rows; as_of: str (YYYYMMDD)
            Output:
                DataFrame  -- PROGRAMME_COLUMNS; programme = 1, 2, … per stock; amounts in 元;
                              state open / stopped / expired
            Raises:
                (none)
        """
        out: list[dict[str, Any]] = []
        known = self._build_order(rows[rows["ann_date"].astype(str) <= as_of])
        for code, stock in known.groupby("ts_code", sort=False):
            out += self._build_stock(str(code), stock, as_of)
        return pd.DataFrame(out, columns=PROGRAMME_COLUMNS)

    def read_programmes(self, as_of: str, codes: list[str] | None = None) -> pd.DataFrame:
        """
        Purpose:
            Programmes as known on `as_of`, read from the lake.

        Contract:
            Input:
                as_of: str; codes: list[str] | None
            Output:
                DataFrame  -- PROGRAMME_COLUMNS
            Raises:
                LakeError  -- the query fails
        """
        return self.build_programmes(self.read_rows(as_of, codes), as_of)

    def compute_executed(self, rows: pd.DataFrame, as_of: str, days: int = 365) -> pd.Series:
        """
        Purpose:
            Buyback money executed in the `days` before `as_of`, per stock.

        Contract:
            Input:
                rows: DataFrame (read_rows); as_of: str; days: int > 0
            Output:
                Series  -- ts_code -> 元 (cumulative executed on as_of minus on as_of - days,
                           summed over programmes); stocks without execution are absent
            Raises:
                (none)
        """
        start = (dt.datetime.strptime(as_of, "%Y%m%d") - dt.timedelta(days=days)).strftime("%Y%m%d")
        now = self.build_programmes(rows, as_of).set_index(["ts_code", "programme"])[
            "executed_amount"
        ]
        before = self.build_programmes(rows, start).set_index(["ts_code", "programme"])[
            "executed_amount"
        ]
        diff = (now - before.reindex(now.index).fillna(0.0)).clip(lower=0.0)
        out = diff.groupby(level="ts_code").sum()
        return out[out > 0]

    def read_executed(
        self, as_of: str, codes: list[str] | None = None, days: int = 365
    ) -> pd.Series:
        """
        Purpose:
            compute_executed over lake rows.

        Contract:
            Input:
                as_of: str; codes: list[str] | None; days: int
            Output:
                Series  -- ts_code -> 元
            Raises:
                LakeError  -- the query fails
        """
        return self.compute_executed(self.read_rows(as_of, codes), as_of, days)

    def _build_stock(self, code: str, stock: pd.DataFrame, as_of: str) -> list[dict[str, Any]]:
        progs: list[dict[str, Any]] = []
        for r in stock.itertuples():
            proc, day = str(r.proc), str(r.ann_date)
            if proc == "预案":
                progs.append(self._open(code, len(progs) + 1, r, seeded=False))
                continue
            live = [p for p in progs if p["state"] == OPEN and p["exp_date"] >= day]
            if proc in _EXECUTED:
                amount = self._to_number(r.amount)
                fits = [
                    p
                    for p in live
                    if p["planned_amount"] is None or p["planned_amount"] * FIT >= amount
                ]
                pool = fits or live
                target: dict[str, Any] | None = pool[-1] if pool else None
                if target is None:
                    target = self._open(code, len(progs) + 1, r, seeded=True)
                    progs.append(target)
                target["executed_amount"] = max(target["executed_amount"], amount)
                target["executed_vol"] = max(target["executed_vol"], self._to_number(r.vol))
                target["last_date"] = day
            elif live:
                live[-1]["last_date"] = day
                if proc in _CLOSING:
                    live[-1]["state"] = _CLOSING[proc]
        for p in progs:
            if p["state"] == OPEN and p["exp_date"] < as_of:
                p["state"] = EXPIRED
        return progs

    @staticmethod
    def _build_order(rows: pd.DataFrame) -> pd.DataFrame:
        amount = pd.to_numeric(rows["amount"], errors="coerce").fillna(0.0)
        keyed = rows.assign(
            _rank=rows["proc"].map(_SAME_DAY).fillna(len(_SAME_DAY)),
            _end=rows["end_date"].fillna("").astype(str),
            _amount=amount.where(rows["proc"] != "预案", -amount),
        )
        order = ["ts_code", "ann_date", "_rank", "_end", "_amount"]
        return keyed.sort_values(order, kind="stable").drop(columns=["_rank", "_end", "_amount"])

    def _open(self, code: str, n: int, r: Any, seeded: bool) -> dict[str, Any]:
        day = str(r.ann_date)
        exp = str(r.exp_date) if isinstance(r.exp_date, str) and r.exp_date else ""
        if not exp:
            start = dt.datetime.strptime(day, "%Y%m%d")
            exp = (start + dt.timedelta(days=DEFAULT_LIFE)).strftime("%Y%m%d")
        return {
            "ts_code": code,
            "programme": n,
            "plan_date": day,
            "planned_amount": None if seeded else self._to_number(r.amount),
            "high_limit": self._to_number(r.high_limit),
            "exp_date": exp,
            "state": OPEN,
            "last_date": day,
            "executed_amount": 0.0,
            "executed_vol": 0.0,
            "seeded": seeded,
        }

    @staticmethod
    def _to_number(v: Any) -> float:
        return 0.0 if v is None or pd.isna(v) else float(v)
