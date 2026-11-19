"""China macro monitor behind the app's 宏观 page and the e-mail block (plan 15 ph7h, D-143)."""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

FILE_NAME = "macro_monitor.json"
WINDOW = 60  # prints in the percentile window and the chart history (5 years)
TABLES = {
    "cn_cpi": ["nt_yoy", "nt_mom"],
    "cn_ppi": ["ppi_yoy", "ppi_mom", "ppi_mp_yoy", "ppi_cg_yoy"],
    "cn_pmi": ["pmi010000", "pmi020100", "pmi030000"],
    "cn_m": ["m1_yoy", "m2_yoy"],
    "sf_month": ["inc_month", "stk_endval"],
}


@dataclass(frozen=True)
class MacroSeries:
    """
    Purpose:
        One monitored line: key, Chinese name, group, unit and the column of the merged monthly
        frame it reads (a vendor column or one of the derived columns).

    Contract:
        Input:
            key, name, group, unit, column: str
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        calculation.MacroMonitorBuilder  -- SERIES

    Test cases:
        TC-MMB-001  every series in SERIES appears in the document built from a full lake
    """

    key: str
    name: str
    group: str
    unit: str
    column: str


SERIES = (
    MacroSeries("cpi", "CPI 同比", "价格", "%", "nt_yoy"),
    MacroSeries("cpi_mom", "CPI 环比", "价格", "%", "nt_mom"),
    MacroSeries("ppi", "PPI 同比", "价格", "%", "ppi_yoy"),
    MacroSeries("ppi_mom", "PPI 环比", "价格", "%", "ppi_mom"),
    MacroSeries("ppi_mp", "PPI 生产资料同比", "价格", "%", "ppi_mp_yoy"),
    MacroSeries("ppi_cg", "PPI 生活资料同比", "价格", "%", "ppi_cg_yoy"),
    MacroSeries("ppi_cpi_gap", "PPI \u2212 CPI", "价格", "pp", "ppi_cpi_gap"),
    MacroSeries("pmi_mfg", "制造业 PMI", "景气", "", "pmi010000"),
    MacroSeries("pmi_non_mfg", "非制造业商务活动", "景气", "", "pmi020100"),
    MacroSeries("pmi_composite", "综合 PMI 产出", "景气", "", "pmi030000"),
    MacroSeries("m1", "M1 同比", "货币", "%", "m1_yoy"),
    MacroSeries("m2", "M2 同比", "货币", "%", "m2_yoy"),
    MacroSeries("m1_m2", "M1 \u2212 M2 剪刀差", "货币", "pp", "m1_m2"),
    MacroSeries("sf_inc", "当月新增社融", "社融", "亿元", "inc_month"),
    MacroSeries("sf_inc_vs_ly", "新增社融 同比多增", "社融", "亿元", "sf_inc_vs_ly"),
    MacroSeries("sf_stock_yoy", "社融存量同比", "社融", "%", "sf_stock_yoy"),
)


class MacroMonitorBuilder:
    """
    Purpose:
        Read the curated monthly macro tables (CPI, PPI, PMI, money supply, 社融), add the
        derived lines (PPI - CPI, M1 - M2, 社融 stock yoy, new 社融 vs the same month last year)
        and summarise each line: latest print, previous print, change, percentile in the last
        60 prints and whether the print is new since the previous document.

    Contract:
        Input:
            query: LakeQuery  -- reads curated.cn_cpi, cn_ppi, cn_pmi, cn_m, sf_month
        Output:
            instance; `build(previous)` -> dict, `write(out_dir)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `macro-monitor` command

    Test cases:
        TC-MMB-001  derived lines from hand values: gap, scissor, stock yoy, vs last year
        TC-MMB-002  new_print is true for a month not in the previous document, then false
        TC-MMB-003  percentile counts only the last 60 prints up to the latest
        TC-MMB-004  a missing table is listed in `missing`; its lines are left out, not zero
        TC-MMB-005  write puts macro_monitor.json in the directory; missing directory raises
        TC-MMB-006  every table missing raises LakeError
    """

    def __init__(self, query: LakeQuery) -> None:
        self._query = query

    def build(self, previous: dict[str, Any] | None) -> dict[str, Any]:
        """
        Purpose:
            The monitor document.

        Contract:
            Input:
                previous: dict | None  -- the last written document (for new_print)
            Output:
                dict  -- {as_of: latest month, missing: [table], new_prints: [key],
                         series: [{key, name, group, unit, month, value, prev_month, prev,
                         change, pct_5y, new_print, history: [{month, value}]}]}
            Raises:
                LakeError  -- every table is missing
        """
        frame, missing = self._read_frame()
        seen = {s["key"]: s["month"] for s in (previous or {}).get("series", [])}
        series = [
            row
            for s in SERIES
            if s.column in frame.columns
            for row in [self._build_series(s, frame[s.column].dropna(), seen)]
            if row is not None
        ]
        return {
            "as_of": max((s["month"] for s in series), default=""),
            "missing": missing,
            "new_prints": [s["key"] for s in series if s["new_print"]],
            "series": series,
        }

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build against the previous `macro_monitor.json` in out_dir and overwrite it.

        Contract:
            Input:
                out_dir: Path  -- existing directory (the chain app's data dir)
            Output:
                Path  -- the written file, UTF-8 JSON
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"macro monitor output directory missing: {out_dir}")
        path = out_dir / FILE_NAME
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        doc = self.build(previous)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("macro monitor: %d new prints -> %s", len(doc["new_prints"]), path)
        return path

    def _read_frame(self) -> tuple[pd.DataFrame, list[str]]:
        frames, missing = [], []
        for table, cols in TABLES.items():
            try:
                df = self._query.sql(f"SELECT month, {', '.join(cols)} FROM curated.{table}")
            except LakeError:
                missing.append(table)
                continue
            frames.append(df.assign(month=df["month"].astype(str)).set_index("month"))
        if not frames:
            raise LakeError("macro monitor: no curated macro table; run make track-daily")
        frame = pd.concat(frames, axis=1).sort_index().apply(pd.to_numeric, errors="coerce")
        return self._add_derived(frame), missing

    @staticmethod
    def _add_derived(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        if {"ppi_yoy", "nt_yoy"} <= set(out.columns):
            out["ppi_cpi_gap"] = out["ppi_yoy"] - out["nt_yoy"]
        if {"m1_yoy", "m2_yoy"} <= set(out.columns):
            out["m1_m2"] = out["m1_yoy"] - out["m2_yoy"]
        if {"inc_month", "stk_endval"} <= set(out.columns):
            last_year = [str(int(m) - 100) for m in out.index]
            stock_ly = out["stk_endval"].reindex(last_year).to_numpy()
            inc_ly = out["inc_month"].reindex(last_year).to_numpy()
            out["sf_stock_yoy"] = (out["stk_endval"] / stock_ly - 1) * 100
            out["sf_inc_vs_ly"] = out["inc_month"] - inc_ly
        return out

    @staticmethod
    def _build_series(
        s: MacroSeries, values: pd.Series, seen: dict[str, str]
    ) -> dict[str, Any] | None:
        if values.empty:
            return None
        window = values.iloc[-WINDOW:]
        month, value = str(values.index[-1]), float(values.iloc[-1])
        prev = float(values.iloc[-2]) if len(values) > 1 else None
        return {
            "key": s.key,
            "name": s.name,
            "group": s.group,
            "unit": s.unit,
            "month": month,
            "value": round(value, 2),
            "prev_month": str(values.index[-2]) if len(values) > 1 else "",
            "prev": None if prev is None else round(prev, 2),
            "change": None if prev is None else round(value - prev, 2),
            "pct_5y": round(float((window <= value).mean()), 3),
            "new_print": seen.get(s.key) != month,
            "history": [
                {"month": str(m), "value": round(float(v), 2)}
                for m, v in window.items()
                if not math.isnan(float(v))
            ],
        }
