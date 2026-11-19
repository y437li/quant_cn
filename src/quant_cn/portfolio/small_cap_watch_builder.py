"""Small-cap bottom watch (小盘观察): e-mail section and #volatility panel (plan 30)."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.calculation.realized_vol_calculator import RealizedVolCalculator
from quant_cn.core.exceptions import LakeError
from quant_cn.core.small_cap_watch_settings import SmallCapWatchSettings
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.etf_flow_calculator import EtfFlowCalculator
from quant_cn.portfolio.small_cap_watch_rows import SmallCapWatchRows

logger = logging.getLogger(__name__)

FILE_NAME = "smallcap_watch.json"
_FULL_DAY = 0.9  # a margin_detail day with fewer stocks than this x the 20-day median is partial
_SESSIONS = "SELECT cal_date FROM curated.trade_cal WHERE is_open = 1 ORDER BY cal_date"
_LAST = "SELECT max(trade_date) AS d FROM curated.daily"
_INDEX = """
SELECT ts_code, trade_date, close, amount FROM curated.index_daily
WHERE list_contains(?, ts_code) AND trade_date <= ? ORDER BY trade_date
"""
_LIMIT = """
SELECT d.trade_date, count(*) FILTER (WHERE l.down_limit > 0 AND d.close <= l.down_limit) AS n
FROM curated.daily d JOIN curated.stk_limit l USING (ts_code, trade_date)
WHERE d.trade_date BETWEEN ? AND ? GROUP BY 1 ORDER BY 1
"""
_FRAME = (
    "OVER (PARTITION BY ts_code ORDER BY trade_date ROWS BETWEEN {n} PRECEDING AND CURRENT ROW)"
)
_BREADTH = """
WITH p AS (
  SELECT ts_code, trade_date, close_adj AS c FROM derived.prices_adj
  WHERE trade_date BETWEEN ? AND ?),
w AS (
  SELECT trade_date, c, min(c) {lo} AS lo, count(*) {lo} AS n_lo, avg(c) {ma} AS ma,
         count(*) {ma} AS n_ma
  FROM p)
SELECT trade_date,
  avg(CASE WHEN n_lo = {n_lo} THEN CAST(c <= lo AS INTEGER) END) AS low_share,
  avg(CASE WHEN n_ma = {n_ma} THEN CAST(c > ma AS INTEGER) END) AS above_ma
FROM w WHERE trade_date >= ? GROUP BY 1 ORDER BY 1
"""
_MARGIN = """
SELECT trade_date, sum(rzye) / 1e8 AS rz, count(DISTINCT exchange_id) AS n FROM curated.margin
WHERE trade_date BETWEEN ? AND ? GROUP BY 1 ORDER BY 1
"""
_DETAIL = """
SELECT trade_date, sum(rzye) / 1e8 AS rz, count(*) AS n FROM curated.margin_detail
WHERE trade_date BETWEEN ? AND ? GROUP BY 1 ORDER BY 1
"""
_CIRC = """
SELECT trade_date, sum(circ_mv) / 1e4 AS circ FROM curated.daily_basic
WHERE trade_date BETWEEN ? AND ? GROUP BY 1
"""
_SMALL = """
SELECT trade_date, close FROM curated.index_daily WHERE ts_code = ? AND trade_date BETWEEN ? AND ?
"""
_FUND_PX = """
SELECT ts_code, trade_date, close, pre_close FROM curated.fund_daily
WHERE list_contains(?, ts_code) AND trade_date BETWEEN ? AND ?
"""
_FUND_SH = """
SELECT ts_code, trade_date, fd_share FROM curated.fund_share
WHERE list_contains(?, ts_code) AND trade_date BETWEEN ? AND ?
"""


class SmallCapWatchBuilder:
    """
    Purpose:
        The daily 小盘观察 document: the signals the user waits on before buying 中证1000 /
        科创50 (plan 30). Rows: limit-down count (close at or below stk_limit.down_limit),
        share of stocks at a `low_window` low and above their `ma_window` average (adjusted
        closes), 中证1000 close against each user level and its drawdown from the year high,
        realised vol (annualised %, `vol_window`) of 中证1000 and 科创50 with its percentile,
        the 1000-300 realised-vol gap with its percentile and exit line, the 中证1000 day
        return and turnover / its prior `turnover_window` mean (ph5 放量大跌 and 建仓档),
        and broad-ETF net flow
        (1 day and `flow_days`, total and the `own_row` ETFs, via EtfFlowCalculator), and the
        market financing balance (curated.margin summed over exchanges; a day with fewer
        exchanges than the most in the window is dropped, ph4) with its drawdown from the
        `margin_high_days` high, `margin_turn_days` and `margin_ma_days` change and its
        `margin_ma_days` mean, and the balance as a share of float market cap (daily_basic)
        with its trailing percentile, ranked on the per-stock margin_detail sum because
        curated.margin starts in 2025 (days under 90% of the median stock count dropped). Rows and
        their on / near / off / info states come from SmallCapWatchRows; `triggered` lists the
        on rows and `new_triggered` those not on in the previous document. Percentile = share
        of the last `pct_window` values at or below the latest (None under `pct_min_obs`).
        ph7: the balance's pace (rz_speed = `margin_speed_span` EMA of the daily change in 亿,
        rz_acc = its `margin_acc_days` change per day) and its depth from the high since
        `margin_long_start` on the full margin_detail days (rz_dd_long); the document carries
        the weekly balance in `margin_share_long` and `margin_episodes` from the settings.

    Contract:
        Input:
            settings: SmallCapWatchSettings
            query:    LakeQuery          -- derived.prices_adj, curated daily, stk_limit,
                                            index_daily, fund_daily, fund_share, margin,
                                            margin_detail, daily_basic, trade_cal
            flows:    EtfFlowCalculator  -- net subscriptions per ETF and day
            rows:     SmallCapWatchRows  -- display rows, states and chart history
            vols:     RealizedVolCalculator  -- realised vol and trailing percentiles
        Output:
            instance; `build(previous)` -> dict, `write(out_dir)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `smallcap-watch` command

    Test cases:
        TC-SCW-001  limit-down count: close at down_limit counts, a tick above does not,
                    down_limit 0 is ignored; panic row on at its trigger
        TC-SCW-002  share at a low_window low (stocks with fewer sessions left out) and share
                    above the ma_window average; near at near_share of the trigger
        TC-SCW-003  level rows: on at or below the level, near within near_level, else off;
                    drawdown from the year high
        TC-SCW-004  realised vol (sample std x sqrt 252 x 100), gap = small - large vol, gap pct
                    = share of the window at or below the latest; no star data gives None, off
        TC-SCW-005  ETF flow = shares added x close (亿): 1-day, flow_days and own rows
        TC-SCW-006  new_triggered lists an on row once; the next build against it lists none
        TC-SCW-007  no fund tables: etf_flow in missing and no flow rows
        TC-SCW-008  write puts smallcap_watch.json in the directory; a missing one raises
                    LakeError
        TC-SCW-009  empty curated.daily raises LakeError
        TC-SCW-010  margin: a day missing an exchange is dropped; balance, drawdown from the
                    window high, turn-days change, share of float cap ranked on full
                    margin_detail days; no margin table lists margin in missing
        TC-SCW-012  ph6: margin_share_long keeps the last full day of each week from
                    margin_long_start, share in %, partial days dropped
        TC-SCW-013  ph7: rz_speed = EMA of the daily change, rz_acc = its margin_acc_days change
                    / margin_acc_days; rz_dd_long from the high since margin_long_start (not
                    the margin_high_days high); weekly points carry rz; episodes in the document
        TC-SCW-011  ph5: small_ret and small_turn (amount / prior turnover_window mean) feed
                    the 放量大跌 row
    """

    def __init__(
        self,
        settings: SmallCapWatchSettings,
        query: LakeQuery,
        flows: EtfFlowCalculator,
        rows: SmallCapWatchRows,
        vols: RealizedVolCalculator,
    ) -> None:
        self._s = settings
        self._query = query
        self._flows = flows
        self._rows = rows
        self._vols = vols

    def build(self, previous: dict[str, Any] | None) -> dict[str, Any]:
        """
        Purpose:
            The watch document as of the last session in curated.daily.

        Contract:
            Input:
                previous: dict | None  -- the last written document (for new_triggered)
            Output:
                dict  -- {as_of, rows: [{key, group, name, value, unit, trigger, state, note,
                         date}], history: [{date, small, limit_downs, low_share, gap,
                         gap_pct, rz, rz_ma, rz_circ}], triggered: [key], new_triggered: [key],
                         missing: [key], margin_share_long: [{date, share, small, rz}] (ph6,
                         rz ph7), margin_episodes: [{name, depth, months}] (ph7)};
                         shares and percentiles as fractions, vol in %, flows in 亿元
            Raises:
                LakeError  -- curated.daily is empty, or a query fails
        """
        last = self._query.sql(_LAST)["d"].iloc[0]
        if last is None or (isinstance(last, float) and math.isnan(last)):
            raise LakeError("curated.daily is empty: run make market-data")
        as_of = str(last)
        sessions = [d for d in self._query.sql(_SESSIONS)["cal_date"].astype(str) if d <= as_of]
        start = sessions[-self._s.history :][0]
        detail = self._read_detail_long(as_of)
        market = self._read_market(sessions, as_of).join(self._read_margin(sessions, as_of))
        if not detail.empty:
            depth = detail["rz"] / detail["rz"].cummax() - 1
            market = market.join(depth.rename("rz_dd_long"))
        vols = self._compute_vols(as_of)
        flows = self._read_flows(sessions, as_of)
        rows, missing = self._rows.build(market, vols, flows)
        on = [r["key"] for r in rows if r["state"] == "on"]
        seen = set((previous or {}).get("triggered", []))
        history = self._rows.build_history(market, vols, start)
        return {
            "as_of": as_of,
            "rows": rows,
            "history": history,
            "triggered": on,
            "new_triggered": [k for k in on if k not in seen],
            "missing": missing,
            "margin_share_long": self._compute_weekly(detail),
            "margin_episodes": [e.model_dump() for e in self._s.margin_episodes],
        }

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build against the previous document in `out_dir` and write smallcap_watch.json.

        Contract:
            Input:
                out_dir: Path  -- existing directory
            Output:
                Path  -- the written file
            Raises:
                LakeError  -- `out_dir` missing, or build fails
        """
        if not out_dir.is_dir():
            raise LakeError(f"output directory does not exist: {out_dir}")
        path = out_dir / FILE_NAME
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        doc = self.build(previous)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("small-cap watch: %d rows as of %s -> %s", len(doc["rows"]), doc["as_of"], path)
        return path

    def _read_market(self, sessions: list[str], as_of: str) -> pd.DataFrame:
        """Per session from the history start: limit_downs, low_share, above_ma."""
        s = self._s
        start = sessions[-s.history :][0]
        lead = sessions[-(s.history + max(s.low_window, s.ma_window)) :][0]
        limit = (
            self._query.sql(_LIMIT, [start, as_of]).set_index("trade_date")["n"]
            if self._query.has_view("curated.stk_limit")
            else pd.Series(dtype=float)
        )
        sql = _BREADTH.format(
            lo=_FRAME.format(n=s.low_window - 1),
            ma=_FRAME.format(n=s.ma_window - 1),
            n_lo=s.low_window,
            n_ma=s.ma_window,
        )
        breadth = self._query.sql(sql, [lead, as_of, start]).set_index("trade_date")
        frame = breadth.join(limit.rename("limit_downs"), how="left")
        frame.index = frame.index.astype(str)
        return frame.sort_index()

    def _read_margin(self, sessions: list[str], as_of: str) -> pd.DataFrame:
        """Financing balance (亿) per session: rz, dd, changes, mean, share of float cap (+ pct)."""
        s = self._s
        if not self._query.has_view("curated.margin"):
            return pd.DataFrame()
        lead = sessions[-(s.history + s.margin_high_days) :][0]
        raw = self._query.sql(_MARGIN, [lead, as_of]).set_index("trade_date")
        rz = raw.loc[raw["n"] == raw["n"].max(), "rz"]  # a day missing an exchange is not a total
        rz.index = rz.index.astype(str)
        share, rank = self._compute_margin_share(rz, sessions, as_of)
        speed = rz.diff().ewm(span=s.margin_speed_span).mean()
        return pd.DataFrame({
            "rz": rz,
            "rz_dd": rz / rz.rolling(s.margin_high_days, min_periods=1).max() - 1,
            "rz_chg": rz / rz.shift(s.margin_turn_days) - 1,
            "rz_chg_ma": rz / rz.shift(s.margin_ma_days) - 1,
            "rz_ma": rz.rolling(s.margin_ma_days).mean(),
            "rz_speed": speed,
            "rz_acc": speed.diff(s.margin_acc_days) / s.margin_acc_days,
            "rz_circ": share,
            "rz_circ_pct": rank,
        })  # fmt: skip

    def _compute_margin_share(
        self, rz: pd.Series, sessions: list[str], as_of: str
    ) -> tuple[pd.Series, pd.Series]:
        """Balance / float cap on rz's dates, and its trailing pct on the margin_detail sum."""
        views = ("curated.daily_basic", "curated.margin_detail")
        if not all(self._query.has_view(v) for v in views):
            return pd.Series(index=rz.index, dtype=float), pd.Series(index=rz.index, dtype=float)
        lead = sessions[-(self._s.history + self._s.pct_window) :][0]
        circ = self._query.sql(_CIRC, [lead, as_of]).set_index("trade_date")["circ"]
        detail = self._query.sql(_DETAIL, [lead, as_of]).set_index("trade_date")
        full = detail["n"] >= _FULL_DAY * detail["n"].rolling(20, min_periods=1).median()
        for frame in (circ, detail):
            frame.index = frame.index.astype(str)
        full.index = detail.index
        rank = self._vols.compute_rank_pct(detail.loc[full, "rz"] / circ)
        return rz / circ.reindex(rz.index), rank.reindex(rz.index)

    def _read_detail_long(self, as_of: str) -> pd.DataFrame:
        """Full margin_detail days from margin_long_start: rz (亿), share (%), 中证1000 close."""
        views = ("curated.daily_basic", "curated.margin_detail")
        if not all(self._query.has_view(v) for v in views):
            return pd.DataFrame()
        start = self._s.margin_long_start
        detail = self._query.sql(_DETAIL, [start, as_of]).set_index("trade_date")
        if detail.empty:
            return pd.DataFrame()
        circ = self._query.sql(_CIRC, [start, as_of]).set_index("trade_date")["circ"]
        detail = detail[detail["n"] >= _FULL_DAY * detail["n"].rolling(20, min_periods=1).median()]
        small = self._query.sql(_SMALL, [self._s.small_index.code, start, as_of])
        frame = pd.DataFrame(
            {"rz": detail["rz"], "share": detail["rz"] / circ.reindex(detail.index) * 100}
        )
        frame["small"] = small.set_index("trade_date")["close"].reindex(frame.index)
        frame = frame.dropna(subset=["share"])
        frame.index = frame.index.astype(str)
        return frame

    @staticmethod
    def _compute_weekly(frame: pd.DataFrame) -> list[dict[str, Any]]:
        """The last full day of each ISO week: share in %, 中证1000 close, rz in 亿 (ph6, ph7)."""
        if frame.empty:
            return []
        days = pd.DatetimeIndex(pd.to_datetime(frame.index, format="%Y%m%d"))
        frame = frame.set_axis(days)
        iso = days.isocalendar()
        weekly = frame.groupby([iso["year"], iso["week"]]).tail(1)
        dates = pd.DatetimeIndex(weekly.index).strftime("%Y%m%d")
        return [
            {"date": d, "share": round(float(sh), 4),
             "small": None if pd.isna(sm) else float(sm), "rz": round(float(rz), 1)}
            for d, sh, sm, rz in zip(dates, weekly["share"], weekly["small"], weekly["rz"],
                                     strict=True)
        ]  # fmt: skip

    def _compute_vols(self, as_of: str) -> pd.DataFrame:
        """Index closes, realised vols, the 1000-300 gap and their percentiles per session."""
        s = self._s
        codes = [s.small_index.code, s.large_index.code, s.star_index.code]
        has_index = self._query.has_view("curated.index_daily")
        px = self._query.sql(_INDEX, [codes, as_of]) if has_index else pd.DataFrame()
        if px.empty:
            return pd.DataFrame(columns=["small", "small_vol", "star_vol", "gap"])
        wide = px.pivot(index="trade_date", columns="ts_code", values="close").sort_index()
        wide.index = wide.index.astype(str)
        vol = self._vols.compute_vol(wide, s.vol_window)
        out = pd.DataFrame(index=wide.index)
        out["small"] = wide.get(s.small_index.code)
        amount = px[px["ts_code"] == s.small_index.code].set_index("trade_date")["amount"]
        amount.index = amount.index.astype(str)
        amount = amount.reindex(out.index)
        out["small_ret"] = out["small"].pct_change(fill_method=None)
        out["small_turn"] = amount / amount.shift(1).rolling(s.turnover_window).mean()
        out["small_vol"] = vol.get(s.small_index.code)
        out["star_vol"] = vol.get(s.star_index.code)
        out["gap"] = out["small_vol"] - vol.get(s.large_index.code)
        for col in ("small_vol", "star_vol", "gap"):
            out[f"{col}_pct"] = self._vols.compute_rank_pct(out[col])
        out["gap_exit"] = (
            out["gap"].rolling(s.pct_window, min_periods=s.pct_min_obs).quantile(s.gap_exit_pct)
        )
        return out

    def _read_flows(self, sessions: list[str], as_of: str) -> pd.DataFrame:
        """Net flow (亿元) per configured ETF (columns) and share date (rows)."""
        etfs = self._s.etfs
        views = ("curated.fund_daily", "curated.fund_share")
        if not etfs or not all(self._query.has_view(v) for v in views):
            return pd.DataFrame()
        codes = [e.code for e in etfs]
        start = sessions[-(self._s.flow_days + 15) :][0]
        prices = self._query.sql(_FUND_PX, [codes, start, as_of])
        shares = self._query.sql(_FUND_SH, [codes, start, as_of])
        if prices.empty or shares.empty:
            return pd.DataFrame()
        members = pd.DataFrame({"ts_code": codes, "index": codes, "is_core": False})
        daily = self._flows.compute_daily(prices, shares, members).dropna(subset=["flow"])
        wide = daily.pivot(index="trade_date", columns="ts_code", values="flow").sort_index()
        wide.index = wide.index.astype(str)
        return wide
