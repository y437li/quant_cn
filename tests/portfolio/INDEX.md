# tests/portfolio/

Tests for `quant_cn.portfolio`. No network, no files outside `tmp_path`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `test_etf_cta_book.py` | contract tests for `EtfCtaBook` on a mini lake |  |
| `test_etf_cta_paper_book.py` | tests for `etf_cta_paper_book`, one function per TC ID |  |
| `test_etf_cta_record.py` | tests for `etf_cta_record`, one function per TC ID |  |
| `test_etf_cta_view_tilt.py` | tests for `etf_cta_view_tilt`, one function per TC ID |  |
| `test_etf_cta_weights.py` | tests for `etf_cta_weights`, one function per TC ID |  |
| `test_holdings_history_writer.py` | tests for `holdings_history_writer`, one function per TC ID |  |
| `test_holdings_risk_builder.py` | tests for `holdings_risk_builder` and `core.positions_book`, one function per TC ID | `FakeReviewer`, `FixedModel` |
| `test_look_through_weights.py` | tests for `look_through_weights`, one function per TC ID (TC-LTW-001..003) |  |
| `test_watchlist_builder.py` | contract tests for `WatchlistBuilder` on a mini lake | `FakeEvaluator` |
| `test_etf_flow_calculator.py` | contract tests for `EtfFlowCalculator` on hand-built frames | TC-EFC-001..005 |
| `test_etf_style_heat.py` | tests for `etf_style_heat`, one function per TC ID | |
| `test_etf_proxy_builder.py` | contract tests for `EtfProxyBuilder` on a mini lake | TC-EP-001..007 |
| `test_small_cap_watch_builder.py` | contract tests for `SmallCapWatchBuilder` on a mini lake | TC-SCW-001..012 |
| `test_small_cap_entry_rows.py` | contract tests for `SmallCapEntryRows` on hand frames | TC-SCE-001..003 |
| `test_small_cap_watch_rows.py` | contract tests for `SmallCapWatchRows` on hand frames | TC-SCR-001..007 |
| `test_app_rank_reader.py` | contract tests for `AppRankReader`, one function per TC ID | — |
| `test_market_signal_reader.py` | contract tests for `MarketSignalReader`, one function per TC ID | — |
| `test_sector_metric_reader.py` | contract tests for `SectorMetricReader`, one function per TC ID | — |
| `test_developer_sales_reader.py` | contract tests for `DeveloperSalesReader`, one function per TC ID | — |
| `test_sector_monitor_builder.py` | contract tests for `SectorMonitorBuilder`, one function per TC ID | `FakeMetrics`, `FakeChips`, `FakeApps`, `FakeSales`, `FakeSignals` |
| `test_sector_earnings_signal_builder.py` | contract tests for `SectorEarningsSignalBuilder`, one function per TC ID | `FixedEvents` |
| `test_condition_evaluator.py` | tests for `condition_evaluator`, one function per TC ID | `FakeChips`, `FakeFundamentals`, `FakeMargin`, `FakeCapital` |
| `test_position_reviewer.py` | tests for `position_reviewer`, one function per TC ID | `FakeChips`, `FakeFundamentals` |
| `test_margin_panel_builder.py` | tests for `margin_panel_builder`, one function per TC ID | `RowsQuery` |
| `test_buyback_events_builder.py` | tests for `buyback_events_builder`, one function per TC ID | `TwoQuery` |
| `test_buyback_monitor_builder.py` | tests for `buyback_monitor_builder`, one function per TC ID | `_FakeLedger`, `_FakeLabels`, `_FakeQuery` |
| `test_buyback_plan_frame.py` | tests for `buyback_plan_frame`, one function per TC ID; hand label / programme builders | — |
| `test_opportunity_rules.py` | tests for `opportunity_rules`, one function per TC ID | |
| `test_opportunity_document.py` | tests for `opportunity_document`, one function per TC ID | |
| `test_opportunity_screen.py` | tests for `opportunity_screen`, one function per TC ID | `FakeChips`, `FakeCycle`, `FakeValuations`, `FakeVersions`, `FixedModel` |
| `test_style_fit_checker.py` | tests for `style_fit_checker`, one function per TC ID | |
