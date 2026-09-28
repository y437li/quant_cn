"""Candlestick + volume chart for one ticker from a PRICE_PANEL frame."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.frames import PRICE_PANEL
from quant_cn.visualization.base_chart import BaseChart
from quant_cn.visualization.chart_theme import ChartTheme

OHLC = ("open", "high", "low", "close")


class PriceChart(BaseChart):
    """
    Purpose:
        Daily candles (backward-adjusted by default: OHLC x adj_factor) over a volume panel for one
        ticker. Two stacked panels with their own y-axes (never a dual axis); x is a category axis
        of trading days so non-trading days leave no gaps. Up candles hollow, down candles filled.

    Contract:
        Input:
            theme:    ChartTheme
            ts_code:  str        -- ticker to plot
            codec:    DateCodec  -- trading-day labels
            adjusted: bool       -- True: multiply OHLC by adj_factor
            width, height: int
        Output:
            instance; BaseChart API (frame = PRICE_PANEL)
        Raises:
            (none at construction)

    Used by:
        research_space/main.ipynb  -- adjusted prices of the sample month

    Test cases:
        TC-PC-001  two traces (candles, volume) on two rows; category x of trading days
        TC-PC-002  adjusted candles equal OHLC x adj_factor; unadjusted equal raw OHLC
        TC-PC-003  ticker absent from the frame raises ValueError; bad frame raises SchemaError
    """

    def __init__(
        self,
        theme: ChartTheme,
        ts_code: str,
        codec: DateCodec,
        adjusted: bool = True,
        width: int = 960,
        height: int = 560,
    ) -> None:
        super().__init__(theme, width, height)
        self.ts_code = ts_code
        self.adjusted = adjusted
        self._codec = codec

    def build_figure(self, frame: pd.DataFrame) -> go.Figure:
        """
        Purpose:
            Candles and volume for `ts_code`.

        Contract:
            Input:
                frame: DataFrame  -- PRICE_PANEL (any tickers, any range)
            Output:
                plotly Figure  -- rows: candles (y "Price, CNY"), volume (y "Volume, lots")
            Raises:
                SchemaError  -- frame is not a PRICE_PANEL
                ValueError   -- no rows for ts_code
        """
        prices = PRICE_PANEL.validate(frame)
        rows = prices[prices["ts_code"] == self.ts_code].sort_values("trade_date")
        if rows.empty:
            raise ValueError(f"no rows for {self.ts_code}")
        days = [self._codec.to_date(str(d)).isoformat() for d in rows["trade_date"]]
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28], vertical_spacing=0.04
        )
        fig.add_trace(self._build_candles(rows, days), row=1, col=1)
        fig.add_trace(self._build_volume(rows, days), row=2, col=1)
        basis = "hfq adjusted" if self.adjusted else "unadjusted"
        fig.update_layout(
            title_text=f"{self.ts_code} daily ({basis})", xaxis_rangeslider_visible=False
        )
        fig.update_xaxes(type="category", nticks=8)
        fig.update_yaxes(title_text="Price, CNY", row=1, col=1)
        fig.update_yaxes(title_text="Volume, lots", row=2, col=1)
        return fig

    def _build_candles(self, rows: pd.DataFrame, days: list[str]) -> go.Candlestick:
        factor = rows["adj_factor"] if self.adjusted else 1.0
        ohlc = {c: rows[c] * factor for c in OHLC}
        t = self.theme
        return go.Candlestick(
            x=days,
            name=self.ts_code,
            **ohlc,
            increasing={"line": {"color": t.up, "width": 1.5}, "fillcolor": t.surface},
            decreasing={"line": {"color": t.down, "width": 1.5}, "fillcolor": t.down},
        )

    def _build_volume(self, rows: pd.DataFrame, days: list[str]) -> go.Bar:
        return go.Bar(
            x=days,
            y=rows["vol"],
            name="volume",
            marker={"color": self.theme.neutral},
            hovertemplate="%{y:,.0f} lots<extra></extra>",
        )
