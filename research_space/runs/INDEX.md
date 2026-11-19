# research_space/runs/

One folder per ad-hoc analysis, `YYYYMMDD_<topic>/` (topic snake_case, ≤ 4 words), logged in [`../RESEARCH_LOG.md`](../RESEARCH_LOG.md). Scripts write outputs to the lake (`meta/runs/research/<folder>/`), never here, and read private data only at runtime from `config/local.*`.

## Folders
| Folder | Purpose |
|---|---|
| [`20261117_all_industries/`](20261117_all_industries/INDEX.md) | loop over all SW L3 industries and their leaders; shortlist |
| [`20261117_more_sectors/`](20261117_more_sectors/INDEX.md) | second-round sector shortlist: express, MDI, coking coal, oil services |
| [`20261117_titanium/`](20261117_titanium/INDEX.md) | titanium dioxide producers panel (龙佰 add-on question) |
| [`20261117_property_services/`](20261117_property_services/INDEX.md) | A-share property managers and brokers panel |
| [`20261117_real_estate/`](20261117_real_estate/INDEX.md) | property chain: developers and building-material leaders' profit, valuation, consensus, chips |
| [`20261117_polyester_chain/`](20261117_polyester_chain/INDEX.md) | polyester chain deep dive: futures spreads, leaders' profit, valuation, consensus, chips |
| [`20261116_muyuan_hedge/`](20261116_muyuan_hedge/INDEX.md) | 牧原 hedging scale and value under the hog futures curve |
| [`20261116_cycle_screen/`](20261116_cycle_screen/INDEX.md) | cyclical industry cycle position (L2/L3) and US 10y yield sensitivity |
| [`20261114_reversal_variants/`](20261114_reversal_variants/INDEX.md) | 1-month reversal split by overnight / intraday and turnover |
| [`20261113_retail_gauge_returns/`](20261113_retail_gauge_returns/INDEX.md) | does the RetailGauge prediction predict returns |
| [`20261113_holder_count_returns/`](20261113_holder_count_returns/INDEX.md) | does the change in shareholder count predict returns |
| [`20261113_minute_factors/`](20261113_minute_factors/INDEX.md) | minute-data factors: overnight/intraday split, index intraday momentum, BaoStock 5-min stock factor pilot |
| [`20261113_duty_free_review/`](20261113_duty_free_review/INDEX.md) | 中国中免: fundamentals, chips, touch odds for 48/46/44, book what-if |
| [`20261113_buyback_yield/`](20261113_buyback_yield/INDEX.md) | buyback plan events and shareholder-yield IC (plan 23 ph4) |
| [`20261113_cost_break/`](20261113_cost_break/INDEX.md) | returns after a first close below the cyq cost_5pct chip floor |
| [`20261113_holder_buying/`](20261113_holder_buying/INDEX.md) | event study of holder increases / decreases |
| [`20261113_chip_migration/`](20261113_chip_migration/INDEX.md) | how a chip distribution migrates down (巨人网络) |
| [`20261113_margin_signals/`](20261113_margin_signals/INDEX.md) | predictive power of margin-trading signals |
| [`20261113_semiconductor/`](20261113_semiconductor/INDEX.md) | semiconductor sub-sector scan (uses the lithium run's script) |
| [`20261113_lithium_chain/`](20261113_lithium_chain/INDEX.md) | lithium battery chain scan; reusable `sector_scan.py` |
| [`20261113_dizal_review/`](20261113_dizal_review/INDEX.md) | 迪哲医药 review: AZ deal, cash and burn, exposures, chips; reusable `stock_extra.py` |
| [`20261113_proya_review/`](20261113_proya_review/INDEX.md) | 珀莱雅 review: expenses, DuPont, factor exposure, chips |
| [`20261113_niche_industries/`](20261113_niche_industries/INDEX.md) | little-covered SW L3 industries with improving fundamentals |
| [`20261113_glass_curve/`](20261113_glass_curve/INDEX.md) | glass / soda ash curve change and 中国巨石 vs glass futures correlation |
| [`20261113_margin_squeeze/`](20261113_margin_squeeze/INDEX.md) | SW L2 industries whose margins the 2026 upstream price surge squeezes most |
| [`20261114_tsmom/`](20261114_tsmom/INDEX.md) | Time-series momentum on China commodity futures (73 families, 2020–2026) |
| [`20261114_mean_reversion/`](20261114_mean_reversion/INDEX.md) | Variance ratios and spread half-lives: trend or mean reversion in China commodity futures |
| [`20261114_tsmom_single/`](20261114_tsmom_single/INDEX.md) | Time-series momentum asset by asset: each futures family and each A-share stock |
| [`20261114_tsmom_robust/`](20261114_tsmom_robust/INDEX.md) | TSMOM and spread reversion: parameter sensitivity, costs, and indices / index and bond futures / ETFs |
| [`20261114_vix_vs_trend/`](20261114_vix_vs_trend/INDEX.md) | Fear (volatility) high vs the short-trend blend on A-share indices: overlap, forward returns, combined rules |
| [`20261114_cta_portfolio/`](20261114_cta_portfolio/INDEX.md) | Equal-risk book of commodity trend, spread reversion, index trend and bond trend sleeves |
| [`20261114_cta_horizon_etf/`](20261114_cta_horizon_etf/INDEX.md) | Lookback per sleeve / per product (walk-forward) and an ETF-only long-flat version of the book |
| [`20261114_etf_universe/`](20261114_etf_universe/INDEX.md) | Buyable ETFs by asset class, liquidity and premium |
| [`20261114_black_litterman/`](20261114_black_litterman/INDEX.md) | Black-Litterman inputs for the liquid ETF book (parked) |
| [`20261114_gold_us_rates/`](20261114_gold_us_rates/INDEX.md) | Gold vs US 10-year nominal and real yields (correlation, beta, now) |
| [`20261114_macro_quadrants/`](20261114_macro_quadrants/INDEX.md) | Plan 27 book and asset groups by China PMI x PPI / CPI quadrant |
| [`20261114_etf_tuning/`](20261114_etf_tuning/INDEX.md) | Walk-forward Optuna tuning of the plan 27 book vs fixed parameters |
| [`20261115_cgo_reproduce/`](20261115_cgo_reproduce/INDEX.md) | Reproduce Tushare cyq_perf with a turnover-decay chip model (plan 29 ph1a) |
| [`20261115_cgo_ic/`](20261115_cgo_ic/INDEX.md) | CGO / winner-rate rank IC, raw and net of reversal, momentum, turnover, size (plan 29 ph1b) |
| [`20261113_metal_curves/`](20261113_metal_curves/INDEX.md) | SHFE copper, aluminium, alumina, tin, nickel curve shape and spread percentiles |
| [`20261113_opportunity_list/`](20261113_opportunity_list/INDEX.md) | plan 21 five rules applied by hand on 2026-11-12 data |
| [`20261113_theme_screen/`](20261113_theme_screen/INDEX.md) | the five rules on grid, gas turbine, rare earth, minor metals and franchise-licence names |
| [`20261113_washout_study/`](20261113_washout_study/INDEX.md) | event study: which post-crash chip signs predict 60-day excess returns |
| [`20261115_retail_gauge_q4_table/`](20261115_retail_gauge_q4_table/INDEX.md) | per-company 2026-12-31 RetailGauge v5 holder-count forecast table |
| [`20261115_clean_chips/`](20261115_clean_chips/INDEX.md) | 筹码干净 screen: retail leaving, concentrated cost band, large-order inflow |
| [`20261115_longxin/`](20261115_longxin/INDEX.md) | 隆鑫通用 chip / holder / valuation dossier |
| [`20261115_watch_conditions_bt/`](20261115_watch_conditions_bt/INDEX.md) | backtest of the watchlist buy conditions (RetailGauge, large-order weeks) |
| [`20261115_gauge_intraquarter/`](20261115_gauge_intraquarter/INDEX.md) | RetailGauge stability inside a quarter (day 15 / 30 / 45 vs quarter end) and mid-quarter return power |
| [`20261115_jianghe/`](20261115_jianghe/INDEX.md) | 江河集团 601886.SH deep dive |
| [`20261115_jinshiyuan/`](20261115_jinshiyuan/INDEX.md) | 今世缘 603369.SH deep dive |
| [`20261115_yunnan_germanium/`](20261115_yunnan_germanium/INDEX.md) | 云南锗业 002428.SZ quick look |
| [`20261115_ynge/`](20261115_ynge/INDEX.md) | 云南锗业 002428.SZ quick review |
| [`20261116_optical_modules/`](20261116_optical_modules/INDEX.md) | 中际旭创 / 新易盛 chips and valuation |
| [`20261116_reversal_perf/`](20261116_reversal_perf/INDEX.md) | reversal_1m vs reversal_intraday_1m: full history, 2026, live month |
| [`20261116_gauge_drivers/`](20261116_gauge_drivers/INDEX.md) | RetailGauge v5 feature drivers (SHAP) |
| [`20261116_holder_persistence/`](20261116_holder_persistence/INDEX.md) | does last quarter's holder change carry into this quarter |
| [`20261116_intraday_15m_turns/`](20261116_intraday_15m_turns/INDEX.md) | 15-minute turning signals on 6 indices |
| [`20261116_vix_divergence/`](20261116_vix_divergence/INDEX.md) | small-cap vs large-cap VIX gap |
| [`20261116_etf_close_15m/`](20261116_etf_close_15m/INDEX.md) | last-15-minute ETF buying and next-day effect |
| [`20261116_market_regime/`](20261116_market_regime/INDEX.md) | trend vs range, drawdowns, long-short pair |
| [`20261116_gauge_filter/`](20261116_gauge_filter/INDEX.md) | does smoothing the mid-quarter RetailGauge help |
| [`20261117_photoresist/`](20261117_photoresist/INDEX.md) | 光刻胶 sector: valuation, growth, gauge, flows |
| [`20261117_gauge_daily/`](20261117_gauge_daily/INDEX.md) | RetailGauge every 3rd day: do short filters help |
| [`20261118_shekou_bollinger/`](20261118_shekou_bollinger/INDEX.md) | 招商蛇口: Bollinger band mean reversion test |
| [`20261118_priced_in/`](20261118_priced_in/INDEX.md) | Earnings priced in before disclosure? SUE event study 2019–2026, valuation split |
| [`20261118_tsmom_now/`](20261118_tsmom_now/INDEX.md) | Current ETF trend scan: which liquid ETFs are in up / down trends (plan-24 blend) |
| [`20261119_margin_share/`](20261119_margin_share/INDEX.md) | 融资余额 / 流通市值 since 2019 and its level at 中证1000 bottoms |
| [`20261119_margin_drawdown/`](20261119_margin_drawdown/INDEX.md) | 融资余额 去杠杆 episodes since 2014 and the smoothed pace of the current one (plan 30 ph7) |
| [`20261119_volume_selloff/`](20261119_volume_selloff/INDEX.md) | 中证1000 ≤ −3% days on ≥ 1.3× 20-day turnover: forward returns (plan 30 ph5 trigger) |
| [`20261118_linear_pricing_gap/`](20261118_linear_pricing_gap/INDEX.md) | Linear-pricing gap (market cap vs consensus value with fading growth) as a factor |
| [`20261118_revision_slowdown/`](20261118_revision_slowdown/INDEX.md) | Consensus upgrade slowdown as a signal (FY2 revisions) |
| [`20261118_turnover_vs_gauge/`](20261118_turnover_vs_gauge/INDEX.md) | RetailGauge vs turnover_60d overlap; the score with the gauge added |
| [`20261118_gauge_risk_style/`](20261118_gauge_risk_style/INDEX.md) | plan 21 ph6: RetailGauge as a risk style (retail_crowding) beside cne5_v4 and as a score input |
| [`20261118_marginal_trader/`](20261118_marginal_trader/INDEX.md) | who is the marginal trader: margin financing, order-size net flow, turnover vs national-team ETFs, 2026-08..11 |
| [`20261119_breadth/`](20261119_breadth/INDEX.md) | breadth and turnover of the decline, re-run with 11-19 data |
| [`20261119_northbound/`](20261119_northbound/INDEX.md) | northbound quarterly active flow from hk_hold (quarter-end disclosure since 2024-08), 沪深300 / 中证1000 split |
| [`20261118_score_vs_barra/`](20261118_score_vs_barra/INDEX.md) | Composite score vs Barra styles: style share and the residual's power |
| [`20261118_score_card/`](20261118_score_card/INDEX.md) | Score card of the user's indicators for holdings / watchlist / any code |
| [`20261118_analyst_coverage/`](20261118_analyst_coverage/INDEX.md) | Coverage of the analyst descriptors for the risk model (plan 37) |
| [`20261118_risk_v4_gate/`](20261118_risk_v4_gate/INDEX.md) | Plan 37 gate: cne5_v4 vs cne5_v3_dy (D-180) |
| [`20261118_retail_gauge_port/`](20261118_retail_gauge_port/INDEX.md) | Plan 21: production RetailGauge vs the v5 prototype |
