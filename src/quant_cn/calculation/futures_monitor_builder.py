"""Futures monitor behind the app's 期货 page and the e-mail block (plan 15 ph7i, D-145)."""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.calculation.futures_broker_nets import FuturesBrokerNets
from quant_cn.calculation.futures_curve import SUFFIX_EXCHANGE, FuturesCurve
from quant_cn.calculation.index_futures_monitor import IndexFuturesMonitor
from quant_cn.calculation.spread_reversion import SpreadReversion
from quant_cn.core.exceptions import LakeError
from quant_cn.core.futures_monitor_settings import FuturesFamily, FuturesMonitorSettings
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

FILE_NAME = "futures_monitor.json"
YEAR, FIVE_YEARS, WEEK, QUARTER = 250, 1250, 5, 63  # sessions
FOURTH = 3  # rank of the 4th listed month (0 = front)
MIN_Z_OBS = 20  # 5-day OI changes needed for a z-score
_LOOKBACK_DAYS = 5 * 366 + 120  # calendar days loaded before the last session
_LAST = "SELECT max(trade_date) AS d FROM curated.fut_daily"
_CONTRACTS = "SELECT ts_code, fut_code, exchange, d_month FROM curated.fut_basic"
_QUOTES = """
SELECT ts_code, trade_date, settle, close, oi, vol FROM curated.fut_daily
WHERE list_contains(?, ts_code) AND trade_date >= ? ORDER BY trade_date
"""


class FuturesMonitorBuilder:
    """
    Purpose:
        Per watched family: the dominant (most-held) contract price with 1- and 5-year
        percentile, 1-week / 3-month change on the same contract and 1-year change on the
        dominant series (rolls included); the curve shape (front vs
        the 4th listed month, front vs ~12 months later, each with its 5-year percentile; front
        = nearest unexpired month with open interest ≥ min_oi); total open interest with its
        5-day change and z vs one year; today's curve. Per spread: the value from the legs'
        dominant prices with 5-year percentile and one-year z. Flags: curve or spread percentile
        at or beyond the bounds, |OI z| ≥ bound, reversion spreads (SpreadReversion); `new_flags`
        are flags not in the previous document.

    Contract:
        Input:
            settings: FuturesMonitorSettings
            query:    LakeQuery  -- reads curated.fut_basic and curated.fut_daily
            index:    IndexFuturesMonitor | None  -- 股指期货 part (ph7k); None = built here
            nets:     FuturesBrokerNets | None    -- top-20 broker nets (ph7l); None = built here
        Output:
            instance; `build(previous)` -> dict, `write(out_dir)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `futures-monitor` command

    Test cases:
        TC-FUM-001  dominant price, changes on the same contract, front vs 4th, OI change
        TC-FUM-002  a delivery-month contract below min_oi is not the front month
        TC-FUM-003  spread from hand leg prices (sum and ratio with coefficients)
        TC-FUM-004  flag fires at the 95th percentile boundary; new_flags only once
        TC-FUM-005  a family with no contracts is listed in `missing`, not zero-filled
        TC-FUM-006  write puts futures_monitor.json in the directory; missing directory raises
        TC-FUM-007  one tick inside the bound (90th pct) fires no flag
        TC-FUM-008  a reversion spread far from its one-year mean is flagged; unmarked is not
    """

    def __init__(
        self,
        settings: FuturesMonitorSettings,
        query: LakeQuery,
        index: IndexFuturesMonitor | None = None,
        nets: FuturesBrokerNets | None = None,
    ) -> None:
        self._s = settings
        self._query = query
        self._index = index if index is not None else IndexFuturesMonitor(settings, query)
        self._nets = nets if nets is not None else FuturesBrokerNets(settings, query)
        self._reversion = SpreadReversion(settings)

    def build(self, previous: dict[str, Any] | None) -> dict[str, Any]:
        """
        Purpose:
            The monitor document as of the last session in curated.fut_daily.

        Contract:
            Input:
                previous: dict | None  -- the last written document (for new_flags)
            Output:
                dict  -- {as_of, families: [...], spreads: [...], index_futures: [...] (see
                         IndexFuturesMonitor.build), flags: [{key, kind, name, message}],
                         new_flags: [key], missing: [family or product]}; ratios as fractions
            Raises:
                LakeError  -- no fut_daily rows, or a query fails
        """
        last = self._query.sql(_LAST)["d"].iloc[0]
        if last is None or (isinstance(last, float) and math.isnan(last)):
            raise LakeError("curated.fut_daily is empty: run make track-daily")
        as_of = str(last)
        contracts = self._query.sql(_CONTRACTS).astype(str)
        curve = FuturesCurve(contracts, {})
        quotes = self._read_quotes(contracts, as_of)
        families, prices, missing = [], {}, []
        for fam in self._s.families:
            mine = quotes[quotes["family"] == fam.family]
            if mine.empty:
                missing.append(fam.family)
                continue
            panel = self._build_panel(mine)
            prices[fam.family] = panel["dom_price"]
            families.append(self._build_family(fam, mine, panel, curve))
        built = [self._build_spread(i, prices) for i in range(len(self._s.spreads))]
        spreads = [s for s in built if s is not None]
        start = (dt.datetime.strptime(as_of, "%Y%m%d") - dt.timedelta(_LOOKBACK_DAYS)).strftime(
            "%Y%m%d"
        )
        index = self._index.build(start)
        nets = self._nets.build(start)
        families = [{**f, "broker": nets.get(f["family"])} for f in families]
        flags = index["flags"] + self._list_flags(families, spreads)
        seen = {f["key"] for f in (previous or {}).get("flags", [])}
        return {
            "as_of": as_of,
            "families": families,
            "spreads": spreads,
            "index_futures": index["products"],
            "flags": flags,
            "new_flags": [f["key"] for f in flags if f["key"] not in seen],
            "missing": missing + index["missing"],
        }

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build against the previous `futures_monitor.json` in out_dir and overwrite it.

        Contract:
            Input:
                out_dir: Path  -- existing directory (the chain app's data dir)
            Output:
                Path  -- the written file, UTF-8 JSON
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"futures monitor output directory missing: {out_dir}")
        path = out_dir / FILE_NAME
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        doc = self.build(previous)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("futures monitor: %d flags (%d new) -> %s", len(doc["flags"]),
                    len(doc["new_flags"]), path)  # fmt: skip
        return path

    def _read_quotes(self, contracts: pd.DataFrame, as_of: str) -> pd.DataFrame:
        listed = contracts[contracts["d_month"].str.fullmatch(r"\d{6}")]
        rows = []
        for fam in self._s.families:
            code, _, suffix = fam.family.partition(".")
            own = listed[(listed["fut_code"] == code)
                         & (listed["exchange"] == SUFFIX_EXCHANGE[suffix])]  # fmt: skip
            rows.append(own.assign(family=fam.family)[["ts_code", "d_month", "family"]])
        empty = pd.DataFrame(columns=["ts_code", "d_month", "family"])
        members = pd.concat(rows) if rows else empty
        start = (dt.datetime.strptime(as_of, "%Y%m%d") - dt.timedelta(_LOOKBACK_DAYS)).strftime(
            "%Y%m%d"
        )
        quotes = self._query.sql(_QUOTES, [members["ts_code"].tolist(), start])
        quotes = quotes.assign(trade_date=quotes["trade_date"].astype(str)).merge(
            members, on="ts_code"
        )
        quotes = quotes.assign(price=quotes["settle"].fillna(quotes["close"]))
        alive = quotes["d_month"] >= quotes["trade_date"].str[:6]
        return quotes[alive & quotes["price"].notna()].reset_index(drop=True)

    def _build_panel(self, q: pd.DataFrame) -> pd.DataFrame:
        by_day = q.groupby("trade_date")
        dom = q.loc[by_day["oi"].idxmax(), ["trade_date", "ts_code", "price"]].set_index(
            "trade_date"
        )
        liquid = q[q["oi"] >= self._s.min_oi].sort_values(["trade_date", "d_month"])
        rank = liquid.groupby("trade_date").cumcount()
        front = liquid[rank == 0].set_index("trade_date")
        fourth = liquid[rank == FOURTH].set_index("trade_date")["price"]
        later = liquid.merge(front[["d_month"]].rename(columns={"d_month": "f_month"}),
                             left_on="trade_date", right_index=True)  # fmt: skip
        months = [(int(a[:4]) - int(b[:4])) * 12 + int(a[4:6]) - int(b[4:6])
                  for a, b in zip(later["d_month"], later["f_month"], strict=True)]  # fmt: skip
        later = later.assign(gap=[abs(m - 12) for m in months])
        later = later[later["gap"] <= 1].sort_values(["trade_date", "gap"])
        m12 = later.groupby("trade_date")["price"].first()
        return pd.DataFrame(
            {
                "dom_code": dom["ts_code"],
                "dom_price": dom["price"],
                "f4": front["price"] / fourth - 1,
                "f12": front["price"] / m12 - 1,
                "oi": by_day["oi"].sum(),
            }
        ).sort_index()

    def _build_family(
        self, fam: FuturesFamily, q: pd.DataFrame, panel: pd.DataFrame, curve: FuturesCurve
    ) -> dict[str, Any]:
        last = str(panel.index[-1])
        code = str(panel["dom_code"].iloc[-1])
        own = q[q["ts_code"] == code].set_index("trade_date")["price"]
        dates = panel.index.tolist()
        today = curve.build_curve(q.drop(columns=["d_month", "family", "price"]), fam.family, last)
        today = today[today["oi"] >= self._s.min_oi]
        shape = curve.compute_summary(today, fam.family, last).shape
        oi_chg = panel["oi"].pct_change(WEEK, fill_method=None)
        return {
            "family": fam.family,
            "name": fam.name,
            "group": fam.group,
            "as_of": last,
            "contract": code,
            "price": self._compute_rounded(panel["dom_price"].iloc[-1], 2),
            "pct_1y": self._compute_pct(panel["dom_price"], YEAR),
            "pct_5y": self._compute_pct(panel["dom_price"], FIVE_YEARS),
            "chg_1w": self._compute_change(own, dates, WEEK),
            "chg_3m": self._compute_change(own, dates, QUARTER),
            "chg_1y": self._compute_change(panel["dom_price"], dates, YEAR),
            "front_vs_4th": self._compute_rounded(panel["f4"].iloc[-1], 4),
            "front_vs_4th_pct": self._compute_pct(panel["f4"], FIVE_YEARS),
            "front_vs_12m": self._compute_rounded(panel["f12"].iloc[-1], 4),
            "front_vs_12m_pct": self._compute_pct(panel["f12"], FIVE_YEARS),
            "shape": shape,
            "oi": self._compute_rounded(panel["oi"].iloc[-1], 0),
            "oi_chg_5d": self._compute_rounded(oi_chg.iloc[-1], 4),
            "oi_z": self._compute_z(oi_chg),
            "curve": [
                {"month": str(m), "price": round(float(p), 2), "oi": round(float(o), 0)}
                for m, p, o in zip(today["d_month"], today["price"], today["oi"], strict=True)
            ],
            "price_history": self._to_points(panel["dom_price"].iloc[-YEAR:], 1),
            "curve_history": self._to_points(panel["f4"].iloc[-FIVE_YEARS:], WEEK),
        }

    def _build_spread(self, i: int, prices: dict[str, pd.Series]) -> dict[str, Any] | None:
        s = self._s.spreads[i]
        if any(leg.family not in prices for leg in s.legs):
            return None
        legs = pd.concat([prices[leg.family] for leg in s.legs], axis=1).dropna()
        if s.kind == "ratio":
            value = (legs.iloc[:, 0] * s.legs[0].coef) / (legs.iloc[:, 1] * s.legs[1].coef)
        else:
            value = sum((legs.iloc[:, j] * leg.coef for j, leg in enumerate(s.legs)),
                        pd.Series(0.0, index=legs.index))  # fmt: skip
        if value.empty:
            return None
        dates = value.index.tolist()
        prev = value.iloc[-1 - WEEK] if len(value) > WEEK else None
        return {
            "key": s.key,
            "name": s.name,
            "unit": s.unit,
            "kind": s.kind,
            "as_of": str(dates[-1]),
            "value": self._compute_rounded(value.iloc[-1], 2),
            "chg_1w": None if prev is None else self._compute_rounded(value.iloc[-1] - prev, 2),
            "pct_5y": self._compute_pct(value, FIVE_YEARS),
            "z_1y": self._reversion.compute_z(value),
            "reversion": s.reversion,
            "half_life_d": s.half_life_d,
            "history": self._to_points(value.iloc[-FIVE_YEARS:], WEEK),
        }

    def _list_flags(
        self, families: list[dict[str, Any]], spreads: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        lo, hi = self._s.flag_low, self._s.flag_high
        for f in families:
            pct, v = f["front_vs_4th_pct"], f["front_vs_4th"]
            if pct is not None and v is not None and (pct <= lo or pct >= hi):
                side = "近月升水" if v > 0 else "近月贴水"
                text = f"{side} {v * 100:+.1f}%（近月比第4个月），5年 {pct * 100:.0f}% 分位"
                out.append(self._build_flag(f"curve:{f['family']}", "curve", f["name"], text))
            z = f["oi_z"]
            if z is not None and abs(z) >= self._s.oi_z:
                chg = f["oi_chg_5d"] or 0.0
                out.append(self._build_flag(f"oi:{f['family']}", "oi", f["name"],
                           f"持仓 5 日 {chg * 100:+.1f}%（z={z:+.1f}）"))  # fmt: skip
        for f in families:
            out += self._nets.list_flags(f["family"], f["name"], f.get("broker"))
        for s in spreads:
            pct = s["pct_5y"]
            if pct is not None and (pct <= lo or pct >= hi):
                text = f"{s['value']:,.2f} {s['unit']}，5年 {pct * 100:.0f}% 分位"
                out.append(self._build_flag(f"spread:{s['key']}", "spread", s["name"], text))
        return out + self._reversion.list_flags(spreads)

    @staticmethod
    def _build_flag(key: str, kind: str, name: str, message: str) -> dict[str, Any]:
        return {"key": key, "kind": kind, "name": name, "message": message}

    @staticmethod
    def _compute_rounded(v: Any, digits: int) -> float | None:
        if v is None or pd.isna(v):
            return None
        return round(float(v), digits)

    @staticmethod
    def _compute_pct(series: pd.Series, window: int) -> float | None:
        values = series.dropna().iloc[-window:]
        if values.empty or pd.isna(series.iloc[-1]):
            return None
        return round(float((values <= values.iloc[-1]).mean()), 3)

    @staticmethod
    def _compute_change(own: pd.Series, dates: list[str], back: int) -> float | None:
        if len(dates) <= back or dates[-1] not in own.index or dates[-1 - back] not in own.index:
            return None
        return round(float(own[dates[-1]] / own[dates[-1 - back]] - 1), 4)

    @staticmethod
    def _compute_z(chg: pd.Series) -> float | None:
        window = chg.dropna().iloc[-YEAR:]
        if len(window) < MIN_Z_OBS or pd.isna(chg.iloc[-1]) or not window.std() > 0:
            return None
        return round(float((chg.iloc[-1] - window.mean()) / window.std()), 2)

    @staticmethod
    def _to_points(series: pd.Series, step: int) -> list[dict[str, Any]]:
        values = series.dropna()
        picked = values.iloc[::-1].iloc[::step].iloc[::-1]
        return [{"d": str(d), "v": round(float(v), 4)} for d, v in picked.items()]
