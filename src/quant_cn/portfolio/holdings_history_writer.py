"""Daily history of the user's book in the lake (plan 15 phase 7d, D-132)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter

POSITIONS_TABLE, RISK_TABLE = "holdings_positions", "holdings_risk"
COLUMNS = {
    POSITIONS_TABLE: ["trade_date", "code", "shares", "cost", "close", "value", "pnl", "weight"],
    RISK_TABLE: ["trade_date", "component", "value"],
}
_POSITION_KEYS = ("code", "shares", "cost", "close", "value", "pnl", "weight")


class HoldingsHistoryWriter:
    """
    Purpose:
        Store one session of the holdings document in the lake so history accumulates outside
        git: derived/holdings_positions (one row per position plus a CASH row) and
        derived/holdings_risk (risk components, `x:<factor>` exposures, `c:<factor>` shares
        of risk), one file per year; rerunning a session replaces its rows.

    Contract:
        Input:
            query:  LakeQuery      -- reads the existing derived.holdings_* views
            writer: ParquetWriter  -- write_derived
        Output:
            instance; `write(doc)` -> list[Path]
        Raises:
            (none at construction)

    Used by:
        portfolio.HoldingsRiskBuilder  -- after the JSON is written
        cli.ResearchCommands           -- `holdings-risk` command wiring

    Test cases:
        TC-HHW-001  both tables written with a CASH row; rerunning the session replaces its
                    rows; other sessions of the year are kept
    """

    def __init__(self, query: LakeQuery, writer: ParquetWriter) -> None:
        self._query = query
        self._writer = writer

    def write(self, doc: dict[str, Any]) -> list[Path]:
        """
        Purpose:
            Replace the session's rows in both year files.

        Contract:
            Input:
                doc: dict  -- a non-empty HoldingsRiskBuilder.build result
            Output:
                list[Path]  -- the two year files written
            Raises:
                LakeError  -- write failed
        """
        day = doc["as_of"]
        positions = [
            {"trade_date": day, **{k: p[k] for k in _POSITION_KEYS}} for p in doc["positions"]
        ]
        cash = {"trade_date": day, "code": "CASH", "value": doc["cash"]}
        positions.append(cash | {"weight": doc["cash"] / doc["value"] if doc["value"] else None})
        risk = [{"trade_date": day, "component": k, "value": v} for k, v in doc["risk"].items()]
        for f in doc["factors"]:
            risk.append(
                {"trade_date": day, "component": f"x:{f['factor']}", "value": f["exposure"]}
            )
            risk.append({"trade_date": day, "component": f"c:{f['factor']}", "value": f["contrib"]})
        frames = {POSITIONS_TABLE: pd.DataFrame(positions), RISK_TABLE: pd.DataFrame(risk)}
        return [self._write_session(name, day, frame) for name, frame in frames.items()]

    def _write_session(self, name: str, day: str, frame: pd.DataFrame) -> Path:
        view, year = f"derived.{name}", day[:4]
        if self._query.has_view(view):
            sql = f"SELECT * FROM {view} WHERE substr(trade_date, 1, 4) = ? AND trade_date <> ?"
            old = self._query.sql(sql, [year, day])
            frame = pd.concat([old, frame], ignore_index=True) if not old.empty else frame
        columns = COLUMNS[name]
        frame = frame.reindex(columns=columns).sort_values(columns[:2]).reset_index(drop=True)
        return self._writer.write_derived(name, int(year), frame)
