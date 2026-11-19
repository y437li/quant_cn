# src/quant_cn/calculation/

L4: domain financial computations over lake frames (CBOE VIX, Black-76); pure, no I/O. May import from: L1. Independent of statistic and pipeline.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `black76_model.py` | Black-76 option prices on a forward and implied volatility by bisection | `Black76Model` |
| `company_cycle_panel.py` | Company cycle panel as known on a date: quarters, TTM, YoY/QoQ, deducted profit, 10-year norm (plan 16) | `CompanyCyclePanel` |
| `forecast_tracker.py` | Earnings previews (all revisions) scored against the first reported profit; per-company hit rate and bias (plan 18) | `ForecastTracker` |
| `expiry_clock.py` | How time to expiry is measured: calendar minutes (CBOE) or trading sessions | `ExpiryClock` |
| `forward_price_estimator.py` | Forward price and K0 from put-call parity (CBOE white paper step 1) | `ForwardPriceEstimator` |
| `futures_positioning.py` | Index-futures positioning: open interest regimes, top-20 broker nets, basis (plan 09) | `FuturesPositioning` |
| `gamma_exposure_calculator.py` | Dealer gamma exposure by strike and across spot levels (plan 09): hedging-flow map | `GammaExposureCalculator` |
| `margin_ladder_estimator.py` | Margin-financing liquidation ladder from per-stock margin data (plan 09) | `MarginLadderEstimator` |
| `option_chain_builder.py` | Tidy option chains from opt_basic + opt_daily, and per-term strike quote tables | `OptionChainBuilder` |
| `risk_free_curve.py` | Risk-free rate for any tenor from SHIBOR fixings (CALCULATION_DESIGN §2 step 2) | `RiskFreeCurve` |
| `term_interpolator.py` | Blend two term variances to the constant-maturity index (CBOE white paper step 4) | `TermInterpolator` |
| `term_selector.py` | Pick the near and next expiries around the 30-day target (CBOE rule, CALCULATION_DESIGN §2) | `TermSelector` |
| `trend_position.py` | Short-trend blend (share of windows up) with volatility sizing on any price series (plan 24 rule, used by plan 27) | `TrendPosition` |
| `variance_strip_calculator.py` | Per-term variance from the out-of-the-money option strip (CBOE white paper steps 2-3) | `VarianceStripCalculator` |
| `realized_vol_calculator.py` | annualised realised vol of price columns and trailing percentiles (plans 30, 31) | `RealizedVolCalculator` |
| `vix_calculator.py` | CBOE-method volatility index for one option underlying over a date range (plan 03) | `VixCalculator` |
| `index_futures_monitor.py` | 股指期货 basis and top-20 nets for the futures monitor, via FuturesPositioning (plan 15 ph7k) | `IndexFuturesMonitor` |
| `futures_broker_nets.py` | top-20 broker net share per commodity family (plan 15 ph7l) | `FuturesBrokerNets` |
| `futures_monitor_builder.py` | futures monitor: dominant price, curve shape, OI and value-chain spreads with 5-year percentiles and flags -> futures_monitor.json (plan 15 ph7i) | `FuturesMonitorBuilder` |
| `spread_reversion.py` | one-year z of a futures spread and the reversion flag for cost-anchored spreads (plan 15 ph7i, D-156) | `SpreadReversion` |
| `volatility_monitor_builder.py` | volatility monitor: US VIX from cboe_vix and A-share VIX via VixCalculator, latest, change, 1-year percentile, alerts -> volatility_monitor.json (plan 03 ph6) | `VolatilityMonitorBuilder` |
| `rates_fx_series_reader.py` | dated series of the rates and RMB monitor lines: 中债 curves, US yields, SHIBOR, FX mids, SAFE fixing, index earnings yield, combos (plan 34) | `RatesFxSeriesReader` |
| `rates_fx_monitor_builder.py` | rates and RMB monitor: level, changes, 5-year percentile, 1-year range, alerts, history, curve snapshot -> rates_fx_monitor.json (plan 34) | `RatesFxMonitorBuilder` |
| `earnings_event_builder.py` | earnings events at first disclosure: SUE, decile within the quarter, pre / reaction / post excess vs the equal-weight market (plan 35, D-172) | `EarningsEventBuilder` |
| `retail_gauge_matrices.py` | RetailGauge daily matrices; v3 / v4 path features over a quarter window and v5 multi-scale features (plan 21 ph2, D-142) | `RetailGaugeMatrices` |
| `holder_count_panel.py` | quarter-end shareholder counts: change labels and point-in-time lags (plan 21) | `HolderCountPanel` |
| `retail_gauge_feature_builder.py` | the 83 v5 RetailGauge features per (as_of, ts_code), PIT; derived/retail_gauge_features (plan 21 ph2) | `RetailGaugeFeatureBuilder` |
| `retail_gauge_model.py` | LightGBM rank model of the RetailGauge: fit, predict, save, load (plan 21 ph3) | `RetailGaugeModel` |
| `retail_gauge_nowcaster.py` | daily RetailGauge readings: retrain keys, walk-forward, calibration, avoid flag and D-167 streaks; derived/retail_gauge (plan 21 ph3) | `RetailGaugeNowcaster` |
| `retail_gauge_evaluator.py` | per-quarter IC, hit rates and avoid excess of the RetailGauge walk-forward (plan 21 ph3) | `RetailGaugeEvaluator` |
| `consensus_panel_builder.py` | analyst consensus FY1-FY3 per stock on given dates, PIT (plan 36, D-173) | `ConsensusPanelBuilder` |
| `macro_monitor_builder.py` | China macro monitor: CPI / PPI / PMI / M1-M2 / 社融 lines and derived spreads, 5-year percentile, new prints -> macro_monitor.json (plan 15 ph7h) | `MacroSeries`, `MacroMonitorBuilder` |
| `futures_curve.py` | futures term structure per contract family and material node from fut_daily + fut_basic: curve rows, front / most-held / 6m / 12m prices, slope from the most-held month (plan 16 ph2) | `CurveSummary`, `FuturesCurve` |
| `implied_expectations.py` | what the market cap already pays for: years of excess profit over three bases (normal PE, own median PE, pre-cycle cap; net and deducted profit) and reverse-DCF implied growth (plan 16 ph2, D-121) | `ImpliedExpectations` |
