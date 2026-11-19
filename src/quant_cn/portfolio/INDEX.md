# src/quant_cn/portfolio/

L5: position sizing, constraints, rebalancing schedules. May import from: L1–L4.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `etf_cta_book.py` | ETF CTA book document `etf_cta.json`: weekly targets, held, trades, groups, signals, premium guard, flags, back-test and paper record (plan 27, D-160) | `EtfCtaBook` |
| `etf_cta_paper_book.py` | Paper account following weekly targets with drift, a per-group no-trade band, costs and no-add codes (plan 27) | `EtfCtaPaperBook` |
| `etf_cta_record.py` | Track record of a paper NAV: ann, vol, Sharpe, drawdown, years, weekly points (plan 27) | `EtfCtaRecord` |
| `etf_cta_view_tilt.py` | Apply the user's views to the system targets: the 含观点 track (plan 27 ph5, D-163) | `EtfCtaViewTilt` |
| `etf_cta_weights.py` | Weekly target weights: equal-risk groups (monthly), A股 trend position, bond switch (plan 27) | `EtfCtaWeights` |
| `holdings_history_writer.py` | Daily history of the user's book in the lake (derived/holdings_positions, holdings_risk; plan 15 ph7d) | `HoldingsHistoryWriter` |
| `holdings_risk_builder.py` | The user's book valued at the last risk session and its risk decomposition for the 持仓 page (plan 15 ph7d, D-132) | `HoldingsRiskBuilder` |
| `watchlist_builder.py` | the chain app's watchlist document: gap to buy price, status, valuation at the buy price (plan 15 ph7, D-120); ETF rows from fund_daily (ph7p) | `WatchlistBuilder` |
| `etf_flow_calculator.py` | ETF membership per index, split-proof daily net flows, position at today's price (plan 15 ph7b, D-126) | `EtfFlowCalculator` |
| `etf_style_heat.py` | style ETF crowding (银行, 红利): 20-day flow vs AUM, z, 过热 / 降温 status (plan 15 ph7g) | `EtfStyleHeat` |
| `etf_proxy_builder.py` | the chain app's 国家队 ETF document: core vs other, per index (rhythm, 近3月 window), weekly, yearly, recent days (plan 15 ph7b, D-126; ph7o) | `EtfProxyBuilder` |
| `small_cap_watch_builder.py` | 小盘观察 document: limit-downs, breadth, index vols and gap, broad-ETF flows, 融资余额 (ph4); writes smallcap_watch.json (plan 30) | `SmallCapWatchBuilder` |
| `app_rank_reader.py` | App Store chart ranks per company and game, leaderboard for the 游戏 行业监控 (plan 19 ph2) | `AppRankReader` |
| `market_signal_reader.py` | 行业监控 market signals: valuation percentile, analyst forecast revision, institutional surveys (plan 33) | `MarketSignalReader` |
| `sector_metric_reader.py` | lake reads behind the 行业监控 charts: house-price tiers, statements, dividends, chips, closes, game approvals (plan 31) | `SectorMetricReader` |
| `developer_sales_reader.py` | developers' monthly contracted sales and land intensity from the 销售简报 labels (plan 31) | `DeveloperSalesReader` |
| `sector_monitor_builder.py` | sector_monitor.json for #sector-monitor: charts, realised vol, company table (plan 31) | `SectorMonitorBuilder` |
| `opportunity_rules.py` | opportunity rule hits, listed / near-miss ranking, new entries (plan 21 ph4) | `OpportunityRules` |
| `opportunity_document.py` | opportunities.json for the #opportunities page and the 机会清单 e-mail (plan 21 ph5) | `OpportunityDocument` |
| `opportunity_screen.py` | daily opportunity list: universe, gauge, signal row, earnings, valuation, fit -> derived/opportunity_list (plan 21 ph4) | `OpportunityScreen` |
| `style_fit_checker.py` | does adding a stock grow the book's largest style exposures (plan 21 ph4) | `StyleFitChecker` |
| `sector_earnings_signal_builder.py` | sector_earnings_signal.json: 财报季信号 per Shenwan L2 sector (好消息涨不动), history, past firings and record (plan 35) | `SectorEarningsSignalBuilder` |
| `small_cap_entry_rows.py` | 小盘观察 放量大跌 row and 建仓档 three-step entry rows (plan 30 ph5) | `SmallCapEntryRows` |
| `small_cap_watch_rows.py` | 小盘观察 display rows with on / near / off states, 杠杆 rows (ph4) and the chart history (plan 30) | `SmallCapWatchRows` |
| `condition_evaluator.py` | gather metrics and evaluate conditions to met / unmet / unknown; entry status buy / near / wait (plan 15 ph7f) | `ConditionResult`, `ConditionEvaluator` |
| `position_reviewer.py` | per-position note, chip row, flags (stop, target, weight, review, missing note) and conditions (plan 15 ph7f) | `PositionReviewer` |
| `margin_panel_builder.py` | per-stock 融资融券 documents with the forced-liquidation ladder (plan 15 ph7m) | `MarginPanelBuilder` |
| `buyback_events_builder.py` | recent large buyback plans and the book's buyback events -> buybacks.json (plan 23 ph6) | `BuybackEventsBuilder` |
| `buyback_monitor_builder.py` | market-wide buyback and 增持 programmes, events and totals -> buyback_monitor.json (plan 32 ph3) | `BuybackMonitorBuilder` |
| `buyback_plan_frame.py` | 回购 programmes and 增持 plans joined to their buyback_terms labels, one frame (plan 32 ph3) | `BuybackPlanFrame` |
