"""Rates and RMB monitor behind the app's 利率汇率 page and the e-mail block (plan 34, D-171)."""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.calculation.rates_fx_series_reader import RatesFxSeriesReader
from quant_cn.core.exceptions import LakeError
from quant_cn.core.rates_fx_monitor_settings import RatesFxLine, RatesFxMonitorSettings
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

FILE_NAME = "rates_fx_monitor.json"
HORIZONS = {"1w": 5, "1m": 21, "3m": 63, "1y": 250}  # observations back
YEAR = 250
WEEK = 5  # history before the last year keeps every WEEK-th observation
_CURVE = "SELECT * FROM curated.cn_bond_yield WHERE curve_name = ? AND trade_date <= ?"


class RatesFxMonitorBuilder:
    """
    Purpose:
        The 利率与汇率 document as of the last date of any line (or a given as_of; nothing
        later is used). Per shown line: latest value and date, changes over 1w / 1m / 3m / 1y
        observations (bp for yield and bp units, fraction for rate, fraction points for gap),
        the percentile in the last pct_years (share at or below; None under min_obs), 1-year
        low / high, stale (date more than stale_days before as_of), alerts that fired and the
        history since history_start for the chart. Alerts: week_move (|1w change|),
        week_widen (1w rise), extreme (beyond the previous year's low or high), pct_above,
        abs_above (|value|), below / above (level). History is daily over the last year and every
        WEEK-th observation before it. `new_flags` are flag keys not in the
        previous document. `curve` holds the configured curve's points today, a month and a
        year earlier.

    Contract:
        Input:
            settings: RatesFxMonitorSettings
            reader:   RatesFxSeriesReader
            query:    LakeQuery  -- the curve snapshot
        Output:
            instance; `build(previous, as_of)` -> dict, `write(out_dir)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `rates-fx-monitor` command

    Test cases:
        TC-RFM-001  yield row: bp changes, percentile, 1-year low / high; rate row: % changes
        TC-RFM-002  alerts: week_move, week_widen, extreme (new low), pct_above, abs_above,
                    below; new_flags only once
        TC-RFM-003  PIT: as_of cuts every series; a line without data is listed in missing,
                    an old one in stale; hidden lines are not rows
        TC-RFM-004  curve snapshot today / 1m / 1y; write puts the file in the folder, a
                    missing folder raises LakeError; no data at all raises LakeError
    """

    def __init__(
        self, settings: RatesFxMonitorSettings, reader: RatesFxSeriesReader, query: LakeQuery
    ) -> None:
        self._s = settings
        self._reader = reader
        self._query = query

    def build(self, previous: dict[str, Any] | None, as_of: str | None = None) -> dict[str, Any]:
        """
        Purpose:
            The monitor document.

        Contract:
            Input:
                previous: dict | None  -- last written document (for new_flags)
                as_of:    str | None   -- YYYYMMDD; default the last date of any line
            Output:
                dict  -- {as_of, groups, rows: [{key, name, group, unit, date, value, chg:
                         {1w,1m,3m,1y}, pct, low_1y, high_1y, stale, alerts: [str], history:
                         [{date, value}]}], flags: [{key, kind, name, message}], new_flags,
                         missing, stale, curve: {tenors, points: [{label, date, values}]}}
            Raises:
                LakeError  -- no line has data
        """
        start = self._compute_day(self._s.history_start, -366 * self._s.pct_years)
        series = self._reader.read_series(min(start, self._s.history_start))
        if as_of is not None:
            series = {k: s[s.index <= as_of] for k, s in series.items()}
        dates = [s.index[-1] for s in series.values() if not s.empty]
        if not dates:
            raise LakeError("rates-fx monitor: no line has data")
        day = as_of or max(dates)
        rows, missing = [], []
        for line in self._s.lines:
            s = series.get(line.key, pd.Series(dtype=float))
            if not line.show:
                continue
            if s.empty:
                missing.append(line.key)
                continue
            rows.append(self._build_row(line, s, day))
        flags = [
            {"key": f"{r['key']}:{kind}", "kind": kind, "name": r["name"], "message": msg}
            for r in rows
            for kind, msg in r.pop("_flags")
        ]
        seen = {f["key"] for f in (previous or {}).get("flags", [])}
        return {
            "as_of": day,
            "groups": list(dict.fromkeys(line.group for line in self._s.lines)),
            "rows": rows,
            "flags": flags,
            "new_flags": [f["key"] for f in flags if f["key"] not in seen],
            "missing": missing,
            "stale": [r["key"] for r in rows if r["stale"]],
            "curve": self._build_curve(day),
        }

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build against the previous `rates_fx_monitor.json` in out_dir and overwrite it.

        Contract:
            Input:
                out_dir: Path  -- existing directory (the chain app's data dir)
            Output:
                Path  -- the written file, UTF-8 JSON
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"rates-fx monitor output directory missing: {out_dir}")
        path = out_dir / FILE_NAME
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        doc = self.build(previous)
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        logger.info("rates-fx monitor: %d rows, %d flags (%d new) -> %s", len(doc["rows"]),
                    len(doc["flags"]), len(doc["new_flags"]), path)  # fmt: skip
        return path

    def _build_row(self, line: RatesFxLine, s: pd.Series, day: str) -> dict[str, Any]:
        value = float(s.iloc[-1])
        window = s[s.index > self._compute_day(day, -366 * self._s.pct_years)]
        year = s.iloc[-YEAR - 1 : -1]
        row: dict[str, Any] = {
            "key": line.key,
            "name": line.name,
            "group": line.group,
            "unit": line.unit,
            "date": str(s.index[-1]),
            "value": round(value, 4),
            "chg": {h: self._compute_change(line, s, n) for h, n in HORIZONS.items()},
            "pct": round(float((window <= value).mean()), 3)
            if len(window) >= self._s.min_obs
            else None,
            "low_1y": round(float(year.min()), 4) if len(year) else None,
            "high_1y": round(float(year.max()), 4) if len(year) else None,
            "stale": str(s.index[-1]) < self._compute_day(day, -self._s.stale_days),
        }
        row["_flags"] = self._list_flags(line, row)
        row["alerts"] = [msg for _, msg in row["_flags"]]
        hist = s[s.index >= self._s.history_start]
        recent = hist.index >= self._compute_day(day, -366)
        older = hist[~recent].iloc[::-WEEK][::-1]  # weekly before the last year, ending at its end
        hist = pd.concat([older, hist[recent]])
        row["history"] = [{"date": str(d), "value": round(float(v), 4)} for d, v in hist.items()]
        return row

    @staticmethod
    def _compute_change(line: RatesFxLine, s: pd.Series, n: int) -> float | None:
        if len(s) <= n:
            return None
        now, then = float(s.iloc[-1]), float(s.iloc[-1 - n])
        if line.unit == "yield":
            return round((now - then) * 100, 1)
        if line.unit == "bp":
            return round(now - then, 1)
        if line.unit == "gap":
            return round(now - then, 4)
        return round(now / then - 1, 4) if then else None

    @staticmethod
    def _list_flags(line: RatesFxLine, row: dict[str, Any]) -> list[tuple[str, str]]:
        name, value, week = line.name, row["value"], row["chg"]["1w"]
        unit = "%" if line.unit == "rate" else "bp"
        shown = f"{value:.4g}"
        found: list[tuple[str, str]] = []
        if line.week_move is not None and week is not None and abs(week) >= line.week_move:
            move = f"{week * 100:+.2f}%" if line.unit == "rate" else f"{week:+.0f}{unit}"
            found.append(("week_move", f"{name} 一周 {move}（{shown}）"))
        if line.week_widen is not None and week is not None and week >= line.week_widen:
            found.append(("week_widen", f"{name} 一周走阔 {week:+.0f}bp（{shown}）"))
        low, high = row["low_1y"], row["high_1y"]
        if line.extreme and low is not None and value < low:
            found.append(("extreme", f"{name} 创 1 年新低 {shown}"))
        if line.extreme and high is not None and value > high:
            found.append(("extreme", f"{name} 创 1 年新高 {shown}"))
        if line.pct_above is not None and row["pct"] is not None and row["pct"] >= line.pct_above:
            found.append(("pct", f"{name} {shown}，处于 5 年 {row['pct'] * 100:.0f}% 分位"))
        if line.abs_above is not None and abs(value) >= line.abs_above:
            found.append(("abs", f"{name} {value * 100:+.2f}%"))
        if line.below is not None and value < line.below:
            found.append(("below", f"{name} {shown} 低于 {line.below:g}"))
        if line.above is not None and value > line.above:
            found.append(("above", f"{name} {shown} 高于 {line.above:g}"))
        return found

    def _build_curve(self, day: str) -> dict[str, Any]:
        name = self._s.curve.get("curve")
        fields = list(self._s.curve.get("fields", []))
        if not name or not fields:
            return {"tenors": [], "points": []}
        try:
            frame = self._query.sql(_CURVE, [name, day]).sort_values("trade_date")
        except LakeError:
            return {"tenors": [], "points": []}
        frame = frame.assign(trade_date=frame["trade_date"].astype(str))
        points = []
        for label, back in (("今天", 0), ("1 月前", 31), ("1 年前", 365)):
            past = frame[frame["trade_date"] <= self._compute_day(day, -back)]
            if past.empty:
                continue
            last = past.iloc[-1]
            values = [None if pd.isna(last[f]) else round(float(last[f]), 4) for f in fields]
            points.append({"label": label, "date": str(last["trade_date"]), "values": values})
        return {"tenors": [f.removeprefix("y_").upper() for f in fields], "points": points}

    @staticmethod
    def _compute_day(day: str, days: int) -> str:
        return (dt.datetime.strptime(day, "%Y%m%d") + dt.timedelta(days=days)).strftime("%Y%m%d")
