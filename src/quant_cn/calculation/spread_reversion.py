"""Mean-reversion flag for cost-anchored futures spreads (plan 15 ph7i, D-156)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_cn.core.futures_monitor_settings import FuturesMonitorSettings

YEAR = 250  # sessions
MIN_OBS = 120  # spread values needed for a one-year z


class SpreadReversion:
    """
    Purpose:
        The one-year z of a spread (latest value against the mean and standard deviation of
        the last YEAR values) and the "reversion" flags: a spread marked `reversion` in the
        settings whose |z| reaches `reversion_z`. Only spreads that reverted out of sample
        carry the mark (research run 20261114_mean_reversion).

    Contract:
        Input:
            settings: FuturesMonitorSettings  -- reversion_z
        Output:
            instance; `compute_z(series)` -> float | None,
            `list_flags(spreads)` -> [{key, kind, name, message}]
        Raises:
            (none at construction)

    Used by:
        calculation.FuturesMonitorBuilder  -- spread z_1y and reversion flags

    Test cases:
        TC-SRV-001  z of a hand series; None under MIN_OBS values or with zero spread
        TC-SRV-002  flag at |z| = reversion_z with side and half-life; none below it or
                    without `reversion`
    """

    def __init__(self, settings: FuturesMonitorSettings) -> None:
        self._z = settings.reversion_z

    @staticmethod
    def compute_z(series: pd.Series) -> float | None:
        """
        Purpose:
            One-year z of the latest value.

        Contract:
            Input:
                series: pd.Series  -- spread values in date order (NaN ignored)
            Output:
                float | None  -- rounded to 2 places; None under MIN_OBS values or zero std
            Raises:
                (none)
        """
        window = series.dropna().iloc[-YEAR:]
        std = float(window.std()) if len(window) >= MIN_OBS else 0.0
        if std <= 0:
            return None
        return round(float((window.iloc[-1] - window.mean()) / std), 2)

    def list_flags(self, spreads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Purpose:
            Reversion flags for the built spreads.

        Contract:
            Input:
                spreads: list[dict]  -- each with key, name, unit, value, z_1y, reversion,
                                        half_life_d
            Output:
                list[dict]  -- {key "reversion:<key>", kind "reversion", name, message}
            Raises:
                (none)
        """
        out = []
        for s in spreads:
            z = s["z_1y"]
            if not s["reversion"] or z is None or abs(z) < self._z:
                continue
            side = "高于" if z > 0 else "低于"
            hl = f"，历史半衰期约 {s['half_life_d']} 个交易日" if s["half_life_d"] else ""
            text = f"{s['value']:,.2f} {s['unit']}，{side}一年均值 {abs(z):.1f} 个标准差{hl}"
            out.append({"key": f"reversion:{s['key']}", "kind": "reversion", "name": s["name"],
                        "message": text})  # fmt: skip
        return out
