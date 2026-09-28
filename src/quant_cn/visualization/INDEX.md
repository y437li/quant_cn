# src/quant_cn/visualization/

L5: charts for prices, factors, backtest results; plotly, themed, notebook + HTML export. May import from: L1–L4. Independent of `back_testing` and `portfolio`: inputs are DataFrames and `core` schemas only (D-019).

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `base_chart.py` | Extension point for charts: DataFrame in, themed plotly figure out (D-019) | `BaseChart` |
| `chart_theme.py` | Theme tokens for charts: surfaces, ink, grid and the up/down pair, per light or dark mode | `ChartTheme` |
| `price_chart.py` | Candlestick + volume chart for one ticker from a PRICE_PANEL frame | `PriceChart` |
