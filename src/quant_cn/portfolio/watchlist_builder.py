"""The watchlist document behind the app's 观察账本 page (plan 15 phase 7, D-120)."""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
import numbers
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.core.watchlist_entry import WatchlistEntry, WatchlistSettings
from quant_cn.lake.chip_structure_reader import GAUGE_KEYS
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.condition_evaluator import ConditionEvaluator

logger = logging.getLogger(__name__)

FILE_NAME = "watchlist.json"
_LATEST = """
SELECT ts_code, max(trade_date) AS price_date, arg_max(close, trade_date) AS price,
       min(close) FILTER (WHERE trade_date > ?) AS low_52w,
       max(close) FILTER (WHERE trade_date > ?) AS high_52w
FROM {prices} WHERE list_contains(?, ts_code) AND trade_date <= ? GROUP BY ts_code
"""
_BASIC = """
SELECT b.ts_code, b.pe_ttm, b.pb, b.dv_ttm FROM curated.daily_basic b
JOIN (SELECT ts_code, max(trade_date) AS d FROM curated.daily
      WHERE list_contains(?, ts_code) AND trade_date <= ? GROUP BY ts_code) l
  ON b.ts_code = l.ts_code AND b.trade_date = l.d
"""
_WEEKLY = """
SELECT ts_code, max(trade_date) AS date, arg_max(close, trade_date) AS close FROM {prices}
WHERE list_contains(?, ts_code) AND trade_date > ? AND trade_date <= ?
GROUP BY ts_code, strftime(strptime(trade_date, '%Y%m%d'), '%G-%V') ORDER BY ts_code, date
"""
_CONSENSUS = """
SELECT ts_code,
       median(eps) FILTER (WHERE quarter = ?) AS eps_fy,
       count(DISTINCT org_name) FILTER (WHERE quarter = ? AND eps IS NOT NULL) AS eps_brokers,
       min(min_price) AS target_low, max(max_price) AS target_high
FROM curated.report_rc
WHERE list_contains(?, ts_code) AND report_date > ? AND report_date <= ? GROUP BY ts_code
"""
_NAMES = "SELECT ts_code, name, '{kind}' AS kind FROM {table} WHERE list_contains(?, ts_code)"
_STOCK_PRICES = "curated.daily"
_ETF_PRICES = (
    "(SELECT ts_code, trade_date, close FROM curated.daily UNION ALL "
    "SELECT ts_code, trade_date, close FROM curated.fund_daily)"
)
_FUND_VIEWS = ("curated.fund_daily", "curated.fund_basic")


class WatchlistBuilder:
    """
    Purpose:
        Join the user's buy targets (Config.watchlist) with the latest lake prices, valuation
        and broker consensus, and compute how far each stock is from its buy price.

    Contract:
        Input:
            config: Config      -- `watchlist` entries and `watchlist_settings`
            query:  LakeQuery   -- reads curated.daily, daily_basic, report_rc, stock_basic;
                                   fund_daily / fund_basic for ETF entries when present (ph7p)
            codec:  DateCodec
            evaluator: ConditionEvaluator | None  -- evaluates entry conditions (plan 15 ph7f);
                                                     None leaves them unevaluated
        Output:
            instance; `build` -> dict, `write` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.AppServiceBuilder  -- wires it

    Test cases:
        TC-WB-001  gap_to_buy = buy_high / price - 1, and 0 once price <= buy_high
        TC-WB-002  status: in at price <= buy_high; near up to near_pct above; far beyond
        TC-WB-003  pe_at_buy and yield_at_buy from consensus EPS and TTM dividend; None without EPS
        TC-WB-004  consensus uses only forecasts for the as-of year inside consensus_days
        TC-WB-005  52-week range, weekly closes one per ISO week, latest close as price
        TC-WB-006  a code without prices goes to `missing`, the rest are still built
        TC-WB-007  no watchlist entries -> empty document without reading prices
        TC-WB-008  write puts watchlist.json in the directory and returns its path
        TC-WB-009  empty curated.daily raises LakeError
        TC-WB-010  entry conditions evaluated with k of n; condition_status buy / near / wait;
                   `retail` carries the RetailGauge reading (None when unknown)
        TC-WB-011  an ETF code is priced from fund_daily, named from fund_basic, kind "etf",
                   valuation fields None; stock rows keep kind "stock"; no fund views -> stocks only
    """

    def __init__(
        self,
        config: Config,
        query: LakeQuery,
        codec: DateCodec,
        evaluator: ConditionEvaluator | None = None,
    ) -> None:
        self._entries = config.watchlist
        self._settings: WatchlistSettings = config.watchlist_settings
        self._query = query
        self._codec = codec
        self._evaluator = evaluator

    def build(self) -> dict[str, Any]:
        """
        Purpose:
            The watchlist document as of the latest trading day in curated.daily.

        Contract:
            Input:
                (none)
            Output:
                dict  -- {as_of: YYYYMMDD | "", near_pct, entries: [...], missing: [ts_code]};
                         entries keep config order and carry `kind` (stock | etf),
                         `conditions` (results),
                         `conditions_needed` and `condition_status` (buy / near / wait);
                         fractions (div_yield, gap_to_buy, yield_at_buy, shareholder_yield)
                         are shares in [0, 1]; buyback_plan_pct (largest live buyback plan,
                         % of market cap, plan 23) in percent; `retail` = the latest
                         RetailGauge reading (GAUGE_KEYS: pct, expected change, avoid /
                         avoid_strong / leaving flags 1.0 / 0.0, streaks; plan 21 ph5);
                         unknown numbers are None
            Raises:
                LakeError  -- curated.daily empty or a query fails
        """
        near = self._settings.near_pct
        if not self._entries:
            return {"as_of": "", "near_pct": near, "entries": [], "missing": []}
        as_of = self._find_as_of()
        frames = self._load_frames(as_of)
        frames["metrics"] = self._read_metrics(frames["latest"], as_of)
        latest = frames["latest"].set_index("ts_code")
        entries, missing = [], []
        for entry in self._entries:
            if entry.code not in latest.index:
                missing.append(entry.code)
                continue
            entries.append(self._build_entry(entry, frames, as_of))
        if missing:
            logger.warning("watchlist: no prices for %s", missing)
        return {"as_of": as_of, "near_pct": near, "entries": entries, "missing": missing}

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build the document and write it as `watchlist.json` for the app's data directory.

        Contract:
            Input:
                out_dir: Path  -- existing directory (the chain app's data dir)
            Output:
                Path  -- the written file, UTF-8 JSON
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"watchlist output directory missing: {out_dir}")
        path = out_dir / FILE_NAME
        doc = self.build()
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("watchlist: %d entries as of %s -> %s", len(doc["entries"]), doc["as_of"], path)
        return path

    @staticmethod
    def compute_status(price: float, buy_high: float, near_pct: float) -> str:
        """
        Purpose:
            Classify a price against the top of its buy range.

        Contract:
            Input:
                price, buy_high: float  -- > 0
                near_pct:        float  -- share above buy_high still counted as near
            Output:
                str  -- "in" | "near" | "far"
            Raises:
                (none)
        """
        if price <= buy_high:
            return "in"
        above = price / buy_high - 1
        return "near" if above <= near_pct or math.isclose(above, near_pct) else "far"

    def _find_as_of(self) -> str:
        found = self._query.sql("SELECT max(trade_date) AS d FROM curated.daily")
        value = found["d"].iloc[0] if not found.empty else None
        if value is None or pd.isna(value):
            raise LakeError("curated.daily is empty: run make download")
        return str(value)

    def _compute_start(self, as_of: str, days: int) -> str:
        return self._codec.to_str(self._codec.to_date(as_of) - dt.timedelta(days=days))

    def _load_frames(self, as_of: str) -> dict[str, pd.DataFrame]:
        codes = [e.code for e in self._entries]
        start = self._compute_start(as_of, self._settings.history_days)
        since = self._compute_start(as_of, self._settings.consensus_days)
        quarter = f"{as_of[:4]}Q4"
        q = self._query
        funds = all(q.has_view(v) for v in _FUND_VIEWS)
        prices = _ETF_PRICES if funds else _STOCK_PRICES
        names = [q.sql(_NAMES.format(kind="stock", table="curated.stock_basic"), [codes])]
        if funds:
            names.append(q.sql(_NAMES.format(kind="etf", table="curated.fund_basic"), [codes]))
        return {
            "latest": q.sql(_LATEST.format(prices=prices), [start, start, codes, as_of]),
            "basic": q.sql(_BASIC, [codes, as_of]),
            "weekly": q.sql(_WEEKLY.format(prices=prices), [codes, start, as_of]),
            "consensus": q.sql(_CONSENSUS, [quarter, quarter, codes, since, as_of]),
            "names": pd.concat(names, ignore_index=True),
        }

    def _build_entry(
        self, entry: WatchlistEntry, frames: dict[str, pd.DataFrame], as_of: str
    ) -> dict[str, Any]:
        latest = self._find_row(frames["latest"], entry.code)
        basic = self._find_row(frames["basic"], entry.code)
        cons = self._find_row(frames["consensus"], entry.code)
        found = self._find_row(frames["names"], entry.code)
        name = found.get("name")
        price = float(latest["price"])
        dv = self._to_number(basic.get("dv_ttm"))
        dps = price * dv / 100 if dv is not None else None
        eps = self._to_number(cons.get("eps_fy"))
        weekly = frames["weekly"][frames["weekly"]["ts_code"] == entry.code]
        metrics = frames["metrics"]
        row = metrics.loc[entry.code].to_dict() if entry.code in metrics.index else {}
        results = self._evaluator.compute_results(entry.conditions, row) if self._evaluator else []
        price_met = price <= entry.buy_high
        return {
            **entry.model_dump(),
            "name": str(name) if name is not None else entry.code,
            "kind": str(found.get("kind") or "stock"),
            "price": price,
            "price_date": str(latest["price_date"]),
            "pe_ttm": self._to_number(basic.get("pe_ttm")),
            "pb": self._to_number(basic.get("pb")),
            "div_yield": dv / 100 if dv is not None else None,
            "dps_ttm": self._to_rounded(dps),
            "eps_year": as_of[:4],
            "eps_fy": eps,
            "eps_brokers": int(self._to_number(cons.get("eps_brokers")) or 0),
            "target_low": self._to_number(cons.get("target_low")),
            "target_high": self._to_number(cons.get("target_high")),
            "low_52w": self._to_number(latest.get("low_52w")),
            "high_52w": self._to_number(latest.get("high_52w")),
            "gap_to_buy": self._to_rounded(min(0.0, entry.buy_high / price - 1)),
            "pe_at_buy": self._to_rounded(entry.buy_high / eps) if eps and eps > 0 else None,
            "yield_at_buy": self._to_rounded(dps / entry.buy_high) if dps is not None else None,
            "shareholder_yield": self._to_number(row.get("shareholder_yield")),
            "buyback_plan_pct": self._to_number(row.get("buyback_plan_pct")),
            "retail": {k: self._to_number(row.get(k)) for k in GAUGE_KEYS},
            "status": self.compute_status(price, entry.buy_high, self._settings.near_pct),
            "conditions": [r.to_record() for r in results],
            "condition_status": ConditionEvaluator.compute_status(
                results, price_met, entry.conditions_needed
            ),
            "weekly": [
                {"date": str(d), "close": float(c)}
                for d, c in zip(weekly["date"], weekly["close"], strict=True)
            ],
        }

    def _read_metrics(self, latest: pd.DataFrame, as_of: str) -> pd.DataFrame:
        if self._evaluator is None:
            return pd.DataFrame()
        closes = dict(zip(latest["ts_code"], latest["price"].astype(float), strict=True))
        series = [c.metric for e in self._entries for c in e.conditions if c.kind == "series"]
        return self._evaluator.read_metrics(closes, as_of, series)

    @staticmethod
    def _find_row(frame: pd.DataFrame, code: str) -> dict[str, Any]:
        rows = frame[frame["ts_code"] == code]
        return {} if rows.empty else dict(rows.iloc[0])

    @staticmethod
    def _to_number(value: object) -> float | None:
        if not isinstance(value, numbers.Real):
            return None
        number = float(value)
        return None if math.isnan(number) else number

    @staticmethod
    def _to_rounded(value: float | None) -> float | None:
        return None if value is None else round(value, 4)
