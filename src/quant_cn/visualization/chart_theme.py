"""Theme tokens for charts: surfaces, ink, grid and the up/down pair, per light or dark mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Mode = Literal["light", "dark"]


@dataclass(frozen=True)
class ChartTheme:
    """
    Purpose:
        The colour and font tokens every chart reads, so charts are written against roles, never
        raw hex. Values follow the dataviz reference palette; `up`/`down` are its red and green
        slots (A-share convention: red up, green down), validated per mode; the light pair sits
        in the CVD 6-8 band, so up candles are hollow as the secondary encoding.

    Contract:
        Input:
            mode: "light" | "dark"
            surface, text_primary, text_secondary, grid, up, down, neutral: str  -- hex
            font: str  -- CSS font family
        Output:
            frozen dataclass; `from_mode`
        Raises:
            (none)

    Used by:
        visualization.BaseChart   -- applied to every figure
        visualization.PriceChart  -- candle and volume colours

    Test cases:
        TC-CT-001  light and dark themes have distinct surfaces and the validated up/down steps
    """

    mode: Mode
    surface: str
    text_primary: str
    text_secondary: str
    grid: str
    up: str
    down: str
    neutral: str
    font: str = "Inter, -apple-system, Segoe UI, sans-serif"

    @classmethod
    def from_mode(cls, mode: Mode = "light") -> ChartTheme:
        """
        Purpose:
            The theme for a display mode.

        Contract:
            Input:
                mode: "light" | "dark"
            Output:
                ChartTheme
            Raises:
                ValueError  -- other mode
        """
        if mode == "light":
            return cls(
                "light", "#fcfcfb", "#0b0b0b", "#52514e", "#e7e6e2", "#e34948", "#008300", "#a9a8a3"
            )
        if mode == "dark":
            return cls(
                "dark", "#1a1a19", "#ffffff", "#c3c2b7", "#383835", "#e66767", "#008300", "#6d6c67"
            )
        raise ValueError(f"unknown mode {mode!r}")
