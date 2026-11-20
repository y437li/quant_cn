"""The user's holdings valued and decomposed by the risk model (plan 15 phase 7d, D-132)."""

from __future__ import annotations

import json
import logging
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.core.positions_book import PositionsBook
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.holdings_history_writer import HoldingsHistoryWriter
from quant_cn.portfolio.look_through_weights import LookThroughWeights
from quant_cn.portfolio.position_reviewer import PositionReviewer
from quant_cn.risk.base_risk_model import BaseRiskModel
from quant_cn.risk.risk_decomposer import RiskDecomposer
from quant_cn.risk.risk_snapshot import RiskSnapshot

logger = logging.getLogger(__name__)

FILE_NAME = "holdings_risk.json"
ANNUAL = math.sqrt(252)
_SESSION = "SELECT max(trade_date) FROM derived.risk_specific_risk WHERE trade_date <= ?"
_CLOSES = (
    "SELECT ts_code, close, 'stock' AS kind FROM curated.daily "
    "WHERE trade_date = ? AND list_contains(?, ts_code)"
)
_FUND_CLOSES = (
    " UNION ALL SELECT ts_code, close, 'etf' AS kind FROM curated.fund_daily "
    "WHERE trade_date = ? AND list_contains(?, ts_code)"
)
_BENCH = """
SELECT con_code AS ts_code, weight FROM curated.index_weight
WHERE index_code = ? AND trade_date = (SELECT max(trade_date) FROM curated.index_weight
                                       WHERE index_code = ? AND trade_date <= ?)
"""
_ZERO = 1e-12  # exposures below this are treated as none
_LABELS = "SELECT DISTINCT l1_code, l1_name FROM derived.industry_l1 WHERE l1_name IS NOT NULL"


class HoldingsRiskBuilder:
    """
    Purpose:
        Value the user's book at the close of the latest risk-model session and decompose its
        forecast risk: total / factor / specific vol and the same against a benchmark index
        (tracking error), style and industry exposures with each factor's share of risk, each
        stock's weight, P&L, own vol and share of portfolio risk, pairwise correlations. Write
        `holdings_risk.json` and hand the session to HoldingsHistoryWriter for the lake. An
        ETF (priced from fund_daily) enters the model through its index constituents
        (LookThroughWeights, ph7q): portfolio risk uses the look-through stock weights,
        per-position vol / contribution / correlation use L Σ Lᵀ.

    Contract:
        Input:
            book:       PositionsBook   -- shares, cost, cash
            query:      LakeQuery       -- curated.daily, fund_daily, index_weight, risk views
            model:      BaseRiskModel   -- `load_snapshot`
            decomposer: RiskDecomposer
            history:    HoldingsHistoryWriter  -- appends the session to the lake
            benchmark:  str             -- index_code of the benchmark, e.g. "000300.SH"
            reviewer:   PositionReviewer | None  -- notes, flags, chips, conditions (ph7f)
            look_through: LookThroughWeights | None  -- ETF baskets; None = stocks only
        Output:
            instance; `build(trade_date)` -> dict, `write(out_dir, trade_date)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.AppServiceBuilder  -- wires it

    Test cases:
        TC-HRB-001  weights = shares x close / (stock value + cash); P&L = shares x (close - cost);
                    total / factor / specific match RiskSnapshot.compute_variance (annualised)
        TC-HRB-002  stock contributions sum to 1 (Euler); correlation diagonal 1; a code without
                    a close or forecast is listed in `missing`, not dropped silently; each
                    stock's style exposures equal its snapshot row, industry = its ind_ column
        TC-HRB-003  write stores the session through the history writer (see TC-HHW-001)
        TC-HRB-004  empty book -> empty document without reading the model; no risk session
                    -> LakeError; write to a missing directory -> LakeError
        TC-HRB-005  with a reviewer, `reviews` holds one row per priced position; without, {}
        TC-HRB-006  cost <= 0 (diluted cost, paid back): pnl = shares x (close - cost), pnl_pct
                    None (D-166)
        TC-HRB-007  an ETF with `tracks` is priced from fund_daily (kind etf), risk equals the
                    look-through stock weights' variance, contributions still sum to 1, its
                    exposures row is the basket average with industry "ETF"; the reviewer
                    sees stocks only; an ETF without `tracks` is in `missing`
    """

    def __init__(
        self,
        book: PositionsBook,
        query: LakeQuery,
        model: BaseRiskModel,
        decomposer: RiskDecomposer,
        history: HoldingsHistoryWriter,
        benchmark: str,
        reviewer: PositionReviewer | None = None,
        look_through: LookThroughWeights | None = None,
    ) -> None:
        self._book = book
        self._query = query
        self._model = model
        self._decomposer = decomposer
        self._history = history
        self._benchmark = benchmark
        self._reviewer = reviewer
        self._look_through = look_through or LookThroughWeights(query)

    def build(self, trade_date: str) -> dict[str, Any]:
        """
        Purpose:
            The holdings risk document at the last risk-model session on or before trade_date.

        Contract:
            Input:
                trade_date: str  -- YYYYMMDD upper bound
            Output:
                dict  -- {as_of, model, benchmark, cash, value, stock_value, pnl, risk: {total,
                         factor, specific, active_total, active_factor, active_specific},
                         positions: [{code, name, shares, cost, close, value, weight, pnl,
                         pnl_pct (None when cost <= 0), vol, contrib, kind}], factors: [{factor,
                         label, kind, exposure, active, contrib}], correlation: {codes,
                         matrix}, stock_exposures: {styles: [factor], rows: [{code,
                         industry, values: [..]}]},
                         missing: [code], reviews: {code: PositionReviewer.build row}};
                         vols annualised fractions; empty lists and "" as_of for an empty book
            Raises:
                LakeError  -- no risk-model session on or before trade_date
        """
        if not self._book.positions:
            return self._build_empty()
        session = self._query.sql(_SESSION, [trade_date]).iloc[0, 0]
        if not isinstance(session, str):
            raise LakeError(f"no risk-model session on or before {trade_date}: run make risk-model")
        snap = self._model.load_snapshot(session)
        held = self._read_positions(session)
        value = float(held["value"].sum()) + self._book.cash
        pw, lt = self._build_look_through(snap, held, value, session)
        missing = sorted(set(held["code"]) - set(pw.index))
        pos_cov = lt @ snap.compute_stock_cov(list(lt.columns)) @ lt.T
        stocks = self._compute_stock_risk(pos_cov, pw)
        held = held.join(stocks, on="code")
        held["weight"] = held["value"] / value
        return {
            "as_of": session,
            "model": self._model.name,
            "benchmark": self._benchmark,
            "cash": self._book.cash,
            "value": round(value, 2),
            "stock_value": round(float(held["value"].sum()), 2),
            "pnl": round(float(held["pnl"].sum()), 2),
            **self._build_risk(snap, lt.T @ pw, session),
            "positions": [self._to_record(r) for r in held.to_dict("records")],
            "correlation": self._build_correlation(pos_cov),
            "stock_exposures": self._build_stock_exposures(snap, lt, held),
            "missing": missing,
            "reviews": self._build_reviews(held, session),
        }

    def write(self, out_dir: Path, trade_date: str) -> Path:
        """
        Purpose:
            Build the document, write `holdings_risk.json` and store the session in the lake.

        Contract:
            Input:
                out_dir: Path; trade_date: str  -- as build
            Output:
                Path  -- the JSON file
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"holdings output directory missing: {out_dir}")
        doc = self.build(trade_date)
        path = out_dir / FILE_NAME
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        if doc["as_of"]:
            self._history.write(doc)
        logger.info(
            "holdings risk: %d positions as of %s -> %s", len(doc["positions"]), doc["as_of"], path
        )
        return path

    def _build_look_through(
        self, snap: RiskSnapshot, held: pd.DataFrame, value: float, session: str
    ) -> tuple[pd.Series, pd.DataFrame]:
        universe = snap.build_covered_weights(pd.Series(dtype=float))[0].index
        lt = self._look_through.build(self._book.positions, session, universe)
        priced = held.set_index("code")["value"].dropna() / value
        pw = priced[priced.index.isin(lt.index) & (priced != 0)]
        return pw, lt.loc[pw.index, (lt.loc[pw.index] != 0).any(axis=0)]

    def _read_positions(self, session: str) -> pd.DataFrame:
        book = pd.DataFrame([p.model_dump() for p in self._book.positions])
        codes = book["code"].tolist()
        funds = self._query.has_view("curated.fund_daily")
        sql = _CLOSES + (_FUND_CLOSES if funds else "")
        params = [session, codes] * (2 if funds else 1)
        closes = self._query.sql(sql, params).drop_duplicates("ts_code").set_index("ts_code")
        book["close"] = book["code"].map(closes["close"])
        book["kind"] = book["code"].map(closes["kind"]).fillna("stock")
        book["value"] = book["shares"] * book["close"]
        book["pnl"] = book["shares"] * (book["close"] - book["cost"])
        book["pnl_pct"] = (book["close"] / book["cost"] - 1).where(book["cost"] > 0)
        return book

    def _build_risk(self, snap: RiskSnapshot, weights: pd.Series, session: str) -> dict[str, Any]:
        bench = self._query.sql(_BENCH, [self._benchmark, self._benchmark, session])
        bw = (
            bench.set_index("ts_code")["weight"] / bench["weight"].sum()
            if not bench.empty
            else None
        )
        rows = self._decomposer.compute(snap, weights, "holdings", bw).set_index("component")
        risk_of = rows["risk"].astype(float)
        pct_of = rows["pct"].astype(float)
        parts = ["total", "factor", "specific"]
        names = parts + ([f"active_{k}" for k in parts] if bw is not None else [])
        labels = self._read_labels()
        factors = [
            {
                "factor": f,
                "label": labels.get(f.removeprefix("ind_"), f),
                "kind": self._get_kind(f),
                "exposure": self._to_number(risk_of[f"x:{f}"]),
                "active": self._to_number(risk_of[f"active_x:{f}"]) if bw is not None else None,
                "contrib": self._to_number(pct_of[f"f:{f}"]),
            }
            for f in snap.cov.columns
            if abs(risk_of[f"x:{f}"]) > _ZERO
            or (bw is not None and abs(risk_of[f"active_x:{f}"]) > _ZERO)
        ]
        risk = {k: self._to_number(risk_of[k] * ANNUAL) for k in names}
        return {"risk": risk, "factors": factors}

    @staticmethod
    def _get_kind(factor: str) -> str:
        if factor == "country":
            return "country"
        return "industry" if factor.startswith("ind_") else "style"

    @staticmethod
    def _compute_stock_risk(pos_cov: pd.DataFrame, h: pd.Series) -> pd.DataFrame:
        cov = pos_cov.to_numpy(float)
        w = h.to_numpy(float)
        variance = float(w @ cov @ w)
        contrib = w * (cov @ w) / variance if variance > 0 else np.zeros(len(w))
        vol = np.sqrt(np.diag(cov)) * ANNUAL
        return pd.DataFrame({"vol": vol, "contrib": contrib}, index=h.index)

    @staticmethod
    def _build_correlation(pos_cov: pd.DataFrame) -> dict[str, Any]:
        codes = [str(c) for c in pos_cov.index]
        if not codes:
            return {"codes": [], "matrix": []}
        cov = pos_cov.to_numpy(float)
        sd = np.sqrt(np.diag(cov))
        corr = cov / np.outer(sd, sd)
        return {"codes": codes, "matrix": [[round(float(v), 3) for v in row] for row in corr]}

    def _build_stock_exposures(
        self, snap: RiskSnapshot, lt: pd.DataFrame, held: pd.DataFrame
    ) -> dict[str, Any]:
        styles = [f for f in snap.exposures.columns if self._get_kind(f) == "style"]
        codes = [str(c) for c in lt.index]
        labels, x = self._read_labels(), lt @ snap.exposures.loc[list(lt.columns)]
        etfs = set(held.loc[held["kind"] == "etf", "code"])
        columns = [str(c) for c in x.columns]
        industries = [f for f in columns if f.startswith("ind_")]
        rows = []
        for code, values_row in zip(codes, x.to_numpy(float), strict=True):
            row = dict(zip(columns, values_row.tolist(), strict=True))
            industry = next((f for f in industries if row[f] > 0), "")
            values = [self._to_number(row[f]) for f in styles]
            label = "ETF" if code in etfs else labels.get(industry[4:], industry)
            rows.append({"code": code, "industry": label, "values": values})
        return {"styles": styles, "rows": rows}

    def _build_reviews(self, held: pd.DataFrame, session: str) -> dict[str, Any]:
        if self._reviewer is None:
            return {}
        stocks = held[held["kind"] == "stock"]
        priced = stocks.dropna(subset=["close"])[["code", "close", "weight"]]
        return self._reviewer.build(priced, session)

    def _read_labels(self) -> dict[str, str]:
        if not self._query.has_view("derived.industry_l1"):
            return {}
        rows = self._query.sql(_LABELS)
        return dict(zip(rows["l1_code"], rows["l1_name"], strict=True))

    def _to_record(self, row: Mapping[Any, Any]) -> dict[str, Any]:
        keys = (
            "code",
            "name",
            "shares",
            "cost",
            "close",
            "value",
            "weight",
            "pnl",
            "pnl_pct",
            "vol",
            "contrib",
        )
        record = {k: row[k] if k in ("code", "name") else self._to_number(row.get(k)) for k in keys}
        return record | {"kind": str(row.get("kind") or "stock")}

    def _build_empty(self) -> dict[str, Any]:
        return {
            "as_of": "",
            "model": self._model.name,
            "benchmark": self._benchmark,
            "cash": self._book.cash,
            "value": self._book.cash,
            "stock_value": 0.0,
            "pnl": 0.0,
            "risk": {},
            "positions": [],
            "factors": [],
            "correlation": {"codes": [], "matrix": []},
            "stock_exposures": {"styles": [], "rows": []},
            "missing": [],
            "reviews": {},
        }

    @staticmethod
    def _to_number(value: object) -> float | None:
        if value is None:
            return None
        number = float(value)  # type: ignore[arg-type]
        return None if math.isnan(number) or math.isinf(number) else round(number, 6)
