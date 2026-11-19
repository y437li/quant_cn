"""Volatility monitor behind the app's 波动率 page and the e-mail block (plan 03 ph6, D-152)."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Final

import pandas as pd

from quant_cn.calculation.expiry_clock import ExpiryClock
from quant_cn.calculation.forward_price_estimator import ForwardPriceEstimator
from quant_cn.calculation.option_chain_builder import OptionChainBuilder
from quant_cn.calculation.risk_free_curve import RiskFreeCurve
from quant_cn.calculation.term_interpolator import TermInterpolator
from quant_cn.calculation.term_selector import TermSelector
from quant_cn.calculation.variance_strip_calculator import VarianceStripCalculator
from quant_cn.calculation.vix_calculator import VixCalculator
from quant_cn.core.exceptions import LakeError
from quant_cn.core.volatility_monitor_settings import VolatilityLine, VolatilityMonitorSettings
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

FILE_NAME = "volatility_monitor.json"
STRIP_CUTOFF: Final = "price_or_volume"  # strike-strip stop rule used by the plan 03 notebook
_LAST = "SELECT max(trade_date) AS d FROM curated.opt_daily"
_SESSIONS = "SELECT cal_date FROM curated.trade_cal WHERE is_open = 1 ORDER BY cal_date"
_BASIC = "SELECT * FROM curated.opt_basic WHERE list_contains(?, opt_code)"
_DAILY = """
SELECT * FROM curated.opt_daily WHERE list_contains(?, ts_code) AND trade_date BETWEEN ? AND ?
"""
_SHIBOR = "SELECT * FROM curated.shibor ORDER BY date"
_CBOE = """
SELECT trade_date, close AS vix FROM curated.cboe_vix WHERE index_code = ? AND trade_date <= ?
ORDER BY trade_date DESC LIMIT ?
"""


class VolatilityMonitorBuilder:
    """
    Purpose:
        One document line per configured volatility index over the last `window` sessions:
        US VIX read from curated.cboe_vix, A-share VIX computed by VixCalculator (trading clock,
        D-052) from curated.opt_basic / opt_daily / shibor / trade_cal. Per line: latest value
        and date, one-day change (points and fraction), percentile in the window (share of
        window values at or below the latest; None under min_obs values), median / min / max,
        the latest day's quality_flag and the history for the chart. Flags: level, jump and
        percentile alerts from the settings; `new_flags` are flags not in the previous document.
        The VIX building blocks are made inside `build` because the rate curve and the trading
        clock are built from that day's lake data.

    Contract:
        Input:
            settings: VolatilityMonitorSettings
            query:    LakeQuery  -- reads the curated tables above
        Output:
            instance; `build(previous)` -> dict, `write(out_dir)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `volatility-monitor` command

    Test cases:
        TC-VMB-001  cboe line: latest, one-day change, percentile, history from curated.cboe_vix
        TC-VMB-002  option line: VIX from a synthetic flat-20% chain is 15–30 (trading clock)
        TC-VMB-003  level and jump alerts fire; new_flags only once; percentile alert needs
                    min_obs values
        TC-VMB-004  a line without data (or without the cboe_vix table) is listed in `missing`
        TC-VMB-005  write puts volatility_monitor.json in the directory; missing directory
                    raises LakeError
        TC-VMB-006  no opt_daily rows raises LakeError
    """

    def __init__(self, settings: VolatilityMonitorSettings, query: LakeQuery) -> None:
        self._s = settings
        self._query = query

    def build(self, previous: dict[str, Any] | None) -> dict[str, Any]:
        """
        Purpose:
            The monitor document as of the last session in curated.opt_daily.

        Contract:
            Input:
                previous: dict | None  -- the last written document (for new_flags)
            Output:
                dict  -- {as_of, window, lines: [{key, name, group, kind, code, date, value,
                         chg, chg_pct, pct, median, low, high, n_obs, quality_flag,
                         history: [{date, value}]}], flags: [{key, kind, name, message}],
                         new_flags: [key], missing: [line key]}; fractions, not percents
            Raises:
                LakeError  -- no opt_daily rows, or a query fails
        """
        last = self._query.sql(_LAST)["d"].iloc[0]
        if last is None or (isinstance(last, float) and math.isnan(last)):
            raise LakeError("curated.opt_daily is empty: run make market-data")
        as_of = str(last)
        sessions = self._query.sql(_SESSIONS)["cal_date"].astype(str).tolist()
        past = [d for d in sessions if d <= as_of][-self._s.window :]
        series = self._compute_option_series(as_of, past[0], sessions)
        lines, missing = [], []
        for line in self._s.lines:
            values = (
                series.get(line.code) if line.kind == "option" else self._read_cboe(line, as_of)
            )
            if values is None or values.dropna().empty:
                missing.append(line.key)
                continue
            lines.append(self._build_line(line, values))
        flags = [f for item in lines for f in self._list_flags(item)]
        seen = {f["key"] for f in (previous or {}).get("flags", [])}
        return {
            "as_of": as_of,
            "window": self._s.window,
            "lines": lines,
            "flags": flags,
            "new_flags": [f["key"] for f in flags if f["key"] not in seen],
            "missing": missing,
        }

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build against the previous `volatility_monitor.json` in out_dir and overwrite it.

        Contract:
            Input:
                out_dir: Path  -- existing directory (the chain app's data dir)
            Output:
                Path  -- the written file, UTF-8 JSON
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"volatility monitor output directory missing: {out_dir}")
        path = out_dir / FILE_NAME
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        doc = self.build(previous)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("volatility monitor: %d lines, %d flags (%d new) -> %s", len(doc["lines"]),
                    len(doc["flags"]), len(doc["new_flags"]), path)  # fmt: skip
        return path

    def _compute_option_series(
        self, as_of: str, start: str, sessions: list[str]
    ) -> dict[str, pd.DataFrame]:
        codes = [line.code for line in self._s.lines if line.kind == "option"]
        if not codes:
            return {}
        basic = self._query.sql(_BASIC, [codes])
        daily = self._query.sql(_DAILY, [basic["ts_code"].astype(str).tolist(), start, as_of])
        chains = OptionChainBuilder(exclude_adjusted=True)
        calc = VixCalculator(
            RiskFreeCurve(self._query.sql(_SHIBOR)),
            chains,
            TermSelector(self._s.min_days),
            ForwardPriceEstimator(),
            VarianceStripCalculator(STRIP_CUTOFF),
            TermInterpolator(),
            ExpiryClock("trading", [d for d in sessions if d > start]),
        )
        out = {}
        for code in codes:
            chain = chains.build_chain(basic, daily, code)
            if chain.empty:
                continue
            panel = calc.compute(chain, code)
            out[code] = panel[["trade_date", "vix", "quality_flag"]].astype({"trade_date": str})
        return out

    def _read_cboe(self, line: VolatilityLine, as_of: str) -> pd.DataFrame:
        try:
            rows = self._query.sql(_CBOE, [line.code, as_of, self._s.window])
        except LakeError as exc:  # cboe_vix not downloaded yet: the line goes to `missing`
            logger.warning("volatility monitor: %s unreadable: %s", line.key, exc)
            return pd.DataFrame(columns=["trade_date", "vix", "quality_flag"])
        return rows.astype({"trade_date": str}).sort_values("trade_date").assign(quality_flag="ok")

    def _build_line(self, line: VolatilityLine, values: pd.DataFrame) -> dict[str, Any]:
        rows = values.dropna(subset=["vix"]).sort_values("trade_date")
        v = rows["vix"].astype(float)
        value = float(v.iloc[-1])
        prev = float(v.iloc[-2]) if len(v) > 1 else None
        enough = len(v) >= self._s.min_obs
        return {
            "key": line.key,
            "name": line.name,
            "group": line.group,
            "kind": line.kind,
            "code": line.code,
            "date": str(rows["trade_date"].iloc[-1]),
            "value": round(value, 2),
            "chg": None if prev is None else round(value - prev, 2),
            "chg_pct": None if not prev else round(value / prev - 1, 4),
            "pct": round(float((v <= value).mean()), 3) if enough else None,
            "median": round(float(v.median()), 2),
            "low": round(float(v.min()), 2),
            "high": round(float(v.max()), 2),
            "n_obs": len(v),
            "quality_flag": str(values.sort_values("trade_date")["quality_flag"].iloc[-1]),
            "alerts": {"level": line.alert_level, "jump": line.alert_jump, "pct": line.alert_pct},
            "history": [
                {"date": str(d), "value": round(float(x), 2)}
                for d, x in zip(rows["trade_date"], v, strict=True)
            ],
        }

    @staticmethod
    def _list_flags(item: dict[str, Any]) -> list[dict[str, str]]:
        a, name, value = item["alerts"], item["name"], item["value"]
        found = []
        if a["level"] is not None and value >= a["level"]:
            found.append(("level", f"{name} {value:.1f} ≥ {a['level']:g}"))
        if a["jump"] is not None and item["chg_pct"] is not None and item["chg_pct"] >= a["jump"]:
            found.append(("jump", f"{name} 单日 {item['chg_pct'] * 100:+.0f}%（{value:.1f}）"))
        if a["pct"] is not None and item["pct"] is not None and item["pct"] >= a["pct"]:
            found.append(("pct", f"{name} {value:.1f}，处于 1 年 {item['pct'] * 100:.0f}% 分位"))
        return [
            {"key": f"{item['key']}:{kind}", "kind": kind, "name": name,
             "message": msg}
            for kind, msg in found
        ]  # fmt: skip
