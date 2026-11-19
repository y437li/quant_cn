"""Per-stock 融资融券 documents for the app (plan 15 ph7m)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.calculation.margin_ladder_estimator import MarginLadderEstimator
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

FOLDER = "margin"
DAYS = 130  # sessions in the daily series (~ 6 months)
WINDOW = 20  # sessions of the 20-day changes
DRAWDOWNS = (10, 20, 25, 30, 35, 40)
MAINTENANCE, LOW_MARGIN = 1.3, 0.8  # maintenance ratio; the lower initial-margin assumption
_DETAIL = """
SELECT m.ts_code, m.trade_date, m.rzye, m.rzmre, m.rzche, m.rqye, m.rqyl, m.rqmcl, d.close,
       b.circ_mv
FROM curated.margin_detail m JOIN curated.daily d USING (ts_code, trade_date)
LEFT JOIN curated.daily_basic b USING (ts_code, trade_date)
WHERE m.trade_date >= ? AND m.trade_date <= ? {codes}
ORDER BY m.ts_code, m.trade_date
"""


class MarginPanelBuilder:
    """
    Purpose:
        For every stock with margin data on the last session (or the given codes): the last ~6
        months of financing balance, buying and repayment, short balance and short sales; the
        balances as % of float market cap; 20-day changes; the short balance vs its own maximum
        since `start`; and plan 09's FIFO forced-liquidation ladder (debt forced at each further
        fall, first liquidation price at 100% and at 80% initial margin). One JSON per stock.

    Contract:
        Input:
            query:     LakeQuery              -- curated.margin_detail, daily, daily_basic
            estimator: MarginLadderEstimator  -- FIFO vintages (maintenance 1.3, margin 100%)
            start:     str                    -- YYYYMMDD, first day of vintages and history
        Output:
            instance; `build(as_of, codes)` -> dict code -> document, `write(out_dir, as_of)`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `margin-panel` command

    Test cases:
        TC-MPB-001  document fields on hand rows: % of float, 20-day change, net buying, short
                    max ratio, daily series length
        TC-MPB-002  ladder: first liquidation price at 100% and 80% margin, debt forced by fall
        TC-MPB-003  write puts one file per stock under margin/; a missing directory raises
    """

    def __init__(
        self, query: LakeQuery, estimator: MarginLadderEstimator, start: str = "20250601"
    ) -> None:
        self._query = query
        self._estimator = estimator
        self._start = start

    def build(self, as_of: str, codes: list[str] | None = None) -> dict[str, dict[str, Any]]:
        """
        Purpose:
            One document per stock with margin data on the last session on or before `as_of`.

        Contract:
            Input:
                as_of: str (YYYYMMDD); codes: list[str] | None  -- None = every margin stock
            Output:
                dict  -- ts_code -> {code, as_of, float_mv_yi, rz_yi, rz_pct_float, rz_chg_20d,
                         rz_net_20d_yi, rq_wan, rq_pct_float, rq_max_wan, rq_sell_20d_wan,
                         ladder: {...}, daily: [{d, close, rz, buy, repay, rq, rq_sell}]}
                         (money in 亿, short balance in 万元)
            Raises:
                LakeError  -- a query fails
        """
        sql = _DETAIL.format(codes="" if codes is None else "AND list_contains(?, m.ts_code)")
        params: list[object] = [self._start, as_of] + ([codes] if codes is not None else [])
        rows = self._query.sql(sql, params)
        if rows.empty:
            return {}
        last = str(rows["trade_date"].max())
        rows = rows[rows["ts_code"].isin(rows.loc[rows["trade_date"] == last, "ts_code"])]
        ladder = self._estimator.compute_ladder(
            rows[["ts_code", "trade_date", "rzye", "rzmre", "rzche"]],
            rows[["ts_code", "trade_date", "close"]],
            last,
        )
        lad = dict(tuple(ladder.groupby("ts_code")))
        return {
            str(code): self.build_document(str(code), stock, lad.get(code))
            for code, stock in rows.groupby("ts_code")
        }

    def build_document(
        self, code: str, stock: pd.DataFrame, ladder: pd.DataFrame | None
    ) -> dict[str, Any]:
        """
        Purpose:
            The document of one stock from its rows and ladder.

        Contract:
            Input:
                code: str; stock: rows of one stock sorted by date; ladder: its vintages or None
            Output:
                dict  -- as one value of build
            Raises:
                (none)
        """
        s = stock.sort_values("trade_date").reset_index(drop=True)
        last = s.iloc[-1]
        mv = float(last["circ_mv"]) * 1e4 if pd.notna(last["circ_mv"]) else None
        prev = s.iloc[-WINDOW - 1] if len(s) > WINDOW else None
        tail = s.iloc[-WINDOW:]
        rq_max = float(s["rqye"].max()) if s["rqye"].notna().any() else None
        return {
            "code": code,
            "as_of": str(last["trade_date"]),
            "float_mv_yi": None if mv is None else round(mv / 1e8, 2),
            "rz_yi": self._to_yi(last["rzye"]),
            "rz_pct_float": None if mv is None else round(float(last["rzye"]) / mv * 100, 3),
            "rz_chg_20d": None if prev is None or not prev["rzye"] else
            round(float(last["rzye"]) / float(prev["rzye"]) - 1, 4),
            "rz_net_20d_yi": self._to_yi((tail["rzmre"] - tail["rzche"]).sum()),
            "rq_wan": self._to_wan(last["rqye"]),
            "rq_pct_float": None if mv is None else round(float(last["rqye"] or 0) / mv * 100, 4),
            "rq_max_wan": self._to_wan(rq_max),
            "rq_sell_20d_wan": round(float(tail["rqmcl"].fillna(0).sum()) / 1e4, 2),
            "ladder": self._build_ladder(ladder, float(last["close"])),
            "daily": [
                {"d": str(r["trade_date"]), "close": self._to_number(r["close"]),
                 "rz": self._to_yi(r["rzye"]), "buy": self._to_yi(r["rzmre"]),
                 "repay": self._to_yi(r["rzche"]), "rq": self._to_wan(r["rqye"]),
                 "rq_sell": self._to_number(r["rqmcl"])}
                for r in s.iloc[-DAYS:].to_dict("records")
            ],
        }  # fmt: skip

    def write(self, out_dir: Path, as_of: str) -> int:
        """
        Purpose:
            Build every stock and write `<out_dir>/margin/<code>.json`.

        Contract:
            Input:
                out_dir: Path  -- existing directory (the chain app's data dir); as_of: str
            Output:
                int  -- files written
            Raises:
                LakeError  -- a query fails, or out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"margin panel output directory missing: {out_dir}")
        folder = out_dir / FOLDER
        folder.mkdir(exist_ok=True)
        docs = self.build(as_of)
        for code, doc in docs.items():
            (folder / f"{code}.json").write_text(
                json.dumps(doc, ensure_ascii=False), encoding="utf-8"
            )
        logger.info("margin panel: %d stocks -> %s", len(docs), folder)
        return len(docs)

    def _build_ladder(self, ladder: pd.DataFrame | None, price: float) -> dict[str, Any]:
        if ladder is None or ladder.empty:
            return {"debt_yi": 0.0, "first_liq": None, "first_liq_low_margin": None, "forced": []}
        top = float(ladder["entry_price"].max())
        curve = self._estimator.compute_curve(ladder, DRAWDOWNS)
        return {
            "debt_yi": self._to_yi(ladder["debt"].sum()),
            "first_liq": round(float(ladder["liquidation_price"].max()), 2),
            "first_liq_low_margin": round(top * MAINTENANCE / (1 + LOW_MARGIN), 2),
            "forced": [
                {"fall_pct": fall, "price": round(price * (1 - fall / 100), 2),
                 "debt_yi": self._to_yi(debt), "share": round(share, 3)}
                for fall, debt, share in zip(
                    curve["drawdown_pct"].astype(float), curve["debt_forced"].astype(float),
                    curve["share_of_debt"].astype(float), strict=True,
                )
            ],
        }  # fmt: skip

    @staticmethod
    def _to_yi(v: Any) -> float | None:
        return None if v is None or pd.isna(v) else round(float(v) / 1e8, 3)

    @staticmethod
    def _to_number(v: Any) -> float | None:
        return None if v is None or pd.isna(v) else float(v)

    @staticmethod
    def _to_wan(v: Any) -> float | None:
        return None if v is None or pd.isna(v) else round(float(v) / 1e4, 1)
