"""放量大跌 row and 建仓档 (three-step entry) rows of the small-cap watch (plan 30 ph5)."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from quant_cn.core.small_cap_watch_settings import SmallCapWatchSettings

Row = dict[str, Any]
STEP_NAMES = ("第一档 1/3", "第二档 1/3", "第三档 1/3")


class SmallCapEntryRows:
    """
    Purpose:
        The entry rows of the small-cap watch (research 20261119_volume_selloff):
        - 放量大跌 (group 恐慌): 中证1000 day return against `selloff_drop` with turnover /
          its prior `turnover_window` mean against `selloff_turnover`; on when both hold,
          near at `selloff_near_drop` and `selloff_near_turnover`, else off;
        - 建仓档 (only when `entry_since` is set): step 1 = buy now; step 2 = panic day
          (limit_downs >= panic_limit_downs) or 放量大跌 or 中证1000 at or below the lowest
          level; step 3 = 融资余额企稳 (rz_dd <= margin_dd_trigger and rz_chg >= 0). A step
          already bought (`entry_bought`) is info; a step not bought is on from the first
          session since `entry_since` its condition held, and stays on after it clears, with
          that date in the note; otherwise off.

    Contract:
        Input:
            settings: SmallCapWatchSettings
        Output:
            instance; `build_selloff_row(vols)` -> Row | None,
            `build_tranche_rows(market, vols)` -> list[Row]
        Raises:
            (none at construction)

    Used by:
        portfolio.SmallCapWatchRows  -- adds the rows to the document

    Test cases:
        TC-SCE-001  放量大跌 on at -3.0% / 1.3x, off at -2.99% or 1.29x, near at -2% / 1.0x;
                    no return or turnover gives None
        TC-SCE-002  step 2 fires on a panic day, a 放量大跌 day or the lowest level, keeps its
                    first date after the condition clears; days before entry_since ignored
        TC-SCE-003  step 3 on 企稳; bought steps are info; no entry_since gives no rows
    """

    def __init__(self, settings: SmallCapWatchSettings) -> None:
        self._s = settings

    def build_selloff_row(self, vols: pd.DataFrame) -> Row | None:
        """
        Purpose:
            The 放量大跌 row of the last session with a 中证1000 return.

        Contract:
            Input:
                vols: DataFrame  -- index trade_date; small_ret (fraction), small_turn (ratio)
            Output:
                Row | None  -- unit 涨跌, value and trigger as fractions; None without data
            Raises:
                (none)
        """
        s = self._s
        if "small_ret" not in vols or "small_turn" not in vols:
            return None
        ok = vols.dropna(subset=["small_ret", "small_turn"])
        if ok.empty:
            return None
        date, ret, turn = str(ok.index[-1]), ok["small_ret"].iloc[-1], ok["small_turn"].iloc[-1]
        if self._is_selloff(ret, turn):
            state = "on"
        elif ret <= s.selloff_near_drop and turn >= s.selloff_near_turnover:
            state = "near"
        else:
            state = "off"
        note = (
            f"成交额为前 {s.turnover_window} 日均值的 {turn:.2f} 倍 (触发 ≥ {s.selloff_turnover});"
            " 历史 21 次, 20 天平均 +5.9% (上涨 86%), 60 天 +2.9%"
        )
        return {"key": "selloff", "group": "恐慌", "name": f"{s.small_index.name} 放量大跌",
                "value": float(ret), "unit": "涨跌", "trigger": s.selloff_drop, "state": state,
                "note": note, "date": date}  # fmt: skip

    def build_tranche_rows(self, market: pd.DataFrame, vols: pd.DataFrame) -> list[Row]:
        """
        Purpose:
            The three 建仓档 rows, or [] when `entry_since` is not set.

        Contract:
            Input:
                market: DataFrame  -- index trade_date; limit_downs and, with margin data,
                                      rz_dd, rz_chg
                vols:   DataFrame  -- index trade_date; small, small_ret, small_turn
            Output:
                list[Row]  -- keys entry_1..entry_3, group 建仓档, value None
            Raises:
                (none)
        """
        s = self._s
        if s.entry_since is None:
            return []
        frame = market.join(vols, how="outer").sort_index()
        frame = frame[frame.index >= s.entry_since]
        date = str(frame.index[-1]) if len(frame) else s.entry_since
        step2, step3 = self._compute_step2(frame), self._compute_step3(frame)
        low = f" 或跌到 {min(s.levels):,.0f}" if s.levels else ""
        specs = [
            ("现在买", pd.Series(True, index=frame.index[-1:]) if len(frame) else None),
            (f"恐慌日 / 放量大跌{low}", step2),
            ("融资余额企稳", step3),
        ]
        return [self._build_step(i, name, fired, date) for i, (name, fired) in enumerate(specs, 1)]

    def _build_step(self, i: int, cond: str, fired: pd.Series | None, date: str) -> Row:
        """One step row: info when bought, on from its first fire, else off."""
        name = f"{STEP_NAMES[i - 1]}: {cond}"
        row: Row = {"key": f"entry_{i}", "group": "建仓档", "name": name, "value": None,
                    "unit": "", "trigger": None, "date": date}  # fmt: skip
        if i <= self._s.entry_bought:
            return row | {"state": "info", "note": "已买"}
        hits = [] if fired is None else list(fired[fired].index)
        if not hits:
            return row | {"state": "off", "note": f"{self._s.entry_since} 以来未触发"}
        first, today = str(hits[0]), str(hits[-1]) == date
        when = "今天触发" if today else f"首次触发 {first}, 今天未触发"
        note = "条件已满足, 还没买" if i == 1 else f"{when}; 还没买"
        return row | {"state": "on", "note": note}

    def _compute_step2(self, frame: pd.DataFrame) -> pd.Series:
        """Per session: panic day, 放量大跌 or at / below the lowest level."""
        s = self._s
        fired = pd.Series(False, index=frame.index)
        if "limit_downs" in frame:
            fired |= frame["limit_downs"].fillna(0) >= s.panic_limit_downs
        if "small_ret" in frame and "small_turn" in frame:
            pairs = zip(frame["small_ret"], frame["small_turn"], strict=True)
            fired |= pd.Series([self._is_selloff(r, t) for r, t in pairs], index=frame.index)
        if s.levels and "small" in frame:
            fired |= frame["small"] <= min(s.levels)
        return fired

    def _compute_step3(self, frame: pd.DataFrame) -> pd.Series:
        """Per session: financing balance 企稳."""
        if "rz_dd" not in frame or "rz_chg" not in frame:
            return pd.Series(False, index=frame.index)
        return (frame["rz_dd"] <= self._s.margin_dd_trigger) & (frame["rz_chg"] >= 0)

    def _is_selloff(self, ret: Any, turn: Any) -> bool:
        """Day return at or below selloff_drop on turnover at or above selloff_turnover."""
        if ret is None or turn is None or math.isnan(ret) or math.isnan(turn):
            return False
        return bool(ret <= self._s.selloff_drop and turn >= self._s.selloff_turnover)
