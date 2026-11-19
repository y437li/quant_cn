"""Apply the user's views to the ETF CTA targets: the 含观点 track (plan 27 ph5, D-163)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.etf_cta_settings import BONDS, EtfCtaSettings
from quant_cn.core.etf_cta_views import HIGH, LOW, EtfCtaView, EtfCtaViews

EPS = 1e-9


class EtfCtaViewTilt:
    """
    Purpose:
        Turn the system targets into the 含观点 targets on each decision date, in this order:
        (0) the A股 floor lifts each timed ETF to floor x its untimed weight when lower;
        (1) scale views multiply their ETFs; a subset inside one group (A股, 港股, one ETF) is
        rescaled so the group total stays, a whole group or a cross-group set changes capital;
        the combined multiplier per ETF against the system is clipped to 0.5..2;
        (2) relative views move points of capital from `under` to `over` pro rata, capped by
        what `under` holds, skipped when `over` holds nothing (A股 timing is respected);
        (3) when the total passes 100% every line scales down to fit; the rest is cash.
        A view is live from start to expires; with a price condition it waits until the close
        on a decision date meets it, then stays live until it expires.

    Contract:
        Input:
            settings: EtfCtaSettings
            codec:    DateCodec
        Output:
            instance; `compute_targets(targets, views, closes, full)` -> DataFrame like targets;
            `build_summary(system, tilted, views, closes)` -> dict for the last date
        Raises:
            ConfigError  -- (from settings.list_members) a view names an unknown set

    Used by:
        portfolio.EtfCtaBook  -- the 含观点 track

    Test cases:
        TC-ECVT-001  no live views leaves the targets unchanged; outside start..expires ignored
        TC-ECVT-002  a whole-group scale changes capital; a subset scale keeps the group total
        TC-ECVT-003  the combined multiplier is clipped to 0.5..2; the total is capped at 100%
        TC-ECVT-004  a relative view moves points pro rata, capped by the source, skipped into
                     a zero target
        TC-ECVT-005  a price condition waits, then latches until expiry
        TC-ECVT-006  the floor lifts A股 only when below floor x untimed weight
        TC-ECVT-007  build_summary gives statuses, group effects and flags for expired and
                     newly triggered views
    """

    def __init__(self, settings: EtfCtaSettings, codec: DateCodec) -> None:
        self._s = settings
        self._codec = codec
        self._group_of = {c: g.name for g in settings.groups for c in g.members}
        self._group_of |= {c: BONDS for c in settings.bonds}

    def compute_targets(
        self,
        targets: pd.DataFrame,
        views: EtfCtaViews,
        closes: pd.DataFrame,
        full: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            The 含观点 targets.

        Contract:
            Input:
                targets: DataFrame         -- decision dates x codes (cash excluded), system
                views:   EtfCtaViews
                closes:  DataFrame         -- sessions x codes, close prices (conditions)
                full:    DataFrame | None  -- untimed targets like targets (for the floor)
            Output:
                DataFrame  -- same index and columns, weights >= 0, row sum <= 1
            Raises:
                ConfigError  -- unknown set name
        """
        out = targets.copy()
        timed = [c for c in self._s.timed if c in out.columns]
        if views.a_share_floor is not None and full is not None and timed:
            floor = full.reindex(index=out.index, columns=timed).fillna(0.0) * views.a_share_floor
            out[timed] = np.maximum(out[timed], floor)
        live = self._find_live(views.views, closes, pd.DatetimeIndex(out.index))
        for day in out.index:
            on = [v for i, v in enumerate(views.views) if live.loc[day, i]]
            if on:
                out.loc[day] = self._compute_row(out.loc[day], on)
        return out

    def build_summary(
        self, system: pd.DataFrame, tilted: pd.DataFrame, views: EtfCtaViews, closes: pd.DataFrame
    ) -> dict[str, Any]:
        """
        Purpose:
            The views block of the document for the last decision date.

        Contract:
            Input:
                system, tilted: DataFrame  -- decision dates x codes, as compute_targets
                views:  EtfCtaViews
                closes: DataFrame
            Output:
                dict  -- {floor, items: [{..view, status}], groups: [{name, system, views,
                         effect}], flags: [{key, kind, message}]}; status one of 未开始 /
                         等待触发 / 生效 / 已过期
            Raises:
                (none)
        """
        dates = pd.DatetimeIndex(system.index)
        live = self._find_live(views.views, closes, dates)
        day = dates[-1]
        items, flags = [], []
        for i, view in enumerate(views.views):
            status = self._to_status(view, day, bool(live.loc[day, i]))
            items.append(view.model_dump(exclude_none=True) | {"status": status})
            if status == "已过期":
                flags.append(self._build_flag(f"view:expired:{i}:{view.expires}", view, "已过期"))
            elif view.when and live.loc[day, i] and (len(dates) == 1 or not live.iloc[-2, i]):
                flags.append(self._build_flag(f"view:on:{i}:{view.start}", view, "已触发"))
        names = [g.name for g in self._s.groups] + [BONDS]
        groups = []
        for name in names:
            codes = self._s.list_members(name)
            a, b = float(system.iloc[-1][codes].sum()), float(tilted.iloc[-1][codes].sum())
            groups.append(
                {
                    "name": name,
                    "system": round(a, 4),
                    "views": round(b, 4),
                    "effect": round(b - a, 4),
                }
            )
        a, b = 1.0 - float(system.iloc[-1].sum()), 1.0 - float(tilted.iloc[-1].sum())
        groups.append(
            {"name": "现金", "system": round(a, 4), "views": round(b, 4), "effect": round(b - a, 4)}
        )
        return {"floor": views.a_share_floor, "items": items, "groups": groups, "flags": flags}

    def _find_live(
        self, views: list[EtfCtaView], closes: pd.DataFrame, dates: pd.DatetimeIndex
    ) -> pd.DataFrame:
        live = pd.DataFrame(False, index=dates, columns=range(len(views)))
        for i, v in enumerate(views):
            start = pd.Timestamp(self._codec.to_date(v.start))
            end = pd.Timestamp(self._codec.to_date(v.expires))
            window = pd.Series((dates >= start) & (dates <= end), index=dates)
            if v.when is not None:
                px = closes[v.when.code].reindex(dates) if v.when.code in closes else None
                met = (
                    pd.Series(False, index=dates)
                    if px is None
                    else (px < v.when.below if v.when.below is not None else px > v.when.above)
                )
                window = window & (window & met.fillna(False)).cummax()
            live[i] = window.to_numpy()
        return live

    def _compute_row(self, row: pd.Series, views: list[EtfCtaView]) -> pd.Series:
        inner = pd.Series(1.0, index=row.index)
        outer = pd.Series(1.0, index=row.index)
        for v in (v for v in views if v.kind == "scale"):
            codes = self._s.list_members(str(v.target))
            part = inner if self._is_inner(codes) else outer
            part[codes] = part[codes] * float(v.multiplier or 1.0)
        w = row * inner
        for name in {self._group_of[c] for c in row.index if inner[c] != 1.0}:
            codes = [c for c in row.index if self._group_of[c] == name]
            if float(w[codes].sum()) > EPS:
                w[codes] = w[codes] * float(row[codes].sum()) / float(w[codes].sum())
        ratio = (w * outer / row.where(row > EPS)).clip(LOW, HIGH).fillna(1.0)
        w = row * ratio
        for v in (v for v in views if v.kind == "relative"):
            w = self._compute_move(
                w,
                self._s.list_members(str(v.under)),
                self._s.list_members(str(v.over)),
                float(v.points or 0.0),
            )
        total = float(w.sum())
        return w / total if total > 1.0 else w

    def _is_inner(self, codes: list[str]) -> bool:
        groups = {self._group_of[c] for c in codes}
        if len(groups) != 1:
            return False
        whole = [c for c, g in self._group_of.items() if g in groups]
        return set(codes) != set(whole)

    @staticmethod
    def _compute_move(w: pd.Series, src: list[str], dst: list[str], points: float) -> pd.Series:
        have, into = float(w[src].sum()), float(w[dst].sum())
        amount = min(points, have)
        if amount <= EPS or into <= EPS:
            return w
        out = w.copy()
        out[src] = w[src] * (1.0 - amount / have)
        out[dst] = w[dst] * (1.0 + amount / into)
        return out

    def _to_status(self, view: EtfCtaView, day: pd.Timestamp, live: bool) -> str:
        if day < pd.Timestamp(self._codec.to_date(view.start)):
            return "未开始"
        if day > pd.Timestamp(self._codec.to_date(view.expires)):
            return "已过期"
        return "生效" if live else "等待触发"

    @staticmethod
    def _build_flag(key: str, view: EtfCtaView, what: str) -> dict[str, Any]:
        name = view.target if view.kind == "scale" else f"{view.over}好于{view.under}"
        return {"key": key, "kind": "view", "message": f"观点{what}: {name} ({view.reason})"}
