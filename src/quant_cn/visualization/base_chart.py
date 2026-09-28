"""Extension point for charts: DataFrame in, themed plotly figure out (D-019)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from quant_cn.visualization.chart_theme import ChartTheme


class BaseChart(ABC):
    """
    Purpose:
        Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never
        objects from other packages); the base applies theme, size, hover and export.

    Contract:
        Input:
            theme:  ChartTheme  -- colours and font
            width:  int > 0     -- pixels
            height: int > 0     -- pixels
        Output:
            instance; `render`, `to_html`, `write_html`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        visualization.PriceChart  -- subclass

    Test cases:
        TC-BCA-001  render applies surface, ink, grid and size from the theme
        TC-BCA-002  to_html returns a self-contained div; write_html writes the file and returns it
    """

    def __init__(self, theme: ChartTheme, width: int = 960, height: int = 560) -> None:
        self.theme = theme
        self.width = width
        self.height = height

    @abstractmethod
    def build_figure(self, frame: pd.DataFrame) -> go.Figure:
        """
        Purpose:
            Build the unthemed figure from the input frame.

        Contract:
            Input:
                frame: DataFrame  -- the subclass's documented schema
            Output:
                plotly Figure
            Raises:
                ValueError   -- frame has nothing to plot
                SchemaError  -- frame violates the schema
        """

    def render(self, frame: pd.DataFrame) -> go.Figure:
        """
        Purpose:
            Build the figure and apply the theme: surfaces, ink, recessive grid, unified hover.

        Contract:
            Input:
                frame: DataFrame
            Output:
                plotly Figure  -- ready for `.show()` in a notebook
            Raises:
                ValueError, SchemaError  -- from build_figure
        """
        fig = self.build_figure(frame)
        t = self.theme
        fig.update_layout(
            width=self.width,
            height=self.height,
            paper_bgcolor=t.surface,
            plot_bgcolor=t.surface,
            font={"family": t.font, "color": t.text_primary, "size": 12},
            title_font={"color": t.text_primary, "size": 15},
            hovermode="x unified",
            hoverlabel={"bgcolor": t.surface, "font_color": t.text_primary},
            margin={"l": 64, "r": 24, "t": 56, "b": 40},
            showlegend=False,
        )
        axis = {
            "gridcolor": t.grid,
            "zeroline": False,
            "linecolor": t.grid,
            "tickfont": {"color": t.text_secondary},
            "title_font": {"color": t.text_secondary},
        }
        fig.update_xaxes(**axis)
        fig.update_yaxes(**axis)
        return fig

    def to_html(self, frame: pd.DataFrame) -> str:
        """
        Purpose:
            The themed chart as an HTML fragment (plotly.js from its CDN).

        Contract:
            Input:
                frame: DataFrame
            Output:
                str  -- a `<div>` with its script
            Raises:
                ValueError, SchemaError
        """
        html: str = self.render(frame).to_html(full_html=False, include_plotlyjs="cdn")
        return html

    def write_html(self, frame: pd.DataFrame, path: Path) -> Path:
        """
        Purpose:
            Save the themed chart as a standalone HTML page.

        Contract:
            Input:
                frame: DataFrame; path: Path  -- parent folders are created
            Output:
                Path  -- the file written
            Raises:
                ValueError, SchemaError, OSError
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        self.render(frame).write_html(str(path), include_plotlyjs="cdn")
        return path
