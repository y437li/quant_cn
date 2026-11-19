# tests/calculation/

Tests for `quant_cn.calculation`; known answers from Black-76 synthetic chains (`SampleOptions`).

## Files
| File | Purpose | Contains |
|---|---|---|
| `test_black76_model.py` | tests for `black76_model`, one function per TC ID |  |
| `test_company_cycle_panel.py` | tests for `company_cycle_panel`, one function per TC ID | `PanelHarness` |
| `test_forecast_tracker.py` | tests for `forecast_tracker`, one function per TC ID |  |
| `test_expiry_clock.py` | tests for `expiry_clock`, one function per TC ID |  |
| `test_forward_price_estimator.py` | tests for `forward_price_estimator`, one function per TC ID |  |
| `test_futures_positioning.py` | tests for `futures_positioning`, one function per TC ID |  |
| `test_gamma_exposure_calculator.py` | tests for `gamma_exposure_calculator`, one function per TC ID |  |
| `test_margin_ladder_estimator.py` | tests for `margin_ladder_estimator`, one function per TC ID |  |
| `test_option_chain_builder.py` | tests for `option_chain_builder`, one function per TC ID |  |
| `test_risk_free_curve.py` | tests for `risk_free_curve`, one function per TC ID |  |
| `test_term_interpolator.py` | tests for `term_interpolator`, one function per TC ID |  |
| `test_term_selector.py` | tests for `term_selector`, one function per TC ID |  |
| `test_trend_position.py` | tests for `trend_position`, one function per TC ID |  |
| `test_variance_strip_calculator.py` | tests for `variance_strip_calculator`, one function per TC ID |  |
| `test_realized_vol_calculator.py` | tests for `realized_vol_calculator`, one function per TC ID |  |
| `test_vix_calculator.py` | tests for `vix_calculator`, one function per TC ID |  |
| `test_index_futures_monitor.py` | tests for `index_futures_monitor`, one function per TC ID | `EmptyQuery` |
| `test_futures_broker_nets.py` | tests for `futures_broker_nets`, one function per TC ID | `RowsQuery` |
| `test_futures_monitor_builder.py` | tests for `futures_monitor_builder`, one function per TC ID; `_write` writes a hand CU / RB curve | |
| `test_spread_reversion.py` | tests for `spread_reversion`, one function per TC ID | |
| `test_volatility_monitor_builder.py` | tests for `volatility_monitor_builder`, one function per TC ID; `_write` writes a cboe_vix series and a synthetic flat-20% option chain | |
| `test_rates_fx_monitor_builder.py` | tests for `rates_fx_series_reader` and `rates_fx_monitor_builder`, one function per TC ID; `_write` writes curves, FX, fixing, weights and daily_basic | |
| `test_earnings_event_builder.py` | tests for `earnings_event_builder`, one function per TC ID; `write_lake` writes prices, statements, previews and flashes | |
| `test_retail_gauge_matrices.py` | tests for `retail_gauge_matrices`, one function per TC ID | |
| `test_holder_count_panel.py` | tests for `holder_count_panel`, one function per TC ID | |
| `test_retail_gauge_feature_builder.py` | tests for `retail_gauge_feature_builder`; `write_lake` writes a 3-stock, 3-quarter lake | |
| `test_retail_gauge_model.py` | tests for `retail_gauge_model` on a synthetic panel | |
| `test_retail_gauge_nowcaster.py` | tests for `retail_gauge_nowcaster` with fake feature / holder panels | `FakeFeatures`, `FakeHolders` |
| `test_retail_gauge_evaluator.py` | tests for `retail_gauge_evaluator`, one function per TC ID | |
| `test_consensus_panel_builder.py` | tests for `consensus_panel_builder`, one function per TC ID | |
| `test_macro_monitor_builder.py` | tests for `macro_monitor_builder`, one function per TC ID; `_write_all` writes the five macro tables | |
| `test_futures_curve.py` | tests for `futures_curve`, one function per TC ID | |
| `test_implied_expectations.py` | tests for `implied_expectations`, one function per TC ID | |
