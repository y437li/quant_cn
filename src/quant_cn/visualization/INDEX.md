# src/quant_cn/visualization/

L5: charts for prices, factors, backtest results; plotly, themed, notebook + HTML export. May import from: L1–L4. Independent of `back_testing` and `portfolio`: inputs are DataFrames and `core` schemas only (D-019).

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `base_chart.py` | Extension point for charts: DataFrame in, themed plotly figure out (D-019) | `BaseChart` |
| `chart_theme.py` | Theme tokens for charts: surfaces, ink, grid and the up/down pair, per light or dark mode | `ChartTheme` |
| `factor_chart.py` | Factor campaign charts: rolling IC with a band, ICIR bars, quantile ladder, IC by horizon | `FactorChart` |
| `price_chart.py` | Candlestick + volume chart for one ticker from a PRICE_PANEL frame | `PriceChart` |
| `risk_chart.py` | Risk model charts: cumulative factor returns, factor correlations, risk decomposition (plan 05) | `RiskChart` |
| `email_format.py` | number and date formats of the morning e-mails; colour constants (red up, green down) | `EmailFormat` |
| `email_html.py` | e-mail-safe HTML blocks: cells, tables, sections, pairs, bars, tiles, page shell (960 px) | `EmailHtml` |
| `monitor_report_renderer.py` | the 持仓监测 e-mail: alerts first, holdings, exposures, factors, industries, national-team ETF | `MonitorReportRenderer` |
| `opportunity_report_renderer.py` | the 机会清单 e-mail: plan 21 list (when live) and the watchlist with condition status | `OpportunityReportRenderer` |
| `report_section.py` | base of the optional 持仓监测 blocks | `ReportSection` |
| `etf_report_section.py` | the ETF 资金强度 line of the 持仓监测 e-mail (plan 15 ph7g) | `EtfReportSection` |
| `futures_report_section.py` | the 期货 block of the 持仓监测 e-mail (plan 15 ph7i) | `FuturesReportSection` |
| `small_cap_report_section.py` | the 小盘观察 block of the 持仓监测 e-mail (plan 30 ph2) | `SmallCapReportSection` |
| `rates_fx_report_section.py` | the 利率汇率 block of the 持仓监测 e-mail (plan 34 ph4) | `RatesFxReportSection` |
| `sector_earnings_report_section.py` | the 财报季信号 block of the 持仓监测 e-mail (plan 35) | `SectorEarningsReportSection` |
| `task_status_report_section.py` | 数据更新 line and failed / skipped step rows of the 持仓监测 e-mail from task_status.json (plan 38) | `TaskStatusReportSection` |
| `volatility_report_section.py` | the 波动率 block of the 持仓监测 e-mail (plan 03 ph6) | `VolatilityReportSection` |
| `alert_message_builder.py` | plain-language phone alerts from the monitor documents and one message per run (plan 22) | `CardShot`, `Alert`, `AlertMessageBuilder` |
| `card_screenshotter.py` | PNG screenshots of app cards for phone alerts through shot_cards.mjs (plan 22) | `CardScreenshotter` |
| `macro_report_section.py` | the 宏观 block of the 持仓监测 e-mail (plan 15 ph7h) | `MacroReportSection` |
| `morning_report_builder.py` | read the app documents, skip stale data, write (dry run) or send both e-mails | `ReportOutcome`, `MorningReportBuilder` |
| `buyback_market_report_section.py` | the 回购增持（全市场） block of the 持仓监测 e-mail from buyback_monitor.json (plan 32 ph4) | `BuybackMarketReportSection` |
| `buyback_report_section.py` | the 回购 block of the 持仓监测 e-mail (plan 23 ph6) | `BuybackReportSection` |
