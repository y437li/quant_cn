"""Display rows and chart history of the small-cap watch (小盘观察, plan 30)."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from quant_cn.core.small_cap_watch_settings import SmallCapWatchSettings

Row = dict[str, Any]


class SmallCapWatchRows:
    """
    Purpose:
        Turn the watch's daily frames into display rows with a state against each trigger,
        and into the chart history. States:
        - on / near / off: count and share rows are near at `near_share` of the trigger;
          percentile rows within `near_pct` points below it; level rows within `near_level`
          above the level (on at or below it);
        - info: rows without a trigger;
        - 杠杆 (ph4): 融资余额 and its share of float market cap with percentile (info), and
          企稳, on when the balance is at least `margin_dd_trigger` below its high and its
          `margin_turn_days` change is >= 0.

    Contract:
        Input:
            settings: SmallCapWatchSettings
        Output:
            instance; `build(market, vols, flows)` -> (rows, missing),
            `build_history(market, vols, start)` -> list
        Raises:
            (none at construction)

    Used by:
        portfolio.SmallCapWatchBuilder  -- rows and history of the document
        cli.ReportCommands              -- wiring of `smallcap-watch`

    Test cases:
        TC-SCR-001  count rows: on at the trigger, near at near_share of it, off below; a
                    missing value is off
        TC-SCR-002  percentile rows: on at the trigger, near within near_pct, carry `pct`
        TC-SCR-003  level rows: on at or below the level, near within near_level above it
        TC-SCR-004  empty frames list their keys in `missing` and give no rows
        TC-SCR-005  history keeps sessions from `start`, NaN as None
        TC-SCR-006  企稳 on at the drawdown trigger with change >= 0, off at a shallower
                    drawdown or a negative change; no margin columns lists margin in missing
    """

    def __init__(self, settings: SmallCapWatchSettings) -> None:
        self._s = settings

    def build(
        self, market: pd.DataFrame, vols: pd.DataFrame, flows: pd.DataFrame
    ) -> tuple[list[Row], list[str]]:
        """
        Purpose:
            All rows in display order (panic, leverage, index, volatility, flows) and the keys
            without data.

        Contract:
            Input:
                market: DataFrame  -- index trade_date; limit_downs, low_share, above_ma and,
                                      when margin data exists, rz, rz_dd, rz_chg, rz_chg_ma,
                                      rz_ma, rz_circ, rz_circ_pct (亿 / fractions)
                vols:   DataFrame  -- index trade_date; small, small_vol, star_vol, gap, their
                                      `_pct` columns, gap_exit
                flows:  DataFrame  -- index share date; one column of 亿元 per ETF code
            Output:
                (rows, missing)  -- rows: [{key, group, name, value, unit, trigger, state,
                                    note, date} (+ pct on percentile rows)]; missing: [key]
            Raises:
                (none)
        """
        missing: list[str] = []
        rows = self._build_market_rows(market, missing) + self._build_margin_rows(market, missing)
        ok = vols.dropna(subset=["small"]) if "small" in vols else vols
        if ok.empty:
            missing += ["levels", "small_vol", "star_vol", "gap"]
        else:
            rows += self._build_level_rows(ok) + self._build_vol_rows(ok)
        rows += self._build_flow_rows(flows, missing)
        return rows, missing

    def build_history(self, market: pd.DataFrame, vols: pd.DataFrame, start: str) -> list[Row]:
        """
        Purpose:
            Chart rows from `start`: index close, limit-downs, share at a low, gap and its pct.

        Contract:
            Input:
                market, vols: DataFrame  -- as in `build`; start: str YYYYMMDD
            Output:
                list[dict]  -- {date, small, limit_downs, low_share, gap, gap_pct, rz, rz_ma,
                               rz_circ}, by date;
                               missing values None
            Raises:
                (none)
        """
        cols = [c for c in ("small", "gap", "gap_pct") if c in vols]
        frame = market.join(vols[cols], how="outer")
        frame = frame[frame.index >= start]
        keys = ("small", "limit_downs", "low_share", "gap", "gap_pct", "rz", "rz_ma", "rz_circ")
        return [
            {"date": str(d)} | {k: self._as_float(r.get(k)) for k in keys}
            for d, r in frame.iterrows()
        ]

    def _build_market_rows(self, market: pd.DataFrame, missing: list[str]) -> list[Row]:
        """Panic rows: limit-down count, share at a low, share above the moving average."""
        s = self._s
        if market.empty:
            missing += ["limit_downs", "low_share", "above_ma"]
            return []
        last, date = market.iloc[-1], str(market.index[-1])
        ld, low = self._as_float(last.get("limit_downs")), self._as_float(last.get("low_share"))
        panic = f"≥ {s.panic_limit_downs} 只为恐慌日: 历史 7 次, 之后 20 天全部上涨, 平均 +13%"
        specs = [
            ("limit_downs", "跌停家数", ld, "只", s.panic_limit_downs, panic),
            ("low_share", f"创 {s.low_window} 日新低的股票占比", low, "占比",
             s.low_share_trigger, "大面积创新低, 抛压出清"),
        ]  # fmt: skip
        rows = [
            self._build_row(k, "恐慌", n, v, u, t, self._get_count_state(v, t), date, note)
            for k, n, v, u, t, note in specs
        ]
        above = self._as_float(last.get("above_ma"))
        name = f"站上 {s.ma_window} 日均线的股票占比"
        rows.append(self._build_row("above_ma", "恐慌", name, above, "占比", None, "info", date,
                                    "只作参考, 回升不等于见底"))  # fmt: skip
        return rows

    def _build_margin_rows(self, market: pd.DataFrame, missing: list[str]) -> list[Row]:
        """杠杆 rows: financing balance and its 企稳 state (20261118_marginal_trader)."""
        s = self._s
        ok = market.dropna(subset=["rz"]) if "rz" in market else pd.DataFrame()
        if ok.empty:
            missing.append("margin")
            return []
        last, date = ok.iloc[-1], str(ok.index[-1])
        dd, chg = self._as_float(last.get("rz_dd")), self._as_float(last.get("rz_chg"))
        ma, chg_ma = self._as_float(last.get("rz_ma")), self._as_float(last.get("rz_chg_ma"))
        share = self._as_float(last.get("rz_circ"))
        share = None if share is None else share * 100  # "%" rows hold percent, like vol
        deep = dd is not None and dd <= s.margin_dd_trigger
        state = "on" if deep and chg is not None and chg >= 0 else "off"
        n, m = s.margin_turn_days, s.margin_ma_days
        balance = (
            f"{n} 日 {chg or 0:+.1%}, {m} 日 {chg_ma or 0:+.1%}; {m} 日均线 {ma or 0:,.0f} 亿;"
            f" 距 {s.margin_high_days} 日高点 {dd or 0:+.1%}"
        )
        level = "2019 年以来 1.8% ~ 2.9%, 中位 2.3%; 底部参照 2024-09 2.2%, 2019-01 2.1%"
        turn = (
            f"距高点 ≤ {s.margin_dd_trigger:.0%} 且 {n} 日变化转正: 历史 12 次,"
            " 中证1000 60 天平均 +7.4% (中位 +4.3%); 2026-08、09 两次失败"
        )
        return [
            self._build_row("margin_balance", "杠杆", "融资余额", self._as_float(last["rz"]),
                            "亿元", None, "info", date, balance),
            self._build_row("margin_level", "杠杆", "融资余额 / 流通市值", share, "%", None,
                            "info", date, level) | {"pct": self._as_float(last.get("rz_circ_pct"))},
            self._build_row("margin_turn", "杠杆", f"融资余额企稳 ({n} 日变化)", chg, "占比",
                            0.0, state, date, turn),
        ]  # fmt: skip

    def _build_level_rows(self, ok: pd.DataFrame) -> list[Row]:
        """中证1000 against each user level, and its drawdown from the year high."""
        s = self._s
        last, date = ok.iloc[-1], str(ok.index[-1])
        close = float(last["small"])
        rows = [
            self._build_row(f"level_{int(lv)}", "点位", f"{s.small_index.name} 跌到 {lv:,.0f}",
                            close, "点", lv, self._get_level_state(close, lv), date,
                            f"距离 {close / lv - 1:+.1%}")
            for lv in s.levels
        ]  # fmt: skip
        high = float(ok[ok.index >= f"{date[:4]}0101"]["small"].max())
        rows.append(self._build_row("drawdown", "点位", f"{s.small_index.name} 距年内高点",
                                    close / high - 1, "占比", None, "info", date,
                                    f"收盘 {close:,.0f}"))  # fmt: skip
        return rows

    def _build_vol_rows(self, ok: pd.DataFrame) -> list[Row]:
        """Realised vol of 中证1000 and 科创50, and the 1000-300 gap with its exit line."""
        s = self._s
        last, date = ok.iloc[-1], str(ok.index[-1])
        exit_line = self._as_float(last.get("gap_exit"))
        exit_note = f"低于 {s.gap_exit_pct:.0%} 分位(≈ {exit_line or 0:.1f})为退出线"
        specs = [
            ("small_vol", f"{s.small_index.name} 实际波动({s.vol_window} 日)",
             s.vol_pct_trigger, "高波动是恐慌的前兆"),
            ("star_vol", f"{s.star_index.name} 实际波动({s.vol_window} 日)",
             s.vol_pct_trigger, "高波动是恐慌的前兆"),
            ("gap", f"{s.small_index.name} - {s.large_index.name} 波动差", s.gap_entry_pct,
             exit_note),
        ]  # fmt: skip
        rows = []
        for key, name, trigger, note in specs:
            pct = self._as_float(last.get(f"{key}_pct"))
            state = self._get_pct_state(pct, trigger)
            value = self._as_float(last.get(key))
            row = self._build_row(key, "波动", name, value, "%", trigger, state, date, note)
            rows.append(row | {"pct": pct})
        return rows

    def _build_flow_rows(self, flows: pd.DataFrame, missing: list[str]) -> list[Row]:
        """Broad-ETF net flow rows: total and own-row ETFs, one day and flow_days."""
        s = self._s
        if flows.empty:
            missing.append("etf_flow")
            return []
        date, recent, n = str(flows.index[-1]), flows.iloc[-s.flow_days :], len(s.etfs)
        specs = [
            ("etf_flow_1d", f"{n} 只宽基 ETF 净申购(1 天)", float(flows.iloc[-1].sum()),
             "大额流入多为托底资金"),
            ("etf_flow_nd", f"{n} 只宽基 ETF 净申购({s.flow_days} 天)",
             float(recent.sum().sum()), ""),
        ]  # fmt: skip
        specs += [
            (f"flow_{e.code}", f"{e.name} 净申购(1 天)", float(flows[e.code].iloc[-1]),
             f"{s.flow_days} 天合计 {float(recent[e.code].sum()):+.1f} 亿")
            for e in s.etfs
            if e.own_row and e.code in flows
        ]  # fmt: skip
        return [
            self._build_row(k, "资金", name, v, "亿", None, "info", date, note)
            for k, name, v, note in specs
        ]

    def _get_count_state(self, value: float | None, trigger: float) -> str:
        """on at or above the trigger, near at near_share of it."""
        if value is None:
            return "off"
        if value >= trigger:
            return "on"
        return "near" if value >= self._s.near_share * trigger else "off"

    def _get_pct_state(self, pct: float | None, trigger: float) -> str:
        """on at or above the percentile trigger, near within near_pct below it."""
        if pct is None:
            return "off"
        if pct >= trigger:
            return "on"
        return "near" if pct >= trigger - self._s.near_pct else "off"

    def _get_level_state(self, close: float, level: float) -> str:
        """on at or below the level, near within near_level above it."""
        if close <= level:
            return "on"
        return "near" if close <= level * (1 + self._s.near_level) else "off"

    @staticmethod
    def _build_row(
        key: str, group: str, name: str, value: float | None, unit: str,
        trigger: float | None, state: str, date: str, note: str,
    ) -> Row:  # fmt: skip
        """One display row."""
        return {"key": key, "group": group, "name": name, "value": value, "unit": unit,
                "trigger": trigger, "state": state, "note": note, "date": date}  # fmt: skip

    @staticmethod
    def _as_float(value: Any) -> float | None:
        """JSON-safe float: None for missing or NaN."""
        if value is None:
            return None
        try:
            out = float(value)
        except (TypeError, ValueError):
            return None
        return None if math.isnan(out) else out
