# Class Registry

Single source of truth for every class, base class, exception, schema and allowed standalone
function in `quant_cn`. Rules: `plans/standards/CODING_STANDARD.md` §5. Maintained with the `registry` skill.

**Before writing anything new:** search this file and `grep` the codebase. Extend or subclass a match
instead of writing a duplicate.
**After creating or changing a class:** update its index row *and* its detail block in the same
change set, and add the new caller to the `Used by` of every class or method it calls.

Layers: 1 core, 2 lake, 3 data_loading, 4 pipeline/statistic, 5 back_testing/portfolio, 6 research_space.

---

## A. Index (one row per class; details in section B)

| Class | Module | Layer | Base | Purpose (one line) | Public methods (count) | Used by | Tests | Added |
|---|---|---|---|---|---|---|---|---|
| `Black76Model` | `quant_cn.calculation.black76_model` | 4 | none | Price European options on a forward (Black-76, discounted at the continuous rate) and invert a price to implied volatility | 3 | `research_space/notebooks/20260927_vix_calculation.ipynb`, `calculation.GammaExposureCalculator` | `tests/calculation/test_black76_model.py` (TC-BM-001..004) | 2026-09-27 |
| `ExpiryClock` | `quant_cn.calculation.expiry_clock` | 4 | none | Convert (trade_date, expiry) to the time units the VIX formulas use | 3 | `calculation.VixCalculator` | `tests/calculation/test_expiry_clock.py` (TC-EC-001..003) | 2026-09-27 |
| `ForwardPriceEstimator` | `quant_cn.calculation.forward_price_estimator` | 4 | none | Per term: F = K* + e^{RT}(C - P) at the strike K* with the smallest /C - P/, and K0 the largest strike at or below F. | 1 | `calculation.VixCalculator`, `calculation.GammaExposureCalculator` | `tests/calculation/test_forward_price_estimator.py` (TC-FPE-001..002) | 2026-09-27 |
| `FuturesPositioning` | `quant_cn.calculation.futures_positioning` | 4 | none | Per trading day for one CFFEX index-futures product (IF, IH, IC, IM): total open interest and its change, the main contract's price change, the OI x price regime (new shorts, long liquidation, short covering, new longs), top-20 broker gross long / short / net summed over the product's contracts, and the main contract's basis to the index, raw and annualised to its third-Friday expiry | 3 | `research_space/notebooks/20260929_positioning_flows.ipynb` | `tests/calculation/test_futures_positioning.py` (TC-FP-001..004) | 2026-09-27 |
| `GammaExposureCalculator` | `quant_cn.calculation.gamma_exposure_calculator` | 4 | none | Estimate the gamma dealers carry per option and strike, in CNY of underlying they must trade for a 1% move: GEX = sign * Gamma_F * OI * multiplier * F^2 * 1%, with Gamma from Black-76 at each option's own implied volatility | 3 | `research_space/notebooks/20260929_positioning_flows.ipynb` | `tests/calculation/test_gamma_exposure_calculator.py` (TC-GEC-001..004) | 2026-09-27 |
| `MarginLadderEstimator` | `quant_cn.calculation.margin_ladder_estimator` | 4 | none | Estimate where margin-financed positions face forced selling | 2 | `research_space/notebooks/20260929_positioning_flows.ipynb` | `tests/calculation/test_margin_ladder_estimator.py` (TC-MLE-001..004) | 2026-09-27 |
| `OptionChainBuilder` | `quant_cn.calculation.option_chain_builder` | 4 | none | Join the option master (opt_basic) with daily prices (opt_daily) into one tidy chain per underlying, and turn one expiry of it into a strike x (call, put) quote table. | 2 | `calculation.VixCalculator`, `calculation.GammaExposureCalculator` | `tests/calculation/test_option_chain_builder.py` (TC-OCB-001..003) | 2026-09-27 |
| `RiskFreeCurve` | `quant_cn.calculation.risk_free_curve` | 4 | none | Continuously compounded risk-free rate for a tenor in calendar days, from the latest SHIBOR fixing on or before the date, linearly interpolated between tenors and clamped outside them. | 1 | `calculation.VixCalculator`, `calculation.GammaExposureCalculator` | `tests/calculation/test_risk_free_curve.py` (TC-RFC-001..003) | 2026-09-27 |
| `TermInterpolator` | `quant_cn.calculation.term_interpolator` | 4 | none | VIX = 100 * sqrt([T1 s1^2 (N2 - Nt)/(N2 - N1) + T2 s2^2 (Nt - N1)/(N2 - N1)] * Ny / Nt), with N in the clock's unit (minutes or sessions) and Ny one year in that unit. | 1 | `calculation.VixCalculator` | `tests/calculation/test_term_interpolator.py` (TC-TI-001..002) | 2026-09-27 |
| `TermSelector` | `quant_cn.calculation.term_selector` | 4 | none | Choose the two nearest expiries with at least `min_days` calendar days to expiry. | 1 | `calculation.VixCalculator` | `tests/calculation/test_term_selector.py` (TC-TS-001..002) | 2026-09-27 |
| `VarianceStripCalculator` | `quant_cn.calculation.variance_strip_calculator` | 4 | none | sigma^2 = (2/T) sum(dK/K^2 e^{RT} Q(K)) - (1/T)(F/K0 - 1)^2 over puts below K0, calls above K0 and the call/put average at K0 | 1 | `calculation.VixCalculator` | `tests/calculation/test_variance_strip_calculator.py` (TC-VSC-001..003) | 2026-09-27 |
| `VixCalculator` | `quant_cn.calculation.vix_calculator` | 4 | none | Orchestrate the white-paper steps per trading day: select near/next terms, rate per term, forward and K0, variance strip, interpolation on the chosen clock | 1 | `research_space/notebooks/20260927_vix_calculation.ipynb` | `tests/calculation/test_vix_calculator.py` (TC-VC-001..003) | 2026-09-27 |
| `RealizedVolCalculator` | `quant_cn.calculation.realized_vol_calculator` | 4 | none | Annualised realised vol of close columns (log-return std × √252 × 100) and the trailing percentile of a series; extracted from SmallCapWatchBuilder (plans 30, 31). | 2 | `portfolio.SmallCapWatchBuilder`, `portfolio.SectorMonitorBuilder`, `cli.ReportCommands` | `tests/calculation/test_realized_vol_calculator.py` (TC-RVC-001..002) | 2026-11-17 |
| `CompanyCyclePanel` | `quant_cn.calculation.company_cycle_panel` | 4 | none | Place every company's latest quarter in its own cycle, point in time: single quarter and TTM, YoY and QoQ, deducted profit, 10-year median profit and max margin, margin_peak (plan 16 ph1, D-121) | 4 | `portfolio.OpportunityScreen`, `cli.GaugeCommands` | `tests/calculation/test_company_cycle_panel.py` (TC-CCP-001..010) | 2026-11-09 |
| `ForecastTracker` | `quant_cn.calculation.forecast_tracker` | 4 | none | Score every earnings preview (all revisions) against the first reported parent net profit: range in CNY, in / above / below / pending / no_range / after_actual, position, surprise, revision path, days_after_end / ex_ante; per-company hit rate and bias over window_years, overall and for previews published before the period end (plan 18 ph1, D-124) | 3 | (none yet) | `tests/calculation/test_forecast_tracker.py` (TC-FT-001..010) | 2026-11-11 |
| `QuantCnCli` | `quant_cn.cli` | 8 | none | `python -m quant_cn.cli <command>`: doctor, download, compact, curate, rebuild, backup, project-catalog, query | 1 | `Makefile targets doctor, download, compact, lake-rebuild, lake-backup` | `tests/test_cli.py` (TC-QCC-001..007) | 2026-09-27 |
| `ResearchCommands` | `quant_cn.cli` | 8 | none | The research-side CLI commands, kept apart so QuantCnCli stays within its size limit: `release-lags` (D-086), `evaluate` (factor campaign reports and trial log, plan 04 phase 5), `risk-model` (D-127), `watchlist` (D-120), `etf-proxy` (D-126), `factor-monitor` and `holdings-risk` (D-132) | 1 | `cli.QuantCnCli` | `tests/test_cli.py` (TC-QCC-008..009, 011..014) | 2026-09-27 |
| `BaseApiClient` | `quant_cn.core.base_api_client` | 1 | ABC | Abstract vendor client: one logical query returns all pages as one DataFrame. | 1 | `data_loading.TushareClient`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher`, `data_loading.AkshareClient`, `data_loading.BaostockClient`, `data_loading.ManualSeriesClient` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `BaseFetchLog` | `quant_cn.core.base_fetch_log` | 1 | ABC | Abstract record of which (dataset, key) pairs are fully downloaded. | 5 | `lake.FetchLog`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher` | `tests/lake/test_fetch_log.py` (TC-FL-001..003) | 2026-09-27 |
| `BaseFetcher` | `quant_cn.core.base_fetcher` | 1 | ABC | Download one dataset as a sequence of keys | 5 | `data_loading.SingleCallFetcher`, `data_loading.EnumFetcher`, `data_loading.DateSweepFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.FetcherFactory.build`, `pipeline.FetchStep`, `data_loading.DateWindowFetcher` | `tests/core/test_base_fetcher.py` (TC-BF-001..007) | 2026-09-27 |
| `BaseRunLog` | `quant_cn.core.base_run_log` | 1 | ABC | Abstract append-only log of runs and per-key events | 3 | `lake.RunLog`, `core.BaseFetcher.run`, `pipeline.LocalRunner`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.PrefectRunner`, `data_loading.DateWindowFetcher` | `tests/lake/test_run_log.py` (TC-RL-001..001) | 2026-09-27 |
| `BaseStep` | `quant_cn.core.base_step` | 1 | ABC | Abstract unit of pipeline work: list its units, then run and report. | 3 | `pipeline.FetchStep`, `pipeline.BaseRunner.run`, `pipeline.LocalRunner.run`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `pipeline.PrefectRunner`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `BaseStore` | `quant_cn.core.base_store` | 1 | ABC | Abstract sink for raw fetch results and curated partitions. | 2 | `lake.ParquetWriter`, `core.BaseFetcher`, `lake.Compactor`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `Clock` | `quant_cn.core.clock` | 1 | none | The single source of wall time, monotonic time and sleeping | 4 | `data_loading.TushareClient`, `core.BaseFetcher.run`, `lake.RunLog`, `lake.Compactor.rebuild`, `pipeline.DownloadPipeline`, `cli.QuantCnCli`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.FetcherFactory`, `data_loading.PeriodSweepFetcher`, `lake.ProjectCatalog`, `cli.ServiceBuilder`, `data_loading.DateWindowFetcher`, `data_loading.AkshareClient`, `data_loading.BaostockClient`, `lake.RebuildAudit`, `cli.ResearchCommands`, `cli.DocumentCommands`, `data_loading.DocumentDownloader`, `data_loading.RequestPacer`, `data_loading.AppStoreClient` | `tests/core/test_clock.py` (TC-CL-001..002) | 2026-09-27 |
| `LakeConfig` | `quant_cn.core.config` | 1 | BaseModel | Where the lake lives and whether it may sit inside the repository. | 0 | `core.Config` | `tests/core/test_config.py` (TC-C-001..001) | 2026-09-27 |
| `TushareConfig` | `quant_cn.core.config` | 1 | BaseModel | Tushare endpoint, paging, retry and rate-limit settings | 0 | `core.Config`, `data_loading.TushareClient` | `tests/core/test_config.py` (TC-C-002..002) | 2026-09-27 |
| `DownloadConfig` | `quant_cn.core.config` | 1 | BaseModel | Which datasets to download, in what order, and from which start dates (D-015b). | 0 | `core.Config` | `tests/core/test_config.py` (TC-C-004..004) | 2026-09-27 |
| `FactorSpec` | `quant_cn.core.config` | 1 | BaseModel | One factor of config/factors.yaml: its name, implementing class and parameters. | 0 | `core.Config`, `factor.FactorFactory` | `tests/core/test_config.py` (TC-C-012..012) | 2026-09-27 |
| `CampaignConfig` | `quant_cn.core.config` | 1 | BaseModel | Settings of one factor campaign (config/factors.yaml `campaign`, plan 04 phase 5). | 0 | `core.Config` | `tests/core/test_config.py` (TC-C-013..013) | 2026-09-27 |
| `UniverseConfig` | `quant_cn.core.config` | 1 | BaseModel | Rules of the tradeable universe per session (FACTOR_TESTING_DESIGN §11, D-054). | 0 | `core.Config`, `pipeline.UniverseStep` | `tests/core/test_config.py` (TC-C-011..011) | 2026-09-27 |
| `FuturesCategory` | `quant_cn.core.config` | 1 | BaseModel | One member-category label that `fut_holding` lists among real brokers (D-079). | 0 | `core.Config`, `lake.DerivedViews` | `tests/core/test_config.py` (TC-C-009..009) | 2026-09-27 |
| `TickerAlias` | `quant_cn.core.config` | 1 | BaseModel | One retired code and the code its company trades on afterwards (D-053, D-089). | 0 | `core.Config`, `lake.TickerAliasMap`, `lake.DerivedViews` | `tests/core/test_config.py` (TC-C-010..010) | 2026-09-27 |
| `Config` | `quant_cn.core.config` | 1 | BaseModel | The typed configuration injected everywhere: YAML defaults, machine overrides, environment. | 3 | `cli.QuantCnCli`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`, `cli.ServiceBuilder`, `cli.ResearchCommands`, `cli.DocumentCommands`, `portfolio.WatchlistBuilder`, `portfolio.EtfProxyBuilder`, `cli.GaugeCommands` | `tests/core/test_config.py` (TC-C-001..020) | 2026-09-27 |
| `WatchlistEntry` | `quant_cn.core.config` | 1 | BaseModel | One stock the user watches, the price range at which they would buy it and its structured conditions (k of n) (D-120, plan 15 ph7f). | 0 | `core.Config`, `portfolio.WatchlistBuilder` | `tests/core/test_config.py` (TC-C-015) | 2026-11-08 |
| `Condition` | `quant_cn.core.condition` | 1 | BaseModel | One structured buy / falsifier condition `<metric> <op> <value>` of a kind (price, flow, chip, retail, heat, statement, series, manual); metric checked against the kind (plan 15 ph7f). | 1 | `core.WatchlistEntry`, `core.PositionNote`, `portfolio.ConditionEvaluator` | `tests/core/test_condition.py` (TC-CND-001..003) | 2026-11-13 |
| `PositionNote` | `quant_cn.core.positions_book` | 1 | BaseModel | Why a position is held and what would make the user act: thesis, falsifier, stop, target, action, watch, last review, conditions (plan 15 ph7f). | 0 | `core.PositionsBook`, `portfolio.PositionReviewer` | `tests/portfolio/test_holdings_risk_builder.py` (TC-PB-003) | 2026-11-13 |
| `BookRules` | `quant_cn.core.positions_book` | 1 | BaseModel | Position-size and process rules: weight cap with exceptions, before-buy checklist, review interval (plan 15 ph7f). | 0 | `core.PositionsBook` | `tests/portfolio/test_holdings_risk_builder.py` (TC-PB-003) | 2026-11-13 |
| `WatchlistSettings` | `quant_cn.core.config` | 1 | BaseModel | Thresholds and windows of the watchlist page (base.yaml `watchlist`, D-120). | 0 | `core.Config`, `portfolio.WatchlistBuilder` | `tests/core/test_config.py` (TC-C-016) | 2026-11-08 |
| `EtfProxyIndex` | `quant_cn.core.etf_proxy_settings` | 1 | BaseModel | One broad index whose ETFs are summed into the national-team proxy: name, benchmark regex on fund_basic.benchmark, optional exclude regex, reference ETF (D-126). | 0 | `core.EtfProxySettings`, `core.EtfProxyStyle` | `tests/core/test_config.py` (TC-C-020) | 2026-11-11 |
| `EtfProxyStyle` | `quant_cn.core.etf_proxy_settings` | 1 | EtfProxyIndex | A style ETF group (银行, 红利) watched for crowding, with a key for its condition metric "<key>_etf_z" (plan 15 ph7g). | 0 | `core.EtfProxySettings` | `tests/core/test_config.py` (TC-C-021) | 2026-11-13 |
| `EtfProxySettings` | `quant_cn.core.etf_proxy_settings` | 1 | BaseModel | Which ETFs make up the national-team proxy (indices, core list, member name / benchmark rules) and its start, recent window and per-index rhythm weeks, the 近3月 percentile window and matrix weeks (ph7o), plus style groups and their crowding windows (config/etf_proxies.yaml, D-126, ph7g). | 0 | `core.Config`, `portfolio.EtfProxyBuilder`, `portfolio.EtfFlowCalculator`, `portfolio.EtfStyleHeat` | `tests/core/test_config.py` (TC-C-020..021) | 2026-11-18 |
| `LabelSource` | `quant_cn.core.label_source` | 1 | BaseModel | One existing label file (jsonl or parse parquet) to import into the parquet label store: its label set, period, document key, date field, anchor set, taxonomy version and an optional exclude list of keys; `read_all` loads config/label_sources.yaml (plan 28, D-161). | 2 | `cli.DocumentCommands`, `industry_graph.LegacyLabelImporter` | `tests/core/test_label_source.py` (TC-LSR-001..004) | 2026-11-15 |
| `MailSettings` | `quant_cn.core.mail_sender` | 1 | BaseModel | SMTP host / port, sender, recipients and the env variable holding the app password, from git-ignored config/local.mail.yaml (plan 15 ph7e). | 1 | `core.MailSender`, `cli.ReportCommands` | `tests/core/test_mail_sender.py` (TC-MS-001..001) | 2026-11-13 |
| `FuturesFamily` | `quant_cn.core.futures_monitor_settings` | 1 | BaseModel | One watched contract family: "<CODE>.<suffix>", name, group (plan 15 ph7i). | 0 | `core.FuturesMonitorSettings` | `tests/core/test_futures_monitor_settings.py` (TC-FMS-001) | 2026-11-13 |
| `FuturesSpreadLeg` | `quant_cn.core.futures_monitor_settings` | 1 | BaseModel | One spread leg: family and coefficient on the dominant price. | 0 | `core.FuturesSpread` | `tests/core/test_futures_monitor_settings.py` (TC-FMS-001) | 2026-11-13 |
| `FuturesSpread` | `quant_cn.core.futures_monitor_settings` | 1 | BaseModel | A value-chain spread: sum of coef x price, or a two-leg ratio. | 0 | `core.FuturesMonitorSettings` | `tests/core/test_futures_monitor_settings.py` (TC-FMS-002..003) | 2026-11-13 |
| `IndexFuturesProduct` | `quant_cn.core.futures_monitor_settings` | 1 | BaseModel | One CFFEX index-futures product and its index (plan 15 ph7k). | 0 | `core.FuturesMonitorSettings` | `tests/core/test_futures_monitor_settings.py` (TC-FMS-001) | 2026-11-13 |
| `FuturesMonitorSettings` | `quant_cn.core.futures_monitor_settings` | 1 | BaseModel | Families, spreads, OI floor and flag bounds of the futures monitor, from config/futures_monitor.yaml (plan 15 ph7i, D-145). | 1 | `calculation.FuturesMonitorBuilder`, `calculation.IndexFuturesMonitor`, `calculation.FuturesBrokerNets`, `cli.ReportCommands` | `tests/core/test_futures_monitor_settings.py` (TC-FMS-001..003) | 2026-11-13 |
| `EtfCtaGroup` | `quant_cn.core.etf_cta_settings` | 1 | BaseModel | One risk group of the ETF CTA book: name and ETFs with inner capital weights (plan 27). | 0 | `core.EtfCtaSettings` | `tests/core/test_etf_cta_settings.py` (TC-ECS-001) | 2026-11-14 |
| `EtfCtaPremium` | `quant_cn.core.etf_cta_settings` | 1 | BaseModel | Premium guard for QDII / LOF lines: codes, buy_below / high / switch thresholds, lower-premium alternative (plan 27). | 0 | `core.EtfCtaSettings` | `tests/core/test_etf_cta_settings.py` (TC-ECS-002) | 2026-11-14 |
| `EtfCtaSettings` | `quant_cn.core.etf_cta_settings` | 1 | BaseModel | The ETF CTA book from config/etf_cta.yaml: equal-risk groups at risk_share, bond sleeve at bond_share with switch, timed A股 ETFs, windows, band, costs, record dates, premium guard, view subsets and views file (plan 27, D-160, D-163). | 3 | `portfolio.EtfCtaBook`, `portfolio.EtfCtaWeights`, `cli.ReportCommands`, `core.EtfCtaViews`, `portfolio.EtfCtaViewTilt` | `tests/core/test_etf_cta_settings.py` (TC-ECS-001..004) | 2026-11-14 |
| `EtfCtaWhen` | `quant_cn.core.etf_cta_views` | 1 | BaseModel | Price condition of a view: ETF close below / above a level, latches once met (plan 27 ph5, D-163). | 0 | `core.EtfCtaView` | `tests/core/test_etf_cta_views.py` (TC-ECV-002) | 2026-11-14 |
| `EtfCtaView` | `quant_cn.core.etf_cta_views` | 1 | BaseModel | One user view: scale a set x 0.5–2 or move ≤ 5 points between sets; reason, start, expiry ≤ 92 days, optional condition (D-163). | 1 | `core.EtfCtaViews`, `portfolio.EtfCtaViewTilt` | `tests/core/test_etf_cta_views.py` (TC-ECV-001..002) | 2026-11-14 |
| `EtfCtaViews` | `quant_cn.core.etf_cta_views` | 1 | BaseModel | All user views plus optional A股 floor, from the git-ignored views_file; missing file = none; names checked (D-163). | 1 | `portfolio.EtfCtaViewTilt`, `portfolio.EtfCtaBook`, `cli.ReportCommands` | `tests/core/test_etf_cta_views.py` (TC-ECV-001..003) | 2026-11-14 |
| `VolatilityLine` | `quant_cn.core.volatility_monitor_settings` | 1 | BaseModel | One monitored volatility index: key, name, group, kind (cboe / option), code and level / jump / percentile alerts (plan 03 ph6). | 0 | `core.VolatilityMonitorSettings`, `calculation.VolatilityMonitorBuilder` | `tests/core/test_volatility_monitor_settings.py` (TC-VMS-001) | 2026-11-13 |
| `VolatilityMonitorSettings` | `quant_cn.core.volatility_monitor_settings` | 1 | BaseModel | Lines, percentile window, min_obs and TermSelector min_days of the volatility monitor, from config/volatility_monitor.yaml (plan 03 ph6, D-152). | 1 | `calculation.VolatilityMonitorBuilder`, `cli.ReportCommands` | `tests/core/test_volatility_monitor_settings.py` (TC-VMS-001) | 2026-11-13 |
| `RatesFxLine` | `quant_cn.core.rates_fx_monitor_settings` | 1 | BaseModel | One monitored rates / FX series: key, name, group, source kind (curve, us, shibor, fx, fixing, equity_ep, combo) and its parameters, unit (yield / bp / rate / gap), show, alerts (week_move, week_widen, extreme, pct_above, abs_above, below, above) (plan 34). | 0 | `core.RatesFxMonitorSettings`, `calculation.RatesFxSeriesReader`, `calculation.RatesFxMonitorBuilder` | `tests/core/test_rates_fx_monitor_settings.py` (TC-RFS-001) | 2026-11-18 |
| `RatesFxMonitorSettings` | `quant_cn.core.rates_fx_monitor_settings` | 1 | BaseModel | Lines (unique keys, combos name earlier lines), percentile years, min_obs, history start, staleness and the curve snapshot of the rates and RMB monitor, from config/rates_fx_monitor.yaml (plan 34, D-171). | 1 | `calculation.RatesFxSeriesReader`, `calculation.RatesFxMonitorBuilder`, `cli.ReportCommands` | `tests/core/test_rates_fx_monitor_settings.py` (TC-RFS-001) | 2026-11-18 |
| `SectorEarningsSignalSettings` | `quant_cn.core.sector_earnings_signal_settings` | 1 | BaseModel | Windows and thresholds of the earnings events and the 财报季信号 (start, SUE window, top decile, min events, pre / react / back / fwd windows, report share, pre_min, react_max, rally_min, excluded exchanges) from config/sector_earnings_signal.yaml (plan 35, D-172). | 1 | `calculation.EarningsEventBuilder`, `portfolio.SectorEarningsSignalBuilder`, `cli.AppServiceBuilder` | `tests/core/test_sector_earnings_signal_settings.py` (TC-SES-001) | 2026-11-18 |
| `RetailGaugeSettings` | `quant_cn.core.retail_gauge_settings` | 1 | BaseModel | Feature windows, LightGBM params, label clip, training minimum, avoid / leaving / inflow thresholds, D-167 streak rule, retrain months and model version of the RetailGauge from config/retail_gauge.yaml (plan 21). | 1 | `calculation.RetailGaugeMatrices`, `calculation.RetailGaugeFeatureBuilder`, `calculation.RetailGaugeModel`, `calculation.RetailGaugeNowcaster`, `calculation.RetailGaugeEvaluator`, `cli.GaugeCommands` | `tests/core/test_retail_gauge_settings.py` (TC-RGS-001) | 2026-11-18 |
| `WatchIndex` | `quant_cn.core.small_cap_watch_settings` | 1 | BaseModel | One index of the small-cap watch: ts_code in curated.index_daily and its name (plan 30). | 0 | `core.SmallCapWatchSettings` | `tests/core/test_small_cap_watch_settings.py` (TC-SCS-001) | 2026-11-17 |
| `WatchEtf` | `quant_cn.core.small_cap_watch_settings` | 1 | BaseModel | One broad ETF in the small-cap watch flow total; `own_row` also gives it its own row (plan 30). | 0 | `core.SmallCapWatchSettings` | `tests/core/test_small_cap_watch_settings.py` (TC-SCS-001) | 2026-11-17 |
| `SmallCapWatchSettings` | `quant_cn.core.small_cap_watch_settings` | 1 | BaseModel | Indices, user levels (git-ignored local file overrides), panic / breadth / vol / gap triggers, near rules, windows and ETFs of the 小盘观察, plus the 融资余额 企稳 drawdown trigger and windows (ph4), from config/smallcap_watch.yaml (plan 30). | 1 | `portfolio.SmallCapWatchBuilder`, `portfolio.SmallCapWatchRows`, `cli.ReportCommands` | `tests/core/test_small_cap_watch_settings.py` (TC-SCS-001..003) | 2026-11-18 |
| `MonitoredSecurity` | `quant_cn.core.sector_monitor_settings` | 1 | BaseModel | One company or index of a monitored sector: ts_code and name (plan 31). | 0 | `core.MonitoredSector` | `tests/core/test_sector_monitor_settings.py` (TC-SMS-001) | 2026-11-17 |
| `MonitoredSector` | `quant_cn.core.sector_monitor_settings` | 1 | BaseModel | One sector of the monitor: key, name, Shenwan index, companies, chart metric keys (plan 31). | 0 | `core.SectorMonitorSettings`, `portfolio.SectorMonitorBuilder` | `tests/core/test_sector_monitor_settings.py` (TC-SMS-002) | 2026-11-17 |
| `AppPublisher` | `quant_cn.core.app_publisher_settings` | 1 | BaseModel | One App Store seller account (artist_id) → company and listed code (plan 19 ph2). | 0 | `core.AppPublisherSettings` | `tests/core/test_app_publisher_settings.py` (TC-APS-001) | 2026-11-17 |
| `AppPublisherSettings` | `quant_cn.core.app_publisher_settings` | 1 | BaseModel | config/app_publishers.yaml: App Store accounts → company / code; unique artist ids (plan 19 ph2, D-137 u1). | 3 | `portfolio.AppRankReader`, `cli.AppServiceBuilder` | `tests/core/test_app_publisher_settings.py` (TC-APS-001..002) | 2026-11-17 |
| `SectorMonitorSettings` | `quant_cn.core.sector_monitor_settings` | 1 | BaseModel | config/sector_monitors.yaml: 70-city tier lists, realised-vol windows and percentile window, chart lengths, App Store home market and top length, sectors (plan 31, D-168). | 1 | `portfolio.SectorMonitorBuilder`, `portfolio.SectorMetricReader`, `cli.AppServiceBuilder` | `tests/core/test_sector_monitor_settings.py` (TC-SMS-001..002) | 2026-11-17 |
| `MailContent` | `quant_cn.core.mail_sender` | 1 | none | One rendered e-mail: subject, HTML, plain text. | 0 | `core.MailSender`, `visualization.MonitorReportRenderer`, `visualization.OpportunityReportRenderer`, `visualization.MorningReportBuilder` | `tests/core/test_mail_sender.py` (TC-MSN-001) | 2026-11-13 |
| `MailSender` | `quant_cn.core.mail_sender` | 1 | none | Build a multipart message and send it over SMTP with STARTTLS and login; password only from the environment, checked before connecting (plan 15 ph7e). | 2 | `visualization.MorningReportBuilder`, `cli.ReportCommands` | `tests/core/test_mail_sender.py` (TC-MSN-001..003) | 2026-11-13 |
| `NotifyRecipient` | `quant_cn.core.message_sender` | 1 | BaseModel | One alert recipient: display name and iMessage handle (phone with country code or Apple ID e-mail) (plan 22). | 0 | `core.NotifySettings` | `tests/core/test_message_sender.py` (TC-NS-001) | 2026-11-13 |
| `NotifySettings` | `quant_cn.core.message_sender` | 1 | BaseModel | Recipients, triggers on and max lines per message, from git-ignored config/local.notify.yaml (plan 22, D-153). | 2 | `cli.ReportCommands` | `tests/core/test_message_sender.py` (TC-NS-001..002) | 2026-11-13 |
| `MessageSender` | `quant_cn.core.message_sender` | 1 | ABC | Base of a channel delivering one short text to one handle. | 1 | `core.IMessageSender`, `cli.ReportCommands` | `tests/core/test_message_sender.py` (TC-IMS-001) | 2026-11-13 |
| `IMessageSender` | `quant_cn.core.message_sender` | 1 | MessageSender | Send an iMessage through this Mac's Messages app: osascript with handle and text as argv, iMessage account (plan 22, D-153). | 1 | `cli.ReportCommands` | `tests/core/test_message_sender.py` (TC-IMS-001..003) | 2026-11-13 |
| `SentAlertLog` | `quant_cn.core.sent_alert_log` | 1 | none | JSON list of alert keys sent and still active: new = active not sent; write keeps active sent keys so a cleared alert is sent again when it returns (plan 22). | 3 | `cli.ReportCommands` | `tests/core/test_sent_alert_log.py` (TC-SAL-001..002) | 2026-11-13 |
| `PositionsBook` | `quant_cn.core.positions_book` | 1 | BaseModel | The user's holdings as one combined book (cash, positions) read from git-ignored `config/local.positions.yaml`; loaded here, not by Config, because config.py is at its size limit (plan 15 ph7d, D-132). | 2 | `portfolio.HoldingsRiskBuilder`, `cli.ResearchCommands`, `core.docs.ContractLinter`, `portfolio.OpportunityScreen`, `cli.GaugeCommands` | `tests/portfolio/test_holdings_risk_builder.py` (TC-PB-001..002) | 2026-11-12 |
| `Position` | `quant_cn.core.positions_book` | 1 | BaseModel | One holding: code, name, shares, cost per share (diluted 摊薄成本 after partial sells; <= 0 allowed once paid back, D-166); broker snapshot fields ignored. | 0 | `core.PositionsBook` | `tests/portfolio/test_holdings_risk_builder.py` (TC-PB-001) | 2026-11-16 |
| `DiscoverySettings` | `quant_cn.core.discovery_settings` | 1 | BaseModel | Thresholds and windows of the discovery pipeline (base.yaml `discovery`, plan 16, D-121) | 0 | `core.Config`, `calculation.CompanyCyclePanel`, `calculation.ImpliedExpectations` | `tests/core/test_config.py` (TC-C-017..018) | 2026-11-09 |
| `GuidanceSettings` | `quant_cn.core.guidance_settings` | 1 | BaseModel | Windows and minimum sample of guidance tracking (base.yaml `guidance`, plan 18, D-124) | 0 | `core.Config`, `calculation.ForecastTracker` | `tests/core/test_config.py` (TC-C-019) | 2026-11-11 |
| `ValuesFromDataset` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Enumerate sweep keys from another curated dataset (e.g | 0 | `core.SweepSpec` | `tests/data_loading/test_fetcher_factory.py` (TC-FF-003..003) | 2026-09-27 |
| `SweepSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | How a dataset is swept so each call returns the whole market for one key. | 1 | `core.DatasetSpec` | `tests/core/test_dataset_spec.py` (TC-DS-001..001) | 2026-09-27 |
| `CuratedSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Where a dataset lands in `curated/` and which date column drives its yearly partition. | 0 | `core.DatasetSpec` | `tests/core/test_dataset_spec.py` (TC-DS-001..001) | 2026-09-27 |
| `DatasetSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Everything the lake and the fetchers need to know about one dataset, as data (D-012). | 2 | `core.Config`, `core.BaseFetcher`, `core.BaseStore`, `lake.ParquetWriter`, `lake.LakeCatalog`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory.build`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.CompactStep`, `lake.DerivedViews`, `lake.ProjectCatalog`, `data_loading.DateWindowFetcher`, `lake.EffectiveDateResolver`, `lake.ReleaseLagChecker`, `lake.LakeReader` | `tests/core/test_dataset_spec.py` (TC-DS-001..009) | 2026-09-27 |
| `DateCodec` | `quant_cn.core.date_codec` | 1 | none | Validate and convert Tushare `YYYYMMDD` date strings and generate date keys for sweeps. | 6 | `core.Config.load`, `data_loading.DateSweepFetcher.list_keys`, `data_loading.PeriodSweepFetcher.list_keys`, `pipeline.DownloadPipeline.run`, `data_loading.FetcherFactory`, `cli.QuantCnCli`, `lake.PitAligner`, `visualization.PriceChart`, `cli.ServiceBuilder`, `data_loading.DateWindowFetcher`, `lake.EffectiveDateResolver`, `factor.FactorFactory`, `calculation.ForecastTracker`, `portfolio.EtfProxyBuilder`, `cli.GaugeCommands` | `tests/core/test_date_codec.py` (TC-DC-001..006) | 2026-09-27 |
| `Finding` | `quant_cn.core.docs.base_checker` | 1 | none | One rule violation at a location, printable as `path:line [rule] message`. | 1 | `core.docs.BaseChecker.run`, `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.PlanStatusChecker`, `core.docs.ResearchLogChecker`, `core.docs.ContractLinter` | `tests/core/docs/test_base_checker.py` (TC-BCH-001..001) | 2026-09-27 |
| `BaseChecker` | `quant_cn.core.docs.base_checker` | 1 | ABC | Abstract repository check: inspect the tree, return findings (empty = pass). | 1 | `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.PlanStatusChecker`, `core.docs.ResearchLogChecker`, `core.docs.ContractLinter` | `tests/core/docs/test_base_checker.py` (TC-BCH-001..001) | 2026-09-27 |
| `MethodInfo` | `quant_cn.core.docs.code_scanner` | 1 | none | One function defined directly in a class body. | 2 | `core.docs.ClassInfo`, `core.docs.CodeScanner.read_module`, `core.docs.ModuleInfo` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..001) | 2026-09-27 |
| `ClassInfo` | `quant_cn.core.docs.code_scanner` | 1 | none | One top-level class: span, bases, docstring, methods and the names its body references. | 2 | `core.docs.ModuleInfo`, `core.docs.CodeScanner.read_module`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..002) | 2026-09-27 |
| `ModuleInfo` | `quant_cn.core.docs.code_scanner` | 1 | none | One scanned Python file. | 0 | `core.docs.CodeScanner.read_module`, `core.docs.ContractChecker`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..001) | 2026-09-27 |
| `CodeScanner` | `quant_cn.core.docs.code_scanner` | 1 | none | Parse Python files with `ast` into ModuleInfo records (no import, no execution). | 1 | `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..003) | 2026-09-27 |
| `CodeTableBuilder` | `quant_cn.core.docs.code_table_builder` | 1 | none | Turn src/ classes (AST + contract docstrings), the class registry and tests/ into the code-side tables of the `project` schema, one DataFrame per table with fixed columns. | 1 | `lake.ProjectCatalog`, `cli.ServiceBuilder` | `tests/core/docs/test_code_table_builder.py` (TC-CTB-001..002) | 2026-09-27 |
| `CodeUnit` | `quant_cn.core.docs.contract_checker` | 1 | none | A class with the module it lives in and its parsed contract. | 0 | `core.docs.ContractChecker` | `tests/core/docs/test_contract_checker.py` (TC-CC-001..001) | 2026-09-27 |
| `ContractChecker` | `quant_cn.core.docs.contract_checker` | 1 | BaseChecker | Check contracts across the tree: class docstrings carry all sections and public methods Purpose + Contract | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_contract_checker.py` (TC-CC-001..005) | 2026-09-27 |
| `ContractLinter` | `quant_cn.core.docs.contract_linter` | 1 | none | Build the four checkers (contracts, index, size, names) for one repository and run the selected groups, returning all findings sorted. | 1 | `scripts/lint_contracts.py`, `tests/test_contracts.py`, `lake.ProjectCatalog`, `cli.ServiceBuilder` | `tests/test_contracts.py` (TC-CTL-001..002) | 2026-09-27 |
| `ConventionReader` | `quant_cn.core.docs.convention_reader` | 1 | none | Extract the allowed method-name verb prefixes from the naming convention's §2.1 table. | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_convention_reader.py` (TC-CR-001..002) | 2026-09-27 |
| `DecisionRecord` | `quant_cn.core.docs.decisions_reader` | 1 | none | One decision: its log-table row joined with the Context and Decision bullets of its block. | 0 | `core.docs.DecisionsReader` | `tests/core/docs/test_decisions_reader.py` (TC-DR-001..001) | 2026-09-27 |
| `DecisionsReader` | `quant_cn.core.docs.decisions_reader` | 1 | none | Parse DECISIONS.md: the ID/Date/Title/Status/Where table plus `### D-NNN` detail blocks. | 1 | `core.docs.DocTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_decisions_reader.py` (TC-DR-001..002) | 2026-09-27 |
| `DocTableBuilder` | `quant_cn.core.docs.doc_table_builder` | 1 | none | Turn the INDEX.md tree, the files on disk, the decision log and the execution plans into the document-side tables of the `project` schema. | 1 | `lake.ProjectCatalog`, `cli.ServiceBuilder` | `tests/core/docs/test_doc_table_builder.py` (TC-DTB-001..002) | 2026-09-27 |
| `UsedByEntry` | `quant_cn.core.docs.docstring_parser` | 1 | none | One line of a `Used by:` section, split into the caller reference and its note. | 0 | `core.docs.DocContract`, `core.docs.DocstringParser.parse` | `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001) | 2026-09-27 |
| `DocContract` | `quant_cn.core.docs.docstring_parser` | 1 | none | The parsed contract of one class, method or module docstring. | 1 | `core.docs.DocstringParser.parse`, `core.docs.CodeUnit` | `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001) | 2026-09-27 |
| `DocstringParser` | `quant_cn.core.docs.docstring_parser` | 1 | none | Split a contract docstring into its sections: Purpose, Contract (Input, Output, Raises), Used by, Test cases. | 1 | `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..005) | 2026-09-27 |
| `IndexChecker` | `quant_cn.core.docs.index_checker` | 1 | BaseChecker | Every visible folder has an INDEX.md whose folder and file rows equal what is on disk, and whose Contains cell for a .py file lists exactly its top-level classes (fixtures for conftest.py | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_index_checker.py` (TC-IC-001..004) | 2026-09-27 |
| `IndexEntry` | `quant_cn.core.docs.index_reader` | 1 | none | One row of an INDEX.md table: a subfolder or a file with its purpose and named contents. | 0 | `core.docs.IndexInfo`, `core.docs.IndexReader.read` | `tests/core/docs/test_index_reader.py` (TC-IR-001..001) | 2026-09-27 |
| `IndexInfo` | `quant_cn.core.docs.index_reader` | 1 | none | Parsed INDEX.md: title line, subfolder entries, file entries. | 0 | `core.docs.IndexReader.read`, `core.docs.IndexChecker`, `core.docs.DocTableBuilder` | `tests/core/docs/test_index_reader.py` (TC-IR-001..001) | 2026-09-27 |
| `IndexReader` | `quant_cn.core.docs.index_reader` | 1 | none | Parse the fixed INDEX.md format: `## Folders` (Folder, Purpose) and `## Files` (File, Purpose, Contains) tables. | 1 | `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_index_reader.py` (TC-IR-001..002) | 2026-09-27 |
| `MarkdownTable` | `quant_cn.core.docs.markdown_table` | 1 | none | One pipe table with the heading it sits under. | 1 | `core.docs.MarkdownTableReader.read` | `tests/core/docs/test_markdown_table.py` (TC-MTR-001..001) | 2026-09-27 |
| `MarkdownTableReader` | `quant_cn.core.docs.markdown_table` | 1 | none | Extract every pipe table from markdown text, and backticked names from a cell. | 2 | `core.docs.IndexReader`, `core.docs.RegistryReader`, `core.docs.ConventionReader`, `core.docs.ContractLinter`, `core.docs.DecisionsReader`, `core.docs.PlanReader`, `core.docs.ResearchLogReader`, `cli.ServiceBuilder` | `tests/core/docs/test_markdown_table.py` (TC-MTR-001..003) | 2026-09-27 |
| `NameChecker` | `quant_cn.core.docs.name_checker` | 1 | BaseChecker | Enforce names: lowercase paths (governance `UPPER_SNAKE.md` and tool files excepted), verb-first method and function names from the convention's verb table, no banned verbs, test functions named `test_tc_<id>_<desc>`, and module name matching its primary class. | 2 | `core.docs.ContractLinter` | `tests/core/docs/test_name_checker.py` (TC-NC-001..004) | 2026-09-27 |
| `PhaseRecord` | `quant_cn.core.docs.plan_reader` | 1 | none | One row of a plan's Phases table. | 0 | `core.docs.PlanRecord`, `core.docs.PlanReader.read` | `tests/core/docs/test_plan_reader.py` (TC-PR-001..003) | 2026-09-27 |
| `PlanRecord` | `quant_cn.core.docs.plan_reader` | 1 | none | One execution plan: number, title, header fields and phases. | 0 | `core.docs.PlanReader.read` | `tests/core/docs/test_plan_reader.py` (TC-PR-001..001) | 2026-09-27 |
| `PlanReader` | `quant_cn.core.docs.plan_reader` | 1 | none | Parse a plan file: `# NN — Title`, the two-column header table (Status, Decisions, Depends on plans) and the Phases table. | 1 | `core.docs.DocTableBuilder`, `core.docs.PlanStatusChecker`, `core.docs.ResearchLogChecker`, `core.docs.ContractLinter`, `cli.ServiceBuilder` | `tests/core/docs/test_plan_reader.py` (TC-PR-001..003) | 2026-09-27 |
| `PhaseStatus` | `quant_cn.core.docs.phase_status_parser` | 1 | none | A phase status split into fields: the state word, the first date, the commit hashes and the remaining text. | 1 | `core.docs.PhaseStatusParser.parse` | `tests/core/docs/test_phase_status_parser.py` (TC-PSP-001..002) | 2026-11-13 |
| `PhaseStatusParser` | `quant_cn.core.docs.phase_status_parser` | 1 | none | Parse the Status cell of a plan's Phases table into state, date, commits and note; legacy free-text spellings parse too. | 1 | `core.docs.PlanReader`, `core.docs.ContractLinter`, `cli.ServiceBuilder` | `tests/core/docs/test_phase_status_parser.py` (TC-PSP-001..003) | 2026-11-13 |
| `PlanStatusChecker` | `quant_cn.core.docs.plan_status_checker` | 1 | BaseChecker | Report every plan phase whose Status cell does not start with todo, doing, blocked or done. | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_plan_status_checker.py` (TC-PSC-001..001) | 2026-11-13 |
| `RegistryInfo` | `quant_cn.core.docs.registry_reader` | 1 | none | The registry's content as sets and maps the linter can compare with code. | 0 | `core.docs.RegistryReader.read`, `core.docs.ContractChecker`, `core.docs.CodeTableBuilder` | `tests/core/docs/test_registry_reader.py` (TC-RR-001..001) | 2026-09-27 |
| `RegistryReader` | `quant_cn.core.docs.registry_reader` | 1 | none | Parse CLASS_REGISTRY.md: section A index, section B detail blocks and their method tables, and the class/schema names of sections C, D, E. | 1 | `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_registry_reader.py` (TC-RR-001..003) | 2026-09-27 |
| `RepoFiles` | `quant_cn.core.docs.repo_files` | 1 | none | The set of repository files a linter should see: `git ls-files --cached --others --exclude-standard`, so .gitignore (caches, .env, lake guards) decides what is ignored. | 2 | `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_repo_files.py` (TC-RF-001..003) | 2026-09-27 |
| `ResearchLogChecker` | `quant_cn.core.docs.research_log_checker` | 1 | BaseChecker | Check the research log (slug format and uniqueness, date match, scripts exist) and that committed research runs do not hard-code the private book. | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_research_log_checker.py` (TC-RSC-001..002) | 2026-11-13 |
| `ResearchRun` | `quant_cn.core.docs.research_log_reader` | 1 | none | One ad-hoc analysis as logged: when, what was asked, where its scripts and outputs live, what it concluded and what followed. | 0 | `core.docs.ResearchLogReader.read` | `tests/core/docs/test_research_log_reader.py` (TC-RLR-001..001) | 2026-11-13 |
| `ResearchLogReader` | `quant_cn.core.docs.research_log_reader` | 1 | none | Parse research_space/RESEARCH_LOG.md: the first table whose header is the log columns. | 1 | `core.docs.DocTableBuilder`, `core.docs.ResearchLogChecker`, `core.docs.ContractLinter`, `cli.ServiceBuilder` | `tests/core/docs/test_research_log_reader.py` (TC-RLR-001..002) | 2026-11-13 |
| `SizeChecker` | `quant_cn.core.docs.size_checker` | 1 | BaseChecker | Fail any .py file over 600 lines, class over 300, function or method over 50 (physical lines, docstrings included), and INDEX.md / SKILL.md / execution plan over 300 lines. | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_size_checker.py` (TC-SC-001..002) | 2026-09-27 |
| `Schema` | `quant_cn.core.schema` | 1 | none | Declare and enforce a DataFrame shape: text columns are pandas `string`, all other declared columns are `float64`, and the primary key is unique and non-null. | 4 | `core.DatasetSpec.build_schema`, `lake.LakeReader` | `tests/core/test_schema.py` (TC-S-001..006) | 2026-09-27 |
| `StepReport` | `quant_cn.core.step_report` | 1 | none | Counts and status of one step (usually one dataset's fetch) so runs can be summarised. | 0 | `core.BaseFetcher.run`, `core.BaseStep.run`, `lake.Compactor.rebuild`, `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `pipeline.FetchStep`, `pipeline.PipelineReport`, `pipeline.CompactStep`, `pipeline.DeriveStep`, `pipeline.PrefectRunner`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `data_loading.DocumentDownloader` | `tests/core/test_base_fetcher.py` (TC-BF-001..001) | 2026-09-27 |
| `TickerNormalizer` | `quant_cn.core.ticker_normalizer` | 1 | none | Turn common A-share ticker spellings into Tushare `ts_code` and check `ts_code` validity. | 2 | `industry_graph.LegacyLabelImporter` | `tests/core/test_ticker_normalizer.py` (TC-TN-001..005) | 2026-11-14 |
| `AkshareClient` | `quant_cn.data_loading.akshare_client` | 3 | BaseApiClient | Call one AkShare function per query (`api_name` = function name, `params` = its keyword arguments) and return its frame with dates normalised to YYYYMMDD strings, so the lake's schema and PIT rules apply unchanged | 1 | `cli.ServiceBuilder` | `tests/data_loading/test_akshare_client.py` (TC-AKC-001..002) | 2026-09-27 |
| `BaostockClient` | `quant_cn.data_loading.baostock_client` | 3 | BaseApiClient | Call one BaoStock query per request (`api_name` = method, e.g | 1 | `cli.ServiceBuilder` | `tests/data_loading/test_baostock_client.py` (TC-BSC-001..006) | 2026-09-27 |
| `FetcherFactory` | `quant_cn.data_loading.fetcher_factory` | 3 | none | Build the right fetcher for a DatasetSpec and inject the shared dependencies. | 1 | `pipeline.DownloadPipeline`, `cli.ServiceBuilder` | `tests/data_loading/test_fetcher_factory.py` (TC-FF-001..004) | 2026-09-27 |
| `SingleCallFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Datasets fetched in one (paged) call, key "all": trade_cal, namechange. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-SCF-001..001) | 2026-09-27 |
| `EnumFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Datasets swept over an enumerated list: stock_basic by list_status (L, D, P), index_daily / fund_daily by ts_code, opt_basic by exchange. | 2 | `data_loading.FetcherFactory.build`, `data_loading.SnapshotFetcher` | `tests/data_loading/test_fetchers.py` (TC-EF-001..001) | 2026-09-27 |
| `DateSweepFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Whole-market daily sweeps: trade_date and nav_date keys are trading days (daily, adj_factor, daily_basic, moneyflow, stk_limit, fund_nav) | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-DSF-001..005) | 2026-09-27 |
| `PeriodSweepFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Whole-market report-period sweeps (the *_vip fundamentals): one key per quarter end. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-PSF-001..001) | 2026-09-27 |
| `DateWindowFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Range-only endpoints swept by calendar window (D-063): one call per month ("YYYYMM" keys) or year ("YYYY" keys) with start_date / end_date clipped to the run range | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-DWF-001..004) | 2026-09-27 |
| `HttpTransport` | `quant_cn.data_loading.http_transport` | 3 | none | Send one HTTP request and return the decoded JSON object or the raw bytes (JSON POST, form POST, GET JSON, GET bytes). | 4 | `data_loading.TushareClient`, `data_loading.CninfoClient`, `data_loading.EastmoneyReportClient`, `data_loading.AppStoreClient`, `data_loading.BaseWebClient`, `data_loading.DocumentDownloader` | `tests/data_loading/test_tushare_client.py`, `test_http_transport.py` (TC-TC-001, TC-HT-001) | 2026-09-27 |
| `TushareClient` | `quant_cn.data_loading.tushare_client` | 3 | BaseApiClient | Query Tushare Pro: one logical query follows limit/offset paging until a short page and returns all rows | 1 | `cli.ServiceBuilder` | `tests/data_loading/test_tushare_client.py` (TC-TC-001..009) | 2026-09-27 |
| `FactorInputs` | `quant_cn.factor.base_factor` | 5 | none | The panels a factor may read, loaded once by FactorFactory for all factors of a run | 1 | `factor.BaseFactor`, `factor.FactorFactory`, `factor.library.DividendYieldFactor`, `factor.library.EarningsYieldFactor`, `factor.library.IntradayReversalFactor`, `factor.library.MomentumFactor`, `factor.library.ProfitGrowthFactor`, `factor.library.ReversalFactor`, `factor.library.RoeFactor`, `factor.library.TurnoverFactor` | `tests/factor/test_base_factor.py` (TC-FIN-001..001) | 2026-09-27 |
| `BaseFactor` | `quant_cn.factor.base_factor` | 5 | ABC | Abstract factor: declares which inputs, fundamentals fields and daily_basic columns it needs and how many sessions of price history before the first output date | 4 | `factor.FactorFactory`, `factor.library.*`, `factor.library.DividendYieldFactor`, `factor.library.EarningsYieldFactor`, `factor.library.MomentumFactor`, `factor.library.ProfitGrowthFactor`, `factor.library.ReversalFactor`, `factor.library.RoeFactor`, `factor.library.TurnoverFactor`, `pipeline.FeatureStep` | `tests/factor/test_base_factor.py` (TC-BFA-001..002) | 2026-09-27 |
| `FactorAcceptance` | `quant_cn.factor.factor_acceptance` | 5 | none | Criteria 1-3 of FACTOR_TESTING_DESIGN §6 per factor at one horizon, from the campaign's IC_TEST: (1) NW t of the full-window mean IC >= t_min (HLZ) and BHY-adjusted p <= alpha | 1 | `research_space/notebooks/20260930_factor_campaign_01.ipynb`, `plan 06 ReportBuilder` | `tests/factor/test_factor_acceptance.py` (TC-FA-001..003) | 2026-09-27 |
| `FactorReport` | `quant_cn.factor.factor_evaluator` | 5 | none | The evaluation of one campaign: IC series, every test result, quantile ladders. | 0 | `factor.FactorEvaluator` | `tests/factor/test_factor_evaluator.py` (TC-FEV-001..001) | 2026-09-27 |
| `FactorEvaluator` | `quant_cn.factor.factor_evaluator` | 5 | none | Evaluate every factor of a campaign (FACTOR_TESTING_DESIGN §2, §3, §6): tradeable forward returns from the open of t+1, IC series per horizon, the IcSignificance tests, decay across horizons (half-life), rank autocorrelation (turnover proxy), quantile ladders and long-short statistics on non-overlapping samples, then the campaign-level Holm / BHY / Romano-Wolf adjustment and HLZ flag over all factor x horizon mean-IC tests | 2 | `notebooks`, `pipeline.EvaluationStep`, `cli.ServiceBuilder` | `tests/factor/test_factor_evaluator.py` (TC-FEV-001..003) | 2026-09-27 |
| `FactorFactory` | `quant_cn.factor.factor_factory` | 5 | none | Resolve config/factors.yaml entries to BaseFactor instances (every module under factor/library/ is imported so its classes register themselves | 2 | `notebooks`, `pipeline.FeatureStep`, `cli.ServiceBuilder` | `tests/factor/test_factor_factory.py` (TC-FAF-001..003) | 2026-09-27 |
| `FactorPreprocessor` | `quant_cn.factor.factor_preprocessor` | 5 | none | The ordered chain applied to every raw factor, each step optional and logged: winsorise (median +- k * 1.4826 * MAD per date) -> standardise (z per date) -> neutralise (per-date OLS residual on Shenwan L1 dummies and log market cap, D-093) -> standardise again, so the processed value is a unit-dispersion, industry- and size-neutral z-score | 2 | `pipeline.FeatureStep`, `cli.ServiceBuilder` | `tests/factor/test_factor_preprocessor.py` (TC-FPP-001..002) | 2026-09-27 |
| `EarningsYieldFactor` | `quant_cn.factor.library.earnings_yield_factor` | 5 | BaseFactor | Earnings yield EP_TTM = net profit attributable to parent over the trailing twelve months (PIT, D-092) / total market value at the close of t | 1 | (none yet) | `tests/factor/test_fundamental_factors.py` (TC-EYF-001..001) | 2026-09-27 |
| `MomentumFactor` | `quant_cn.factor.library.momentum_factor` | 5 | BaseFactor | MOM_{12-1} = P_adj(t - skip) / P_adj(t - window) - 1 on the backward-adjusted close (ratios are PIT-safe, FACTOR_TESTING_DESIGN §11), skipping the most recent month to avoid the short-term reversal (Jegadeesh & Titman 1993) | 2 | (none yet) | `tests/factor/test_price_factors.py` (TC-MOM-001..001) | 2026-09-27 |
| `ProfitGrowthFactor` | `quant_cn.factor.library.profit_growth_factor` | 5 | BaseFactor | Growth = (NI_TTM(P) - NI_TTM(P - 1 year)) / /NI_TTM(P - 1 year)/ for the latest PIT-visible period P, both TTMs from the versions known at the announcement (the lake's `n_income_attr_p_ttm_yoy`, D-092) | 1 | (none yet) | `tests/factor/test_fundamental_factors.py` (TC-PGF-001..001) | 2026-09-27 |
| `IntradayReversalFactor` | `quant_cn.factor.library.intraday_reversal_factor` | 5 | ReversalFactor | IRV = -sum(ln(close / open)) over the `top_k` sessions with the highest free-float turnover among the last `window` grid sessions | 1 | (none yet) | `tests/factor/test_intraday_reversal_factor.py` (TC-IRV-001..005) | 2026-11-14 |
| `PricingGapFactor` | `quant_cn.factor.library.pricing_gap_factor` | 5 | BaseFactor | Linear-pricing gap: -log(total_mv / value of consensus FY1-FY3 with growth fading ×0.7 for 7 years and exit PE 15 at 9%); higher = cheaper; month-end consensus carried to sessions (plan 36, D-173). | 3 | (none yet) | `tests/factor/test_pricing_gap_factor.py` (TC-LPG-001..003) | 2026-11-18 |
| `RetailGaugeFactor` | `quant_cn.factor.library.retail_gauge_factor` | 5 | BaseFactor | Minus the latest 散户温度计 reading (derived.retail_gauge pct, as_of <= t, at most max_age_days old); higher = retail leaving (plan 21 ph6). | 1 | (none yet) | `tests/factor/test_retail_gauge_factor.py` (TC-RGFA-001..002) | 2026-11-19 |
| `ReversalFactor` | `quant_cn.factor.library.reversal_factor` | 5 | BaseFactor | REV = -(P_adj(t) / P_adj(t - window) - 1): last month's losers tend to rebound, strongly so in China's retail-driven market (Jegadeesh 1990 | 2 | `factor.library.IntradayReversalFactor` | `tests/factor/test_price_factors.py` (TC-REV-001..001) | 2026-09-27 |
| `RoeFactor` | `quant_cn.factor.library.roe_factor` | 5 | BaseFactor | Return on equity ROE_TTM = net profit attributable to parent over the trailing twelve months / equity attributable to parent in the latest PIT-visible balance sheet (both D-092 PIT) | 1 | (none yet) | `tests/factor/test_fundamental_factors.py` (TC-ROE-001..001) | 2026-09-27 |
| `DividendYieldFactor` | `quant_cn.factor.library.dividend_yield_factor` | 5 | BaseFactor | DP = trailing 12-month dividend yield (daily_basic dv_ttm / 100); 0 for a stock with a market cap and no dividend; no value without daily_basic (D-148 descriptor as an alpha factor) | 2 | (none yet) | `tests/factor/test_price_factors.py` (TC-DYF-001..001) | 2026-11-12 |
| `TurnoverFactor` | `quant_cn.factor.library.turnover_factor` | 5 | BaseFactor | TURN = -mean(turnover_rate_f over the last `window` sessions, at least `min_obs` traded): heavily traded stocks underperform, a liquidity / attention effect that is strong in China (Datar, Naik & Radcliffe 1998 | 2 | (none yet) | `tests/factor/test_price_factors.py` (TC-TRN-001..001) | 2026-09-27 |
| `SignalCombiner` | `quant_cn.factor.signal_combiner` | 5 | none | score_{i,t} = sum_f w_f z_{f,i,t} / sum_{f available} /w_f/ over the processed factors a stock has at t (at least `min_factors`), then standardised per date: an equal-risk blend of z-scores that tolerates a missing factor instead of dropping the stock. | 1 | `pipeline.FeatureStep`, `cli.ServiceBuilder` | `tests/factor/test_signal_combiner.py` (TC-SGC-001..002) | 2026-09-27 |
| `Compactor` | `quant_cn.lake.compactor` | 2 | none | Rebuild a dataset's curated partitions from its raw files: select declared fields, cast dtypes, fill `key_defaults` into NULL key columns, drop duplicate primary keys (keeping one), sort by partition date then key, validate, write, and record a manifest in `meta/manifest/<dataset>.json`. | 1 | `cli.QuantCnCli`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `cli.ServiceBuilder` | `tests/lake/test_compactor.py` (TC-CO-001..006) | 2026-09-27 |
| `DerivedViews` | `quant_cn.lake.derived_views` | 2 | none | Create the `derived` schema views built only from curated/: `derived.prices_adj` (daily bars joined to adj_factor, close_adj = close * adj_factor | 2 | `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `cli.ServiceBuilder`, `pipeline.FeatureStep`, `cli.GaugeCommands` | `tests/lake/test_derived_views.py` (TC-DV-001..010) | 2026-09-27 |
| `EffectiveDateResolver` | `quant_cn.lake.effective_date_resolver` | 2 | none | Turn a dataset's `known_on` value into `effective_date`, the first China trading session the row may be used (FACTOR_TESTING_DESIGN §11): as_is          -> that session, or the next one if the day is closed (same-day data) | 2 | (none yet) | `tests/lake/test_effective_date_resolver.py` (TC-EDR-001..006) | 2026-09-27 |
| `ExposureReader` | `quant_cn.lake.exposure_reader` | 2 | none | Per universe member and session: the Shenwan L1 group in effect (derived.industry_l1, l1_grouping = the PIT row or the back-filled first-known L1, flagged | 1 | `pipeline.FeatureStep`, `cli.ServiceBuilder` | `tests/lake/test_lake_reader.py` (TC-EXR-001..001) | 2026-09-27 |
| `FetchLog` | `quant_cn.lake.fetch_log` | 2 | BaseFetchLog | Record finished (dataset, key) pairs in `meta.fetch_log`, mirror them to `meta/fetch_log.parquet` on save, and rebuild the table after the DuckDB file is lost. | 6 | `cli.QuantCnCli`, `cli.ServiceBuilder` | `tests/lake/test_fetch_log.py` (TC-FL-001..006) | 2026-09-27 |
| `LakeCatalog` | `quant_cn.lake.lake_catalog` | 2 | none | Own the lake's single DuckDB connection (`meta/quant_cn.duckdb`): schemas `raw`, `curated`, `meta` | 8 | `lake.FetchLog`, `lake.RunLog`, `lake.LakeQuery`, `lake.Compactor`, `pipeline.FetchStep.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `lake.DerivedViews`, `lake.PitAligner`, `lake.ProjectCatalog`, `cli.ServiceBuilder`, `lake.QualityViews`, `lake.LakeReader`, `lake.TickerAliasMap`, `cli.ResearchCommands`, `cli.DocumentCommands`, `cli.GaugeCommands` | `tests/lake/test_lake_catalog.py` (TC-LC-001..005) | 2026-09-27 |
| `LakeQuery` | `quant_cn.lake.lake_query` | 2 | none | Run read queries against the catalog views | 5 | `lake.TradingCalendar`, `portfolio.SmallCapWatchBuilder`, `lake.Compactor.rebuild`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `lake.DerivedViews`, `lake.PitAligner`, `cli.ServiceBuilder`, `data_loading.FetcherFactory`, `lake.QualityViews`, `lake.ReleaseLagChecker`, `lake.LakeReader`, `lake.TickerAliasMap`, `pipeline.UniverseStep`, `lake.ExposureReader`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `cli.ResearchCommands`, `cli.DocumentCommands`, `data_loading.DocumentDownloader`, `portfolio.WatchlistBuilder`, `portfolio.EtfProxyBuilder`, `risk.FactorMonitorBuilder`, `portfolio.BuybackMonitorBuilder`, `cli.GaugeCommands`, `calculation.HolderCountPanel`, `calculation.RetailGaugeEvaluator`, `calculation.RetailGaugeFeatureBuilder`, `portfolio.OpportunityScreen`, `lake.ValuationHistoryReader` | `tests/lake/test_lake_query.py` (TC-LQ-001..005) | 2026-09-27 |
| `LakeReader` | `quant_cn.lake.lake_reader` | 2 | none | The read API factors, the universe step and notebooks use (SRC_DESIGN §2.2b, D-089): one curated dataset as a panel, dense or sparse prices, point-in-time fundamentals, reference tables (in-memory frames and view discovery: LakeQuery) | 5 | `cli.ServiceBuilder`, (none yet), `factor.FactorFactory`, `pipeline.EvaluationStep`, `pipeline.FeatureStep` | `tests/lake/test_lake_reader.py` (TC-LRD-001..007) | 2026-09-27 |
| `PanelCache` | `quant_cn.lake.panel_cache` | 2 | none | Keep recently read panels in memory, keyed by (method, arguments), least recently used evicted first once the total size exceeds `max_bytes` | 4 | `lake.LakeReader`, `cli.ServiceBuilder` | `tests/lake/test_panel_cache.py` (TC-PCH-001..003) | 2026-09-27 |
| `ParquetWriter` | `quant_cn.lake.parquet_writer` | 2 | BaseStore | Write raw fetch results and curated partitions as zstd parquet, atomically (write `.tmp`, fsync, rename), so a crash never leaves a half-written file. | 6 | `cli.QuantCnCli`, `cli.ServiceBuilder`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `cli.ReportCommands`, `lake.DatedTableStore`, `cli.GaugeCommands`, `calculation.RetailGaugeEvaluator`, `calculation.RetailGaugeNowcaster` | `tests/lake/test_parquet_writer.py` (TC-PW-001..008) | 2026-09-27 |
| `GraphStore` | `quant_cn.lake.graph_store` | 2 | none | The plan 28 graph tables (entity_map, company_edge, edge_span, company_period, node_member, node_lineage, node_edge) and plan 31 game_alias / game_company as one parquet each under derived/graph/, atomic whole-table writes (D-161). | 3 | `industry_graph.GraphBuilder`, `cli.DocumentCommands`, `lake` | `tests/lake/test_graph_store.py` (TC-GS-001..003) | 2026-11-16 |
| `LabelStore` | `quant_cn.lake.label_store` | 2 | none | Every label set as parquet under derived/labels/<set>/year=<YYYY>/, one row per (company, document) with period, known_on, event_date, taxonomy_version and the record as JSON; upserts on (ts_code, doc_key), optionally replacing all earlier rows of one source; point-in-time read by known_on (plan 28, D-161). | 3 | `industry_graph.LegacyLabelImporter`, `cli.DocumentCommands`, `portfolio.BuybackMonitorBuilder`, `cli.ReportCommands` | `tests/lake/test_label_store.py` (TC-LBS-001..005) | 2026-11-15 |
| `DatedTableStore` | `quant_cn.lake.dated_table_store` | 2 | none | Own derived year tables keyed by a YYYYMMDD column without the DuckDB catalog: write replaces the written dates and keeps the other dates of the year; read returns some years; read_report reads one whole derived table (plan 21). | 3 | `calculation.RetailGaugeFeatureBuilder`, `calculation.RetailGaugeNowcaster`, `cli.GaugeCommands`, `portfolio.OpportunityScreen`, `factor.FactorFactory`, `cli.ServiceBuilder` | `tests/lake/test_dated_table_store.py` (TC-DTW-001..002) | 2026-11-18 |
| `ValuationHistoryReader` | `quant_cn.lake.valuation_history_reader` | 2 | none | Latest pb / pe_ttm of each stock on a date (0 for a loss) and the median of its positive values over a window, from curated.daily_basic (plan 21 ph4). | 1 | `portfolio.OpportunityScreen`, `cli.GaugeCommands` | `tests/lake/test_valuation_history_reader.py` (TC-VHR-001) | 2026-11-18 |
| `PitAligner` | `quant_cn.lake.pit_aligner` | 2 | none | Align fundamentals to trading days without look-ahead | 2 | `pipeline.CuratePipeline`, `research_space/main.ipynb`, `pipeline.DeriveStep`, `cli.ServiceBuilder`, `lake.LakeReader` | `tests/lake/test_pit_aligner.py` (TC-PAD-001..003) | 2026-09-27 |
| `ProjectCatalog` | `quant_cn.lake.project_catalog` | 2 | none | Rebuild schema `project` in the lake's DuckDB from the repository: folders, files, classes, methods, used_by, contracts, test_cases, decisions, plans, phases, datasets, lint_findings, plus views tree, class_graph, stale and todo | 1 | `cli.ServiceBuilder` | `tests/lake/test_project_catalog.py` (TC-PJC-001..004) | 2026-09-27 |
| `QualityViews` | `quant_cn.lake.quality_views` | 2 | none | Create the `quality` schema: cross-source comparisons that report, never overwrite (D-065) | 1 | `lake.DerivedViews.refresh` | `tests/lake/test_quality_views.py` (TC-QV-001..003) | 2026-09-27 |
| `RebuildAudit` | `quant_cn.lake.rebuild_audit` | 2 | none | Record, on `rebuild`, what changed below raw/ since the last one | 2 | `cli.QuantCnCli` | `tests/lake/test_rebuild_audit.py` (TC-RA-001..002) | 2026-09-27 |
| `BuybackEventsBuilder` | `quant_cn.portfolio.buyback_events_builder` | 5 | none | Buyback announcements of the last 7 days: new plans ≥ 2% of market cap market-wide and every event of held / watched stocks -> buybacks.json (plan 23 ph6). | 3 | `cli.ReportCommands` | `tests/portfolio/test_buyback_events_builder.py` (TC-BEB-001..002) | 2026-11-13 |
| `BuybackMonitorBuilder` | `quant_cn.portfolio.buyback_monitor_builder` | 5 | none | Market-wide buyback and 增持 document, kinds apart: live programmes with planned / executed / % done / price cap vs close / labels, the window's new / completed / stopped / expired / ended events, totals by purpose or holder type and funding (专项贷款 sum), counts per month -> buyback_monitor.json (plan 32 ph3, D-169). | 3 | `cli.ReportCommands` | `tests/portfolio/test_buyback_monitor_builder.py` (TC-BMB-001..002) | 2026-11-18 |
| `BuybackPlanFrame` | `quant_cn.portfolio.buyback_plan_frame` | 5 | none | One row per 回购 programme (BuybackLedger, joined to its buyback_terms labels; unlabelled restricted-stock or cap-less ones dropped) and per 增持 plan (label items, repeats dropped, executed from the named holders' stk_holdertrade IN rows) (plan 32 ph3). | 3 | `portfolio.BuybackMonitorBuilder`, `cli.ReportCommands` | `tests/portfolio/test_buyback_plan_frame.py` (TC-BPF-001..003) | 2026-11-18 |
| `MarginPanelBuilder` | `quant_cn.portfolio.margin_panel_builder` | 5 | none | One 融资融券 document per stock: 6-month financing / short series, % of float, 20-day changes, FIFO forced-liquidation ladder at 100% / 80% margin; writes margin/<code>.json (plan 15 ph7m). | 3 | `cli.ReportCommands` | `tests/portfolio/test_margin_panel_builder.py` (TC-MPB-001..003) | 2026-11-13 |
| `WatchlistBuilder` | `quant_cn.portfolio.watchlist_builder` | 5 | none | Join the user's buy targets with the latest lake prices, valuation and broker consensus; compute the gap to the buy price, status and valuation at that price (plan 15 ph7, D-120); entry conditions via ConditionEvaluator (ph7f); ETF entries priced from fund_daily / fund_basic, kind etf (ph7p) | 3 | `cli.AppServiceBuilder` | `tests/portfolio/test_watchlist_builder.py` (TC-WB-001..011) | 2026-11-19 |
| `EtfFlowCalculator` | `quant_cn.portfolio.etf_flow_calculator` | 5 | none | Pick the ETFs tracking each configured index and compute daily AUM, split- and gap-proof net subscriptions and position at today's price (plan 15 ph7b, D-126). | 2 | `portfolio.EtfProxyBuilder`, `portfolio.EtfStyleHeat`, `portfolio.SmallCapWatchBuilder`, `cli.ResearchCommands`, `cli.ReportCommands` | `tests/portfolio/test_etf_flow_calculator.py` (TC-EFC-001..006) | 2026-11-11 |
| `EtfProxyBuilder` | `quant_cn.portfolio.etf_proxy_builder` | 5 | none | Sum broad-index ETFs into the national-team proxy (core vs other, per index with its rhythm and 近3月 window, weekly, yearly, recent days) and write `etf_proxy.json` for the chain app (plan 15 ph7b, D-126); style crowding via EtfStyleHeat (ph7g). | 2 | `cli.ResearchCommands` | `tests/portfolio/test_etf_proxy_builder.py` (TC-EP-001..007) | 2026-11-18 |
| `SmallCapWatchBuilder` | `quant_cn.portfolio.small_cap_watch_builder` | 5 | none | 小盘观察 rows per day: limit-downs, share at a 60-day low / above MA20, 中证1000 vs user levels and drawdown, realised vol of 中证1000 / 科创50 and the 1000−300 gap with percentiles, broad-ETF net flow, market financing balance (curated.margin, complete-exchange days only) with drawdown, changes, mean and share of float cap (ph4); rows and states via SmallCapWatchRows, new_triggered; writes smallcap_watch.json (plan 30). | 2 | `cli.ReportCommands` | `tests/portfolio/test_small_cap_watch_builder.py` (TC-SCW-001..010) | 2026-11-18 |
| `SectorMetricReader` | `quant_cn.portfolio.sector_metric_reader` | 5 | none | Sector-monitor lines (label, period, value): 70-city tier MoM, quarterly contract liabilities / impairment / revenue / selling ratio, dividends, winner rate, closes for vol, game approvals per month (plan 31 ph4). | 8 | `portfolio.SectorMonitorBuilder`, `portfolio.DeveloperSalesReader`, `cli.AppServiceBuilder` | `tests/portfolio/test_sector_metric_reader.py` (TC-SMR-001..004) | 2026-11-17 |
| `DeveloperSalesReader` | `quant_cn.portfolio.developer_sales_reader` | 5 | none | Developers' monthly contracted sales and 12-month land intensity from the operating_data label set (销售简报, plan 31 ph4, D-168). | 4 | `portfolio.SectorMonitorBuilder`, `cli.AppServiceBuilder` | `tests/portfolio/test_developer_sales_reader.py` (TC-DEV-001..004) | 2026-11-17 |
| `SectorMonitorBuilder` | `quant_cn.portfolio.sector_monitor_builder` | 5 | none | sector_monitor.json for #sector-monitor: per sector one chart per metric, realised vol of index and companies, company table with latest values, vol percentiles and RetailGauge, App Store rankings for app_rank sectors (plan 31 ph4, plan 19 ph2). | 2 | `cli.AppServiceBuilder` | `tests/portfolio/test_sector_monitor_builder.py` (TC-SMB-001..005) | 2026-11-17 |
| `SectorEarningsSignalBuilder` | `quant_cn.portfolio.sector_earnings_signal_builder` | 5 | none | 财报季信号 per Shenwan L2 sector and quarter: share reported, best-surprise pre / reaction excess, signal date, prior sector rally, holder change, status firing / provisional / none, past firings with forward excess and the record; writes sector_earnings_signal.json (plan 35, D-172). | 2 | `cli.AppServiceBuilder` | `tests/portfolio/test_sector_earnings_signal_builder.py` (TC-SEB-001..003) | 2026-11-18 |
| `MarketSignalReader` | `quant_cn.portfolio.market_signal_reader` | 5 | none | Sector market signals: valuation (PB / PE TTM) 5-year percentile lines and latest levels for companies and the Shenwan index, FY1 analyst forecast revision (report_rc), institutional survey days (stk_surv) (plan 33, D-170). | 3 | `portfolio.SectorMonitorBuilder`, `cli.AppServiceBuilder` | `tests/portfolio/test_market_signal_reader.py` (TC-MKS-001..003) | 2026-11-17 |
| `AppRankReader` | `quant_cn.portfolio.app_rank_reader` | 5 | none | App Store chart ranks per company through the publisher map: best home grossing rank per company and date; leaderboard of the games of the sector companies and every A-share company in the map (home grossing / free, best overseas, markets) and the home top list with companies (plan 19 ph2, D-137 u1). | 2 | `portfolio.SectorMonitorBuilder`, `cli.AppServiceBuilder` | `tests/portfolio/test_app_rank_reader.py` (TC-ARR-001..003) | 2026-11-17 |
| `SmallCapWatchRows` | `quant_cn.portfolio.small_cap_watch_rows` | 5 | none | 小盘观察 display rows with on / near / off / info states (count share, percentile points, level fraction), 杠杆 rows with the 融资余额 企稳 state (ph4), and the chart history (plan 30). | 2 | `portfolio.SmallCapWatchBuilder`, `cli.ReportCommands` | `tests/portfolio/test_small_cap_watch_rows.py` (TC-SCR-001..006) | 2026-11-18 |
| `EtfStyleHeat` | `quant_cn.portfolio.etf_style_heat` | 5 | none | Style ETF crowding (银行, 红利): 20-day net flow vs AUM, z vs the previous 250 sessions, 过热 at z ≥ 1.5 until z ≤ 0; never in core / other totals (plan 15 ph7g). | 2 | `portfolio.EtfProxyBuilder` | `tests/portfolio/test_etf_style_heat.py` (TC-ESH-001..003) | 2026-11-13 |
| `EtfCtaWeights` | `quant_cn.portfolio.etf_cta_weights` | 5 | none | Weekly target weights of the ETF CTA book: equal-risk groups (1 / vol, monthly) at risk_share, A股 trend position, bond sleeve x bond switch; signal summary (plan 27). | 3 | `portfolio.EtfCtaBook` | `tests/portfolio/test_etf_cta_weights.py` (TC-ECW-001..006) | 2026-11-14 |
| `EtfCtaPaperBook` | `quant_cn.portfolio.etf_cta_paper_book` | 5 | none | Paper account following the weekly targets: drift, per-group 2-point no-trade band, zero target always sold, costs, no-add codes (plan 27). | 1 | `portfolio.EtfCtaBook` | `tests/portfolio/test_etf_cta_paper_book.py` (TC-ECP-001..007) | 2026-11-14 |
| `EtfCtaBook` | `quant_cn.portfolio.etf_cta_book` | 5 | none | Build `etf_cta.json`: latest weekly decision (target, held, trade per ETF), groups, signals, premium guard, flags, back-test and paper record, 含观点 track (plan 27, D-160, D-163). | 2 | `cli.ReportCommands` | `tests/portfolio/test_etf_cta_book.py` (TC-ECB-001..006) | 2026-11-14 |
| `EtfCtaViewTilt` | `quant_cn.portfolio.etf_cta_view_tilt` | 5 | none | Apply user views to the system targets: A股 floor, scale (subset keeps group total, clip 0.5–2), relative moves, cap at 100%; statuses, group effects, view flags (D-163). | 2 | `portfolio.EtfCtaBook` | `tests/portfolio/test_etf_cta_view_tilt.py` (TC-ECVT-001..007) | 2026-11-14 |
| `EtfCtaRecord` | `quant_cn.portfolio.etf_cta_record` | 5 | none | Track record of a paper NAV: nav, ann, vol, Sharpe over cash, max dd, years, weekly points (plan 27). | 1 | `portfolio.EtfCtaBook` | `tests/portfolio/test_etf_cta_record.py` (TC-ECR-001) | 2026-11-14 |
| `HoldingsHistoryWriter` | `quant_cn.portfolio.holdings_history_writer` | 5 | none | Store one session of the holdings document in the lake (derived/holdings_positions with a CASH row, derived/holdings_risk), one file per year, the session replaced on rerun (plan 15 ph7d, D-132). | 1 | `portfolio.HoldingsRiskBuilder`, `cli.ResearchCommands`, `core.docs.ContractLinter` | `tests/portfolio/test_holdings_history_writer.py` (TC-HHW-001..001) | 2026-11-12 |
| `ConditionResult` | `quant_cn.portfolio.condition_evaluator` | 5 | none | One condition with the value found (None = unknown) and its state met / unmet / unknown. | 1 | `portfolio.ConditionEvaluator` | `tests/portfolio/test_condition_evaluator.py` (TC-CE-001) | 2026-11-13 |
| `ConditionEvaluator` | `quant_cn.portfolio.condition_evaluator` | 5 | none | Gather condition metrics (closes, chips, statements, series, market heat, margin signals ph7m; required conditions ph7n) and evaluate conditions; entry status buy / near / wait with k of n; unknown never counts as met (plan 15 ph7f); a low retail_gauge condition also needs D-167 retail_leaving (plan 21 ph5). | 3 | `portfolio.PositionReviewer`, `portfolio.WatchlistBuilder`, `cli.AppServiceBuilder` | `tests/portfolio/test_condition_evaluator.py` (TC-CE-001..006) | 2026-11-13 |
| `PositionReviewer` | `quant_cn.portfolio.position_reviewer` | 5 | none | Per held stock: note, chip and statement row, conditions and flags (stop, target, weight above cap, review overdue, missing note) (plan 15 ph7f). | 1 | `portfolio.HoldingsRiskBuilder`, `cli.AppServiceBuilder` | `tests/portfolio/test_position_reviewer.py` (TC-PRV-001..003) | 2026-11-13 |
| `HoldingsRiskBuilder` | `quant_cn.portfolio.holdings_risk_builder` | 5 | none | Value the user's book at the last risk-model session and decompose its risk (total / factor / specific, active vs a benchmark, exposures, per-stock vol and share of risk, correlations); write `holdings_risk.json` and the lake history (plan 15 ph7d, D-132); `reviews` from PositionReviewer (ph7f); pnl_pct None when cost <= 0 (D-166). | 2 | `cli.AppServiceBuilder` | `tests/portfolio/test_holdings_risk_builder.py` (TC-HRB-001..006) | 2026-11-16 |
| `ReleaseLagChecker` | `quant_cn.lake.release_lag_checker` | 2 | none | For every dataset with `known_on_rule: period_end_lag` and `release_dates` set, measure the observed lag (release date - period end) in that curated release-date dataset and count releases that came later than the rule | 2 | `cli.ResearchCommands` | `tests/lake/test_release_lag_checker.py` (TC-RLC-001..003) | 2026-09-27 |
| `RunLog` | `quant_cn.lake.run_log` | 2 | BaseRunLog | Append run and per-key events to `meta.run_log` (run_id, started_at, finished_at, kind, dataset, key, status, n_rows, duration_ms, message) and echo them to logging. | 3 | `cli.QuantCnCli`, `cli.ServiceBuilder`, `cli.ResearchCommands` | `tests/lake/test_run_log.py` (TC-RL-001..002) | 2026-09-27 |
| `TickerAliasMap` | `quant_cn.lake.ticker_alias_map` | 2 | none | Map retired codes to their surviving codes so a company has one history | 4 | `lake.DerivedViews`, `lake.LakeReader`, `cli.ServiceBuilder`, `cli.GaugeCommands` | `tests/lake/test_ticker_alias_map.py` (TC-TAM-001..004) | 2026-09-27 |
| `MarginSignalReader` | `quant_cn.lake.margin_signal_reader` | 2 | none | Margin signals per stock before a date: financing 20-day change, 20-day net buying and short balance as % of float cap, short balance over its 1-year max (plan 15 ph7m). | 2 | `portfolio.ConditionEvaluator`, `cli.AppServiceBuilder` | `tests/lake/test_margin_signal_reader.py` (TC-MSR-001) | 2026-11-13 |
| `BuybackLedger` | `quant_cn.lake.buyback_ledger` | 2 | none | Buyback programmes from curated.repurchase, point in time: planned amount, cumulative executed amount, state; money executed in a window (plan 23, D-154). | 5 | `lake.ShareholderYieldReader`, `portfolio.BuybackMonitorBuilder`, `cli.ReportCommands` | `tests/lake/test_buyback_ledger.py` (TC-BBL-001..005) | 2026-11-13 |
| `ShareholderYieldReader` | `quant_cn.lake.shareholder_yield_reader` | 2 | none | Dividend yield (dv_ttm) + executed buybacks over 12 months ÷ total market cap per stock; condition metrics incl. the largest live plan as % of market cap (plan 23, D-154). | 4 | `portfolio.ConditionEvaluator`, `cli.AppServiceBuilder` | `tests/lake/test_shareholder_yield_reader.py` (TC-SYR-001..002) | 2026-11-13 |
| `ChipStructureReader` | `quant_cn.lake.chip_structure_reader` | 2 | none | 筹码结构 signals as known on a date: holder and institutional change, northbound (last two disclosures), margin, large / small order weekly flows, unlocks, insider sales, RetailGauge (derived.retail_gauge with flags and streaks); winner rate and cost-band gaps (close vs cost_15 / 85pct) from cyq_perf (plan 15 ph7f, plan 21 ph4). | 1 | `portfolio.ConditionEvaluator`, `cli.AppServiceBuilder`, `portfolio.OpportunityScreen`, `cli.GaugeCommands` | `tests/lake/test_chip_structure_reader.py` (TC-CSR-001..004) | 2026-11-13 |
| `FundamentalSignalReader` | `quant_cn.lake.fundamental_signal_reader` | 2 | none | Single-quarter GM and deducted-profit YoY, TTM OCF / NP from statement versions known on a date; latest manual-series values (plan 15 ph7f). | 2 | `portfolio.ConditionEvaluator`, `cli.AppServiceBuilder` | `tests/lake/test_fundamental_signal_reader.py` (TC-FSR-001..003) | 2026-11-13 |
| `StatementVersionReader` | `quant_cn.lake.statement_version_reader` | 2 | none | Statement values per (company, period, field) as known on a date: latest known_on <= as_of, or the first announced version with its known_on (D-124); retired codes mapped (plan 16 ph1, plan 18 ph1) | 2 | `lake.FundamentalSignalReader`, `cli.AppServiceBuilder`, `portfolio.OpportunityScreen`, `cli.GaugeCommands` | `tests/lake/test_statement_version_reader.py` (TC-SVR-001..005) | 2026-11-09 |
| `TradingCalendar` | `quant_cn.lake.trading_calendar` | 2 | none | Answer trading-day questions (sessions in a range, is_open, next, prev) from the SSE calendar in the lake | 5 | `data_loading.DateSweepFetcher.list_keys`, `data_loading.FetcherFactory`, `cli.ServiceBuilder`, `lake.EffectiveDateResolver`, `lake.LakeReader`, `factor.FactorFactory` | `tests/lake/test_trading_calendar.py` (TC-TCA-001..004) | 2026-09-27 |
| `CompactStep` | `quant_cn.pipeline.curate_pipeline` | 6 | BaseStep | Adapt Compactor to a pipeline step: one unit per dataset. | 3 | `pipeline.CuratePipeline` | `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..001) | 2026-09-27 |
| `DeriveStep` | `quant_cn.pipeline.curate_pipeline` | 6 | BaseStep | Build the derived views and the PIT states view, then record a digest per derived view (hash digest for `derived.risk_*`, D-135). | 5 | `pipeline.CuratePipeline`, `pipeline.FeatureStep`, `cli.ServiceBuilder`, `pipeline.RiskModelStep` | `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..006) | 2026-09-27 |
| `CuratePipeline` | `quant_cn.pipeline.curate_pipeline` | 6 | none | Rebuild everything below raw/: compact every dataset, create derived views and PIT states, regenerate lake indexes, and record digests in meta/manifest/derived_digests.json. | 1 | `cli.ServiceBuilder` | `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..003) | 2026-09-27 |
| `FetchStep` | `quant_cn.pipeline.download_pipeline` | 6 | BaseStep | Adapt one dataset's fetcher to a pipeline step: keys computed in list_units (so the calendar fetched earlier in the run is visible), catalog view refreshed after the run. | 3 | `pipeline.DownloadPipeline.run` | `tests/pipeline/test_download_pipeline.py` (TC-DP-002..002) | 2026-09-27 |
| `DownloadPipeline` | `quant_cn.pipeline.download_pipeline` | 6 | none | Resolve which datasets and date ranges to download, run one FetchStep per dataset through the runner, and regenerate the lake indexes | 1 | `cli.ServiceBuilder` | `tests/pipeline/test_download_pipeline.py` (TC-DP-001..007) | 2026-09-27 |
| `EvaluationStep` | `quant_cn.pipeline.evaluation_step` | 6 | BaseStep | Evaluate every factor in derived.features (FactorEvaluator, one factor at a time to bound memory, forward returns from the open of t+1 on dense prices), apply the campaign-level adjustment once over all factor x horizon tests, and write derived/reports/<campaign>/ ic_series, ic_test and quantiles | 3 | `cli.ServiceBuilder` | `tests/pipeline/test_evaluation_step.py` (TC-ES-001..002) | 2026-09-27 |
| `FeatureStep` | `quant_cn.pipeline.feature_step` | 6 | BaseStep | Build derived/features, one file per year from the campaign start: the six library factors (FactorFactory, PIT inputs from LakeReader), restricted to universe members, preprocessed (winsorise -> standardise -> neutralise on Shenwan L1 + log market cap, D-093) and the combined "score" (SignalCombiner), as FACTOR_PANEL | 3 | `cli.ServiceBuilder` | `tests/pipeline/test_feature_step.py` (TC-FS-001..002) | 2026-09-27 |
| `PrefectRunner` | `quant_cn.pipeline.prefect_runner` | 6 | BaseRunner | Same contract as LocalRunner, executed as a Prefect flow named "quant_cn <kind>" whose run name is the RunLog run id | 1 | `cli.ServiceBuilder` | `tests/pipeline/test_prefect_runner.py` (TC-PFR-001..003) | 2026-09-27 |
| `PipelineReport` | `quant_cn.pipeline.runner` | 6 | none | Result of one pipeline run: its id, overall status and one StepReport per step. | 2 | `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.BaseRunner`, `pipeline.CuratePipeline`, `pipeline.PrefectRunner` | `tests/pipeline/test_runner.py` (TC-LR-001..001) | 2026-09-27 |
| `BaseRunner` | `quant_cn.pipeline.runner` | 6 | ABC | Extension point for how steps are executed (local now, Prefect later, D-022) | 1 | `pipeline.LocalRunner`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`, `pipeline.PrefectRunner`, `cli.ServiceBuilder` | `tests/pipeline/test_runner.py` (TC-LR-001..001) | 2026-09-27 |
| `LocalRunner` | `quant_cn.pipeline.runner` | 6 | BaseRunner | Run steps serially in this process with a rich progress bar per step | 1 | `cli.ServiceBuilder` | `tests/pipeline/test_runner.py` (TC-LR-001..003) | 2026-09-27 |
| `UniverseStep` | `quant_cn.pipeline.universe_step` | 6 | BaseStep | Build UNIVERSE_PANEL: one row per stock listed on each session (list_date <= t < delist_date | 3 | `cli.ServiceBuilder` | `tests/core/docs/test_contract_checker.py`, `tests/pipeline/test_universe_step.py` (TC-US-001..004) | 2026-09-27 |
| `AppServiceBuilder` | `quant_cn.app_service_builder` | 8 | none | Wire the app's watchlist and holdings-risk builders with condition evaluation (chips, statements, series) and the position reviewer (plan 15 ph7f); style ETF heat from etf_proxy.json (ph7g); sector monitor and 财报季信号 builders (plans 31, 35). | 5 | `cli.ResearchCommands` | `tests/test_app_service_builder.py` (TC-ASB-001..004) | 2026-11-18 |
| `ReportCommands` | `quant_cn.report_commands` | 8 | none | CLI `morning-report`: last session from the lake calendar, build and send (or dry-run) the two e-mails; `macro-monitor` / `futures-monitor` / `volatility-monitor` / `smallcap-watch` (plan 30) and others write their JSON; kept out of cli.py (size limit). | 1 | `cli.QuantCnCli` | `tests/test_report_commands.py` (TC-RPC-001..012) | 2026-11-17 |
| `ServiceBuilder` | `quant_cn.service_builder` | 8 | none | Wire services for the CLI commands (the composition root's constructors): download and curate pipelines with the chosen runner, and the project catalog. | 8 | `cli.QuantCnCli`, `cli.ResearchCommands` | `tests/test_cli.py` (TC-QCC-002..003) | 2026-09-27 |
| `BlockBootstrap` | `quant_cn.statistic.block_bootstrap` | 4 | none | Resample a time series (or several aligned series with the same draws) in blocks so serial correlation survives: stationary bootstrap with geometric block lengths (Politis & Romano 1994) or circular block bootstrap with fixed blocks (Politis & Romano 1992) | 4 | `statistic.IcSignificance`, `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_block_bootstrap.py` (TC-BB-001..004) | 2026-09-27 |
| `HacVariance` | `quant_cn.statistic.hac_variance` | 4 | none | Heteroskedasticity- and autocorrelation-consistent variance of a sample mean with the Bartlett kernel (Newey & West 1987 | 4 | `statistic.IcSignificance`, `cli.ServiceBuilder` | `tests/statistic/test_hac_variance.py` (TC-HAC-001..004) | 2026-09-27 |
| `IcCalculator` | `quant_cn.statistic.ic_calculator` | 4 | none | Per-date information coefficient between factor values and forward returns across the universe: IC_t = corr_rank(f_{i,t}, r_{i,t->t+h}) (Spearman | 2 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_ic_calculator.py` (TC-ICC-001..004) | 2026-09-27 |
| `IcSignificance` | `quant_cn.statistic.ic_significance` | 4 | none | The §2 tests for one factor at one horizon: Newey-West t on mean IC (Newey & West 1987, 1994, prewhitened per D-090), stationary block-bootstrap CI of mean IC and ICIR (Politis & Romano 1994), Fisher-z / Stouffer screen, sign consistency per sub-period, single break in mean (Bai & Perron 1998 | 4 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_ic_significance.py` (TC-ICS-001..005) | 2026-09-27 |
| `MultipleTestingAdjuster` | `quant_cn.statistic.multiple_testing_adjuster` | 4 | none | Adjust the p-values of many factor tests run in one campaign: Holm step-down FWER (Holm 1979), Benjamini-Hochberg FDR (1995), Benjamini-Hochberg-Yekutieli FDR under arbitrary dependence (2001), Romano-Wolf bootstrap step-down FWER (Romano & Wolf 2005, 2016), and the Harvey-Liu-Zhu (2016) /t/ >= 3.0 hurdle | 5 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_multiple_testing_adjuster.py` (TC-MTA-001..005) | 2026-09-27 |
| `Neutralizer` | `quant_cn.statistic.neutralizer` | 4 | none | Remove what industry membership and numeric exposures (e.g | 1 | `factor.FactorPreprocessor`, `cli.ServiceBuilder` | `tests/statistic/test_neutralizer.py` (TC-NEU-001..002) | 2026-09-27 |
| `QuantileReturns` | `quant_cn.statistic.quantile_returns` | 4 | none | Sort names into n quantiles of the factor within each date and horizon, and report each quantile's equal-weighted mean forward return plus the long-short spread (top minus bottom, stored as quantile 0): the monotone "ladder" that complements the IC. | 1 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_quantile_returns.py` (TC-QR-001..002) | 2026-09-27 |
| `ReturnStats` | `quant_cn.statistic.return_stats` | 4 | none | Summarise a series of period returns: annualised mean and volatility, Sharpe (per period and annualised with sqrt(244 / h)), maximum drawdown of the compounded path, hit rate, skewness and non-excess kurtosis (the PSR / DSR inputs of Bailey & López de Prado 2012). | 1 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_return_stats.py` (TC-RS-001..002) | 2026-09-27 |
| `Standardizer` | `quant_cn.statistic.standardizer` | 4 | none | Put factor values on a common scale within each date: z = (x - m) / s with m the equal-weighted mean (or a weighted mean, e.g | 1 | `factor.FactorPreprocessor`, `factor.SignalCombiner`, `cli.ServiceBuilder` | `tests/statistic/test_standardizer.py` (TC-STD-001..002) | 2026-09-27 |
| `TrialLog` | `quant_cn.statistic.trial_log` | 4 | none | Record every factor / parameter / horizon variant evaluated in a campaign, including the failures, because the deflated Sharpe ratio (Bailey & López de Prado 2014) and the multiple-testing adjusters need the number and dispersion of all trials, not just the winners | 5 | `factor.FactorEvaluator`, `pipeline.EvaluationStep` | `tests/statistic/test_trial_log.py` (TC-TL-001..004) | 2026-09-27 |
| `Winsorizer` | `quant_cn.statistic.winsorizer` | 4 | none | Clip extreme factor values within each date so a few outliers do not dominate ranks, z-scores or regressions: median +- k * 1.4826 * MAD (robust default) or the q / 1 - q cross-sectional quantiles. | 1 | `factor.FactorPreprocessor`, `cli.ServiceBuilder` | `tests/statistic/test_winsorizer.py` (TC-WZ-001..002) | 2026-09-27 |
| `BaseChart` | `quant_cn.visualization.base_chart` | 7 | ABC | Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never objects from other packages) | 4 | `visualization.PriceChart`, `visualization.FactorChart` | `tests/visualization/test_charts.py` (TC-BCA-001..002) | 2026-09-27 |
| `ChartTheme` | `quant_cn.visualization.chart_theme` | 7 | none | The colour and font tokens every chart reads, so charts are written against roles, never raw hex | 1 | `visualization.BaseChart`, `visualization.PriceChart`, `visualization.FactorChart` | `tests/visualization/test_charts.py` (TC-CT-001..001) | 2026-09-27 |
| `FactorChart` | `quant_cn.visualization.factor_chart` | 7 | BaseChart | The four views of a factor campaign (plan 04 phase 6), one single-series chart each so identity never rests on colour: "ic_series" (IC_SERIES) the rolling mean IC of one factor and horizon with a band of +/- 1.96 sd / sqrt(window / h), the effective number of non-overlapping observations | 1 | `research_space/notebooks/20260930_factor_campaign_01.ipynb`, `plan 06 ReportBuilder` | `tests/visualization/test_factor_chart.py` (TC-FC-001..004) | 2026-09-27 |
| `PriceChart` | `quant_cn.visualization.price_chart` | 7 | BaseChart | Daily candles (backward-adjusted by default: OHLC x adj_factor) over a volume panel for one ticker | 1 | `research_space/main.ipynb` | `tests/visualization/test_charts.py` (TC-PC-001..003) | 2026-09-27 |
| `DocumentRule` | `quant_cn.core.document_source` | 1 | BaseModel | One title rule: a title matching `include` and not `exclude` (regular expressions) is a document of `doc_type` | 0 | `core.DocumentSource`, `data_loading.DocumentClassifier` | `tests/core/test_document_source.py` (TC-DSR-001..001) | 2026-11-07 |
| `DocumentSource` | `quant_cn.core.document_source` | 1 | BaseModel | One document source of config/documents.yaml: the curated metadata dataset listing the documents, its key columns, the PDF URL and file-name templates (`{column}` placeholders), the folder under `documents/`, and how a row gets its doc type (a fixed `doc_type` or title `rules`, first match wins) | 0 | `core.Config`, `data_loading.DocumentClassifier`, `data_loading.DocumentDownloader` | `tests/core/test_document_source.py` (TC-DSR-001..002) | 2026-11-07 |
| `DocumentViews` | `quant_cn.lake.document_views` | 2 | none | Expose the document manifest in the catalog. | 1 | `lake.LakeCatalog.refresh_views`, `cli.DocumentCommands` | `tests/lake/test_document_views.py` (TC-DOV-001..001) | 2026-11-07 |
| `RequestPacer` | `quant_cn.data_loading.request_pacer` | 3 | none | Run one request callable at a time-spaced rate with retries: request starts are at least `min_interval_s` apart across all threads sharing the pacer, and a call raising OSError, ValueError or KeyError is retried after `retry_sleep_s` up to `retries` times | 2 | `data_loading.BaseWebClient`, `data_loading.DocumentDownloader` | `tests/data_loading/test_document_downloader.py` (TC-RP-001..002) | 2026-11-07 |
| `BaseWebClient` | `quant_cn.data_loading.base_web_client` | 3 | BaseApiClient | Base for vendor clients that page a public website's JSON API (CNINFO, Eastmoney). | 1 | `data_loading.CninfoClient`, `data_loading.EastmoneyReportClient`, `data_loading.AppStoreClient`, `data_loading.CboeClient`, `data_loading.BaseHtmlListClient` | `tests/data_loading/test_web_clients.py` (TC-BWC-001..002) | 2026-11-17 |
| `CninfoClient` | `quant_cn.data_loading.cninfo_client` | 3 | BaseWebClient | List CNINFO announcements for the whole A-share market (`column=szse` covers SZ, SH and BJ) over a date range, optionally one category (e.g. | 2 | `cli.ServiceBuilder` | `tests/data_loading/test_web_clients.py` (TC-CNC-001..005) | 2026-11-07 |
| `EastmoneyReportClient` | `quant_cn.data_loading.eastmoney_report_client` | 3 | BaseWebClient | List Eastmoney (东方财富) broker research reports published in a date range for one report kind (`q_type` "0" stock, "1" industry, "2" strategy), following `pageNo` until `TotalPage`. | 2 | `cli.ServiceBuilder` | `tests/data_loading/test_web_clients.py` (TC-EMR-001..002) | 2026-11-07 |
| `AppStoreClient` | `quant_cn.data_loading.app_store_client` | 3 | BaseWebClient | One country's App Store top charts (legacy iTunes RSS JSON, top 100) flattened to rows: rank, app and artist ids, release date, price, capture time (D-137). | 2 | `cli.ServiceBuilder` | `tests/data_loading/test_web_clients.py` (TC-ASC-001..003) | 2026-11-11 |
| `CboeClient` | `quant_cn.data_loading.cboe_client` | 3 | BaseWebClient | Full daily history of one CBOE index (VIX) from the public CSV: YYYYMMDD dates, float OHLC (D-152). | 2 | `cli.ServiceBuilder` | `tests/data_loading/test_cboe_client.py` (TC-CBC-001..002) | 2026-11-13 |
| `BaseHtmlListClient` | `quant_cn.data_loading.base_html_list_client` | 3 | BaseWebClient | Base for clients of government sites that list monthly releases on paged HTML index pages and publish each as HTML tables (plan 31). | 6 | `data_loading.NbsHousePriceClient`, `data_loading.NppaGameClient` | `tests/data_loading/test_nbs_house_price_client.py` (TC-BHL-001..002) | 2026-11-17 |
| `PageLink` | `quant_cn.data_loading.base_html_list_client` | 3 | none (frozen dataclass) | One release linked from a list page: url, title, publication date from the url (plan 31). | 0 | `data_loading.BaseHtmlListClient`, `data_loading.NppaGameClient` | `tests/data_loading/test_nbs_house_price_client.py` (TC-BHL-001) | 2026-11-17 |
| `NbsHousePriceClient` | `quant_cn.data_loading.nbs_house_price_client` | 3 | BaseHtmlListClient | 国家统计局 70-city new-home and second-hand price indices (mom / yoy), city by city, from the monthly releases (plan 31). | 3 | `cli.ServiceBuilder` | `tests/data_loading/test_nbs_house_price_client.py` (TC-NHP-001..004) | 2026-11-17 |
| `NppaGameClient` | `quant_cn.data_loading.nppa_game_client` | 3 | BaseHtmlListClient | 国家新闻出版署 game approvals (版号), domestic and imported, one row per approval (plan 31). | 3 | `cli.ServiceBuilder` | `tests/data_loading/test_nppa_game_client.py` (TC-NGC-001..002) | 2026-11-17 |
| `ManualSeriesClient` | `quant_cn.data_loading.manual_series_client` | 3 | BaseApiClient | Hand-entered cycle series (public `config/manual_series.yaml` + git-ignored `config/local.manual_series.yaml`) served as one vendor frame for curated `alt/manual_series`, known_on = published (plan 20, D-139). | 1 | `cli.ServiceBuilder` | `tests/data_loading/test_manual_series_client.py` (TC-MSC-001..003) | 2026-11-12 |
| `ManualSeriesDef` | `quant_cn.data_loading.manual_series_client` | 3 | BaseModel | One manual series definition: id, name, unit, freq, kind, linked ts_codes. | 0 | `data_loading.ManualSeriesClient`, `data_loading.ManualSeriesFile` | `tests/data_loading/test_manual_series_client.py` (TC-MSC-001) | 2026-11-12 |
| `ManualObservation` | `quant_cn.data_loading.manual_series_client` | 3 | BaseModel | One manual value: series, date, value, published (>= date), source URL, note, revision flag. | 0 | `data_loading.ManualSeriesClient`, `data_loading.ManualSeriesFile` | `tests/data_loading/test_manual_series_client.py` (TC-MSC-002) | 2026-11-12 |
| `ManualSeriesFile` | `quant_cn.data_loading.manual_series_client` | 3 | BaseModel | Content of one manual-series YAML file: series and observations. | 0 | `data_loading.ManualSeriesClient` | `tests/data_loading/test_manual_series_client.py` (TC-MSC-001) | 2026-11-12 |
| `SnapshotFetcher` | `quant_cn.data_loading.snapshot_fetcher` | 3 | EnumFetcher | Sweep for sources with no history: keys "<today>_<value>" from the Clock, run range ignored, never backfilled (D-137). | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_snapshot_fetcher.py` (TC-SNF-001..003) | 2026-11-11 |
| `DocumentClassifier` | `quant_cn.data_loading.document_classifier` | 3 | none | Give each listed document its type: the source's fixed `doc_type`, or the first title rule whose `include` matches and whose `exclude` does not (e.g. | 1 | `data_loading.DocumentDownloader` | `tests/data_loading/test_document_downloader.py` (TC-DCL-001..002) | 2026-11-07 |
| `DocumentDownloader` | `quant_cn.data_loading.document_downloader` | 3 | none | Download the PDFs listed in a document source's curated metadata (config/documents.yaml) into `documents/<folder>/<doc_type>/<YYYY>/<MM>/<file>` (D-101); manifest parts through DocumentManifestWriter. | 3 | `cli.DocumentCommands` | `tests/data_loading/test_document_downloader.py` (TC-DD-001..006) | 2026-11-12 |
| `DocumentManifestWriter` | `quant_cn.data_loading.document_manifest_writer` | 3 | none | Write one append-only manifest part (MANIFEST_COLUMNS, zstd parquet, tmp + rename) under meta/document_manifest/; later rows per doc_id supersede earlier ones (D-101, D-149) | 3 | `data_loading.DocumentDownloader`, `data_loading.DocumentRetyper` | `tests/data_loading/test_document_retyper.py` (TC-DMW-001) | 2026-11-12 |
| `DocumentRetyper` | `quant_cn.data_loading.document_retyper` | 3 | none | Re-apply changed title rules to downloaded documents: a new type moves the file and appends a manifest row, no matching rule appends `excluded` (plan 18 ph2, D-149) | 1 | (none yet) | `tests/data_loading/test_document_retyper.py` (TC-DRT-001) | 2026-11-12 |
| `DocumentCommands` | `quant_cn.document_commands` | 8 | none | The document-side CLI commands `download-docs` (plan 12 phase 2, D-101) and `import-labels` (plan 28 ph0: label files -> derived/labels parquet) | 1 | `cli.QuantCnCli` | `tests/test_cli.py` (TC-QCC-010, 015) | 2026-11-14 |
| `GaugeCommands` | `quant_cn.gauge_commands` | 8 | none | The RetailGauge CLI commands `retail-gauge` (daily readings for a session range, one quarter at a time), `retail-gauge-backtest` (walk-forward + quarterly evaluation) (plan 21 ph3) and `opportunity-list` (daily list, ph4). | 1 | `cli.QuantCnCli` | `tests/test_cli.py` (TC-QCC-019..020) | 2026-11-18 |
| `OpportunitySettings` | `quant_cn.core.opportunity_settings` | 1 | BaseModel | Universe, rule thresholds, required rules and list sizes of the daily opportunity list from config/discovery_rules.yaml `opportunity` (plan 21 ph4). | 2 | `portfolio.OpportunityRules`, `portfolio.OpportunityScreen`, `portfolio.StyleFitChecker`, `cli.GaugeCommands` | `tests/core/test_opportunity_settings.py` (TC-OPS-001) | 2026-11-18 |
| `OpportunityRules` | `quant_cn.portfolio.opportunity_rules` | 5 | none | Rule hits (retail leaving, inflow weeks, earnings YoY / QoQ, valuation below median, style fit) and the ranked list: listed = every rule, near = one non-required rule missing; avoid never listed; NaN never hits (plan 21 ph4). | 2 | `portfolio.OpportunityScreen`, `cli.GaugeCommands` | `tests/portfolio/test_opportunity_rules.py` (TC-OPR-001..003) | 2026-11-18 |
| `StyleFitChecker` | `quant_cn.portfolio.style_fit_checker` | 5 | none | Factor-fit rule: adding a stock at fit_weight must not raise the absolute exposure of the book's largest styles (plan 21 ph4). | 1 | `portfolio.OpportunityScreen`, `cli.GaugeCommands` | `tests/portfolio/test_style_fit_checker.py` (TC-SFC-001..002) | 2026-11-18 |
| `OpportunityScreen` | `quant_cn.portfolio.opportunity_screen` | 5 | none | Daily opportunity list: cap / ST / holdings universe with a recent RetailGauge reading, signal row, earnings, valuation and fit metrics, OpportunityRules ranking, new entries vs the last list -> derived/opportunity_list (plan 21 ph4). | 3 | `cli.GaugeCommands` | `tests/portfolio/test_opportunity_screen.py` (TC-OSC-001..002) | 2026-11-18 |
| `OpportunityDocument` | `quant_cn.portfolio.opportunity_document` | 5 | none | opportunities.json for the app and the morning report: new listed, stayed, near-misses with rules hit / missing, dropped names, rule thresholds (plan 21 ph5). | 2 | `cli.GaugeCommands` | `tests/portfolio/test_opportunity_document.py` (TC-OPD-001..002) | 2026-11-19 |
| `ReportPages` | `quant_cn.quant_cn.industry_graph.pdf_text_extractor` | 4 | none | The text of one report PDF, page by page, plus its outline (bookmarks) when present. | 1 | `industry_graph.PdfTextExtractor`, `industry_graph.SectionDetector`, `industry_graph.AnnualReportParser` | `tests/industry_graph/test_report_parsing.py` (TC-PTE-001..001) | 2026-11-07 |
| `PdfTextExtractor` | `quant_cn.quant_cn.industry_graph.pdf_text_extractor` | 4 | none | Read the native text layer of a PDF page by page (no OCR; D-102) and remove the running header and footer: a line with at least four letters or CJK characters that, with digits ignored, appears on at least `header_share` of the pages (e.g. | 2 | `industry_graph.AnnualReportParser` | `tests/industry_graph/test_report_parsing.py` (TC-PTE-001..003) | 2026-11-07 |
| `Section` | `quant_cn.quant_cn.industry_graph.section_detector` | 4 | none | One located section: its key, the heading-matched start page and the page before the next section (or the chapter end), 1-based, inclusive. | 0 | `industry_graph.SectionDetector`, `industry_graph.ParsedReport` | `tests/industry_graph/test_report_parsing.py` (TC-SD-001..001) | 2026-11-07 |
| `SectionDetector` | `quant_cn.quant_cn.industry_graph.section_detector` | 4 | none | Locate the MD&A chapter (管理层讨论与分析, 第三节 in the 2021 standard; 第二节/第四节 in older or exchange-specific layouts; 第二章 董事会报告 for A+H; BSE 业务概要 / 第五节 重大事件) and the chain sections inside it by heading text, not by number. | 3 | `industry_graph.AnnualReportParser`, `industry_graph.GuidanceExtractor` | `tests/industry_graph/test_report_parsing.py` (TC-SD-001..006) | 2026-11-07 |
| `CounterpartyRow` | `quant_cn.quant_cn.industry_graph.counterparty_table_parser` | 4 | none | One ranked customer or supplier of a top-5 table. | 1 | `industry_graph.CounterpartyTable`, `industry_graph.CounterpartyTableParser` | `tests/industry_graph/test_report_parsing.py` (TC-CTP-001..001) | 2026-11-07 |
| `CounterpartyTable` | `quant_cn.quant_cn.industry_graph.counterparty_table_parser` | 4 | none | The top-5 customers or suppliers of one report: stated totals and the ranked rows (empty when only the totals sentence is disclosed, as on the SSE main board). | 1 | `industry_graph.CounterpartyTableParser`, `industry_graph.ParsedReport` | `tests/industry_graph/test_report_parsing.py` (TC-CTP-004..004) | 2026-11-07 |
| `CounterpartyTableParser` | `quant_cn.quant_cn.industry_graph.counterparty_table_parser` | 4 | none | Parse the "主要销售客户和主要供应商情况" block into a customer and a supplier CounterpartyTable. | 1 | `industry_graph.AnnualReportParser` | `tests/industry_graph/test_report_parsing.py` (TC-CTP-001..010) | 2026-11-07 |
| `ParsedReport` | `quant_cn.quant_cn.industry_graph.annual_report_parser` | 4 | none | What the rule-based pass extracts from one annual report. | 1 | `industry_graph.AnnualReportParser` | `tests/industry_graph/test_report_parsing.py` (TC-ARP-001..001) | 2026-11-07 |
| `AnnualReportParser` | `quant_cn.quant_cn.industry_graph.annual_report_parser` | 4 | none | Run the rule-based pass of plan 12 phase 3 on one annual report: read the pages (PdfTextExtractor), locate the MD&A chapter and chain sections (SectionDetector), and parse the top-5 customer and supplier tables (CounterpartyTableParser). | 2 | `research_space` | `tests/industry_graph/test_report_parsing.py` (TC-ARP-001..003) | 2026-11-07 |
| `LlmReply` | `quant_cn.quant_cn.core.base_llm_client` | 1 | none | One LLM answer as parsed JSON, with the model and token usage, and whether it came from the response cache (a cached reply costs nothing and makes rebuilds deterministic). | 0 | `core.BaseLlmClient`, `data_loading.DeepSeekClient` | `tests/data_loading/test_deep_seek_client.py` (TC-DSC-001..001) | 2026-11-07 |
| `BaseLlmClient` | `quant_cn.quant_cn.core.base_llm_client` | 1 | ABC | Abstract chat-completion client that returns a JSON object: one system prompt, one user message, an optional model override. | 1 | `data_loading.DeepSeekClient`, `industry_graph.ApplicationExtractor` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-11-07 |
| `LlmConfig` | `quant_cn.quant_cn.core.config` | 1 | BaseModel | The LLM endpoint used for extraction (D-098): OpenAI-compatible chat completions URL, default model, limits, and the API key, which comes from env DEEPSEEK_API_KEY only. | 0 | `core.Config`, `data_loading.DeepSeekClient` | `tests/core/test_config.py` (TC-C-014..014) | 2026-11-07 |
| `DeepSeekClient` | `quant_cn.quant_cn.data_loading.deep_seek_client` | 3 | BaseLlmClient | Call the DeepSeek (OpenAI-compatible) chat-completions endpoint with JSON output and temperature 0 and model reasoning off unless LlmConfig.thinking, paced and retried by RequestPacer. | 4 | `research_space` | `tests/data_loading/test_deep_seek_client.py` (TC-DSC-001..003) | 2026-11-07 |
| `Evidence` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | none | A verbatim quote and the page it was found on (after the quote check). | 0 | `industry_graph.ApplicationResult` | `tests/industry_graph/test_application_extractor.py` (TC-AE-002..002) | 2026-11-07 |
| `ApplicationResult` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | none | What the model found in one report, after validation: per revenue line the downstream applications (taxonomy node or proposed name, main/secondary, evidence) and customer types; named counterparties with role and evidence; and the items dropped because their quote was not in the text. | 0 | `industry_graph.ApplicationExtractor` | `tests/industry_graph/test_application_extractor.py` (TC-AE-001..001) | 2026-11-07 |
| `ApplicationExtractor` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | none | Send the business / industry pages of one report, its revenue lines and the candidate downstream taxonomy nodes to the LLM, and keep only answers whose verbatim quote is found in the supplied pages (whitespace ignored). | 1 | `research_space` | `tests/industry_graph/test_application_extractor.py` (TC-AE-001..003) | 2026-11-07 |
| `ApplicationItem` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | BaseModel | One downstream application of a revenue line as the LLM returned it. | 0 | `industry_graph.LineItem` | `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003) | 2026-11-07 |
| `LineItem` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | BaseModel | One revenue line with its applications and customer types as returned. | 0 | `industry_graph.ApplicationReply` | `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003) | 2026-11-07 |
| `CounterpartyItem` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | BaseModel | One company named in the text, with its role, as returned. | 0 | `industry_graph.ApplicationReply` | `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003) | 2026-11-07 |
| `ApplicationReply` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | BaseModel | The whole LLM reply of one report, validated before the quote check. | 0 | `industry_graph.ApplicationExtractor` | `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003) | 2026-11-07 |
| `QuoteChecker` | `quant_cn.quant_cn.industry_graph.quote_checker` | 4 | none | Hold the pages sent to an LLM and accept a returned quote only if it occurs verbatim (whitespace ignored) on one of them. | 2 | `industry_graph.ApplicationExtractor`, `industry_graph.ValuationExtractor`, `industry_graph.BaseQuotedExtractor` | `tests/industry_graph/test_valuation_extractor.py` (TC-QC-001..002) | 2026-11-07 |
| `ValuationItem` | `quant_cn.quant_cn.industry_graph.valuation_extractor` | 4 | BaseModel | Base of the reply shapes: unknown keys ignored, so a richer reply still validates. | 0 | `industry_graph.ValuationReply` | `tests/industry_graph/test_valuation_extractor.py` (TC-VE-003..003) | 2026-11-07 |
| `ValuationReply` | `quant_cn.quant_cn.industry_graph.valuation_extractor` | 4 | ValuationItem | The LLM reply for one broker report, before the quote check: rating, target price, methods (multiple, implied or target, base year), forecasts, comparables, assumptions. | 0 | `industry_graph.ValuationExtractor` | `tests/industry_graph/test_valuation_extractor.py` (TC-VE-003..003) | 2026-11-07 |
| `ValuationResult` | `quant_cn.quant_cn.industry_graph.valuation_extractor` | 4 | none | One report's valuation after validation: only quote-checked target price, methods and assumptions; methods carry `multiple_kind` (D-109) and a base year; comparables carry a ts_code when it could be resolved. | 0 | `industry_graph.ValuationExtractor` | `tests/industry_graph/test_valuation_extractor.py` (TC-VE-001..001) | 2026-11-07 |
| `ValuationExtractor` | `quant_cn.quant_cn.industry_graph.valuation_extractor` | 4 | none | Extract how a broker values a company (plan 13, D-105, D-109). | 2 | `research_space` | `tests/industry_graph/test_valuation_extractor.py` (TC-VE-001..003) | 2026-11-07 |
| `QuarterlyNoteItem` | `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` | 4 | BaseModel | One fact the LLM found in the notes, before the quote check. | 0 | `industry_graph.QuarterlyNoteReply` | `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-003..003) | 2026-11-07 |
| `QuarterlyNoteReply` | `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` | 4 | BaseModel | The LLM reply for one quarterly report. | 0 | `industry_graph.QuarterlyNoteExtractor` | `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-003..003) | 2026-11-07 |
| `QuarterlyNoteResult` | `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` | 4 | none | The quote-checked facts of one quarterly report. | 0 | `industry_graph.QuarterlyNoteExtractor` | `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-002..002) | 2026-11-07 |
| `QuarterlyNoteExtractor` | `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` | 4 | none | Q1 and Q3 reports carry no business chapter; their only narrative is the "主要会计数据、 财务指标发生变动的情况及原因" table and the "其他提醒事项" note. | 3 | `lake` | `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-001..003) | 2026-11-07 |
| `LegacyLabelImporter` | `quant_cn.industry_graph.legacy_label_importer` | 4 | none | Turn the label files of earlier runs into LabelStore rows: document key, doc type, period, known_on from the document lists, anchored keys for company-only records; skips bad codes, excluded keys and documents public before their period ended; each source file replaces its own earlier rows (plan 28 ph0–1). | 4 | `cli.DocumentCommands` | `tests/industry_graph/test_legacy_label_importer.py` (TC-LLI-001..007) | 2026-11-15 |
| `LenientItem` | `quant_cn.quant_cn.industry_graph.lenient_item` | 4 | BaseModel | Pydantic base for LLM reply items: unknown keys ignored, float fields accept numeric text ("30%", "1,234.5万元"). | 0 | `industry_graph.GuidanceItem`, `industry_graph.ContractItem`, `industry_graph.QuotedItem` | `tests/industry_graph/test_lenient_item.py` (TC-LI-001..001) | 2026-11-13 |
| `GuidanceItem` | `quant_cn.quant_cn.industry_graph.guidance_extractor` | 4 | LenientItem | One guidance statement the LLM found, before the checks. | 0 | `industry_graph.GuidanceReply` | `tests/industry_graph/test_guidance_extractor.py` (TC-GE-003..003) | 2026-11-13 |
| `GuidanceReply` | `quant_cn.quant_cn.industry_graph.guidance_extractor` | 4 | BaseModel | The LLM reply for one guidance document. | 0 | `industry_graph.GuidanceExtractor` | `tests/industry_graph/test_guidance_extractor.py` (TC-GE-003..003) | 2026-11-13 |
| `GuidanceResult` | `quant_cn.quant_cn.industry_graph.guidance_extractor` | 4 | none | The checked guidance items of one document. | 0 | `industry_graph.GuidanceExtractor` | `tests/industry_graph/test_guidance_extractor.py` (TC-GE-002..002) | 2026-11-13 |
| `GuidanceExtractor` | `quant_cn.quant_cn.industry_graph.guidance_extractor` | 4 | none | Quote-checked quantitative guidance rows from an annual plan (outlook section), an IR record or an incentive draft's 业绩考核 pages (plan 18 ph3). | 2 | `lake` | `tests/industry_graph/test_guidance_extractor.py` (TC-GE-001..003) | 2026-11-13 |
| `ContractItem` | `quant_cn.quant_cn.industry_graph.contract_extractor` | 4 | LenientItem | One contract, bid win or period order total the LLM found, before the checks. | 0 | `industry_graph.ContractReply` | `tests/industry_graph/test_contract_extractor.py` (TC-CEX-002..002) | 2026-11-13 |
| `ContractReply` | `quant_cn.quant_cn.industry_graph.contract_extractor` | 4 | BaseModel | The LLM reply for one contract announcement. | 0 | `industry_graph.ContractExtractor` | `tests/industry_graph/test_contract_extractor.py` (TC-CEX-002..002) | 2026-11-13 |
| `ContractResult` | `quant_cn.quant_cn.industry_graph.contract_extractor` | 4 | none | The checked contract rows of one announcement, amounts scaled to currency units. | 0 | `industry_graph.ContractExtractor` | `tests/industry_graph/test_contract_extractor.py` (TC-CEX-001..001) | 2026-11-13 |
| `ContractExtractor` | `quant_cn.quant_cn.industry_graph.contract_extractor` | 4 | none | Quote-checked contract rows (contract / bid with status, or period order total) from 重大合同 / 中标 / 经营数据 announcements (plan 18 ph3). | 1 | `lake` | `tests/industry_graph/test_contract_extractor.py` (TC-CEX-001..002) | 2026-11-13 |
| `QuotedItem` | `quant_cn.quant_cn.industry_graph.base_quoted_extractor` | 4 | LenientItem | Base of one reply item of a plan 28 extractor: subclass fields plus verbatim quote and page. | 0 | `industry_graph.BaseQuotedExtractor`, `industry_graph.InquiryCounterpartyItem`, `industry_graph.InquiryCustomerExtractor` | `tests/industry_graph/test_base_quoted_extractor.py` (TC-BQE-002..002) | 2026-11-15 |
| `QuotedResult` | `quant_cn.quant_cn.industry_graph.base_quoted_extractor` | 4 | none | The checked items of one document, with dropped count, tokens and pages sent. | 0 | `industry_graph.BaseQuotedExtractor` | `tests/industry_graph/test_base_quoted_extractor.py` (TC-BQE-001..001) | 2026-11-15 |
| `BaseQuotedExtractor` | `quant_cn.quant_cn.industry_graph.base_quoted_extractor` | 4 | ABC | Base of the plan 28 ph2 document extractors: prompt file, per-item validation, quote check, subclass item check; keyword page picking; is_item_anchored hook (D-161 updates 6, 8). | 7 | `industry_graph.InquiryCustomerExtractor`, `industry_graph.IrCustomerExtractor`, `industry_graph.DealExtractor`, `industry_graph.OperatingDataExtractor`, `industry_graph.BuybackTermsExtractor` | `tests/industry_graph/test_base_quoted_extractor.py` (TC-BQE-001..005) | 2026-11-16 |
| `InquiryCounterpartyItem` | `quant_cn.quant_cn.industry_graph.inquiry_customer_extractor` | 4 | QuotedItem | One customer or supplier named in an inquiry reply (role, name, alias, period, rank, amount, share, share_base, product, region), before the checks. | 0 | `industry_graph.InquiryCustomerExtractor` | `tests/industry_graph/test_inquiry_customer_extractor.py` (TC-ICE-001..001) | 2026-11-15 |
| `InquiryCustomerExtractor` | `quant_cn.quant_cn.industry_graph.inquiry_customer_extractor` | 4 | BaseQuotedExtractor | Quote-checked customer and supplier rows from exchange inquiry replies, real names behind 客户一…, share_base, is_named; name must be in the quote (plan 28 ph2). | 4 | `industry_graph.ProspectusExtractor`, `lake` | `tests/industry_graph/test_inquiry_customer_extractor.py` (TC-ICE-001..003) | 2026-11-16 |
| `CounterpartyName` | `quant_cn.quant_cn.industry_graph.counterparty_name` | 4 | none | Rules for an LLM-returned counterparty name: is_named (not 客户一 / 某 / 头部车企 / 第四名供应商 / 无) and is_in_text (name, alias or short form in a quote) (D-161 update 8). | 2 | `industry_graph.InquiryCustomerExtractor`, `industry_graph.IrCustomerExtractor`, `industry_graph.CompanyEdgeBuilder` | `tests/industry_graph/test_counterparty_name.py` (TC-CPN-001..003) | 2026-11-16 |
| `EntityMatch` | `quant_cn.quant_cn.industry_graph.entity_resolver` | 4 | none | Where one counterparty name resolved to: entity id, ts_code, method, group member. | 0 | `industry_graph.EntityResolver` | `tests/industry_graph/test_entity_resolver.py` (TC-ER-001..001) | 2026-11-16 |
| `EntityResolver` | `quant_cn.quant_cn.industry_graph.entity_resolver` | 4 | none | One entity id per counterparty name: alias map, A-share full and short names (current and former), region-less key, 4-character short-name prefix; group tails marked; else "x:<key>"; find_by_code confirms a proposed A-share code; find_by_alias resolves an LLM alias proposal by rule (plan 28 ph3, D-161 update 9; plan 31). | 4 | `lake`, `industry_graph.CompanyEdgeBuilder`, `industry_graph.GameCompanyBuilder` | `tests/industry_graph/test_entity_resolver.py` (TC-ER-001..008) | 2026-11-17 |
| `AliasItem` | `quant_cn.quant_cn.industry_graph.entity_alias_extractor` | 4 | BaseModel | One reply row of EntityAliasExtractor before the checks. | 0 | `industry_graph.EntityAliasExtractor` | `tests/industry_graph/test_entity_alias_extractor.py` (TC-EAX-001..001) | 2026-11-16 |
| `EntityAlias` | `quant_cn.quant_cn.industry_graph.entity_alias_extractor` | 4 | none | The entity one name stands for as the model proposed it: canonical, kind, is_member, listed code. | 0 | `industry_graph.EntityAliasExtractor` | `tests/industry_graph/test_entity_alias_extractor.py` (TC-EAX-001..001) | 2026-11-16 |
| `EntityAliasExtractor` | `quant_cn.quant_cn.industry_graph.entity_alias_extractor` | 4 | none | DeepSeek proposes the entity of a batch of counterparty names (canonical short name, kind, member of a group, security code hint) (plan 28 ph3, D-161 update 9). | 1 | `lake` | `tests/industry_graph/test_entity_alias_extractor.py` (TC-EAX-001..002) | 2026-11-16 |
| `EdgeItem` | `quant_cn.quant_cn.industry_graph.base_edge_reader` | 4 | none | One raw edge a document states (name, relation, stage, period, known_on, amount, share, share_base, product, quote, page), before resolution. | 0 | `industry_graph.BaseEdgeReader`, `industry_graph.CounterpartyEdgeReader`, `industry_graph.TopFiveEdgeReader`, `industry_graph.DealEdgeReader`, `industry_graph.CompanyEdgeBuilder` | `tests/industry_graph/test_edge_readers.py` (TC-BER-001..001) | 2026-11-16 |
| `BaseEdgeReader` | `quant_cn.quant_cn.industry_graph.base_edge_reader` | 4 | ABC | Base of the plan 28 ph4 readers that list the raw edges of one label-store row; build_period parses an item's own period text. | 2 | `industry_graph.CounterpartyEdgeReader`, `industry_graph.TopFiveEdgeReader`, `industry_graph.DealEdgeReader`, `industry_graph.CompanyEdgeBuilder` | `tests/industry_graph/test_edge_readers.py` (TC-BER-001..001) | 2026-11-16 |
| `CounterpartyEdgeReader` | `quant_cn.quant_cn.industry_graph.counterparty_edge_reader` | 4 | BaseEdgeReader | Raw edges of a counterparty-list row (plan 28 sets under items, applications under counterparties); roles mapped, subsidiary → holds; IR Q&A item date from dates[page-1]. | 1 | `lake`, `industry_graph.GraphBuilder`, `cli.DocumentCommands` | `tests/industry_graph/test_edge_readers.py` (TC-CER-001..002) | 2026-11-16 |
| `TopFiveEdgeReader` | `quant_cn.quant_cn.industry_graph.top_five_edge_reader` | 4 | BaseEdgeReader | Raw edges of the rule-parsed annual top-5 customer and supplier tables (named rows; share of revenue / purchases). | 1 | `lake`, `industry_graph.GraphBuilder`, `cli.DocumentCommands` | `tests/industry_graph/test_edge_readers.py` (TC-TFR-001..001) | 2026-11-16 |
| `DealEdgeReader` | `quant_cn.quant_cn.industry_graph.deal_edge_reader` | 4 | BaseEdgeReader | Raw invests_in edges of outward deals (new company, capital increase, stake purchase, acquisition, JV, fund) with status and stake. | 1 | `lake`, `industry_graph.GraphBuilder`, `cli.DocumentCommands` | `tests/industry_graph/test_edge_readers.py` (TC-DER-001..001) | 2026-11-16 |
| `CompanyEdgeBuilder` | `quant_cn.quant_cn.industry_graph.company_edge_builder` | 4 | none | company_edge rows: one per stated edge, counterparty resolved (EntityResolver), oriented seller → buyer, item period / known_on, non-flow shares cleared (plan 28 ph4, D-161 update 7). | 1 | `lake`, `industry_graph.GraphBuilder`, `cli.DocumentCommands` | `tests/industry_graph/test_company_edge_builder.py` (TC-CEB-001..003) | 2026-11-16 |
| `EdgeSpanBuilder` | `quant_cn.quant_cn.industry_graph.edge_span_builder` | 4 | none | edge_span rows: observations of one (src, dst, kind) joined into first / last seen, stage path, status active / ended / denied / silent, shares and amounts per period and base; point in time with as_of (plan 28 ph4, D-161 update 7). | 1 | `lake`, `industry_graph.GraphBuilder`, `cli.DocumentCommands` | `tests/industry_graph/test_edge_span_builder.py` (TC-ESB-001..003) | 2026-11-16 |
| `GraphBuilder` | `quant_cn.quant_cn.industry_graph.graph_builder` | 4 | none | Rebuild company_edge, edge_span and company_period from the label store and entity_map (EntityResolver, CompanyEdgeBuilder, EdgeSpanBuilder, CompanyPeriodBuilder); no LLM call, same lake → same tables (plan 28 ph4). | 2 | `cli.DocumentCommands` | `tests/industry_graph/test_graph_builder.py` (TC-GB-001..004) | 2026-11-16 |
| `CompanyPeriodBuilder` | `quant_cn.quant_cn.industry_graph.company_period_builder` | 4 | none | company_period, the company leaf: one row per (company, period, label set, document) over every label set, with doc type, known_on and n_items; payload stays in the LabelStore (plan 28 ph4). | 1 | `industry_graph.GraphBuilder`, `cli.DocumentCommands` | `tests/industry_graph/test_company_period_builder.py` (TC-CPB-001..002) | 2026-11-16 |
| `GraphQuery` | `quant_cn.quant_cn.industry_graph.graph_query` | 4 | none | Point-in-time questions to the plan 28 graph: find_leaf (company as known on a date), list_spans (edge spans as of a date), list_timeline (labels and edge observations by known_on); industry nodes: list_node_members, list_node_neighbours, list_node_history, list_node_lineage. | 7 | (none yet; plan 28 ph5 app) | `tests/industry_graph/test_graph_query.py` (TC-GQ-001..006) | 2026-11-19 |
| `NodeMemberBuilder` | `quant_cn.quant_cn.industry_graph.node_member_builder` | 4 | none | node_member: company → taxonomy product / segment per period from 主营构成 lines through ProductMatcher, with sales and revenue weight; unmapped and generic lines kept (plan 28 ph3b-1). | 1 | `cli.DocumentCommands` | `tests/industry_graph/test_node_member_builder.py` (TC-NMB-001..005) | 2026-11-16 |
| `NodeStatsBuilder` | `quant_cn.quant_cn.industry_graph.node_stats_builder` | 4 | none | Curation material from node_member: per-segment stats of a period, the change between two periods (joined / left companies), unmatched revenue lines by sector (plan 28 ph3b-2). | 3 | `lake` | `tests/industry_graph/test_node_stats_builder.py` (TC-NSB-001..003) | 2026-11-16 |
| `TaxonomyChange` | `quant_cn.quant_cn.industry_graph.taxonomy_change_set` | 4 | BaseModel | One change of a taxonomy version: upsert a node (name / segment / parent, aliases added and dropped) or retire it into a successor; kind and split_from feed the lineage. | 1 | `industry_graph.TaxonomyChangeSet`, `industry_graph.ProductTaxonomy`, `industry_graph.NodeLineageBuilder` | `tests/industry_graph/test_taxonomy_change_set.py` (TC-TCS-001..001) | 2026-11-17 |
| `TaxonomyChangeSet` | `quant_cn.quant_cn.industry_graph.taxonomy_change_set` | 4 | BaseModel | One accepted taxonomy version under config/industry_chain/_changes/<version>.yaml, applied in name order on top of v0 (plan 28 ph3b-4). | 1 | `industry_graph.ProductTaxonomy`, `industry_graph.NodeLineageBuilder`, `cli.DocumentCommands` | `tests/industry_graph/test_taxonomy_change_set.py` (TC-TCS-001..002) | 2026-11-17 |
| `NodeLineageBuilder` | `quant_cn.quant_cn.industry_graph.node_lineage_builder` | 4 | none | node_lineage rows per accepted taxonomy version (new, split, rename, move, alias, merge / retire) by diffing the taxonomy before and after; checks successors exist and retire chains are acyclic (plan 28 ph3b-4). | 1 | `cli.DocumentCommands` | `tests/industry_graph/test_node_lineage_builder.py` (TC-NLB-001..002) | 2026-11-17 |
| `NodeEdgeBuilder` | `quant_cn.quant_cn.industry_graph.node_edge_builder` | 4 | none | node_edge rows (plan 28 ph4d): supplier segment -> buyer segment per year from A-share company_edge pairs (sales; holds / invests_in as invests) spread over node_member segment weights (weight = Σ w_src × w_dst), merged with taxonomy prior edges (prior / evidenced / both); as_of point in time. | 1 | `cli.DocumentCommands` | `tests/industry_graph/test_node_edge_builder.py` (TC-NEB-001..004) | 2026-11-19 |
| `GameCompanyBuilder` | `quant_cn.industry_graph.game_company_builder` | 4 | none | game_company: one row per approved game (版号) and role (operator / publisher) with the listed company behind the holder, by rule or through its game_alias proposal; publishing houses marked; unresolved holders listed for review (plan 31 ph2). | 2 | `cli.DocumentCommands` | `tests/industry_graph/test_game_company_builder.py` (TC-GCB-001..002) | 2026-11-17 |
| `IrCounterpartyItem` | `quant_cn.quant_cn.industry_graph.ir_customer_extractor` | 4 | QuotedItem | One customer, supplier or partner named in an IR answer or record, with the stage reached, before the checks. | 0 | `industry_graph.IrCustomerExtractor` | `tests/industry_graph/test_ir_customer_extractor.py` (TC-IRC-001..001) | 2026-11-15 |
| `IrCustomerExtractor` | `quant_cn.quant_cn.industry_graph.ir_customer_extractor` | 4 | BaseQuotedExtractor | Quote-checked customer / supplier / partner rows with stage (contact … volume, ended, denied) from IR Q&A and IR records; only answers quotable; unnamed rows dropped, name in quote or referred back (plan 28 ph2). | 5 | `industry_graph.BrokerCustomerExtractor`, `lake` | `tests/industry_graph/test_ir_customer_extractor.py` (TC-IRC-001..003) | 2026-11-16 |
| `ProspectusExtractor` | `quant_cn.quant_cn.industry_graph.prospectus_extractor` | 4 | InquiryCustomerExtractor | Quote-checked top customers, suppliers per year and named competitors from IPO prospectuses (plan 28 ph2). | 0 | `lake` | `tests/industry_graph/test_prospectus_extractor.py` (TC-PRE-001..002) | 2026-11-15 |
| `DealItem` | `quant_cn.quant_cn.industry_graph.deal_extractor` | 4 | QuotedItem | One investment, acquisition, disposal or restructuring (kind, target, target_business, counterparty, stake, amount, status), before the checks. | 0 | `industry_graph.DealExtractor` | `tests/industry_graph/test_deal_extractor.py` (TC-DEX-001..001) | 2026-11-15 |
| `DealExtractor` | `quant_cn.quant_cn.industry_graph.deal_extractor` | 4 | BaseQuotedExtractor | Quote-checked deal rows from outside-investment announcements and restructuring reports; finance / invest edges (plan 28 ph2). | 3 | `lake` | `tests/industry_graph/test_deal_extractor.py` (TC-DEX-001..002) | 2026-11-15 |
| `OperatingDataItem` | `quant_cn.quant_cn.industry_graph.operating_data_extractor` | 4 | QuotedItem | One operating figure of the announcement's own period (metric class, metric, product, segment, period, value, unit, yoy), before the checks. | 0 | `industry_graph.OperatingDataExtractor` | `tests/industry_graph/test_operating_data_extractor.py` (TC-ODX-001..001) | 2026-11-15 |
| `OperatingDataExtractor` | `quant_cn.quant_cn.industry_graph.operating_data_extractor` | 4 | BaseQuotedExtractor | Quote-checked per-product revenue, output, volume, price, orders, backlog and capacity from 主要经营数据 announcements (plan 28 ph2). | 3 | `lake` | `tests/industry_graph/test_operating_data_extractor.py` (TC-ODX-001..002) | 2026-11-15 |
| `BuybackTermsItem` | `quant_cn.quant_cn.industry_graph.buyback_terms_extractor` | 4 | QuotedItem | The terms of one buyback or 增持 plan as read (kind, purpose, holder type and names, funding, loan, amount / share / ratio range with units, price cap, period, method), before the checks. | 0 | `industry_graph.BuybackTermsExtractor` | `tests/industry_graph/test_buyback_terms_extractor.py` (TC-BTX-001..001) | 2026-11-17 |
| `BuybackTermsExtractor` | `quant_cn.quant_cn.industry_graph.buyback_terms_extractor` | 4 | BaseQuotedExtractor | Quote-checked terms of buyback plans and holder 增持 plans: kind, purpose / holder type, funding incl. 专项贷款 with bank and amount, amount range in yuan, share / ratio range, price cap, period, method (plan 32 ph2, D-169). | 3 | `lake` | `tests/industry_graph/test_buyback_terms_extractor.py` (TC-BTX-001..003) | 2026-11-17 |
| `BrokerCustomerExtractor` | `quant_cn.quant_cn.industry_graph.broker_customer_extractor` | 4 | IrCustomerExtractor | Quote-checked customers / suppliers / partners and stage named in broker stock reports (plan 28 ph2). | 0 | `lake` | `tests/industry_graph/test_broker_customer_extractor.py` (TC-BCE-001..002) | 2026-11-15 |
| `TaxonomyNode` | `quant_cn.quant_cn.industry_graph.product_taxonomy` | 4 | none | One node of the taxonomy as the matcher and views need it. | 1 | `industry_graph.ProductTaxonomy`, `industry_graph.ProductMatcher` | `tests/industry_graph/test_product_matcher.py` (TC-PT-001..005) | 2026-11-07 |
| `ProductTaxonomy` | `quant_cn.quant_cn.industry_graph.product_taxonomy` | 4 | none | Load config/industry_chain/*.yaml once: nodes (names and aliases always strings, even when YAML reads "1,4-丁二醇" style values as numbers), the merged-id map, the Shenwan L3 → segment map (`sw_l3_map`) and the prior edges. | 7 | `industry_graph.ProductMatcher`, `industry_graph.NodeEdgeBuilder`, `research_space` | `tests/industry_graph/test_product_matcher.py` (TC-PT-001..006) | 2026-11-19 |
| `ProductMatch` | `quant_cn.quant_cn.industry_graph.product_matcher` | 4 | none | One taxonomy node a revenue line maps to, with how it was found. | 0 | `industry_graph.ProductMatcher` | `tests/industry_graph/test_product_matcher.py` (TC-PM-001..009) | 2026-11-07 |
| `ProductMatcher` | `quant_cn.quant_cn.industry_graph.product_matcher` | 4 | none | Map a company's revenue line to taxonomy nodes without the LLM. | 3 | `research_space` | `tests/industry_graph/test_product_matcher.py` (TC-PM-001..009) | 2026-11-07 |
| `ReportDigest` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | none | One broker report reduced to what the synthesis needs: the quote-checked fields of a ValuationExtractor result (plan 13), tagged with a short id the model must cite. | 1 | `industry_graph.BrokerViewSynthesizer` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..001) | 2026-11-07 |
| `ViewPoint` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | BaseModel | One synthesized point with the report refs it rests on. | 0 | `industry_graph.BrokerViewReply` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-002..002) | 2026-11-07 |
| `BrokerViewReply` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | BaseModel | The LLM reply before the citation check. | 0 | `industry_graph.BrokerViewSynthesizer` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-003..003) | 2026-11-07 |
| `BrokerView` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | none | The synthesized view after the citation check. | 0 | `industry_graph.BrokerViewSynthesizer` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..001) | 2026-11-07 |
| `BrokerViewSynthesizer` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | none | Synthesize the broker view of one product, Shenwan L3 industry or company from many report digests (user, 2026-11-08: the broker part must be the pattern across reports, not a list). | 1 | `lake` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..003) | 2026-11-07 |
| `ModeClaim` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | BaseModel | One quoted answer: a value (variant id, pricing mode, pass-through) with its evidence. | 0 | `industry_graph.BusinessModeReply` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-003..003) | 2026-11-07 |
| `PriceAction` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | BaseModel | A stated price move: direction, what, magnitude, evidence. | 0 | `industry_graph.BusinessModeReply` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-002..002) | 2026-11-07 |
| `BusinessModeReply` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | BaseModel | The LLM reply for one report before validation. | 0 | `industry_graph.BusinessModeExtractor` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-003..003) | 2026-11-07 |
| `BusinessModeResult` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | none | The quote-checked reading: each claim is a dict {value, reason, evidence} or None. | 0 | `industry_graph.BusinessModeExtractor` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-001..001) | 2026-11-07 |
| `BusinessModeExtractor` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | none | Read the business-section pages of one annual report for the business-model fields that only the text can give (BUSINESS_MODEL_DESIGN §4.5 T1, §4b.7): which candidate variant of the company's archetype fits (or a proposed new one), the pricing mode, the cost pass-through and the stated price actions. | 1 | `lake` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-001..003) | 2026-11-07 |
| `Reason` | `quant_cn.quant_cn.industry_graph.pricing_adjudicator` | 4 | BaseModel | One reason for the verdict with the evidence keys it rests on. | 0 | `industry_graph.AdjudicationReply` | `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-002..002) | 2026-11-07 |
| `AdjudicationReply` | `quant_cn.quant_cn.industry_graph.pricing_adjudicator` | 4 | BaseModel | The LLM reply before validation. | 0 | `industry_graph.PricingAdjudicator` | `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-003..003) | 2026-11-07 |
| `Adjudication` | `quant_cn.quant_cn.industry_graph.pricing_adjudicator` | 4 | none | The validated verdict. | 0 | `industry_graph.PricingAdjudicator` | `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-001..003) | 2026-11-07 |
| `PricingAdjudicator` | `quant_cn.quant_cn.industry_graph.pricing_adjudicator` | 4 | none | For a company whose rule-based pricing-power label is insufficient or whose archetype check is inconsistent (BUSINESS_MODEL_DESIGN §4.5, §4b.7), give the model every measured signal, the annual-report claims and the broker-view summary, each under a key, and ask for one label, a confidence, whether the default archetype holds (or which allowed archetype fits) and the reasons. | 1 | `lake` | `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-001..003) | 2026-11-07 |
| `MoatClaim` | `quant_cn.quant_cn.industry_graph.moat_extractor` | 4 | BaseModel | One claimed advantage: its moat type, a short statement, the figure the company gives (if any) and the evidence. | 0 | `industry_graph.MoatReply`, `industry_graph.MoatExtractor` | `tests/industry_graph/test_moat_extractor.py` (TC-ME-002..002) | 2026-11-07 |
| `MoatReply` | `quant_cn.quant_cn.industry_graph.moat_extractor` | 4 | BaseModel | The LLM reply before validation. | 0 | `industry_graph.MoatExtractor` | `tests/industry_graph/test_moat_extractor.py` (TC-ME-003..003) | 2026-11-07 |
| `MoatResult` | `quant_cn.quant_cn.industry_graph.moat_extractor` | 4 | none | The quote-checked claims of one report. | 0 | `industry_graph.MoatExtractor` | `tests/industry_graph/test_moat_extractor.py` (TC-ME-001..001) | 2026-11-07 |
| `MoatExtractor` | `quant_cn.quant_cn.industry_graph.moat_extractor` | 4 | none | Read the 核心竞争力分析 pages of one annual report and list the advantages the company claims, each classified as one of MOAT_TYPES (cost, switching costs, intangibles, network effects, efficient scale) with the figure it cites. | 1 | `lake` | `tests/industry_graph/test_moat_extractor.py` (TC-ME-001..003) | 2026-11-07 |
| `IndexFuturesMonitor` | `quant_cn.calculation.index_futures_monitor` | 4 | none | 股指期货 IF/IH/IC/IM via FuturesPositioning: annualised basis and top-20 net with 5-year percentiles, OI change, regime, flags (plan 15 ph7k). | 3 | `calculation.FuturesMonitorBuilder` | `tests/calculation/test_index_futures_monitor.py` (TC-IFM-001..002) | 2026-11-13 |
| `FuturesBrokerNets` | `quant_cn.calculation.futures_broker_nets` | 4 | none | Top-20 broker net per commodity family as (long − short)/(long + short) with 5-day change, 5-year percentile and flags (plan 15 ph7l, D-079). | 2 | `calculation.FuturesMonitorBuilder` | `tests/calculation/test_futures_broker_nets.py` (TC-FBN-001..003) | 2026-11-13 |
| `SpreadReversion` | `quant_cn.calculation.spread_reversion` | 4 | none | One-year z of a futures spread and the reversion flag for spreads marked `reversion` when the absolute z reaches reversion_z (plan 15 ph7i, D-156). | 2 | `calculation.FuturesMonitorBuilder` | `tests/calculation/test_spread_reversion.py` (TC-SRV-001..002) | 2026-11-14 |
| `TrendPosition` | `quant_cn.calculation.trend_position` | 4 | none | Plan 24 trend rule on any price series: blend = share of windows up, size = min(1, vol_target / vol), position = blend x size (no sizing when vol_target is None). | 3 | `portfolio.EtfCtaWeights` | `tests/calculation/test_trend_position.py` (TC-TP-001..004) | 2026-11-14 |
| `FuturesMonitorBuilder` | `quant_cn.calculation.futures_monitor_builder` | 4 | none | Per family: dominant price, percentiles, same-contract changes, front vs 4th / 12m with 5-year percentile, OI change and z, today's curve; spreads; flags and new flags; writes futures_monitor.json (plan 15 ph7i, D-145). | 2 | `cli.ReportCommands` | `tests/calculation/test_futures_monitor_builder.py` (TC-FUM-001..008) | 2026-11-13 |
| `VolatilityMonitorBuilder` | `quant_cn.calculation.volatility_monitor_builder` | 4 | none | Per line: US VIX from cboe_vix or A-share VIX via VixCalculator (trading clock) over the window; latest, one-day change, percentile, range, history; level / jump / percentile flags and new flags; writes volatility_monitor.json (plan 03 ph6, D-152). | 2 | `cli.ReportCommands` | `tests/calculation/test_volatility_monitor_builder.py` (TC-VMB-001..006) | 2026-11-13 |
| `RatesFxSeriesReader` | `quant_cn.calculation.rates_fx_series_reader` | 4 | none | One dated series per rates / FX line: 中债 curves, US yields, SHIBOR, FXCM mids, SAFE fixing per unit, index earnings yield from members, combos (diff / mul / div / gap with b carried forward) (plan 34). | 1 | `calculation.RatesFxMonitorBuilder`, `cli.ReportCommands` | `tests/calculation/test_rates_fx_monitor_builder.py` (TC-RFR-001..004) | 2026-11-18 |
| `RatesFxMonitorBuilder` | `quant_cn.calculation.rates_fx_monitor_builder` | 4 | none | Per shown line: latest, 1w / 1m / 3m / 1y changes by unit, 5-year percentile, 1-year range, stale, alerts, history (daily last year, weekly before); flags and new flags; curve snapshot; writes rates_fx_monitor.json (plan 34, D-171). | 2 | `cli.ReportCommands` | `tests/calculation/test_rates_fx_monitor_builder.py` (TC-RFM-001..004) | 2026-11-18 |
| `EarningsEventBuilder` | `quant_cn.calculation.earnings_event_builder` | 4 | none | One event per company and fiscal quarter at its first disclosure (preview / flash / report): SUE from first-reported single quarters, SUE decile within the quarter, pre / react / post excess vs the equal-weight market (plan 35, D-172). | 3 | `portfolio.SectorEarningsSignalBuilder`, `cli.AppServiceBuilder` | `tests/calculation/test_earnings_event_builder.py` (TC-EEB-001..003) | 2026-11-18 |
| `RetailGaugeMatrices` | `quant_cn.calculation.retail_gauge_matrices` | 4 | none | Daily session x stock matrices of the RetailGauge (adjusted close, turnover, float cap, large / extra-large / small order flow, margin balance) and the v3 / v4 path features over a quarter window plus the v5 multi-scale / EWMA / slope features at an as-of session (plan 21 ph2, D-142). | 2 | `calculation.RetailGaugeFeatureBuilder` | `tests/calculation/test_retail_gauge_matrices.py` (TC-RGM-001..002) | 2026-11-18 |
| `HolderCountPanel` | `quant_cn.calculation.holder_count_panel` | 4 | none | Quarter-end shareholder counts (latest value, first announcement date): label y = ln change from the previous quarter with ann_y, and the point-in-time lags prev / prev2 (plan 21, D-142). | 4 | `calculation.RetailGaugeFeatureBuilder`, `calculation.RetailGaugeNowcaster`, `cli.GaugeCommands` | `tests/calculation/test_holder_count_panel.py` (TC-HCP-001..002) | 2026-11-18 |
| `RetailGaugeFeatureBuilder` | `quant_cn.calculation.retail_gauge_feature_builder` | 4 | none | The 83 v5 RetailGauge features per (as_of, ts_code): path / flow / multi-scale (RetailGaugeMatrices), cyq_perf chips and their change since the previous quarter end, PIT holder lags, quarter number and previous-quarter lags; writes derived/retail_gauge_features (plan 21 ph2, D-142). | 6 | `calculation.RetailGaugeNowcaster`, `cli.GaugeCommands` | `tests/calculation/test_retail_gauge_feature_builder.py` (TC-RGF-001..003) | 2026-11-18 |
| `RetailGaugeModel` | `quant_cn.calculation.retail_gauge_model` | 4 | none | LightGBM regressor on within-quarter percentile ranks (training medians fill NaN), target the within-quarter rank of the holder change; predict -> pct rank; save / load (plan 21 ph3, D-142). | 5 | `calculation.RetailGaugeNowcaster`, `cli.GaugeCommands` | `tests/calculation/test_retail_gauge_model.py` (TC-RGMD-001..002) | 2026-11-18 |
| `RetailGaugeNowcaster` | `quant_cn.calculation.retail_gauge_nowcaster` | 4 | none | Daily RetailGauge readings: models per retrain key (1st of the retrain months, labels announced by then), expanding walk-forward at quarter ends (backtest), decile calibration of the expected change and IQR, avoid flag (D-155) and D-167 streaks; writes derived/retail_gauge (plan 21 ph3). | 6 | `cli.GaugeCommands` | `tests/calculation/test_retail_gauge_nowcaster.py` (TC-RGN-001..004) | 2026-11-18 |
| `RetailGaugeEvaluator` | `quant_cn.calculation.retail_gauge_evaluator` | 4 | none | Per walk-forward quarter: rank IC vs the realised holder change, top / bottom decile hit rates, avoid names' 60-session excess vs the equal-weight mean, ic_low flag; writes derived/reports/retail_gauge/evaluation.parquet (plan 21 ph3). | 2 | `cli.GaugeCommands` | `tests/calculation/test_retail_gauge_evaluator.py` (TC-RGE-001..001) | 2026-11-18 |
| `ConsensusPanelBuilder` | `quant_cn.calculation.consensus_panel_builder` | 4 | none | Analyst consensus on given dates, PIT: report_rc notes in (date − window, date), latest per broker and fiscal year, median FY1 / FY2 / FY3 net profit and broker count; FY1 rolls in May (plan 36, D-173). | 2 | `factor.FactorFactory`, `risk.RiskInputLoader`, `cli.ServiceBuilder` | `tests/calculation/test_consensus_panel_builder.py` (TC-CNS-001..003) | 2026-11-18 |
| `MacroSeries` | `quant_cn.calculation.macro_monitor_builder` | 4 | none | One monitored macro line: key, name, group, unit, column of the merged monthly frame. | 0 | `calculation.MacroMonitorBuilder` | `tests/calculation/test_macro_monitor_builder.py` (TC-MMB-001) | 2026-11-13 |
| `MacroMonitorBuilder` | `quant_cn.calculation.macro_monitor_builder` | 4 | none | CPI / PPI / PMI / M1-M2 / 社融 lines plus derived gap, scissor, 社融 stock yoy and vs last year: latest, previous, change, 5-year percentile, new_print; writes macro_monitor.json (plan 15 ph7h, D-143). | 2 | `cli.ReportCommands` | `tests/calculation/test_macro_monitor_builder.py` (TC-MMB-001..006) | 2026-11-13 |
| `CurveSummary` | `quant_cn.quant_cn.calculation.futures_curve` | 4 | none | The shape of one contract family's curve on one date: front, most-held, 6- and 12-month and last prices, and the slope from the most-held month to 12 months after it (or to the last later month when the curve is shorter). | 0 | `calculation.FuturesCurve` | `tests/calculation/test_futures_curve.py` (TC-FCV-002..002) | 2026-11-07 |
| `FuturesCurve` | `quant_cn.quant_cn.calculation.futures_curve` | 4 | none | Back-month futures curve per contract family (e.g. | 5 | `plan` | `tests/calculation/test_futures_curve.py` (TC-FCV-001..006) | 2026-11-07 |
| `ImpliedExpectations` | `quant_cn.quant_cn.calculation.implied_expectations` | 4 | none | Turn a market cap into what it already pays for (D-121: "priced in", not "cheap"). | 5 | `plan` | `tests/calculation/test_implied_expectations.py` (TC-IE-001..007) | 2026-11-07 |
| `BaseRiskModel` | `quant_cn.risk.base_risk_model` | 5 | ABC | Abstract risk model: produces the RISK_EXPOSURE / FACTOR_RETURN / FACTOR_COV / SPECIFIC_RISK frames for a pipeline step and answers portfolio-risk questions for a session from those frames. | 2 | `risk.RiskModel`, `risk.RiskModelValidator`, `portfolio.HoldingsRiskBuilder`, `portfolio.OpportunityScreen` | `tests/risk/test_base_risk_model.py` (TC-BRM-001..001) | 2026-11-11 |
| `BayesianShrinker` | `quant_cn.risk.bayesian_shrinker` | 5 | none | Pull each stock's specific vol toward the cap-weighted mean of its size group, more so the further it is from it: sigma_sh = v sigma_bar + (1 - v) sigma with v = q \|sigma - sigma_bar\| / (delta + q \|sigma - sigma_bar\|), delta the root mean square deviation inside the group. | 1 | `risk.SpecificRiskEstimator`, `risk.RiskModelFactory` | `tests/risk/test_bayesian_shrinker.py` (TC-BS-001..002) | 2026-11-11 |
| `DescriptorBuilder` | `quant_cn.risk.descriptor_builder` | 5 | none | One row per universe member and session in [start, end] with its Shenwan L1 group, circulating market cap (regression weight base, CNY) and every raw CNE5 descriptor: LNCAP = ln(total market cap in CNY), NLSIZE = cube of the cap-weighted standardised LNCAP, the price descriptors (PriceDescriptors on the dense return matrix; market = previous-day circ_mv weighted return of all stocks), the value / leverage descriptors, DTOP = dv_ttm / 100 (0 for non-payers; D-148) and the growth descriptors from the latest monthly snapshot on or before the session, and one partial beta per configured external series (the foreign return that closed between the previous and the current China close, e.g. | 3 | `risk.RiskModel`, `risk.RiskModelFactory` | `tests/risk/test_descriptor_builder.py` (TC-DB-001..006) | 2026-11-12 |
| `EigenfactorAdjuster` | `quant_cn.risk.eigenfactor_adjuster` | 5 | none | Remove the systematic underestimation of risk of the smallest-variance eigenportfolios of a sample covariance. | 2 | `risk.FactorCovarianceEstimator`, `risk.RiskModelFactory` | `tests/risk/test_eigenfactor_adjuster.py` (TC-EFA-001..003) | 2026-11-11 |
| `EwmWindow` | `quant_cn.risk.ewm_window` | 5 | none | The trailing-window kernel of every Barra descriptor and covariance estimate: weight w_k = 0.5^(k / half_life) on the observation k sessions before the current one (k = lag .. | 3 | `risk.PriceDescriptors`, `risk.FactorCovarianceEstimator`, `risk.SpecificRiskEstimator`, `risk.VolatilityRegimeAdjuster` | `tests/risk/test_ewm_window.py` (TC-EW-001..003) | 2026-11-11 |
| `ExposureStandardizer` | `quant_cn.risk.exposure_standardizer` | 5 | none | Turn the descriptor table into RISK_EXPOSURE, per session: each descriptor is standardised (circ_mv-weighted mean 0, equal-weighted sd 1), then clipped at +-winsor_sd and standardised again until no value exceeds the bound (at most 20 rounds); a style is the weighted mean of its descriptors' z-scores (weights renormalised over the descriptors a stock has), restandardised and clipped, then orthogonalised to its configured styles (OLS residual, Neutralizer) and restandardised; a style with raw coverage below `min_coverage` of the session's names is dropped for that session. | 1 | `risk.RiskModel`, `risk.RiskModelFactory` | `tests/risk/test_exposure_standardizer.py` (TC-EXS-001..004) | 2026-11-11 |
| `FactorCovarianceEstimator` | `quant_cn.risk.factor_covariance_estimator` | 5 | none | For every session t, the factor covariance forecast for t+1 from factor returns up to t over the last `cov_window` sessions: zero-mean exponentially weighted covariances with pairwise missing-data normalisation and Newey-West autocorrelation terms (Bartlett weights, `cov_nw_lags`), volatilities with `vol_half_life` and correlations with `corr_half_life` (CNE5 90 / 480), combined as D C D and made PSD (cov_raw); then the eigenfactor adjustment (gamma profile refitted every `eigen_refit_days` sessions or when the factor set changes) and the volatility regime multiplier lambda^2 (cov). | 2 | `risk.RiskModel`, `risk.RiskModelFactory` | `tests/risk/test_factor_covariance_estimator.py` (TC-FCE-001..003) | 2026-11-11 |
| `FactorMonitorBuilder` | `quant_cn.risk.factor_monitor_builder` | 5 | none | Turn the stored risk-model frames into the factor monitor: for every factor (country, Shenwan L1 industries, styles) its compounded return over 1 d / 1 w / 1 m / 3 m / YTD / 1 y, forecast volatility (sqrt of the covariance diagonal, annualised with 252), realized volatility over 21 and 63 sessions, their ratio, and today's return in units of the forecast daily sigma made at the previous close; plus daily series of the cumulative return, forecast vol and 21-session realized vol for the last `series_days` sessions. | 2 | `cli.ResearchCommands` | `tests/risk/test_factor_monitor_builder.py` (TC-FMB-001..004) | 2026-11-11 |
| `FactorReturnEstimator` | `quant_cn.risk.factor_return_estimator` | 5 | none | For each return session t, regress stock returns from the close of t-1 to the close of t on exposures known at the close of t-1: r = f_c + sum_i X_i f_i + sum_s X_s f_s + u, weights sqrt(circ_mv at t-1) capped at the `weight_cap_quantile` cross-sectional quantile. | 3 | `risk.RiskModel`, `risk.RiskModelFactory` | `tests/risk/test_factor_return_estimator.py` (TC-FRE-001..005) | 2026-11-11 |
| `FundamentalDescriptors` | `quant_cn.risk.fundamental_descriptors` | 5 | none | CNE5 descriptors from statements already aligned point in time (FUNDAMENTALS_PIT for balance and TTM fields; StatementVersionReader snapshots for annual history): BTOP = common equity / market cap; ETOP, CETOP = TTM net profit (parent) and operating cash flow / market cap; MLEV = (ME + LD) / ME, DTOA = total liabilities / total assets, FCFP = (TTM operating cash flow - TTM capex, c_pay_acq_const_fiolta) / market cap (D-131); BLEV = (BE + LD) / BE with LD = long-term borrowings + bonds payable (preferred equity is not reported separately and taken as 0); EGRO, SGRO = slope of the last up to `years` annual EPS / revenue on time divided by their mean absolute value (revenue instead of revenue per share: a constant share count cancels in slope / mean). | 2 | `risk.DescriptorBuilder`, `risk.RiskModelFactory` | `tests/risk/test_fundamental_descriptors.py` (TC-FD-001..003) | 2026-11-11 |
| `AnalystDescriptors` | `quant_cn.risk.analyst_descriptors` | 5 | none | CNE5 analyst descriptors per stock and session from the latest consensus reading: EPFWD (12-month forward earnings blended FY1 / FY2 by months left / market value), EGRSF (FY2 / FY1 − 1), EGRLF ((FY3 / FY1)^½ − 1) (plan 37). | 1 | `risk.DescriptorBuilder`, `risk.RiskModelFactory` | `tests/risk/test_analyst_descriptors.py` (TC-AND-001..003) | 2026-11-18 |
| `PriceDescriptors` | `quant_cn.risk.price_descriptors` | 5 | none | The CNE5 descriptors that need only daily returns and turnover, computed for every session and stock at once on wide matrices (rows = sessions in order, columns = stocks): BETA and HSIGMA (exponentially weighted regression on the cap-weighted market, 252 d, half-life 63), RSTR (weighted sum of log returns over 504 d, half-life 126, lag 21), DASTD (weighted sd of returns, 252 d, half-life 42), CMRA (range of cumulative log returns over the last 12 months), STOM / STOQ / STOA (log share turnover over 1 / 3 / 12 months). | 6 | `risk.DescriptorBuilder`, `risk.RiskModelFactory` | `tests/risk/test_price_descriptors.py` (TC-PD-001..005) | 2026-11-11 |
| `RiskDecomposer` | `quant_cn.risk.risk_decomposer` | 5 | none | Euler decomposition of a portfolio's forecast volatility at one session: total, factor and specific risk, each factor's contribution b_k (F b)_k / sigma (contributions plus the specific part h' D h / sigma sum to sigma), and the portfolio's factor exposures. | 1 | `research_space/notebooks/20261111_risk_model_validation.ipynb`, `portfolio.HoldingsRiskBuilder`, `cli.ResearchCommands`, `core.docs.ContractLinter` | `tests/risk/test_risk_decomposer.py` (TC-RD-001..002) | 2026-11-11 |
| `RiskInputs` | `quant_cn.risk.risk_input_loader` | 5 | none | Everything the descriptors need for exposures on [start, end], all point in time: dense prices and daily_basic from PRICE_HISTORY sessions before start (descriptor windows), universe members with their Shenwan L1 group (EXPOSURE_PANEL), balance and TTM fields (FUNDAMENTALS_PIT) and month-end snapshots of annual EPS and revenue. | 0 | `risk.RiskInputLoader`, `risk.DescriptorBuilder`, `risk.RiskModel` | `tests/risk/test_risk_input_loader.py` (TC-RIL-001..001) | 2026-11-11 |
| `RiskInputLoader` | `quant_cn.risk.risk_input_loader` | 5 | none | Read RiskInputs for one exposure window through the lake readers only (no parquet paths): LakeReader for prices, daily_basic and FUNDAMENTALS_PIT, ExposureReader for universe members with Shenwan L1 (D-093), StatementVersionReader for the annual reports known on each month-end session (growth descriptors refresh monthly, PIT at the snapshot date; D-127). | 2 | `pipeline.RiskModelStep`, `cli.ServiceBuilder` | `tests/risk/test_risk_input_loader.py` (TC-RIL-001..003) | 2026-11-11 |
| `RiskModel` | `quant_cn.risk.risk_model` | 5 | BaseRiskModel | CNE5-style model for A-shares (country + Shenwan L1 + configured styles) as a sequence of pure stages the pipeline step runs year by year: exposures from RiskInputs (DescriptorBuilder -> ExposureStandardizer), factor returns and residuals (exposures at t-1, returns t-1 -> t, circ_mv at t-1; FactorReturnEstimator), the factor covariance over the whole factor-return history (FactorCovarianceEstimator) and specific risk (SpecificRiskEstimator). | 9 | `risk.RiskModelFactory`, `pipeline.RiskModelStep` | `tests/risk/test_risk_model.py` (TC-RM-001..003) | 2026-11-11 |
| `RiskModelFactory` | `quant_cn.risk.risk_model_factory` | 5 | none | Wire a RiskModel and all its estimators from one RiskModelSettings (config/ risk_model.yaml), so variants (six styles vs ten, other half-lives) are config only. | 1 | `cli.ServiceBuilder`, `research_space/notebooks/20261111_risk_model_validation.ipynb`, `cli.ResearchCommands`, `cli.GaugeCommands` | `tests/risk/test_risk_model_factory.py` (TC-RMF-001..001) | 2026-11-11 |
| `RiskModelValidator` | `quant_cn.risk.risk_model_validator` | 5 | none | Test whether forecasts match realised risk. | 5 | `research_space/notebooks/20261111_risk_model_validation.ipynb`, `pipeline.RiskValidationWriter`, `cli.ServiceBuilder` | `tests/risk/test_risk_model_validator.py` (TC-RMV-001..004) | 2026-11-11 |
| `RiskSnapshot` | `quant_cn.risk.risk_snapshot` | 5 | none | The model as of one session's close, ready for portfolio arithmetic: X (stocks x factors, country column = 1), F (factors x factors, daily variance) and specific vol. | 5 | `risk.RiskModel`, `risk.RiskDecomposer`, `risk.BaseRiskModel`, `risk.RiskModelValidator`, `portfolio.HoldingsRiskBuilder`, `portfolio.StyleFitChecker` | `tests/risk/test_risk_snapshot.py` (TC-RSN-001..004) | 2026-11-11 |
| `SpecificRiskEstimator` | `quant_cn.risk.specific_risk_estimator` | 5 | none | Specific (idiosyncratic) volatility forecasts in three steps. | 3 | `risk.RiskModel`, `risk.RiskModelFactory` | `tests/risk/test_specific_risk_estimator.py` (TC-SRE-001..003) | 2026-11-11 |
| `StructuralSpecificRisk` | `quant_cn.risk.structural_specific_risk` | 5 | none | Predict specific volatility from exposures (USE4 / CNE5 structural model): regress ln(sigma_ts) on the factor exposures (industry dummies and styles) over stocks with a full residual history, weighted by cap, then sigma_str = E0 exp(X b) with E0 = sum w sigma_ts / sum w exp(X b) over the fit set (removes the log-retransformation bias). | 1 | `risk.SpecificRiskEstimator`, `risk.RiskModelFactory` | `tests/risk/test_structural_specific_risk.py` (TC-SSR-001..002) | 2026-11-11 |
| `VolatilityRegimeAdjuster` | `quant_cn.risk.volatility_regime_adjuster` | 5 | none | Scale risk forecasts by lambda_t so they track the current volatility regime: the cross-sectional bias statistic B_t^2 = weighted mean of (x_t / sigma_{t-1})^2 (factor returns over their forecast vol, equal weights; or specific returns over specific risk, cap weights) is averaged with an exponential kernel (half-life h, window 6 h) and lambda_t = sqrt(of that average). | 2 | `risk.FactorCovarianceEstimator`, `risk.SpecificRiskEstimator`, `risk.RiskModelFactory` | `tests/risk/test_volatility_regime_adjuster.py` (TC-VRA-001..003) | 2026-11-11 |
| `StyleSpec` | `quant_cn.core.risk_model_settings` | 1 | BaseModel | One style factor: its descriptors with CNE5 weights and the factors it is orthogonalised against (RISK_FACTOR_LIST §1). | 1 | `core.RiskModelSettings`, `risk.ExposureStandardizer` | `tests/core/test_risk_model_settings.py` (TC-RMS-001..001) | 2026-11-11 |
| `ExternalSeriesSpec` | `quant_cn.core.risk_model_settings` | 1 | BaseModel | One external daily series behind a partial-beta descriptor (D-128, D-134): where it is in the lake and how its dates map to China sessions. | 0 | `core.RiskModelSettings`, `risk.RiskInputLoader` | `tests/core/test_risk_model_settings.py` (TC-RMS-003..003) | 2026-11-11 |
| `ThemeBasketSpec` | `quant_cn.core.risk_model_settings` | 1 | BaseModel | A theme basket behind a partial-beta descriptor (D-130): the circ_mv-weighted return of a concept's current members (excluding the stock itself), from the concept's list date on. | 0 | `core.RiskModelSettings`, `risk.RiskInputLoader` | `tests/core/test_risk_model_settings.py` (TC-RMS-003..003) | 2026-11-11 |
| `RiskModelSettings` | `quant_cn.core.risk_model_settings` | 1 | BaseModel | Every tunable of the risk model in one typed object, CNE5 defaults (RISK_MODEL_DESIGN §1): estimation universe, style set, regression weights, covariance and specific-risk half-lives and lags, eigenfactor and volatility-regime adjustments. | 2 | `core.Config`, `risk.ExposureStandardizer`, `risk.FactorCovarianceEstimator`, `risk.SpecificRiskEstimator`, `risk.RiskModelFactory`, `risk.RiskModel`, `pipeline.RiskModelStep`, `pipeline.RiskValidationWriter` | `tests/core/test_risk_model_settings.py` (TC-RMS-001..002) | 2026-11-11 |
| `RiskModelStep` | `quant_cn.pipeline.risk_model_step` | 6 | BaseStep | Fit the configured RiskModel from `settings.start` to the last universe session and write one file per year of each frame (derived/risk_exposure, risk_factor_return, risk_specific_return, risk_factor_cov, risk_specific_risk). | 3 | `cli.ServiceBuilder` | `tests/pipeline/test_risk_model_step.py` (TC-RMST-001..002) | 2026-11-11 |
| `RiskValidationWriter` | `quant_cn.pipeline.risk_validation_writer` | 6 | none | After a fit, test the stored model over the last `validation_sessions` forecast sessions and write derived/reports/risk_<name>/validation.parquet (RISK_VALIDATION): median / mean R^2 (whole history and window), the bias statistic of every factor, of `validation_portfolios` random long-only portfolios of `validation_names` stocks drawn from the names with a forecast on the first window session, and of each benchmark index (index_weight weights on or before the window start, held fixed), plus the summary rows share_in_band and median_bias over the random portfolios. | 1 | `pipeline.RiskModelStep`, `cli.ServiceBuilder` | `tests/pipeline/test_risk_validation_writer.py` (TC-RVW-001..002) | 2026-11-11 |
| `EmailFormat` | `quant_cn.visualization.email_format` | 7 | none | Number and date formats of the morning e-mails and the colour of a signed number. | 7 | `visualization.MonitorReportRenderer`, `visualization.OpportunityReportRenderer` | `tests/visualization/test_email_html.py` (TC-EH-001) | 2026-11-13 |
| `EmailHtml` | `quant_cn.visualization.email_html` | 7 | none | E-mail-safe HTML blocks: cells, tables, sections, pairs, signed bars, tiles, page shell (D-136). | 9 | `visualization.MonitorReportRenderer`, `visualization.OpportunityReportRenderer`, `visualization.SmallCapReportSection` | `tests/visualization/test_email_html.py` (TC-EH-002) | 2026-11-13 |
| `MonitorReportRenderer` | `quant_cn.visualization.monitor_report_renderer` | 7 | none | The 持仓监测 e-mail: alerts (flags, retail inflow, conditions met, factor moves), holdings, exposures, factors, industries, national-team ETF (plan 15 ph7e), optional blocks (`ReportSection`: 宏观 ph7h, 期货 ph7i). | 1 | `visualization.MorningReportBuilder`, `cli.ReportCommands` | `tests/visualization/test_monitor_report_renderer.py` (TC-MRR-001..004) | 2026-11-13 |
| `ReportSection` | `quant_cn.visualization.report_section` | 7 | ABC | Base of an optional 持仓监测 block fed by one document (DOC): summary line and rows. | 2 | `visualization.MonitorReportRenderer`, `visualization.MacroReportSection`, `visualization.FuturesReportSection`, `visualization.EtfReportSection`, `visualization.VolatilityReportSection`, `visualization.SmallCapReportSection` | `tests/visualization/test_monitor_report_renderer.py` (TC-MRR-003) | 2026-11-13 |
| `FuturesReportSection` | `quant_cn.visualization.futures_report_section` | 7 | ReportSection | The 期货 block of the 持仓监测 e-mail: signal count daily, new signals as a table (plan 15 ph7i). | 2 | `cli.ReportCommands` | `tests/visualization/test_futures_report_section.py` (TC-FRS-001..002) | 2026-11-13 |
| `BuybackReportSection` | `quant_cn.visualization.buyback_report_section` | 7 | ReportSection | The 回购 block of the 持仓监测 e-mail: book events and new large plans (plan 23 ph6). | 2 | `cli.ReportCommands` | `tests/visualization/test_buyback_report_section.py` (TC-BRS-001..002) | 2026-11-13 |
| `BuybackMarketReportSection` | `quant_cn.visualization.buyback_market_report_section` | 7 | ReportSection | The 回购增持（全市场） block of the 持仓监测 e-mail from buyback_monitor.json: per kind the window's new programmes by label, 专项贷款 count and live totals; table of the largest new programmes with labels (plan 32 ph4). | 2 | `cli.ReportCommands` | `tests/visualization/test_buyback_market_report_section.py` (TC-BMR-001..002) | 2026-11-18 |
| `EtfReportSection` | `quant_cn.visualization.etf_report_section` | 7 | ReportSection | The ETF 资金强度 line of the 持仓监测 e-mail from etf_proxy.json styles (plan 15 ph7g). | 2 | `cli.ReportCommands` | `tests/visualization/test_etf_report_section.py` (TC-ERS-001) | 2026-11-13 |
| `MacroReportSection` | `quant_cn.visualization.macro_report_section` | 7 | ReportSection | The 宏观 block of the 持仓监测 e-mail: daily summary line, full table on a new print (plan 15 ph7h). | 2 | `cli.ReportCommands` | `tests/visualization/test_macro_report_section.py` (TC-MRS-001..002) | 2026-11-13 |
| `VolatilityReportSection` | `quant_cn.visualization.volatility_report_section` | 7 | ReportSection | The 波动率 block of the 持仓监测 e-mail: daily summary line, table of every line with alerts (plan 03 ph6). | 2 | `cli.ReportCommands` | `tests/visualization/test_volatility_report_section.py` (TC-VRS-001..002) | 2026-11-13 |
| `SmallCapReportSection` | `quant_cn.visualization.small_cap_report_section` | 7 | ReportSection | The 小盘观察 block of the 持仓监测 e-mail: summary line (triggered, new, near) and a table of every signal with triggered rows first in red (plan 30 ph2). | 2 | `cli.ReportCommands` | `tests/visualization/test_small_cap_report_section.py` (TC-SRS-001..002) | 2026-11-17 |
| `RatesFxReportSection` | `quant_cn.visualization.rates_fx_report_section` | 7 | ReportSection | The 利率汇率 block of the 持仓监测 e-mail: summary line (10Y, USDCNH, alerts with new marked) and a table of the key rows with alerting rows red (plan 34 ph4). | 2 | `cli.ReportCommands` | `tests/visualization/test_rates_fx_report_section.py` (TC-RRS-001..002) | 2026-11-18 |
| `SectorEarningsReportSection` | `quant_cn.visualization.sector_earnings_report_section` | 7 | ReportSection | The 财报季信号 block of the 持仓监测 e-mail: summary line (season, firing sectors with numbers, new marked, rally record) and a table of firing and provisional sectors (plan 35). | 2 | `cli.ReportCommands` | `tests/visualization/test_sector_earnings_report_section.py` (TC-SER-001..002) | 2026-11-18 |
| `CardShot` | `quant_cn.visualization.alert_message_builder` | 7 | none | Where an alert's picture is in the app: page hash, card selector, file stem (plan 22). | 0 | `visualization.Alert`, `visualization.AlertMessageBuilder`, `visualization.CardScreenshotter`, `cli.ReportCommands` | `tests/visualization/test_alert_message_builder.py` (TC-AMB-001) | 2026-11-13 |
| `Alert` | `quant_cn.visualization.alert_message_builder` | 7 | none | One phone alert line: stable key, trigger, plain text, optional CardShot (plan 22). | 0 | `visualization.AlertMessageBuilder`, `cli.ReportCommands` | `tests/visualization/test_alert_message_builder.py` (TC-AMB-001) | 2026-11-13 |
| `AlertMessageBuilder` | `quant_cn.visualization.alert_message_builder` | 7 | none | Plain-language phone alert lines from volatility, watchlist, futures and macro documents (no jargon, D-153) and one message per run (plan 22). | 2 | `cli.ReportCommands` | `tests/visualization/test_alert_message_builder.py` (TC-AMB-001..006) | 2026-11-13 |
| `CardScreenshotter` | `quant_cn.visualization.card_screenshotter` | 7 | none | PNG per CardShot via Node + Playwright (shot_cards.mjs, phone style, 3x) against the running app; failures give no picture, never raise (plan 22). | 1 | `cli.ReportCommands` | `tests/visualization/test_card_screenshotter.py` (TC-CSS-001..002) | 2026-11-13 |
| `OpportunityReportRenderer` | `quant_cn.visualization.opportunity_report_renderer` | 7 | none | The 机会清单 e-mail: plan 21 list when live, watchlist with condition status and marks (plan 15 ph7e). | 1 | `visualization.MorningReportBuilder`, `cli.ReportCommands` | `tests/visualization/test_opportunity_report_renderer.py` (TC-ORR-001..002) | 2026-11-13 |
| `ReportOutcome` | `quant_cn.visualization.morning_report_builder` | 7 | none | What happened to one e-mail: written, sent or skipped and why. | 0 | `visualization.MorningReportBuilder.run` | `tests/visualization/test_morning_report_builder.py` (TC-MRB-002) | 2026-11-13 |
| `MorningReportBuilder` | `quant_cn.visualization.morning_report_builder` | 7 | none | Read the app documents, refuse stale data, write (dry run) or send the two morning e-mails (plan 15 ph7e, D-136). | 3 | `cli.ReportCommands` | `tests/visualization/test_morning_report_builder.py` (TC-MRB-001..003) | 2026-11-13 |
| `RiskChart` | `quant_cn.visualization.risk_chart` | 7 | BaseChart | Three views of the risk model (plan 05 phase 5), over frames only: "cumulative" (FACTOR_RETURN) compounded returns of the chosen factors, one line each, labelled at the line end so identity does not rest on colour; "correlation" (FACTOR_COV) the factor correlation matrix of one session as a diverging heatmap (-1..1); "decomposition" (RISK_DECOMP) each factor's contribution to a portfolio's annualised volatility as horizontal bars (specific risk as its own bar), total in the title. | 1 | `research_space/notebooks/20261111_risk_model_validation.ipynb` | `tests/visualization/test_risk_chart.py` (TC-RC-001..003) | 2026-11-11 |
| `UpdateStep` | `quant_cn.core.update_all_settings` | 1 | BaseModel | One update-all step: name, make target, needs, output JSON for `as_of`, timeout, retry (plan 38). | 0 | `core.UpdateAllSettings`, `pipeline.UpdateAllRunner` | `tests/core/test_update_all_settings.py` (TC-UAS-001) | 2026-11-18 |
| `UpdateAllSettings` | `quant_cn.core.update_all_settings` | 1 | BaseModel | Ordered update steps (unique names, needs on earlier steps), default timeout, tail lines and status history from config/update_all.yaml (plan 38, D-181). | 4 | `pipeline.UpdateAllRunner`, `cli.UpdateCommands` | `tests/core/test_update_all_settings.py` (TC-UAS-001..003) | 2026-11-18 |
| `TaskLog` | `quant_cn.lake.task_log` | 2 | none | The update task ledger: one zstd parquet part per step under meta/task_log/ (tmp + rename, no catalog lock), read back in run order, view meta.task_log (plan 38, D-181). | 4 | `pipeline.UpdateAllRunner`, `lake.LakeCatalog`, `pipeline.TaskStatusBuilder`, `cli.UpdateCommands` | `tests/lake/test_task_log.py` (TC-TKL-001..003) | 2026-11-18 |
| `TargetRunner` | `quant_cn.pipeline.update_all_runner` | 6 | Protocol | What UpdateAllRunner needs from a process runner: run_target(target, timeout_s, tail_lines) (plan 38). | 1 | `pipeline.UpdateAllRunner` | `tests/pipeline/test_update_all_runner.py` (TC-UAR-001) | 2026-11-18 |
| `MakeTargetRunner` | `quant_cn.pipeline.make_target_runner` | 6 | none | Run `make <target>` as a subprocess, echo its output, keep the last lines, kill it at the time limit (plan 38). | 1 | `cli.UpdateCommands` | `tests/pipeline/test_update_all_runner.py` (TC-MKR-001) | 2026-11-18 |
| `UpdateAllRunner` | `quant_cn.pipeline.update_all_runner` | 6 | none | Run the update steps in order: continue past failures, skip steps whose needs are not ok, retry, record one ledger row per step with the output `as_of` (plan 38, D-181). | 1 | `cli.UpdateCommands` | `tests/pipeline/test_update_all_runner.py` (TC-UAR-001..003) | 2026-11-18 |
| `TaskStatusBuilder` | `quant_cn.pipeline.task_status_builder` | 6 | none | task_status.json from the ledger: the latest run with counts and steps, and per step its last status, last success, as_of and recent history (plan 38 ph3). | 2 | `cli.UpdateCommands` | `tests/pipeline/test_task_status_builder.py` (TC-TSB-001..002) | 2026-11-18 |
| `UpdateCommands` | `quant_cn.update_commands` | 8 | none | The `update-all` CLI command: check targets, run the steps, print a summary, write task_status.json, refresh meta.task_log (plan 38). | 1 | `cli.QuantCnCli` | `tests/test_update_commands.py` (TC-UPC-001..002) | 2026-11-18 |
| `TaskStatusReportSection` | `quant_cn.visualization.task_status_report_section` | 7 | ReportSection | The 数据更新 line (latest update-all run: time, trigger, ok count, failed steps) and a table of failed / skipped steps in the 持仓监测 e-mail (plan 38). | 2 | `cli.ReportCommands` | `tests/visualization/test_task_status_report_section.py` (TC-TSR-001..002) | 2026-11-18 |

## B. Class details (one block per class; methods carry their own purpose)

Template. Copy verbatim; keep headings so `lint_contracts.py` can parse them.

### `PascalName` — `quant_cn.package.module` (L?)
- **Purpose:** one or two lines, identical in meaning to the docstring.
- **Base:** `BaseX` | none. **Depends on (injected):** `Config`, `BaseY`.
- **Used by:** `package.Class.method`, `research_space/main.ipynb`.
- **Tests:** `tests/<layer>/test_<module>.py` (TC-XX-001..NNN).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__(config, dep)` | wire dependencies | `Config`, `BaseY` -> instance | `ConfigError` | callers of the class | — |
| `method_a(x)` | what it does, one line | `list[str]` -> `DataFrame[SchemaZ]` | `DataSourceError` | `pipeline.DownloadPipeline.step_daily` | TC-XX-001, 003 |

Rules: every public method gets a row; private helpers (`_name`) are listed only if longer than 20
lines, so a reader knows they exist. `Input -> Output` uses type names or a registered `Schema` name,
never column lists (those live in section E).

### `Black76Model` — `quant_cn.calculation.black76_model` (L4)
- **Purpose:** Price European options on a forward (Black-76, discounted at the continuous rate) and invert a price to implied volatility; used for ATM-IV checks and known-answer chains.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `research_space/notebooks/20260927_vix_calculation.ipynb`, `calculation.GammaExposureCalculator`.
- **Tests:** `tests/calculation/test_black76_model.py` (TC-BM-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_price` | Black-76 price. | float, float, float, float, float, Side -> float | — | as class | see class |
| `compute_implied_vol` | Volatility that reproduces `price` (bisection on [1e-4, 5]). | float, float, float, float, float, Side -> float | `ValueError` | as class | see class |
| `compute_gamma` | Black-76 gamma with respect to the forward (same for calls and puts). | float, float, float, float, float -> float | — | as class | see class |

### `ExpiryClock` — `quant_cn.calculation.expiry_clock` (L4)
- **Purpose:** Convert (trade_date, expiry) to the time units the VIX formulas use. "calendar" is the CBOE white paper: minutes, 30-day target, 365-day year. "trading" counts exchange sessions after the trade date up to expiry: 21-session target, 244-session year, so holidays inside a term add no time (the Mid-Autumn / National Day roll artefact disappears).
- **Base:** none. **Depends on (injected):** ClockMode, Sequence[str].
- **Used by:** `calculation.VixCalculator`.
- **Tests:** `tests/calculation/test_expiry_clock.py` (TC-EC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ClockMode, Sequence[str] -> None | `ValueError` | callers of the class | — |
| `get_units` | Time to expiry in the clock's unit (minutes or sessions). | str, str, int -> float | `ValueError` | as class | see class |
| `get_target` | The constant-maturity target in the clock's unit. | — -> float | — | as class | see class |
| `get_year` | One year in the clock's unit. | — -> float | — | as class | see class |

### `ForwardPriceEstimator` — `quant_cn.calculation.forward_price_estimator` (L4)
- **Purpose:** Per term: F = K* + e^{RT}(C - P) at the strike K* with the smallest /C - P/, and K0 the largest strike at or below F.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `calculation.VixCalculator`, `calculation.GammaExposureCalculator`.
- **Tests:** `tests/calculation/test_forward_price_estimator.py` (TC-FPE-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute` | (F, K0) for one term. | pd.DataFrame, float, float -> tuple[float, float] | `ValueError` | as class | see class |

### `FuturesPositioning` — `quant_cn.calculation.futures_positioning` (L4)
- **Purpose:** Per trading day for one CFFEX index-futures product (IF, IH, IC, IM): total open interest and its change, the main contract's price change, the OI x price regime (new shorts, long liquidation, short covering, new longs), top-20 broker gross long / short / net summed over the product's contracts, and the main contract's basis to the index, raw and annualised to its third-Friday expiry. Top-20 figures are gross broker aggregates, not client intent.
- **Base:** none. **Depends on (injected):** str.
- **Used by:** `research_space/notebooks/20260929_positioning_flows.ipynb`.
- **Tests:** `tests/calculation/test_futures_positioning.py` (TC-FP-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str -> None | `ValueError` | callers of the class | — |
| `compute` | One row per trading day for the product. | pd.DataFrame, pd.DataFrame, pd.Series -> pd.DataFrame | `KeyError` | as class | see class |
| `list_brokers` | Brokers' gross long, short and net over the product's contracts on one day. | pd.DataFrame, str -> pd.DataFrame | `KeyError` | as class | see class |
| `get_expiry` | CFFEX index futures expire on the third Friday of the contract month. | str -> dt.date | `ValueError` | as class | see class |

### `GammaExposureCalculator` — `quant_cn.calculation.gamma_exposure_calculator` (L4)
- **Purpose:** Estimate the gamma dealers carry per option and strike, in CNY of underlying they must trade for a 1% move: GEX = sign * Gamma_F * OI * multiplier * F^2 * 1%, with Gamma from Black-76 at each option's own implied volatility. `sign` is an ASSUMPTION about who is short: the default (+1 calls, -1 puts) means dealers are long calls and short puts (customers write calls and buy puts). Negative total GEX = dealers sell into falls (moves amplify).
- **Base:** none. **Depends on (injected):** RiskFreeCurve, OptionChainBuilder, ForwardPriceEstimator, Black76Model, Mapping[str, float], int.
- **Used by:** `research_space/notebooks/20260929_positioning_flows.ipynb`.
- **Tests:** `tests/calculation/test_gamma_exposure_calculator.py` (TC-GEC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | RiskFreeCurve, OptionChainBuilder, ForwardPriceEstimator, Black76Model, Mapping[str, float], int -> None | `ValueError` | callers of the class | — |
| `compute` | Exposure of every option of one day with 1 <= days <= max_days. | pd.DataFrame, str, float -> pd.DataFrame | `ValueError` | as class | see class |
| `compute_profile` | Total dealer GEX if every term's forward moved to each level (IVs held fixed). | pd.DataFrame, Sequence[float] -> pd.DataFrame | — | as class | see class |
| `find_flip` | Level where total GEX changes sign (linear interpolation), the "gamma flip". | pd.DataFrame -> float \| None | — | as class | see class |
| `_build_row` (private) | internal helper over 20 lines | dict[str, Any], str, int, float, float, float, float -> list[dict[str, object]] | — | internal | — |

### `MarginLadderEstimator` — `quant_cn.calculation.margin_ladder_estimator` (L4)
- **Purpose:** Estimate where margin-financed positions face forced selling. Per stock, financing debt is split into first-in-first-out vintages: each day's financed buying (rzmre) opens a vintage at that day's close; repayments (rzche) retire the oldest first; the balance before the window is one "seeded" vintage at the first close. A vintage is force-sold when collateral/debt falls below `maintenance_ratio`; with own capital = initial_margin_ratio x debt at entry, that happens at price entry x maintenance_ratio / (1 + initial_margin_ratio). Pooled per-stock data and cross-collateral make this an estimate of concentration, not prices.
- **Base:** none. **Depends on (injected):** float, float.
- **Used by:** `research_space/notebooks/20260929_positioning_flows.ipynb`.
- **Tests:** `tests/calculation/test_margin_ladder_estimator.py` (TC-MLE-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | float, float -> None | `ValueError` | callers of the class | — |
| `compute_ladder` | Outstanding financing vintages per stock on `as_of` with liquidation prices. | pd.DataFrame, pd.DataFrame, str -> pd.DataFrame | `KeyError` | as class | see class |
| `compute_curve` | Financing debt whose liquidation price is reached if every stock falls by each drawdown. | pd.DataFrame, Sequence[float] -> pd.DataFrame | — | as class | see class |
| `_build_vintages` (private) | internal helper over 20 lines | pd.DataFrame -> list[tuple[str, float, float, bool]] | — | internal | — |

### `OptionChainBuilder` — `quant_cn.calculation.option_chain_builder` (L4)
- **Purpose:** Join the option master (opt_basic) with daily prices (opt_daily) into one tidy chain per underlying, and turn one expiry of it into a strike x (call, put) quote table.
- **Base:** none. **Depends on (injected):** bool.
- **Used by:** `calculation.VixCalculator`, `calculation.GammaExposureCalculator`.
- **Tests:** `tests/calculation/test_option_chain_builder.py` (TC-OCB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | bool -> None | — | callers of the class | — |
| `build_chain` | The chain of one underlying over the dates present in `daily`. | pd.DataFrame, pd.DataFrame, str -> pd.DataFrame | `KeyError` | as class | see class |
| `build_quotes` | Strike x side table of prices and volumes for one expiry on one day. | pd.DataFrame -> tuple[pd.DataFrame, bool] | `KeyError` | as class | see class |

### `RiskFreeCurve` — `quant_cn.calculation.risk_free_curve` (L4)
- **Purpose:** Continuously compounded risk-free rate for a tenor in calendar days, from the latest SHIBOR fixing on or before the date, linearly interpolated between tenors and clamped outside them.
- **Base:** none. **Depends on (injected):** pd.DataFrame.
- **Used by:** `calculation.VixCalculator`, `calculation.GammaExposureCalculator`.
- **Tests:** `tests/calculation/test_risk_free_curve.py` (TC-RFC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | pd.DataFrame -> None | `ValueError` | callers of the class | — |
| `get_rate` | Continuous annual rate for `days` calendar days as of `trade_date`. | str, int -> float | `ValueError` | as class | see class |

### `TermInterpolator` — `quant_cn.calculation.term_interpolator` (L4)
- **Purpose:** VIX = 100 * sqrt([T1 s1^2 (N2 - Nt)/(N2 - N1) + T2 s2^2 (Nt - N1)/(N2 - N1)] * Ny / Nt), with N in the clock's unit (minutes or sessions) and Ny one year in that unit.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `calculation.VixCalculator`.
- **Tests:** `tests/calculation/test_term_interpolator.py` (TC-TI-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute` | The interpolated (or extrapolated) index level. | float, float, float, float, float, float -> float | `ValueError` | as class | see class |

### `TermSelector` — `quant_cn.calculation.term_selector` (L4)
- **Purpose:** Choose the two nearest expiries with at least `min_days` calendar days to expiry.
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `calculation.VixCalculator`.
- **Tests:** `tests/calculation/test_term_selector.py` (TC-TS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | — | callers of the class | — |
| `list_terms` | (near, next) maturity dates for one day's chain. | pd.DataFrame -> tuple[str, str] | `ValueError` | as class | see class |

### `VarianceStripCalculator` — `quant_cn.calculation.variance_strip_calculator` (L4)
- **Purpose:** sigma^2 = (2/T) sum(dK/K^2 e^{RT} Q(K)) - (1/T)(F/K0 - 1)^2 over puts below K0, calls above K0 and the call/put average at K0; walking away from K0 stops after two consecutive "zero" strikes (zero price, or with price_or_volume also zero volume: no bid/ask, D-048).
- **Base:** none. **Depends on (injected):** ZeroRule.
- **Used by:** `calculation.VixCalculator`.
- **Tests:** `tests/calculation/test_variance_strip_calculator.py` (TC-VSC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ZeroRule -> None | — | callers of the class | — |
| `compute` | Variance and number of strikes used for one term. | pd.DataFrame, float, float, float, float -> tuple[float, int] | `KeyError` | as class | see class |

### `CompanyCyclePanel` — `quant_cn.calculation.company_cycle_panel` (L4)
- **Purpose:** For every company, as known on a date, place its latest quarter in its own cycle: single-quarter and TTM revenue, GM, profit and deducted profit with YoY and QoQ, ROE and turnover, 10-year median annual profit and max annual net margin, ttm_vs_med and margin_peak (plan 16 ph1, D-121). Pure: versions come in as a frame from `lake.StatementVersionReader`.
- **Base:** none. **Depends on (injected):** DateCodec, DiscoverySettings.
- **Used by:** (none yet; pipeline.DiscoveryStep plan 16 ph6).
- **Tests:** `tests/calculation/test_company_cycle_panel.py` (TC-CCP-001..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DateCodec, DiscoverySettings -> None | — | callers of the class | — |
| `list_fields` | fundamentals_long fields the panel needs | () -> list[str] | — | callers | TC-CCP-009 |
| `compute_start` | earliest period end needed for as_of | str -> str | `ValueError` | callers | TC-CCP-009 |
| `list_quarters` | single-quarter history per company (last `count`) | pd.DataFrame, str, int -> pd.DataFrame | `ValueError` | research checks; plan 16 ph3 IdeaScreener (sensitivity input to `ImpliedExpectations.compute_sensitivity`) | TC-CCP-010 |
| `build` | the cycle panel as known on as_of | pd.DataFrame, str -> pd.DataFrame | `ValueError` | callers | TC-CCP-001..009 |

### `ForecastTracker` — `quant_cn.calculation.forecast_tracker` (L4)
- **Purpose:** Score every earnings preview (业绩预告, all revisions) against the first reported net profit attributable to the parent, and summarise each company's record as hit rate and bias (plan 18 ph1, D-124). Pure: forecast_vip / express_vip come from `lake.LakeReader.read_panel`, the actual from `lake.StatementVersionReader.read_first_versions`, so a restated actual is never used.
- **Base:** none. **Depends on (injected):** DateCodec, GuidanceSettings.
- **Used by:** (none yet; pipeline.GuidanceStep plan 18 ph6; run script `meta/runs/guidance_forecasts.py`).
- **Tests:** `tests/calculation/test_forecast_tracker.py` (TC-FT-001..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DateCodec, GuidanceSettings -> None | — | callers of the class | — |
| `list_fields` | fundamentals_long field of the actual | () -> list[str] | — | callers | TC-FT-008 |
| `build` | one row per preview version known on as_of with range, outcome, position, surprise, revision, days_after_end / ex_ante, first flash report | pd.DataFrame, pd.DataFrame, pd.DataFrame, str -> pd.DataFrame | `ValueError` | callers | TC-FT-001..006, 008, 009 |
| `build_track_record` | per company: hit / above / below rates, mean and median abs surprise, first-version hit rate, sufficient; the same for the last pre-period-end version (n_ex_ante, ex_ante_hit_rate, ex_ante_mean_surprise, ex_ante_sufficient) | pd.DataFrame, str -> pd.DataFrame | `ValueError` | callers | TC-FT-007, 008, 010 |

### `VixCalculator` — `quant_cn.calculation.vix_calculator` (L4)
- **Purpose:** Orchestrate the white-paper steps per trading day: select near/next terms, rate per term, forward and K0, variance strip, interpolation on the chosen clock; one VIX_PANEL row per (trade_date, underlying). A day that cannot be computed gets vix NaN and a "failed: <reason>" quality_flag instead of stopping the run.
- **Base:** none. **Depends on (injected):** RiskFreeCurve, OptionChainBuilder, TermSelector, ForwardPriceEstimator, VarianceStripCalculator, TermInterpolator, ExpiryClock.
- **Used by:** `research_space/notebooks/20260927_vix_calculation.ipynb`.
- **Tests:** `tests/calculation/test_vix_calculator.py` (TC-VC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | RiskFreeCurve, OptionChainBuilder, TermSelector, ForwardPriceEstimator, VarianceStripCalculator, TermInterpolator, ExpiryClock -> None | — | callers of the class | — |
| `compute` | The index for every trading day in `chain`. | pd.DataFrame, str -> pd.DataFrame | `SchemaError` | as class | see class |
| `_compute_day` (private) | internal helper over 20 lines | pd.DataFrame, str, str -> dict[str, object] | — | internal | — |

### `QuantCnCli` — `quant_cn.cli` (L8)
- **Purpose:** `python -m quant_cn.cli <command>`: doctor, download, compact, curate, rebuild, backup, project-catalog, query. Builds every service from Config (the only place objects are wired) and prints summaries.
- **Base:** none. **Depends on (injected):** Config | None, Console | None.
- **Used by:** `Makefile targets doctor, download, compact, lake-rebuild, lake-backup`.
- **Tests:** `tests/test_cli.py` (TC-QCC-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config \| None, Console \| None -> None | — | callers of the class | — |
| `run` | Parse arguments and dispatch to a command. | Sequence[str] \| None -> int | `SystemExit` | as class | see class |
| `_build_parser` (private) | internal helper over 20 lines | — -> argparse.ArgumentParser | — | internal | — |
| `_run_curate` (private) | internal helper over 20 lines | Config, argparse.Namespace -> int | — | internal | — |

### `ResearchCommands` — `quant_cn.cli` (L8)
- **Purpose:** The research-side CLI commands, kept apart so QuantCnCli stays within its size limit: `release-lags` (D-086), `evaluate` (factor campaign reports and trial log, plan 04 phase 5), `risk-model` (D-127), `watchlist` (D-120), `etf-proxy` (D-126), `factor-monitor` and `holdings-risk` (D-132). QuantCnCli parses the arguments and dispatches here.
- **Base:** none. **Depends on (injected):** Console.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/test_cli.py` (TC-QCC-008..009, 011..014).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Console -> None | — | callers of the class | — |
| `build_parser` | Add the `release-lags`, `watchlist`, `etf-proxy`, `factor-monitor`, `holdings-risk`, `evaluate` and `risk-model` subcommands to the CLI parser. | argparse._SubParsersAction -> None | — | `cli.QuantCnCli._build_parser` | see class |

### `BaseApiClient` — `quant_cn.core.base_api_client` (L1)
- **Purpose:** Abstract vendor client: one logical query returns all pages as one DataFrame.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher`, `data_loading.AkshareClient`, `data_loading.BaostockClient`, `data_loading.BaseWebClient`, `data_loading.ManualSeriesClient`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `query` | Run one query and return every row across pages. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError`, `PermissionDeniedError` | as class | see class |

### `BaseFetchLog` — `quant_cn.core.base_fetch_log` (L1)
- **Purpose:** Abstract record of which (dataset, key) pairs are fully downloaded.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.FetchLog`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher`.
- **Tests:** `tests/lake/test_fetch_log.py` (TC-FL-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_done_keys` | All keys recorded as done for a dataset. | str -> set[str] | `LakeError` | as class | see class |
| `mark_done` | Record a finished key, replacing any earlier record for it. | str, str, int, Path \| None -> None | `LakeError` | as class | see class |
| `save` | Make recorded keys durable (e.g. write the parquet mirror). | — -> Path \| None | `LakeError` | as class | see class |
| `is_done` | True if the key is recorded as done. | str, str -> bool | `LakeError` | as class | see class |
| `list_pending` | The subset of `keys` not yet done, in input order. | str, Sequence[str] -> list[str] | `LakeError` | as class | see class |

### `BaseFetcher` — `quant_cn.core.base_fetcher` (L1)
- **Purpose:** Download one dataset as a sequence of keys; subclasses define the keys and the per-key parameters of one sweep pattern, never one endpoint.
- **Base:** ABC. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock.
- **Used by:** `data_loading.SingleCallFetcher`, `data_loading.EnumFetcher`, `data_loading.DateSweepFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.FetcherFactory.build`, `pipeline.FetchStep`, `data_loading.DateWindowFetcher`.
- **Tests:** `tests/core/test_base_fetcher.py` (TC-BF-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock -> None | `TypeError` | callers of the class | — |
| `list_keys` | All fetch keys for [start, end], ascending. | str, str -> list[str] | `LakeError`, `ValueError` | as class | see class |
| `build_params` | API parameters for one key. | str, str, str -> dict[str, str] | — | as class | see class |
| `list_due_keys` | Keys that must be fetched: all if forced or overwrite, else pending plus the newest `refetch_recent` keys. | Sequence[str], bool -> list[str] | `LakeError` | as class | see class |
| `fetch_one` | Query the endpoint for one key. | str, str, str -> pd.DataFrame | `DataSourceError`, `PermissionDeniedError` | as class | see class |
| `run` | Fetch every key that needs fetching, writing and logging each before the next. | str, str, str, Sequence[str] \| None, bool, ProgressHook \| None -> StepReport | `DataSourceError`, `PermissionDeniedError`, `SchemaError`, `LakeError` | as class | see class |
| `_fetch_key` (private) | internal helper over 20 lines | str, str, str, str, StepReport -> str | — | internal | — |

### `BaseRunLog` — `quant_cn.core.base_run_log` (L1)
- **Purpose:** Abstract append-only log of runs and per-key events; the source of truth for "what happened".
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.RunLog`, `core.BaseFetcher.run`, `pipeline.LocalRunner`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.PrefectRunner`, `data_loading.DateWindowFetcher`.
- **Tests:** `tests/lake/test_run_log.py` (TC-RL-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `open_run` | Open a run and return its id. | str -> str | `LakeError` | as class | see class |
| `record_event` | Append one event (fetched / skipped / empty / failed / blocked). | str, str, str, str, int, int, str -> None | `LakeError` | as class | see class |
| `close_run` | Close a run with its final status. | str, str, str -> None | `LakeError` | as class | see class |

### `BaseStep` — `quant_cn.core.base_step` (L1)
- **Purpose:** Abstract unit of pipeline work: list its units, then run and report.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `pipeline.FetchStep`, `pipeline.BaseRunner.run`, `pipeline.LocalRunner.run`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `pipeline.PrefectRunner`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `name` | Step name shown in progress and reports. | — -> str | — | as class | see class |
| `list_units` | Compute the work units (e.g. keys) just before running. | — -> list[str] | `QuantCnError` | as class | see class |
| `run` | Do the work listed by `list_units`. | str, ProgressHook \| None -> StepReport | `QuantCnError` | as class | see class |

### `BaseStore` — `quant_cn.core.base_store` (L1)
- **Purpose:** Abstract sink for raw fetch results and curated partitions.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.ParquetWriter`, `core.BaseFetcher`, `lake.Compactor`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `write_raw` | Persist one fetch key's rows atomically. | DatasetSpec, str, pd.DataFrame -> Path \| None | `SchemaError`, `LakeError` | as class | see class |
| `write_curated` | Replace one curated partition atomically after validating its schema. | DatasetSpec, int \| None, pd.DataFrame -> Path | `SchemaError`, `LakeError` | as class | see class |

### `Clock` — `quant_cn.core.clock` (L1)
- **Purpose:** The single source of wall time, monotonic time and sleeping; tests inject a fake subclass.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `core.BaseFetcher.run`, `lake.RunLog`, `lake.Compactor.rebuild`, `pipeline.DownloadPipeline`, `cli.QuantCnCli`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.FetcherFactory`, `data_loading.PeriodSweepFetcher`, `lake.ProjectCatalog`, `cli.ServiceBuilder`, `data_loading.DateWindowFetcher`, `data_loading.AkshareClient`, `data_loading.BaostockClient`, `lake.RebuildAudit`, `cli.ResearchCommands`, `cli.DocumentCommands`, `data_loading.DocumentDownloader`, `data_loading.RequestPacer`, `data_loading.AppStoreClient`.
- **Tests:** `tests/core/test_clock.py` (TC-CL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_now` | Current local wall time. | — -> dt.datetime | — | as class | see class |
| `get_today` | Today's date as a Tushare `YYYYMMDD` string. | — -> str | — | as class | see class |
| `get_monotonic` | Monotonic seconds for measuring durations. | — -> float | — | as class | see class |
| `sleep` | Block for `seconds`; fakes record the call instead. | float -> None | — | as class | see class |

### `LakeConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Where the lake lives and whether it may sit inside the repository.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`.
- **Tests:** `tests/core/test_config.py` (TC-C-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `TushareConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Tushare endpoint, paging, retry and rate-limit settings; the token comes from env only.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `data_loading.TushareClient`.
- **Tests:** `tests/core/test_config.py` (TC-C-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DownloadConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Which datasets to download, in what order, and from which start dates (D-015b).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`.
- **Tests:** `tests/core/test_config.py` (TC-C-004..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `FactorSpec` — `quant_cn.core.config` (L1)
- **Purpose:** One factor of config/factors.yaml: its name, implementing class and parameters.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `factor.FactorFactory`.
- **Tests:** `tests/core/test_config.py` (TC-C-012..012).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `CampaignConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Settings of one factor campaign (config/factors.yaml `campaign`, plan 04 phase 5).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`.
- **Tests:** `tests/core/test_config.py` (TC-C-013..013).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `UniverseConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Rules of the tradeable universe per session (FACTOR_TESTING_DESIGN §11, D-054).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `pipeline.UniverseStep`.
- **Tests:** `tests/core/test_config.py` (TC-C-011..011).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `FuturesCategory` — `quant_cn.core.config` (L1)
- **Purpose:** One member-category label that `fut_holding` lists among real brokers (D-079).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `lake.DerivedViews`.
- **Tests:** `tests/core/test_config.py` (TC-C-009..009).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `TickerAlias` — `quant_cn.core.config` (L1)
- **Purpose:** One retired code and the code its company trades on afterwards (D-053, D-089).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `lake.TickerAliasMap`, `lake.DerivedViews`.
- **Tests:** `tests/core/test_config.py` (TC-C-010..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `WatchlistEntry` — `quant_cn.core.config` (L1)
- **Purpose:** One stock the user watches and the price range at which they would buy it (D-120); loaded from git-ignored `config/local.watchlist.yaml`.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `portfolio.WatchlistBuilder`.
- **Tests:** `tests/core/test_config.py` (TC-C-015).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `WatchlistSettings` — `quant_cn.core.config` (L1)
- **Purpose:** Thresholds and windows of the watchlist page: near_pct, history_days, consensus_days (base.yaml `watchlist`, D-120).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `portfolio.WatchlistBuilder`.
- **Tests:** `tests/core/test_config.py` (TC-C-016).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `EtfProxyIndex` — `quant_cn.core.etf_proxy_settings` (L1)
- **Purpose:** One broad index whose ETFs are summed into the proxy: display name, regex searched in `fund_basic.benchmark`, reference ETF whose price deflates positions (D-126).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.EtfProxySettings`.
- **Tests:** `tests/core/test_config.py` (TC-C-020).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `EtfProxyStyle` — `quant_cn.core.etf_proxy_settings` (L1)
- **Purpose:** A style ETF group (银行, 红利): the EtfProxyIndex fields plus `key`; the condition metric is "<key>_etf_z".
- **Base:** EtfProxyIndex. **Depends on (injected):** —.
- **Used by:** `core.EtfProxySettings`.
- **Tests:** `tests/core/test_config.py` (TC-C-021).

### `EtfProxySettings` — `quant_cn.core.etf_proxy_settings` (L1)
- **Purpose:** Members of the national-team ETF proxy: indices (first matching pattern wins), core ts_codes, name / benchmark rules, start date and recent window (config/etf_proxies.yaml; missing file = no indices, D-126).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `portfolio.EtfProxyBuilder`, `portfolio.EtfFlowCalculator`, `portfolio.EtfStyleHeat`.
- **Tests:** `tests/core/test_config.py` (TC-C-020..021). Style groups: `styles`, `style_window` (20), `style_z_days` (250), `style_hot_z` (1.5).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DiscoverySettings` — `quant_cn.core.discovery_settings` (L1)
- **Purpose:** Thresholds and windows of the discovery pipeline: history_years, min_years (base.yaml `discovery`, plan 16, D-121).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `calculation.CompanyCyclePanel`.
- **Tests:** `tests/core/test_config.py` (TC-C-017).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `GuidanceSettings` — `quant_cn.core.guidance_settings` (L1)
- **Purpose:** Windows and minimum sample of guidance tracking: history_start, window_years, min_outcomes (base.yaml `guidance`, plan 18, D-124).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `calculation.ForecastTracker`.
- **Tests:** `tests/core/test_config.py` (TC-C-019).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `Config` — `quant_cn.core.config` (L1)
- **Purpose:** The typed configuration injected everywhere: YAML defaults, machine overrides, environment.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `cli.QuantCnCli`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`, `cli.ServiceBuilder`, `cli.ResearchCommands`, `cli.DocumentCommands`, `portfolio.WatchlistBuilder`, `portfolio.EtfProxyBuilder`.
- **Tests:** `tests/core/test_config.py` (TC-C-001..020).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | Build the configuration from `config/base.yaml`, `config/datasets.yaml`, optional `config/local.yaml`, the repo `.env` and the process environment. | Path \| None, Mapping[str, str] \| None -> Config | `ConfigError` | as class | see class |
| `get_dataset` | Look up one dataset spec by name. | str -> DatasetSpec | `ConfigError` | as class | see class |
| `get_start` | Download start date for a dataset: its own `start`, else long-history start if listed, else the default start. | str -> str | `ConfigError` | as class | see class |

### `ValuesFromDataset` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** Enumerate sweep keys from another curated dataset (e.g. every ETF code in fund_basic).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.SweepSpec`.
- **Tests:** `tests/data_loading/test_fetcher_factory.py` (TC-FF-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `SweepSpec` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** How a dataset is swept so each call returns the whole market for one key.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.DatasetSpec`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `param` | API parameter name carrying the key (None for single-call datasets). | — -> str \| None | — | as class | see class |

### `CuratedSpec` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** Where a dataset lands in `curated/` and which date column drives its yearly partition.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.DatasetSpec`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DatasetSpec` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** Everything the lake and the fetchers need to know about one dataset, as data (D-012).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `core.BaseFetcher`, `core.BaseStore`, `lake.ParquetWriter`, `lake.LakeCatalog`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory.build`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.CompactStep`, `lake.DerivedViews`, `lake.ProjectCatalog`, `data_loading.DateWindowFetcher`, `lake.EffectiveDateResolver`, `lake.ReleaseLagChecker`, `lake.LakeReader`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..009).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_raw_filename` | Hive-style raw file name for one fetch key. | str -> str | — | as class | see class |
| `build_schema` | The dataset's Schema (fields, text fields, primary key). | — -> Schema | `SchemaError` | as class | see class |
| `_check_columns` (private) | internal helper over 20 lines | — -> DatasetSpec | — | internal | — |

### `DateCodec` — `quant_cn.core.date_codec` (L1)
- **Purpose:** Validate and convert Tushare `YYYYMMDD` date strings and generate date keys for sweeps.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.Config.load`, `data_loading.DateSweepFetcher.list_keys`, `data_loading.PeriodSweepFetcher.list_keys`, `pipeline.DownloadPipeline.run`, `data_loading.FetcherFactory`, `cli.QuantCnCli`, `lake.PitAligner`, `visualization.PriceChart`, `cli.ServiceBuilder`, `data_loading.DateWindowFetcher`, `lake.EffectiveDateResolver`, `factor.FactorFactory`, `lake.StatementVersionReader`, `calculation.CompanyCyclePanel`, `portfolio.EtfProxyBuilder`.
- **Tests:** `tests/core/test_date_codec.py` (TC-DC-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `validate` | Return `value` unchanged if it is a valid `YYYYMMDD` date string. | str -> str | `ValueError` | as class | see class |
| `to_date` | Parse a `YYYYMMDD` string. | str -> dt.date | `ValueError` | as class | see class |
| `to_str` | Format a date as `YYYYMMDD`. | dt.date -> str | — | as class | see class |
| `list_quarter_ends` | Report periods (Mar 31, Jun 30, Sep 30, Dec 31) within [start, end]. | str, str -> list[str] | `ValueError` | as class | see class |
| `list_weekdays` | Monday-to-Friday dates within [start, end], for announcement-date sweeps. | str, str -> list[str] | `ValueError` | as class | see class |
| `list_days` | Every calendar day within [start, end], for event sweeps that publish on weekends too. | str, str -> list[str] | `ValueError` | as class | see class |

### `Finding` — `quant_cn.core.docs.base_checker` (L1)
- **Purpose:** One rule violation at a location, printable as `path:line [rule] message`.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.BaseChecker.run`, `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.PlanStatusChecker`, `core.docs.ResearchLogChecker`, `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_base_checker.py` (TC-BCH-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `to_text` | One-line human form. | — -> str | — | as class | see class |

### `BaseChecker` — `quant_cn.core.docs.base_checker` (L1)
- **Purpose:** Abstract repository check: inspect the tree, return findings (empty = pass).
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.PlanStatusChecker`, `core.docs.ResearchLogChecker`, `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_base_checker.py` (TC-BCH-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | Run the check over the repository. | — -> list[Finding] | `OSError`, `SyntaxError` | as class | see class |

### `MethodInfo` — `quant_cn.core.docs.code_scanner` (L1)
- **Purpose:** One function defined directly in a class body.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ClassInfo`, `core.docs.CodeScanner.read_module`, `core.docs.ModuleInfo`.
- **Tests:** `tests/core/docs/test_code_scanner.py` (TC-CS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `n_lines` | Physical lines including docstring and blanks. | — -> int | — | as class | see class |
| `is_public` | True for names without a leading underscore. | — -> bool | — | as class | see class |

### `ClassInfo` — `quant_cn.core.docs.code_scanner` (L1)
- **Purpose:** One top-level class: span, bases, docstring, methods and the names its body references.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ModuleInfo`, `core.docs.CodeScanner.read_module`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder`.
- **Tests:** `tests/core/docs/test_code_scanner.py` (TC-CS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `n_lines` | Physical lines of the class. | — -> int | — | as class | see class |
| `list_public_methods` | Methods and properties without a leading underscore, in source order. | — -> list[MethodInfo] | — | as class | see class |

### `ModuleInfo` — `quant_cn.core.docs.code_scanner` (L1)
- **Purpose:** One scanned Python file.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.CodeScanner.read_module`, `core.docs.ContractChecker`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder`.
- **Tests:** `tests/core/docs/test_code_scanner.py` (TC-CS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `CodeScanner` — `quant_cn.core.docs.code_scanner` (L1)
- **Purpose:** Parse Python files with `ast` into ModuleInfo records (no import, no execution).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_code_scanner.py` (TC-CS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_module` | Scan one file. | Path, Path -> ModuleInfo | `SyntaxError`, `OSError` | as class | see class |

### `CodeTableBuilder` — `quant_cn.core.docs.code_table_builder` (L1)
- **Purpose:** Turn src/ classes (AST + contract docstrings), the class registry and tests/ into the code-side tables of the `project` schema, one DataFrame per table with fixed columns.
- **Base:** none. **Depends on (injected):** Path, CodeScanner, DocstringParser, RegistryReader.
- **Used by:** `lake.ProjectCatalog`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_code_table_builder.py` (TC-CTB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, CodeScanner, DocstringParser, RegistryReader -> None | — | callers of the class | — |
| `build_tables` | Build all five code tables. | — -> dict[str, pd.DataFrame] | `SyntaxError`, `OSError` | as class | see class |
| `_add_class` (private) | internal helper over 20 lines | dict[str, list[list[object]]], str, ModuleInfo, RegistryInfo -> None | — | internal | — |
| `_add_methods` (private) | internal helper over 20 lines | dict[str, list[list[object]]], RegistryInfo -> None | — | internal | — |

### `CodeUnit` — `quant_cn.core.docs.contract_checker` (L1)
- **Purpose:** A class with the module it lives in and its parsed contract.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ContractChecker`.
- **Tests:** `tests/core/docs/test_contract_checker.py` (TC-CC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ContractChecker` — `quant_cn.core.docs.contract_checker` (L1)
- **Purpose:** Check contracts across the tree: class docstrings carry all sections and public methods Purpose + Contract; docstring TC IDs and `test_tc_*` functions match one-to-one; each src class's `Used by` equals the src classes that reference it; every src class has its registry rows and a method table equal to its public methods; class names are unique; no module-level functions in src outside core/utils.
- **Base:** BaseChecker. **Depends on (injected):** Path, CodeScanner, DocstringParser, RegistryReader.
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_contract_checker.py` (TC-CC-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, CodeScanner, DocstringParser, RegistryReader -> None | — | callers of the class | — |
| `run` | Run every contract rule. | — -> list[Finding] | `SyntaxError`, `OSError` | as class | see class |
| `_check_tests` (private) | internal helper over 20 lines | list[tuple[str, ModuleInfo]], list[CodeUnit], list[tuple[str, ModuleInfo]] -> list[Finding] | — | internal | — |
| `_check_used_by` (private) | internal helper over 20 lines | list[CodeUnit], list[CodeUnit] -> list[Finding] | — | internal | — |
| `_check_registry` (private) | internal helper over 20 lines | list[tuple[str, ModuleInfo]], list[CodeUnit], RegistryInfo -> list[Finding] | — | internal | — |
| `_check_registry_class` (private) | internal helper over 20 lines | CodeUnit, RegistryInfo -> list[Finding] | — | internal | — |

### `ContractLinter` — `quant_cn.core.docs.contract_linter` (L1)
- **Purpose:** Build the four checkers (contracts, index, size, names) for one repository and run the selected groups, returning all findings sorted.
- **Base:** none. **Depends on (injected):** Path.
- **Used by:** `scripts/lint_contracts.py`, `tests/test_contracts.py`, `lake.ProjectCatalog`, `cli.ServiceBuilder`.
- **Tests:** `tests/test_contracts.py` (TC-CTL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `run` | Run the selected checker groups. | Iterable[str] -> list[Finding] | `ValueError`, `RuntimeError`, `SyntaxError` | as class | see class |

### `ConventionReader` — `quant_cn.core.docs.convention_reader` (L1)
- **Purpose:** Extract the allowed method-name verb prefixes from the naming convention's §2.1 table.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_convention_reader.py` (TC-CR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read_verbs` | Verb prefixes (e.g. "get_") and bare verbs (e.g. "run") in table order. | Path -> list[str] | `ValueError`, `OSError` | as class | see class |

### `DecisionRecord` — `quant_cn.core.docs.decisions_reader` (L1)
- **Purpose:** One decision: its log-table row joined with the Context and Decision bullets of its block.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.DecisionsReader`.
- **Tests:** `tests/core/docs/test_decisions_reader.py` (TC-DR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DecisionsReader` — `quant_cn.core.docs.decisions_reader` (L1)
- **Purpose:** Parse DECISIONS.md: the ID/Date/Title/Status/Where table plus `### D-NNN` detail blocks.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.DocTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_decisions_reader.py` (TC-DR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | All decisions in table order. | Path -> list[DecisionRecord] | `OSError` | as class | see class |

### `DocTableBuilder` — `quant_cn.core.docs.doc_table_builder` (L1)
- **Purpose:** Turn the INDEX.md tree, the files on disk, the decision log and the execution plans into the document-side tables of the `project` schema.
- **Base:** none. **Depends on (injected):** Path, RepoFiles, IndexReader, DecisionsReader, PlanReader, ResearchLogReader.
- **Used by:** `lake.ProjectCatalog`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_doc_table_builder.py` (TC-DTB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, RepoFiles, IndexReader, DecisionsReader, PlanReader, ResearchLogReader -> None | — | callers of the class | — |
| `build_tables` | Build all five document tables. | — -> dict[str, pd.DataFrame] | `RuntimeError`, `OSError` | as class | see class |
| `_build_tree` (private) | internal helper over 20 lines | — -> dict[str, pd.DataFrame] | — | internal | — |
| `_build_plans` (private) | internal helper over 20 lines | — -> dict[str, pd.DataFrame] | — | internal | — |

### `UsedByEntry` — `quant_cn.core.docs.docstring_parser` (L1)
- **Purpose:** One line of a `Used by:` section, split into the caller reference and its note.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.DocContract`, `core.docs.DocstringParser.parse`.
- **Tests:** `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DocContract` — `quant_cn.core.docs.docstring_parser` (L1)
- **Purpose:** The parsed contract of one class, method or module docstring.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.DocstringParser.parse`, `core.docs.CodeUnit`.
- **Tests:** `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `has` | True if every named section is present. | — -> bool | — | as class | see class |

### `DocstringParser` — `quant_cn.core.docs.docstring_parser` (L1)
- **Purpose:** Split a contract docstring into its sections: Purpose, Contract (Input, Output, Raises), Used by, Test cases.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `parse` | Parse one docstring. | str \| None -> DocContract | — | as class | see class |

### `IndexChecker` — `quant_cn.core.docs.index_checker` (L1)
- **Purpose:** Every visible folder has an INDEX.md whose folder and file rows equal what is on disk, and whose Contains cell for a .py file lists exactly its top-level classes (fixtures for conftest.py; public constants for modules without classes).
- **Base:** BaseChecker. **Depends on (injected):** Path, RepoFiles, IndexReader, CodeScanner.
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_index_checker.py` (TC-IC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, RepoFiles, IndexReader, CodeScanner -> None | — | callers of the class | — |
| `run` | Check every folder's index. | — -> list[Finding] | `RuntimeError`, `SyntaxError` | as class | see class |
| `_check_folder` (private) | internal helper over 20 lines | Path, IndexInfo, list[Path], list[Path] -> list[Finding] | — | internal | — |

### `IndexEntry` — `quant_cn.core.docs.index_reader` (L1)
- **Purpose:** One row of an INDEX.md table: a subfolder or a file with its purpose and named contents.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.IndexInfo`, `core.docs.IndexReader.read`.
- **Tests:** `tests/core/docs/test_index_reader.py` (TC-IR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `IndexInfo` — `quant_cn.core.docs.index_reader` (L1)
- **Purpose:** Parsed INDEX.md: title line, subfolder entries, file entries.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.IndexReader.read`, `core.docs.IndexChecker`, `core.docs.DocTableBuilder`.
- **Tests:** `tests/core/docs/test_index_reader.py` (TC-IR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `IndexReader` — `quant_cn.core.docs.index_reader` (L1)
- **Purpose:** Parse the fixed INDEX.md format: `## Folders` (Folder, Purpose) and `## Files` (File, Purpose, Contains) tables.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_index_reader.py` (TC-IR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | Parse one INDEX.md. | Path -> IndexInfo | `OSError` | as class | see class |

### `MarkdownTable` — `quant_cn.core.docs.markdown_table` (L1)
- **Purpose:** One pipe table with the heading it sits under.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.MarkdownTableReader.read`.
- **Tests:** `tests/core/docs/test_markdown_table.py` (TC-MTR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_column` | All cells of one column. | str -> list[str] | `KeyError` | as class | see class |

### `MarkdownTableReader` — `quant_cn.core.docs.markdown_table` (L1)
- **Purpose:** Extract every pipe table from markdown text, and backticked names from a cell.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.IndexReader`, `core.docs.RegistryReader`, `core.docs.ConventionReader`, `core.docs.ContractLinter`, `core.docs.DecisionsReader`, `core.docs.PlanReader`, `core.docs.ResearchLogReader`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_markdown_table.py` (TC-MTR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read` | All tables in document order. | str -> list[MarkdownTable] | — | as class | see class |
| `list_ticked` | Names written in backticks inside a cell. | str -> list[str] | — | as class | see class |

### `NameChecker` — `quant_cn.core.docs.name_checker` (L1)
- **Purpose:** Enforce names: lowercase paths (governance `UPPER_SNAKE.md` and tool files excepted), verb-first method and function names from the convention's verb table, no banned verbs, test functions named `test_tc_<id>_<desc>`, and module name matching its primary class.
- **Base:** BaseChecker. **Depends on (injected):** Path, CodeScanner, list[Path], Sequence[str].
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_name_checker.py` (TC-NC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, CodeScanner, list[Path], Sequence[str] -> None | — | callers of the class | — |
| `run` | Check every visible path and every code file. | — -> list[Finding] | `SyntaxError`, `OSError` | as class | see class |
| `is_verb_name` | True if `name` (leading underscores ignored) starts with an allowed, unbanned verb. | str -> bool | — | as class | see class |

### `PhaseRecord` — `quant_cn.core.docs.plan_reader` (L1)
- **Purpose:** One row of a plan's Phases table.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.PlanRecord`, `core.docs.PlanReader.read`.
- **Tests:** `tests/core/docs/test_plan_reader.py` (TC-PR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `PlanRecord` — `quant_cn.core.docs.plan_reader` (L1)
- **Purpose:** One execution plan: number, title, header fields and phases.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.PlanReader.read`.
- **Tests:** `tests/core/docs/test_plan_reader.py` (TC-PR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `PlanReader` — `quant_cn.core.docs.plan_reader` (L1)
- **Purpose:** Parse a plan file: `# NN — Title`, the two-column header table (Status, Decisions, Depends on plans) and the Phases table.
- **Base:** none. **Depends on (injected):** MarkdownTableReader, PhaseStatusParser.
- **Used by:** `core.docs.DocTableBuilder`, `core.docs.PlanStatusChecker`, `core.docs.ResearchLogChecker`, `core.docs.ContractLinter`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_plan_reader.py` (TC-PR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader, PhaseStatusParser -> None | — | callers of the class | — |
| `read` | Parse one plan file. | Path -> PlanRecord \| None | `OSError` | as class | see class |

### `PhaseStatus` — `quant_cn.core.docs.phase_status_parser` (L1)
- **Purpose:** A phase status split into fields: the state word, the first date, the commit hashes and the remaining text.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.PhaseStatusParser.parse`.
- **Tests:** `tests/core/docs/test_phase_status_parser.py` (TC-PSP-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `is_valid` | Whether the status starts with one of the four allowed states. | — -> bool | — | as class | TC-PSP-001, TC-PSP-002 |

### `PhaseStatusParser` — `quant_cn.core.docs.phase_status_parser` (L1)
- **Purpose:** Parse the Status cell of a plan's Phases table (`<state> <YYYY-MM-DD> (<commit>) — <note>`); legacy free-text spellings parse too.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.PlanReader`, `core.docs.ContractLinter`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_phase_status_parser.py` (TC-PSP-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `parse` | Split one status cell. | str -> PhaseStatus | — | as class | TC-PSP-001..003 |

### `PlanStatusChecker` — `quant_cn.core.docs.plan_status_checker` (L1)
- **Purpose:** Report every plan phase whose Status cell does not start with todo, doing, blocked or done.
- **Base:** BaseChecker. **Depends on (injected):** Path, PlanReader.
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_plan_status_checker.py` (TC-PSC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, PlanReader -> None | — | callers of the class | — |
| `run` | Parse every plan file and check each phase's state. | — -> list[Finding] | `OSError` | as class | TC-PSC-001 |

### `RegistryInfo` — `quant_cn.core.docs.registry_reader` (L1)
- **Purpose:** The registry's content as sets and maps the linter can compare with code.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.RegistryReader.read`, `core.docs.ContractChecker`, `core.docs.CodeTableBuilder`.
- **Tests:** `tests/core/docs/test_registry_reader.py` (TC-RR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `RegistryReader` — `quant_cn.core.docs.registry_reader` (L1)
- **Purpose:** Parse CLASS_REGISTRY.md: section A index, section B detail blocks and their method tables, and the class/schema names of sections C, D, E.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_registry_reader.py` (TC-RR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | Parse the registry file. | Path -> RegistryInfo | `OSError` | as class | see class |

### `RepoFiles` — `quant_cn.core.docs.repo_files` (L1)
- **Purpose:** The set of repository files a linter should see: `git ls-files --cached --others --exclude-standard`, so .gitignore (caches, .env, lake guards) decides what is ignored.
- **Base:** none. **Depends on (injected):** Path.
- **Used by:** `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_repo_files.py` (TC-RF-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `list_files` | Relative paths of visible files that exist on disk, spelled as on disk, sorted. | — -> list[Path] | `RuntimeError` | as class | see class |
| `list_folders` | Every folder that holds at least one visible file, including the root (Path(".")). | — -> list[Path] | `RuntimeError` | as class | see class |

### `ResearchLogChecker` — `quant_cn.core.docs.research_log_checker` (L1)
- **Purpose:** Check the research log (slug `YYYYMMDD_<topic>`, unique, matching the date; scripts path exists) and that no committed file under research_space/runs/ names 5+ held codes or a private cost / cash figure.
- **Base:** BaseChecker. **Depends on (injected):** Path, ResearchLogReader, list[Path], Collection[str], Collection[str].
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_research_log_checker.py` (TC-RSC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, ResearchLogReader, list[Path], Collection[str], Collection[str] -> None | — | callers of the class | — |
| `run` | Check every log row, then every committed run file. | — -> list[Finding] | `OSError` | as class | TC-RSC-001..002 |

### `ResearchRun` — `quant_cn.core.docs.research_log_reader` (L1)
- **Purpose:** One ad-hoc analysis as logged: when, what was asked, where its scripts and outputs live, what it concluded and what followed.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ResearchLogReader.read`.
- **Tests:** `tests/core/docs/test_research_log_reader.py` (TC-RLR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ResearchLogReader` — `quant_cn.core.docs.research_log_reader` (L1)
- **Purpose:** Parse research_space/RESEARCH_LOG.md: the first table whose header is the log columns; other tables and prose ignored.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.DocTableBuilder`, `core.docs.ResearchLogChecker`, `core.docs.ContractLinter`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_research_log_reader.py` (TC-RLR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | Parse one log file. | Path -> list[ResearchRun] | `OSError` | as class | TC-RLR-001..002 |

### `SizeChecker` — `quant_cn.core.docs.size_checker` (L1)
- **Purpose:** Fail any .py file over 600 lines, class over 300, function or method over 50 (physical lines, docstrings included), and INDEX.md / SKILL.md / execution plan over 300 lines.
- **Base:** BaseChecker. **Depends on (injected):** Path, CodeScanner, list[Path].
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_size_checker.py` (TC-SC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, CodeScanner, list[Path] -> None | — | callers of the class | — |
| `run` | Check every code file and governance doc. | — -> list[Finding] | `SyntaxError`, `OSError` | as class | see class |

### `Schema` — `quant_cn.core.schema` (L1)
- **Purpose:** Declare and enforce a DataFrame shape: text columns are pandas `string`, all other declared columns are `float64`, and the primary key is unique and non-null.
- **Base:** none. **Depends on (injected):** str, Sequence[str], Collection[str], Sequence[str].
- **Used by:** `core.DatasetSpec.build_schema`, `lake.LakeReader`.
- **Tests:** `tests/core/test_schema.py` (TC-S-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str, Sequence[str], Collection[str], Sequence[str] -> None | `SchemaError` | callers of the class | — |
| `get_dtype` | Declared dtype name of `column`. | str -> str | — | as class | see class |
| `normalize` | Return a copy of `df` cast to the declared dtypes. | pd.DataFrame, bool -> pd.DataFrame | `SchemaError` | as class | see class |
| `validate` | Check `df` satisfies the schema exactly. | pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |
| `build_empty` | A zero-row frame with the declared columns and dtypes. | — -> pd.DataFrame | — | as class | see class |

### `StepReport` — `quant_cn.core.step_report` (L1)
- **Purpose:** Counts and status of one step (usually one dataset's fetch) so runs can be summarised.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.BaseFetcher.run`, `core.BaseStep.run`, `lake.Compactor.rebuild`, `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `pipeline.FetchStep`, `pipeline.PipelineReport`, `pipeline.CompactStep`, `pipeline.DeriveStep`, `pipeline.PrefectRunner`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `data_loading.DocumentDownloader`.
- **Tests:** `tests/core/test_base_fetcher.py` (TC-BF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `TickerNormalizer` — `quant_cn.core.ticker_normalizer` (L1)
- **Purpose:** Turn common A-share ticker spellings into Tushare `ts_code` and check `ts_code` validity.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.LegacyLabelImporter`.
- **Tests:** `tests/core/test_ticker_normalizer.py` (TC-TN-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `normalize` | Convert `code` to `ts_code`. | str -> str | `ValueError` | as class | see class |
| `is_valid` | True if `code` is already a well-formed `ts_code`. | str -> bool | — | as class | see class |

### `AkshareClient` — `quant_cn.data_loading.akshare_client` (L3)
- **Purpose:** Call one AkShare function per query (`api_name` = function name, `params` = its keyword arguments) and return its frame with dates normalised to YYYYMMDD strings, so the lake's schema and PIT rules apply unchanged. AkShare scrapes public pages (exchanges, ChinaBond, Jin10, Sina): network failures are retried; the library is imported on first use because it lives in the optional extra "sources" (D-022, D-065).
- **Base:** BaseApiClient. **Depends on (injected):** Clock, int, float, ModuleType | None.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_akshare_client.py` (TC-AKC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, int, float, ModuleType \| None -> None | — | callers of the class | — |
| `query` | Run one AkShare function and normalise its dates. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | as class | see class |

### `BaostockClient` — `quant_cn.data_loading.baostock_client` (L3)
- **Purpose:** Call one BaoStock query per request (`api_name` = method, e.g. query_history_k_data_plus) and return a frame in lake conventions: `ts_code` param converted to BaoStock's code ("600000.SH" -> "sh.600000") and back in the result, YYYYMMDD dates in and out, numeric strings as floats. Logs in once on first use; BaoStock is in the optional extra "sources" and is imported lazily. Verification only: its datasets never replace Tushare's (D-065).
- **Base:** BaseApiClient. **Depends on (injected):** Clock, int, float, ModuleType | None.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_baostock_client.py` (TC-BSC-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, int, float, ModuleType \| None -> None | — | callers of the class | — |
| `query` | Run one BaoStock query for one security. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | as class | see class |

### `FetcherFactory` — `quant_cn.data_loading.fetcher_factory` (L3)
- **Purpose:** Build the right fetcher for a DatasetSpec and inject the shared dependencies.
- **Base:** none. **Depends on (injected):** Config, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec, Mapping[str, BaseApiClient] | None, LakeQuery | None.
- **Used by:** `pipeline.DownloadPipeline`, `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_fetcher_factory.py` (TC-FF-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec, Mapping[str, BaseApiClient] \| None, LakeQuery \| None -> None | — | callers of the class | — |
| `build` | Instantiate the fetcher for `spec.sweep.kind`. | DatasetSpec -> BaseFetcher | `ConfigError` | as class | see class |

### `SingleCallFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Datasets fetched in one (paged) call, key "all": trade_cal, namechange.
- **Base:** BaseFetcher. **Depends on (injected):** —.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-SCF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_keys` | The single key. | str, str -> list[str] | — | as class | see class |
| `build_params` | Constant parameters, plus the run's date range when configured. | str, str, str -> dict[str, str] | — | as class | see class |

### `EnumFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Datasets swept over an enumerated list: stock_basic by list_status (L, D, P), index_daily / fund_daily by ts_code, opt_basic by exchange.
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, Sequence[str].
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-EF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, Sequence[str] -> None | — | callers of the class | — |
| `list_keys` | The enumerated values. | str, str -> list[str] | — | as class | see class |
| `build_params` | Key parameter plus constants and optional date range. | str, str, str -> dict[str, str] | — | as class | see class |

### `DateSweepFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Whole-market daily sweeps: trade_date and nav_date keys are trading days (daily, adj_factor, daily_basic, moneyflow, stk_limit, fund_nav); ann_date keys are weekdays (event datasets). An empty key within the last RECENT_SESSIONS trading sessions is logged `empty_recent` and retried next run instead of being marked done (D-078).
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-DSF-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec -> None | — | callers of the class | — |
| `list_keys` | Trading days (trade_date, nav_date) or weekdays (ann_date) in [start, end]. | str, str -> list[str] | `LakeError`, `ValueError` | as class | see class |
| `build_params` | {param: key} plus constants. | str, str, str -> dict[str, str] | — | as class | see class |

### `PeriodSweepFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Whole-market report-period sweeps (the *_vip fundamentals): one key per quarter end.
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, DateCodec.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-PSF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, DateCodec -> None | — | callers of the class | — |
| `list_keys` | Quarter ends in [start, end]. | str, str -> list[str] | `ValueError` | as class | see class |
| `build_params` | {"period": key} plus constants. | str, str, str -> dict[str, str] | — | as class | see class |

### `DateWindowFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Range-only endpoints swept by calendar window (D-063): one call per month ("YYYYMM" keys) or year ("YYYY" keys) with start_date / end_date clipped to the run range. Used where offset paging is broken or capped (share_float; index_weight past 100k rows) or the API takes ranges only (FRED series, fund_nav ranges). With `sweep.value_param` and values, each window is fetched once per value: keys "<window>_<value>", window-major so the newest `refetch_recent` keys are the latest window of every value (D-069).
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, DateCodec, list[str] | None.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-DWF-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, DateCodec, list[str] \| None -> None | — | callers of the class | — |
| `list_keys` | Window keys covering [start, end]. | str, str -> list[str] | `ValueError` | as class | see class |
| `build_params` | start_date / end_date of the window, clipped to the run range (+ the swept value). | str, str, str -> dict[str, str] | — | as class | see class |

### `HttpTransport` — `quant_cn.data_loading.http_transport` (L3)
- **Purpose:** Send one HTTP request and return the decoded JSON object or the raw bytes: a JSON POST (Tushare), a form POST (CNINFO, D-096), a GET returning JSON (Eastmoney report lists) and a GET returning bytes (PDF downloads). Browser-like User-Agent on every call.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `data_loading.CninfoClient`, `data_loading.EastmoneyReportClient`, `data_loading.BaseWebClient`, `data_loading.DocumentDownloader`, `data_loading.AppStoreClient`.
- **Tests:** `tests/data_loading/test_tushare_client.py` (TC-TC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `fetch_json` | POST `payload` as JSON to `url`. | str, Mapping[str, Any], float -> dict[str, Any] | `OSError`, `ValueError` | as class | see class |
| `fetch_form_json` | POST `form` url-encoded to `url` and decode the JSON reply. | str, Mapping[str, str], float -> dict[str, Any] | `OSError`, `ValueError` | `data_loading.CninfoClient` | TC-CNC-001 |
| `fetch_get_json` | GET `url` and decode the JSON reply. | str, float -> dict[str, Any] | `OSError`, `ValueError` | `data_loading.EastmoneyReportClient`, `data_loading.AppStoreClient` | TC-EMR-001, TC-ASC-001 |
| `fetch_bytes` | GET `url` and return the body (a PDF download). | str, float -> bytes | `OSError` | `data_loading.DocumentDownloader` | TC-DD-002 |

### `TushareClient` — `quant_cn.data_loading.tushare_client` (L3)
- **Purpose:** Query Tushare Pro: one logical query follows limit/offset paging until a short page and returns all rows; rate-limit replies wait and retry without spending retries; permission replies fail fast as PermissionDeniedError; other failures retry up to `retries`.
- **Base:** BaseApiClient. **Depends on (injected):** TushareConfig, Clock, HttpTransport | None.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_tushare_client.py` (TC-TC-001..009).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | TushareConfig, Clock, HttpTransport \| None -> None | — | callers of the class | — |
| `query` | Fetch every page of one query. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `ConfigError`, `PermissionDeniedError`, `DataSourceError` | as class | see class |
| `_fetch_page` (private) | internal helper over 20 lines | str, Mapping[str, object], Sequence[str] -> dict[str, Any] | — | internal | — |

### `FactorInputs` — `quant_cn.factor.base_factor` (L5)
- **Purpose:** The panels a factor may read, loaded once by FactorFactory for all factors of a run. Everything is already point in time: fundamentals come only as FUNDAMENTALS_PIT (effective the session after announcement, TTM from PIT-visible versions, D-092), prices and daily_basic are dated by their session (known at its close); `consensus` holds the analyst consensus on month-end sessions (plan 36).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `factor.BaseFactor`, `factor.FactorFactory`, `factor.library.DividendYieldFactor`, `factor.library.EarningsYieldFactor`, `factor.library.IntradayReversalFactor`, `factor.library.MomentumFactor`, `factor.library.ProfitGrowthFactor`, `factor.library.ReversalFactor`, `factor.library.RoeFactor`, `factor.library.TurnoverFactor`, `factor.library.PricingGapFactor`.
- **Tests:** `tests/factor/test_base_factor.py` (TC-FIN-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_field` | One fundamentals field as (trade_date, ts_code, <name>). | str -> pd.DataFrame | — | as class | see class |

### `BaseFactor` — `quant_cn.factor.base_factor` (L5)
- **Purpose:** Abstract factor: declares which inputs, fundamentals fields and daily_basic columns it needs and how many sessions of price history before the first output date; `compute` turns FactorInputs into FACTOR_PANEL rows for [start, end]. Contract (FACTOR_TESTING_DESIGN §11): the value at t uses only data known by the close of t; fundamentals only through FUNDAMENTALS_PIT. Subclasses register themselves by class name for FactorFactory.
- **Base:** ABC. **Depends on (injected):** str.
- **Used by:** `factor.FactorFactory`, `factor.library.*`, `factor.library.DividendYieldFactor`, `factor.library.EarningsYieldFactor`, `factor.library.MomentumFactor`, `factor.library.ProfitGrowthFactor`, `factor.library.ReversalFactor`, `factor.library.RoeFactor`, `factor.library.TurnoverFactor`, `factor.library.PricingGapFactor`, `pipeline.FeatureStep`.
- **Tests:** `tests/factor/test_base_factor.py` (TC-BFA-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str -> None | `TypeError` | callers of the class | — |
| `lookback` | Sessions of history needed before the first output date (0 = none). | — -> int | — | as class | see class |
| `consensus_days` | Analyst-note window (calendar days) of the `consensus` input (0 = not needed). | — -> int | — | `factor.FactorFactory` | TC-FAF-004 |
| `compute` | FACTOR_PANEL rows of this factor for [start, end]. | FactorInputs, str, str -> pd.DataFrame | `SchemaError` | as class | see class |
| `compute_raw` | The raw factor value per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `FactorAcceptance` — `quant_cn.factor.factor_acceptance` (L5)
- **Purpose:** Criteria 1-3 of FACTOR_TESTING_DESIGN §6 per factor at one horizon, from the campaign's IC_TEST: (1) NW t of the full-window mean IC >= t_min (HLZ) and BHY-adjusted p <= alpha; (2) every sub-period mean IC has the full-window sign with sign-oriented t >= t_sub; (3) the bootstrap CI of ICIR excludes 0. Criterion 4 (DSR, PBO, out-of-sample) needs a traded variant and belongs to plan 06, so `verdict` is "pass" (criteria 1-3 met) or "fail"; the horizon profile (peak, half-life, accumulation ratio; D-095) is attached as notes, never a criterion.
- **Base:** none. **Depends on (injected):** int, float, float, float, Sequence[str].
- **Used by:** `research_space/notebooks/20260930_factor_campaign_01.ipynb`, `plan 06 ReportBuilder`.
- **Tests:** `tests/factor/test_factor_acceptance.py` (TC-FA-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int, float, float, float, Sequence[str] -> None | `ValueError` | callers of the class | — |
| `compute` | One verdict row per factor. | pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |
| `_build_row` (private) | internal helper over 20 lines | pd.DataFrame, pd.DataFrame, str -> dict[str, object] | — | internal | — |

### `FactorReport` — `quant_cn.factor.factor_evaluator` (L5)
- **Purpose:** The evaluation of one campaign: IC series, every test result, quantile ladders.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `factor.FactorEvaluator`.
- **Tests:** `tests/factor/test_factor_evaluator.py` (TC-FEV-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `FactorEvaluator` — `quant_cn.factor.factor_evaluator` (L5)
- **Purpose:** Evaluate every factor of a campaign (FACTOR_TESTING_DESIGN §2, §3, §6): tradeable forward returns from the open of t+1, IC series per horizon, the IcSignificance tests, decay across horizons (half-life), rank autocorrelation (turnover proxy), quantile ladders and long-short statistics on non-overlapping samples, then the campaign-level Holm / BHY / Romano-Wolf adjustment and HLZ flag over all factor x horizon mean-IC tests. Records each variant in the TrialLog (identical variants are not recorded twice).
- **Base:** none. **Depends on (injected):** IcCalculator, IcSignificance, MultipleTestingAdjuster, QuantileReturns, ReturnStats, BlockBootstrap, Sequence[int].
- **Used by:** `notebooks`, `pipeline.EvaluationStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/factor/test_factor_evaluator.py` (TC-FEV-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | IcCalculator, IcSignificance, MultipleTestingAdjuster, QuantileReturns, ReturnStats, BlockBootstrap, Sequence[int] -> None | `ValueError` | callers of the class | — |
| `compute` | The campaign report. | pd.DataFrame, pd.DataFrame, TrialLog \| None, Mapping[str, Mapping[str, object]] \| None, bool -> FactorReport | `SchemaError` | as class | see class |
| `build_campaign` | Campaign-level adjustment over every factor x horizon mean-IC test. | pd.DataFrame, pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |
| `_build_factor_rows` (private) | internal helper over 20 lines | pd.DataFrame, pd.DataFrame, str -> pd.DataFrame | — | internal | — |

### `FactorFactory` — `quant_cn.factor.factor_factory` (L5)
- **Purpose:** Resolve config/factors.yaml entries to BaseFactor instances (every module under factor/library/ is imported so its classes register themselves; adding a factor needs one module, one registry block and one YAML line) and load, once, the panels the chosen factors declare: dense prices from `lookback` sessions before the start, PIT fundamentals for the union of fields, daily_basic columns, and the analyst consensus on month-end sessions from 40 days before the start plus the last session (the longest `consensus_days`; plan 36), and the RetailGauge readings (DatedTableStore derived/retail_gauge) from 60 days before the start when a factor declares `retail_gauge` (plan 21 ph6).
- **Base:** none. **Depends on (injected):** Sequence[FactorSpec], TradingCalendar, DateCodec, ConsensusPanelBuilder | None, DatedTableStore | None.
- **Used by:** `notebooks`, `pipeline.FeatureStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/factor/test_factor_factory.py` (TC-FAF-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Sequence[FactorSpec], TradingCalendar, DateCodec, ConsensusPanelBuilder \| None, DatedTableStore \| None -> None | — | callers of the class | — |
| `build_all` | One instance per configured factor. | — -> list[BaseFactor] | `ConfigError` | as class | see class |
| `build_inputs` | The panels the factors need for outputs in [start, end]. | LakeReader, Sequence[BaseFactor], str, str -> FactorInputs | `LakeError`, `ConfigError` | as class | TC-FAF-003..005 |

### `FactorPreprocessor` — `quant_cn.factor.factor_preprocessor` (L5)
- **Purpose:** The ordered chain applied to every raw factor, each step optional and logged: winsorise (median +- k * 1.4826 * MAD per date) -> standardise (z per date) -> neutralise (per-date OLS residual on Shenwan L1 dummies and log market cap, D-093) -> standardise again, so the processed value is a unit-dispersion, industry- and size-neutral z-score. `value_raw` is kept; `value` holds the result. Rows without exposures are dropped when neutralising.
- **Base:** none. **Depends on (injected):** Winsorizer | None, Standardizer | None, Neutralizer | None.
- **Used by:** `pipeline.FeatureStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/factor/test_factor_preprocessor.py` (TC-FPP-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Winsorizer \| None, Standardizer \| None, Neutralizer \| None -> None | — | callers of the class | — |
| `compute` | Processed FACTOR_PANEL. | pd.DataFrame, pd.DataFrame \| None -> pd.DataFrame | `ValueError`, `SchemaError` | as class | see class |
| `build_log` | What the last compute did. | — -> pd.DataFrame | — | as class | see class |
| `_compute_neutral` (private) | internal helper over 20 lines | pd.DataFrame, pd.DataFrame \| None -> pd.DataFrame | — | internal | — |

### `EarningsYieldFactor` — `quant_cn.factor.library.earnings_yield_factor` (L5)
- **Purpose:** Earnings yield EP_TTM = net profit attributable to parent over the trailing twelve months (PIT, D-092) / total market value at the close of t. Value factor (Basu 1977; Fama & French 1992), EP rather than PE so loss-makers rank low instead of flipping sign.
- **Base:** BaseFactor. **Depends on (injected):** —.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_fundamental_factors.py` (TC-EYF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_raw` | EP per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `MomentumFactor` — `quant_cn.factor.library.momentum_factor` (L5)
- **Purpose:** MOM_{12-1} = P_adj(t - skip) / P_adj(t - window) - 1 on the backward-adjusted close (ratios are PIT-safe, FACTOR_TESTING_DESIGN §11), skipping the most recent month to avoid the short-term reversal (Jegadeesh & Titman 1993). Suspended sessions carry the last close.
- **Base:** BaseFactor. **Depends on (injected):** str, int, int.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_price_factors.py` (TC-MOM-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str, int, int -> None | `ValueError` | callers of the class | — |
| `lookback` | Sessions of history needed. | — -> int | — | as class | see class |
| `compute_raw` | 12-1 momentum per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `ProfitGrowthFactor` — `quant_cn.factor.library.profit_growth_factor` (L5)
- **Purpose:** Growth = (NI_TTM(P) - NI_TTM(P - 1 year)) / /NI_TTM(P - 1 year)/ for the latest PIT-visible period P, both TTMs from the versions known at the announcement (the lake's `n_income_attr_p_ttm_yoy`, D-092). Growth / earnings-momentum factor (Jegadeesh & Livnat 2006). Needs eight quarters of history, so it starts about two years after the statements.
- **Base:** BaseFactor. **Depends on (injected):** —.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_fundamental_factors.py` (TC-PGF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_raw` | TTM profit growth per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `IntradayReversalFactor` — `quant_cn.factor.library.intraday_reversal_factor` (L5)
- **Purpose:** IRV = -sum(ln(close / open)) over the `top_k` sessions with the highest free-float turnover among the last `window` grid sessions. The 1-month reversal lives in the intraday leg of busy sessions; the overnight leg is momentum (research run 20261114_reversal_variants: 20-day rank IC 0.076 vs 0.046 for ReversalFactor). Sign flipped so higher values are expected to earn more. Open and close of one session share the adjustment factor, so unadjusted prices are used.
- **Base:** ReversalFactor. **Depends on (injected):** str, int, int, int.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_intraday_reversal_factor.py` (TC-IRV-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str, int, int, int -> None | `ValueError` | callers of the class | TC-IRV-005 |
| `compute_raw` | Intraday high-turnover reversal per stock and session on the dense session grid. | FactorInputs -> pd.DataFrame | — | as class | TC-IRV-001..004 |

### `PricingGapFactor` — `quant_cn.factor.library.pricing_gap_factor` (L5)
- **Purpose:** Linear-pricing gap (D-173). On each session the latest consensus on or before it: FY1-FY3 median net profit discounted at 9% from each fiscal year end (FY1 end floored at 0.1 years), growth from FY2 -> FY3 (clipped to [-0.3, 1.0]) fading ×0.7 a year for 7 years, exit at PE 15; missing FY3 = FY2²/FY1. value_raw = -log(total_mv / value): higher = cheaper than the linear consensus price. FY1 or FY2 <= 0 -> NaN.
- **Base:** BaseFactor. **Depends on (injected):** str, float, int, float, float, float, float, int.
- **Used by:** (none yet; built by name from config/factors.yaml `pricing_gap` through `factor.FactorFactory`).
- **Tests:** `tests/factor/test_pricing_gap_factor.py` (TC-LPG-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | parameters | str, float, int, float, float, float, float, int -> None | `ValueError` | as class | TC-LPG-003 |
| `consensus_days` | consensus note window | — -> int | — | as class | TC-LPG-003 |
| `compute_raw` | -log(market value / linear consensus value) per stock and session | FactorInputs -> pd.DataFrame | — | `factor.BaseFactor.compute` | TC-LPG-002 |
| `compute_value` | the linear consensus value | ndarray ×4 -> ndarray | — | `compute_raw` | TC-LPG-001 |

### `RetailGaugeFactor` — `quant_cn.factor.library.retail_gauge_factor` (L5)
- **Purpose:** value_raw = -pct of the latest RetailGauge reading with as_of on or before the session and at most `max_age_days` (45) calendar days old; higher = retail leaving, expected better (D-155 sign). Point in time: a reading uses data known by its as_of close (plan 21 ph6).
- **Base:** BaseFactor. **Depends on (injected):** str, int.
- **Used by:** (none yet; built by name from config/factors.yaml `retail_gauge` through `factor.FactorFactory`).
- **Tests:** `tests/factor/test_retail_gauge_factor.py` (TC-RGFA-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | parameters | str, int -> None | `ValueError` | as class | TC-RGFA-002 |
| `compute_raw` | minus the latest fresh reading per stock and session | FactorInputs -> pd.DataFrame | — | `factor.BaseFactor.compute` | TC-RGFA-001..002 |

### `ReversalFactor` — `quant_cn.factor.library.reversal_factor` (L5)
- **Purpose:** REV = -(P_adj(t) / P_adj(t - window) - 1): last month's losers tend to rebound, strongly so in China's retail-driven market (Jegadeesh 1990; Lehmann 1990). Sign flipped so higher values are expected to earn more. Suspended sessions carry the last close.
- **Base:** BaseFactor. **Depends on (injected):** str, int.
- **Used by:** `factor.library.IntradayReversalFactor`.
- **Tests:** `tests/factor/test_price_factors.py` (TC-REV-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str, int -> None | `ValueError` | callers of the class | — |
| `lookback` | Sessions of history needed. | — -> int | — | as class | see class |
| `compute_raw` | Reversal per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `RoeFactor` — `quant_cn.factor.library.roe_factor` (L5)
- **Purpose:** Return on equity ROE_TTM = net profit attributable to parent over the trailing twelve months / equity attributable to parent in the latest PIT-visible balance sheet (both D-092 PIT). Profitability / quality factor (Novy-Marx 2013; Fama & French 2015 RMW).
- **Base:** BaseFactor. **Depends on (injected):** —.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_fundamental_factors.py` (TC-ROE-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_raw` | ROE per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `DividendYieldFactor` — `quant_cn.factor.library.dividend_yield_factor` (L5)
- **Purpose:** DP = trailing 12-month dividend yield (daily_basic dv_ttm, percent -> fraction); 0 for a stock with a market cap and no dividend in the last 12 months; no value for a session without daily_basic. Same descriptor as the risk style dividend_yield (D-148).
- **Base:** BaseFactor. **Depends on (injected):** str.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_price_factors.py` (TC-DYF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `lookback` | Sessions of history needed. | — -> int | — | as class | see class |
| `compute_raw` | Dividend yield per stock and session on the dense session grid. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `TurnoverFactor` — `quant_cn.factor.library.turnover_factor` (L5)
- **Purpose:** TURN = -mean(turnover_rate_f over the last `window` sessions, at least `min_obs` traded): heavily traded stocks underperform, a liquidity / attention effect that is strong in China (Datar, Naik & Radcliffe 1998; Liu, Stambaugh & Yuan 2019). Suspended sessions are missing, not zero.
- **Base:** BaseFactor. **Depends on (injected):** str, int, int.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_price_factors.py` (TC-TRN-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str, int, int -> None | `ValueError` | callers of the class | — |
| `lookback` | Sessions of history needed. | — -> int | — | as class | see class |
| `compute_raw` | Turnover per stock and session on the dense session grid. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `SignalCombiner` — `quant_cn.factor.signal_combiner` (L5)
- **Purpose:** score_{i,t} = sum_f w_f z_{f,i,t} / sum_{f available} /w_f/ over the processed factors a stock has at t (at least `min_factors`), then standardised per date: an equal-risk blend of z-scores that tolerates a missing factor instead of dropping the stock.
- **Base:** none. **Depends on (injected):** Mapping[str, float], Standardizer, int.
- **Used by:** `pipeline.FeatureStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/factor/test_signal_combiner.py` (TC-SGC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Mapping[str, float], Standardizer, int -> None | `ValueError` | callers of the class | — |
| `compute` | Score rows from processed factor rows. | pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |

### `Compactor` — `quant_cn.lake.compactor` (L2)
- **Purpose:** Rebuild a dataset's curated partitions from its raw files: select declared fields, cast dtypes, fill `key_defaults` into NULL key columns, drop duplicate primary keys (keeping one), sort by partition date then key, validate, write, and record a manifest in `meta/manifest/<dataset>.json`.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, BaseStore, Clock.
- **Used by:** `cli.QuantCnCli`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_compactor.py` (TC-CO-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, BaseStore, Clock -> None | — | callers of the class | — |
| `rebuild` | Replace the curated partitions of `spec` (all years, or only `years`). | DatasetSpec, set[int] \| None -> StepReport | `SchemaError`, `LakeError` | as class | see class |

### `DerivedViews` — `quant_cn.lake.derived_views` (L2)
- **Purpose:** Create the `derived` schema views built only from curated/: `derived.prices_adj` (daily bars joined to adj_factor, close_adj = close * adj_factor; PRICE_PANEL columns; retired alias codes absent from stock_basic dropped); `derived.fundamentals_long` = `derived.fundamentals_base` (every statement dataset under curated/fundamentals/ unpivoted to one row per numeric field and announced version, report_type = '1') plus `derived.fundamentals_ttm` (`<flow>_ttm` and `<field>_ttm_yoy` rows from the latest versions known at each announcement, D-092); `derived.fut_holding_brokers` (contract rows of fut_holding without member-category totals, exchange "ZCE" -> "CZCE"; D-079); `derived.fut_daily_one_sided` (fut_daily with vol, amount, oi, oi_chg halved for SHFE/DCE/CZCE/INE before 2020-01-02, flagged two_sided_adjusted; D-079); `derived.industry_l1` (Shenwan L1 validity intervals per stock, PIT rows plus back-filled rows flagged industry_backfilled; l1_pit = rows not back-filled, l1_grouping = any; D-071); `derived.margin_targets` (SZSE official list + SSE proxy from margin_detail, source column; D-084); `derived.universe` / `derived.features` over the UniverseStep / FeatureStep year files (refresh_tables); `derived.ticker_alias` through TickerAliasMap (D-089); then the `quality` schema through QualityViews.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, Mapping[str, DatasetSpec], Sequence[FuturesCategory], Sequence[TickerAlias].
- **Used by:** `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `cli.ServiceBuilder`, `pipeline.FeatureStep`.
- **Tests:** `tests/lake/test_derived_views.py` (TC-DV-001..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, Mapping[str, DatasetSpec], Sequence[FuturesCategory], Sequence[TickerAlias] -> None | — | callers of the class | — |
| `refresh` | (Re)create every derived view whose curated inputs exist; drop the others. | — -> list[str] | `LakeError` | as class | see class |
| `refresh_tables` | (Re)create the views over materialised tables (UniverseStep, FeatureStep outputs). | — -> list[str] | `LakeError` | as class | see class |
| `_build_plan` (private) | internal helper over 20 lines | — -> list[tuple[str, list[str], str]] | — | internal | — |

### `EffectiveDateResolver` — `quant_cn.lake.effective_date_resolver` (L2)
- **Purpose:** Turn a dataset's `known_on` value into `effective_date`, the first China trading session the row may be used (FACTOR_TESTING_DESIGN §11): as_is          -> that session, or the next one if the day is closed (same-day data); next_session   -> the lag_sessions-th session strictly after (default 1: FRED, analyst reports; 2: survey visits, disclosed 1-2 days after the visit); period_end_lag -> period end (a YYYYMM month or YYYYMMDD date) + release_lag_days, then the first session on or after (monthly macro without an announce date); period_start_lag -> month (or date) start + release_lag_days, first session on or after (monthly lists published at the start of the month they apply to).
- **Base:** none. **Depends on (injected):** TradingCalendar, DateCodec.
- **Used by:** (none yet).
- **Tests:** `tests/lake/test_effective_date_resolver.py` (TC-EDR-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | TradingCalendar, DateCodec -> None | — | callers of the class | — |
| `get_effective_date` | Effective session for one known-on value under the dataset's rule. | str, DatasetSpec -> str | `ValueError`, `LakeError` | as class | see class |
| `compute` | Copy of `frame` with an `effective_date` column. | pd.DataFrame, DatasetSpec -> pd.DataFrame | `ValueError`, `LakeError` | as class | see class |

### `ExposureReader` — `quant_cn.lake.exposure_reader` (L2)
- **Purpose:** Per universe member and session: the Shenwan L1 group in effect (derived.industry_l1, l1_grouping = the PIT row or the back-filled first-known L1, flagged; D-071, D-093) and log market cap (ln of total_mv in CNY, from daily_basic at the close of t). The inputs of FactorPreprocessor's neutralisation.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `pipeline.FeatureStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_lake_reader.py` (TC-EXR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery -> None | — | callers of the class | — |
| `read_exposures` | Exposures of universe members in [start, end]. | str, str -> pd.DataFrame | `LakeError` | as class | see class |

### `FetchLog` — `quant_cn.lake.fetch_log` (L2)
- **Purpose:** Record finished (dataset, key) pairs in `meta.fetch_log`, mirror them to `meta/fetch_log.parquet` on save, and rebuild the table after the DuckDB file is lost.
- **Base:** BaseFetchLog. **Depends on (injected):** LakeCatalog.
- **Used by:** `cli.QuantCnCli`, `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_fetch_log.py` (TC-FL-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog -> None | `LakeError` | callers of the class | — |
| `mirror_path` | Location of the durable parquet copy. | — -> Path | — | as class | see class |
| `read_done_keys` | Keys recorded for `dataset`. | str -> set[str] | `LakeError` | as class | see class |
| `mark_done` | Upsert one finished key. | str, str, int, Path \| None -> None | `LakeError` | as class | see class |
| `save` | Atomically rewrite `meta/fetch_log.parquet` from the table. | — -> Path | `LakeError` | as class | see class |
| `rebuild_from_mirror` | Rebuild the table from the parquet mirror, then add raw files the mirror does not know. | — -> int | `LakeError` | as class | see class |
| `remove_orphans` | Drop done-rows whose raw file no longer exists (D-073): keys of a replaced sweep layout or raw files moved out of the lake. Empty keys (n_rows = 0, no file by design) and datasets no longer configured are kept. Saves the mirror when anything was removed. | — -> dict[str, list[str]] | `LakeError` | as class | see class |

### `LakeCatalog` — `quant_cn.lake.lake_catalog` (L2)
- **Purpose:** Own the lake's single DuckDB connection (`meta/quant_cn.duckdb`): schemas `raw`, `curated`, `meta`; one view per dataset and zone; `meta.dataset_meta`; generated INDEX.md files. The DuckDB file is disposable: `rebuild()` recreates it from the parquet files.
- **Base:** none. **Depends on (injected):** Path, Mapping[str, DatasetSpec], bool.
- **Used by:** `lake.FetchLog`, `lake.RunLog`, `lake.LakeQuery`, `lake.Compactor`, `pipeline.FetchStep.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `lake.DerivedViews`, `lake.PitAligner`, `lake.ProjectCatalog`, `cli.ServiceBuilder`, `lake.QualityViews`, `lake.LakeReader`, `lake.TickerAliasMap`, `cli.ResearchCommands`, `cli.DocumentCommands`.
- **Tests:** `tests/lake/test_lake_catalog.py` (TC-LC-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, Mapping[str, DatasetSpec], bool -> None | `LakeError` | callers of the class | — |
| `catalog_path` | Location of the DuckDB catalog file. | — -> Path | — | as class | see class |
| `connection` | The shared DuckDB connection, opened lazily with zones, schemas and dataset_meta. | — -> duckdb.DuckDBPyConnection | `LakeError` | as class | see class |
| `list_raw_files` | Raw parquet files of a dataset, sorted by name. | DatasetSpec -> list[Path] | — | as class | see class |
| `refresh_view` | (Re)create `raw.<name>` and `curated.<name>` views for whatever files exist. | DatasetSpec -> None | `LakeError` | as class | see class |
| `refresh_views` | refresh_view for every configured dataset. | — -> None | `LakeError` | as class | see class |
| `rebuild` | Delete the DuckDB file and recreate schemas, dataset_meta and all views from parquet. Tables owned by FetchLog/RunLog are restored by their own classes. | — -> None | `LakeError` | as class | see class |
| `write_indexes` | Generate INDEX.md in the lake root and each zone: datasets, file counts, last update. | — -> list[Path] | `LakeError` | as class | see class |
| `close` | Close the DuckDB connection if open. | — -> None | — | as class | see class |
| `_write_dataset_meta` (private) | internal helper over 20 lines | duckdb.DuckDBPyConnection -> None | — | internal | — |

### `LakeQuery` — `quant_cn.lake.lake_query` (L2)
- **Purpose:** Run read queries against the catalog views; the only way code above the lake reads data.
- **Base:** none. **Depends on (injected):** LakeCatalog.
- **Used by:** `portfolio.SmallCapWatchBuilder`, `lake.TradingCalendar`, `lake.Compactor.rebuild`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `lake.DerivedViews`, `lake.PitAligner`, `cli.ServiceBuilder`, `data_loading.FetcherFactory`, `lake.QualityViews`, `lake.ReleaseLagChecker`, `lake.LakeReader`, `lake.TickerAliasMap`, `pipeline.UniverseStep`, `lake.ExposureReader`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `cli.ResearchCommands`, `cli.DocumentCommands`, `data_loading.DocumentDownloader`, `lake.StatementVersionReader`, `portfolio.EtfProxyBuilder`, `risk.FactorMonitorBuilder`, `industry_graph.LegacyLabelImporter`, `portfolio.BuybackMonitorBuilder`.
- **Tests:** `tests/lake/test_lake_query.py` (TC-LQ-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog -> None | — | callers of the class | — |
| `sql` | Execute a query and return the result as a DataFrame. | str, Sequence[object] \| None -> pd.DataFrame | `LakeError` | as class | see class |
| `has_view` | True if `schema.view` exists in the catalog. | str -> bool | `LakeError` | as class | see class |
| `read_prices` | Adjusted daily prices from `derived.prices_adj` for a date range. | str, str, Sequence[str] \| None -> pd.DataFrame | `LakeError`, `SchemaError` | as class | see class |
| `register_frame` | Expose an in-memory frame as a view so SQL can join it with lake views. | str, pd.DataFrame -> str | `ValueError`, `LakeError` | as class | see class |
| `list_views` | Every lake view as "schema.view", plus registered frames by bare name. | — -> list[str] | `LakeError` | as class | see class |

### `LakeReader` — `quant_cn.lake.lake_reader` (L2)
- **Purpose:** The read API factors, the universe step and notebooks use (SRC_DESIGN §2.2b, D-089): one curated dataset as a panel, dense or sparse prices, point-in-time fundamentals, reference tables (in-memory frames and view discovery: LakeQuery). Retired codes are mapped to their surviving codes on every per-stock read (TickerAliasMap, new code wins); every output is validated with its schema; an optional PanelCache serves repeated reads. LakeQuery stays the raw SQL layer underneath.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, Mapping[str, DatasetSpec], PitAligner, TickerAliasMap, TradingCalendar, PanelCache | None.
- **Used by:** `cli.ServiceBuilder`, (none yet), `factor.FactorFactory`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`.
- **Tests:** `tests/lake/test_lake_reader.py` (TC-LRD-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, Mapping[str, DatasetSpec], PitAligner, TickerAliasMap, TradingCalendar, PanelCache \| None -> None | — | callers of the class | — |
| `read_panel` | One curated dataset over a date range as a long panel, sorted by primary key. | str, str, str, Sequence[str] \| None, Sequence[str] \| None -> pd.DataFrame | `LakeError`, `SchemaError` | as class | see class |
| `read_prices` | Daily prices (raw and backward-adjusted close) for a date range. | str, str, Sequence[str] \| None, bool -> pd.DataFrame | `LakeError`, `SchemaError` | as class | see class |
| `read_fundamentals_pit` | Point-in-time fundamentals per session (PitAligner), statements filed under a retired code attached to the surviving code (the new code's value wins on the same day). | Sequence[str] \| None, str, str, Sequence[str] \| None -> pd.DataFrame | `ValueError`, `LakeError` | as class | see class |
| `read_universe` | The tradeable universe per session (UniverseStep output). | str, str, bool -> pd.DataFrame | `LakeError` | as class | see class |
| `read_reference` | A whole reference table (curated under reference/: stock_basic, namechange, trade_cal, index_daily, index_classify, fund_basic, fut_basic, ...). | str -> pd.DataFrame | `LakeError` | as class | see class |
| `_load_panel` (private) | internal helper over 20 lines | DatasetSpec, str, str, str, Sequence[str] \| None, list[str] -> pd.DataFrame | — | internal | — |

### `PanelCache` — `quant_cn.lake.panel_cache` (L2)
- **Purpose:** Keep recently read panels in memory, keyed by (method, arguments), least recently used evicted first once the total size exceeds `max_bytes`. Frames are stored and returned as shallow copies: with pandas copy-on-write, a caller modifying its frame never changes the cached one. On by default in notebooks, off in pipelines (LakeReader decides).
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `lake.LakeReader`, `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_panel_cache.py` (TC-PCH-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | `ValueError` | callers of the class | — |
| `size_bytes` | Bytes held by cached frames. | — -> int | — | as class | see class |
| `find` | The cached frame for `key`, marking it most recently used. | Hashable -> pd.DataFrame \| None | — | as class | see class |
| `add` | Cache `frame` under `key`, evicting least recently used entries to stay under the cap. | Hashable, pd.DataFrame -> None | — | as class | see class |
| `remove_all` | Empty the cache (e.g. after a curate run changed the lake). | — -> None | — | as class | see class |

### `ParquetWriter` — `quant_cn.lake.parquet_writer` (L2)
- **Purpose:** Write raw fetch results and curated partitions as zstd parquet, atomically (write `.tmp`, fsync, rename), so a crash never leaves a half-written file.
- **Base:** BaseStore. **Depends on (injected):** Path.
- **Used by:** `cli.QuantCnCli`, `cli.ServiceBuilder`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `cli.ReportCommands`.
- **Tests:** `tests/lake/test_parquet_writer.py` (TC-PW-001..008).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `get_raw_path` | Target path of one raw fetch key. | DatasetSpec, str -> Path | — | as class | see class |
| `get_curated_path` | Target path of one curated partition. | DatasetSpec, int \| None -> Path | — | as class | see class |
| `write_raw` | Persist one fetch key's rows, dtypes coerced by the dataset schema (dates stay strings); an existing file is kept as `<file>.prev` until `rebuild` confirms it (D-083). | DatasetSpec, str, pd.DataFrame -> Path \| None | `SchemaError`, `LakeError` | as class | see class |
| `write_curated` | Replace one curated partition after validating it against the dataset schema. | DatasetSpec, int \| None, pd.DataFrame -> Path | `SchemaError`, `LakeError` | as class | see class |
| `write_derived` | Persist one year of a materialised derived table (e.g. the universe). | str, int, pd.DataFrame -> Path | `LakeError` | as class | see class |
| `write_table` | Persist a whole small table (reports under derived/, logs under meta/). | str, str, pd.DataFrame -> Path | `ValueError`, `LakeError` | as class | see class |

### `PitAligner` — `quant_cn.lake.pit_aligner` (L2)
- **Purpose:** Align fundamentals to trading days without look-ahead. A version announced on `known_on` (f_ann_date / ann_date) becomes effective on the first trading day strictly after it; on each day the visible value of a field is the latest report period effective so far, in its latest effective restatement. Older-period restatements never replace a newer period. Built as the DuckDB view `derived.fundamentals_states` (one row per change) and read with an ASOF JOIN from trading days.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, DateCodec.
- **Used by:** `pipeline.CuratePipeline`, `research_space/main.ipynb`, `pipeline.DeriveStep`, `cli.ServiceBuilder`, `lake.LakeReader`.
- **Tests:** `tests/lake/test_pit_aligner.py` (TC-PAD-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, DateCodec -> None | — | callers of the class | — |
| `refresh` | (Re)create `derived.fundamentals_states` from derived.fundamentals_long and the curated trading calendar. | — -> str | `LakeError` | as class | see class |
| `read_aligned` | Point-in-time values for every trading day in [start, end] and every (ticker, field) that has become visible by that day. | str, str, Sequence[str] \| None, Sequence[str] \| None -> pd.DataFrame | `ValueError`, `LakeError` | as class | see class |

### `ProjectCatalog` — `quant_cn.lake.project_catalog` (L2)
- **Purpose:** Rebuild schema `project` in the lake's DuckDB from the repository: folders, files, classes, methods, used_by, contracts, test_cases, decisions, plans, phases, datasets, lint_findings, plus views tree, class_graph, stale and todo. Markdown and code stay the source of truth; the schema is dropped and rebuilt, never edited.
- **Base:** none. **Depends on (injected):** LakeCatalog, CodeTableBuilder, DocTableBuilder, Mapping[str, DatasetSpec], ContractLinter, Clock.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_project_catalog.py` (TC-PJC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, CodeTableBuilder, DocTableBuilder, Mapping[str, DatasetSpec], ContractLinter, Clock -> None | — | callers of the class | — |
| `rebuild` | Drop and recreate every table and view of schema `project` in one transaction. | bool -> dict[str, int] | `LakeError`, `RuntimeError` | as class | see class |

### `QualityViews` — `quant_cn.lake.quality_views` (L2)
- **Purpose:** Create the `quality` schema: cross-source comparisons that report, never overwrite (D-065). `quality.margin_targets_agreement` (SSE eligibility proxy vs margin_secs, D-084); `quality.price_mismatches` / `quality.price_crosscheck` (Tushare daily close vs BaoStock, relative tolerance 1e-6, per row / per day, D-085); `quality.adj_crosscheck` (adjustment step at each BaoStock dividend date vs Tushare adj_factor).
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery.
- **Used by:** `lake.DerivedViews.refresh`.
- **Tests:** `tests/lake/test_quality_views.py` (TC-QV-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery -> None | — | callers of the class | — |
| `refresh` | (Re)create every quality view whose inputs exist; drop the others. | — -> list[str] | `LakeError` | as class | see class |

### `RebuildAudit` — `quant_cn.lake.rebuild_audit` (L2)
- **Purpose:** Record, on `rebuild`, what changed below raw/ since the last one. Fetch-log rows whose raw file is gone go to meta/manifest/fetch_log_orphans.json (D-073). Raw files rewritten by a refetch keep their previous version as `<file>.prev` (ParquetWriter); `record_rewrites` lists each with old and new row counts in meta/manifest/raw_rewrites.json and then deletes the `.prev` copies, so every forced refetch is auditable (D-083).
- **Base:** none. **Depends on (injected):** Path, Clock.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_rebuild_audit.py` (TC-RA-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, Clock -> None | — | callers of the class | — |
| `record_orphans` | Write the fetch-log orphans removed by this rebuild. | dict[str, list[str]] -> Path | `LakeError` | as class | see class |
| `record_rewrites` | Record every rewritten raw file (old vs new rows) and delete the kept `.prev` copies. | — -> list[dict[str, object]] | `LakeError` | as class | see class |

### `BuybackEventsBuilder` — `quant_cn.portfolio.buyback_events_builder` (L5)
- **Purpose:** Buyback announcements of the last `days` calendar days: new 预案 of at least 2% of total market cap across the market (largest first) and every event of the held and watched stocks (newest first); writes buybacks.json.
- **Base:** none. **Depends on (injected):** LakeQuery, days: int.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/portfolio/test_buyback_events_builder.py` (TC-BEB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the events document | as_of: str, book: list[str] -> dict | LakeError | `write` | — |
| `compute` | document from rows and caps | ev, mv: DataFrame, as_of: str, book: list[str] -> dict | — | `build` | TC-BEB-001 |
| `write` | write buybacks.json | out_dir: Path, as_of: str, book: list[str] -> Path | LakeError | `cli.ReportCommands` | TC-BEB-002 |

### `BuybackMonitorBuilder` — `quant_cn.portfolio.buyback_monitor_builder` (L5)
- **Purpose:** The market-wide buyback and 增持 document, the two kinds apart: live programmes (planned low / high, executed, % done against the low else high, price cap vs close, % of market cap, labels), the window's events (new, completed = executed first reached the low, stopped / expired / ended), totals over live ones (all, by purpose or holder type, by funding, 专项贷款 sum), and per announcement month count, high amount and loans; writes buyback_monitor.json.
- **Base:** none. **Depends on (injected):** LakeQuery, BuybackLedger, LabelStore, BuybackPlanFrame, days: int.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/portfolio/test_buyback_monitor_builder.py` (TC-BMB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the monitor document from the lake | as_of: str -> dict | LakeError | `write` | TC-BMB-002 |
| `compute_section` | one kind's live rows, events, totals and months | rows, mv: DataFrame, as_of, start: str -> dict | — | `build` | TC-BMB-001 |
| `write` | write buyback_monitor.json | out_dir: Path, as_of: str -> Path | LakeError | `cli.ReportCommands` | TC-BMB-002 |

### `BuybackPlanFrame` — `quant_cn.portfolio.buyback_plan_frame` (L5)
- **Purpose:** Both kinds of programme in one frame with label fields. 回购: BuybackLedger programmes since 2024 take the 回购 labels of their stock from 3 days before the 预案 up to 90 days after and before the next 预案 (earliest label gives purpose, amounts, price cap; funding is the union; loan from any); unlabelled ones stay only without a nearby 限制性股票 title and with a price cap. 增持: one row per label item, 方案 / 报告书 repeats dropped, period from the label (6 months default), executed = Σ change_vol × (avg_price, else close) of the named holders' IN trades in the period.
- **Base:** none. **Depends on (injected):** none.
- **Used by:** `portfolio.BuybackMonitorBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/portfolio/test_buyback_plan_frame.py` (TC-BPF-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_items` | one row per label item known on as_of | labels: DataFrame, as_of: str -> DataFrame | — | `portfolio.BuybackMonitorBuilder` | TC-BPF-001 |
| `build_buybacks` | the 回购 rows | progs, before, items, restricted: DataFrame -> DataFrame | — | `portfolio.BuybackMonitorBuilder` | TC-BPF-002 |
| `build_increases` | the 增持 rows | items, trades: DataFrame, as_of, window_start: str -> DataFrame | — | `portfolio.BuybackMonitorBuilder` | TC-BPF-003 |

### `MarginPanelBuilder` — `quant_cn.portfolio.margin_panel_builder` (L5)
- **Purpose:** One 融资融券 document per stock with margin data on the last session: 130 sessions of financing balance / buy / repay, short balance and sales; balances as % of float cap; 20-day changes; short balance vs its max; FIFO forced-liquidation ladder (MarginLadderEstimator) with debt forced at 10–40% falls and first liquidation price at 100% and 80% initial margin.
- **Base:** none. **Depends on (injected):** LakeQuery, MarginLadderEstimator, start: str.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/portfolio/test_margin_panel_builder.py` (TC-MPB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | documents by code | as_of: str, codes -> dict | LakeError | `write` | TC-MPB-001..002 |
| `build_document` | one stock's document | code, stock, ladder -> dict | — | `build` | TC-MPB-001 |
| `write` | write margin/<code>.json | out_dir: Path, as_of: str -> int | LakeError | `cli.ReportCommands` | TC-MPB-003 |

### `WatchlistBuilder` — `quant_cn.portfolio.watchlist_builder` (L5)
- **Purpose:** Join the user's buy targets (`Config.watchlist`) with the latest unadjusted close, daily_basic valuation, 52-week range, weekly closes and the report_rc consensus; compute gap to the buy price, status (in / near / far) and PE and dividend yield at the buy price; write `watchlist.json` for the chain app (plan 15 ph7, D-120). ETF entries (code in fund_basic) are priced from fund_daily and carry `kind: etf` with valuation fields None (ph7p).
- **Base:** none. **Depends on (injected):** `Config`, `LakeQuery`, `DateCodec`.
- **Used by:** `cli.ResearchCommands` (`watchlist` command).
- **Tests:** `tests/portfolio/test_watchlist_builder.py` (TC-WB-001..011).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the watchlist document as of the latest day in curated.daily | () -> dict {as_of, near_pct, entries, missing} | LakeError | `write` | TC-WB-001..007, 009..011 |
| `write` | build and write `watchlist.json` into the app data dir | out_dir: Path -> Path | LakeError | `cli.ResearchCommands._run_watchlist` | TC-WB-008 |
| `compute_status` | classify a price against the top of its buy range | price, buy_high, near_pct -> "in" / "near" / "far" | — | `build` | TC-WB-002 |

### `EtfFlowCalculator` — `quant_cn.portfolio.etf_flow_calculator` (L5)
- **Purpose:** Pick the ETFs tracking each configured index 100% (no feeder / enhanced) and compute per ETF and day: AUM (fd_share x close), net flow = AUM_t - AUM_{t-1} x g_t / g_{t-1} on real share rows (g = cumulative close / pre_close, so splits and missing days give no false flow), position at today's price = AUM x g_last / g of the index's reference ETF (plan 15 ph7b, D-126).
- **Base:** none. **Depends on (injected):** `EtfProxySettings`.
- **Used by:** `portfolio.EtfProxyBuilder`, `portfolio.EtfStyleHeat`, `portfolio.SmallCapWatchBuilder` (broad-ETF flow rows), `cli.ResearchCommands` and `cli.ReportCommands` (wiring).
- **Tests:** `tests/portfolio/test_etf_flow_calculator.py` (TC-EFC-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_members` | members of each configured index, tagged core or not | funds: DataFrame (ts_code, name, benchmark) -> DataFrame (ts_code, index, is_core) | — | `portfolio.EtfProxyBuilder.build` | TC-EFC-005 |
| `compute_daily` | daily AUM, net flow and position at today's price per member ETF | prices, shares, members: DataFrame -> DataFrame (ts_code, index, is_core, trade_date, aum, flow, position; 亿元) | — | `portfolio.EtfProxyBuilder.build`, `portfolio.SmallCapWatchBuilder.build` | TC-EFC-001..004 |

### `SectorMetricReader` — `quant_cn.portfolio.sector_metric_reader` (L5)
- **Purpose:** Sector-monitor lines (LINE_COLUMNS label / period / value) from the lake (plan 31 ph4, D-168): 70-city tier averages of MoM − 100 (%), quarterly contract liabilities, single-quarter impairment (asset + credit, positive = charge), revenue and selling ratio, cash DPS by fiscal year, daily winner rate, wide closes (adjusted companies plus the Shenwan index) and game approvals per month (all and per company). Missing views give empty frames.
- **Base:** none. **Depends on (injected):** SectorMonitorSettings, LakeQuery, GraphStore.
- **Used by:** `portfolio.SectorMonitorBuilder`, `portfolio.DeveloperSalesReader` (get_recent), `cli.ReportCommands`.
- **Tests:** `tests/portfolio/test_sector_metric_reader.py` (TC-SMR-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire settings, query, graph store | SectorMonitorSettings, LakeQuery, GraphStore -> None | — | callers of the class | — |
| `read_house_prices` | tier averages of the 70-city MoM change | str -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-SMR-001 |
| `read_quarterly` | one quarterly statement metric per company | dict[str, str], str -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-SMR-003 |
| `read_dividends` | cash DPS by fiscal year | dict[str, str] -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-SMR-002 |
| `read_winner_rate` | daily 获利盘 | dict[str, str] -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-SMR-002 |
| `read_closes` | wide closes of companies and index | list[str], str -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-SMR-002 |
| `read_game_approvals` | approvals per month, all and per company | dict[str, str] -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-SMR-003 |
| `read_house_breadth` | 70-city count with mom < 100 per month, 新房 / 二手 (plan 33) | — -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-SMR-004 |
| `get_recent` | (static) rows of the last N periods | DataFrame, int -> DataFrame | — | `portfolio.DeveloperSalesReader` | see class |

### `DeveloperSalesReader` — `quant_cn.portfolio.developer_sales_reader` (L5)
- **Purpose:** Developers' monthly contracted sales (亿元, single-month items, latest filing wins) and 12-month land intensity (all parcels of a brief, larger of total / equity price, counted in the month the brief reports) from the operating_data label set (销售简报, D-168).
- **Base:** none. **Depends on (injected):** LabelStore, int (history months).
- **Used by:** `portfolio.SectorMonitorBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/portfolio/test_developer_sales_reader.py` (TC-DEV-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | label store and history length | LabelStore, int -> None | — | callers of the class | — |
| `read_sales` | monthly contracted sales per company | dict[str, str] -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-DEV-001, TC-DEV-003 |
| `read_land_intensity` | trailing 12-month land / sales (%) | dict[str, str] -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-DEV-002 |
| `read_sales_yoy` | rolling 3-month sales yoy (%) (plan 33) | dict[str, str] -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-DEV-004 |
| `read_ytd_yoy` | YTD sales yoy at each company's latest month; stale companies dropped | dict[str, str] -> DataFrame | — | `portfolio.SectorMonitorBuilder` | TC-DEV-004 |

### `SectorEarningsSignalBuilder` — `quant_cn.portfolio.sector_earnings_signal_builder` (L5)
- **Purpose:** 财报季信号 (plan 35, D-172). Events mapped to the SW L2 sector at the quarter end; per sector and quarter: n (events with a decile), expected = max(n, previous quarter), share; n_top / pre / react of SUE deciles ≥ 8; sig_date = day 0 of the int(0.8 × (expected − 1)) + 1-th event; back = sector-index excess vs the mean L2 index over 120 sessions before sig_date (or as_of); hchg = median holder-count change; status firing (share ≥ 0.8, n_top ≥ 5, pre ≥ 15, react ≤ 1) / provisional / none; fwd 60 / 120 after firings; current season, history, firings, record (rally vs all), new_flags.
- **Base:** none. **Depends on (injected):** SectorEarningsSignalSettings, EarningsEventBuilder, LakeQuery.
- **Used by:** `cli.AppServiceBuilder` (the `sector-earnings-signal` command writes through it).
- **Tests:** `tests/portfolio/test_sector_earnings_signal_builder.py` (TC-SEB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the signal document | previous: dict \| None, as_of: str -> dict | LakeError | `write` | TC-SEB-001..002 |
| `write` | build against the previous file and write sector_earnings_signal.json | out_dir: Path, as_of: str -> Path | LakeError | `cli.ResearchCommands` | TC-SEB-003 |

### `SectorMonitorBuilder` — `quant_cn.portfolio.sector_monitor_builder` (L5)
- **Purpose:** sector_monitor.json for #sector-monitor (plan 31 ph4): per configured sector one chart per metric (lines of points), the realised-vol chart (index and companies, first vol window, history_sessions), and a table (index row, then companies) with each line's latest value, vol per window with trailing percentile, and RetailGauge (ChipStructureReader).
- **Base:** none. **Depends on (injected):** SectorMonitorSettings, SectorMetricReader, DeveloperSalesReader, RealizedVolCalculator, ChipStructureReader, AppRankReader, MarketSignalReader. Plan 33 metrics: sales_yoy, house_price_breadth, valuation, revision, surveys; charts carry in_table / extra; stale company points left out of the table.
- **Used by:** `cli.AppServiceBuilder` (`build_sector_monitor`).
- **Tests:** `tests/portfolio/test_sector_monitor_builder.py` (TC-SMB-001..005). Sectors with the app_rank metric get an inverted rank chart and a `rankings` block.

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | SectorMonitorSettings, SectorMetricReader, DeveloperSalesReader, RealizedVolCalculator, ChipStructureReader, AppRankReader, MarketSignalReader -> None | — | callers of the class | — |
| `build` | the whole document | — -> dict | `LakeError` | as class | TC-SMB-001, TC-SMB-002, TC-SMB-004, TC-SMB-005 |
| `write` | build and write sector_monitor.json | Path -> Path | `LakeError` | `cli.ReportCommands` | TC-SMB-003 |

### `MarketSignalReader` — `quant_cn.portfolio.market_signal_reader` (L5)
- **Purpose:** market-side signals of a monitored sector (plan 33, D-170): valuation percentile (trailing val_window sessions, values <= 0 dropped) and latest level for the companies (daily_basic pb / pe_ttm) and the index (sw_daily pb / pe); FY1 median net-profit forecast revision between two revision_days windows of the same FY1 (report_rc); survey days per month and in the trailing survey_days (stk_surv).
- **Base:** none. **Depends on (injected):** SectorMonitorSettings, LakeQuery, RealizedVolCalculator (percentile window), DateCodec.
- **Used by:** `portfolio.SectorMonitorBuilder`, `cli.AppServiceBuilder`.
- **Tests:** `tests/portfolio/test_market_signal_reader.py` (TC-MKS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire settings, query, percentile calculator, codec | SectorMonitorSettings, LakeQuery, RealizedVolCalculator, DateCodec -> None | — | callers of the class | — |
| `read_valuation` | percentile lines and latest levels | dict[str, str], (str, str), str, str -> (DataFrame, DataFrame) | `LakeError` | `portfolio.SectorMonitorBuilder` | TC-MKS-001 |
| `read_revisions` | monthly FY1 forecast revision (%) | dict[str, str], str -> DataFrame | `LakeError` | `portfolio.SectorMonitorBuilder` | TC-MKS-002 |
| `read_surveys` | survey days per month and in the trailing window | dict[str, str], str -> (DataFrame, DataFrame) | `LakeError` | `portfolio.SectorMonitorBuilder` | TC-MKS-003 |

### `AppRankReader` — `quant_cn.portfolio.app_rank_reader` (L5)
- **Purpose:** App Store game charts (curated.app_store_charts) per company through AppPublisherSettings (plan 19 ph2, D-137 update 1): best home grossing rank per company and capture date (LINE_COLUMNS); the leaderboard of the latest capture (companies' games with home grossing rank, previous rank, home free rank, best overseas grossing rank and market, overseas markets; home top `app_top` with companies).
- **Base:** none. **Depends on (injected):** SectorMonitorSettings, AppPublisherSettings, LakeQuery, DateCodec. `read_rankings` also returns `new` (games released within new_game_days, any publisher; plan 33).
- **Used by:** `portfolio.SectorMonitorBuilder`, `cli.AppServiceBuilder`.
- **Tests:** `tests/portfolio/test_app_rank_reader.py` (TC-ARR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire settings, publisher map, query, codec | SectorMonitorSettings, AppPublisherSettings, LakeQuery, DateCodec -> None | — | callers of the class | — |
| `read_rank_lines` | best home grossing rank per company and date | dict[str, str] -> DataFrame (LINE_COLUMNS) | `LakeError` | `portfolio.SectorMonitorBuilder` | TC-ARR-001 |
| `read_rankings` | leaderboard block of the latest capture (names plus every A-share company of the map) and new games | dict[str, str] -> dict | `LakeError` | `portfolio.SectorMonitorBuilder` | TC-ARR-002, TC-ARR-003 |

### `RealizedVolCalculator` — `quant_cn.calculation.realized_vol_calculator` (L4)
- **Purpose:** Annualised realised vol of close-price columns: rolling sample std of daily log returns over `window` × √252 × 100 (%). Trailing percentile of a series: share of the last `pct_window` non-missing values at or below the latest, from `pct_min_obs` on. Extracted from SmallCapWatchBuilder (plan 30) for the sector monitor (plan 31 ph4).
- **Base:** none. **Depends on (injected):** int, int (pct_window, pct_min_obs).
- **Used by:** `portfolio.SmallCapWatchBuilder`, `portfolio.SectorMonitorBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/calculation/test_realized_vol_calculator.py` (TC-RVC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | percentile window and minimum observations | int, int -> None | — | callers of the class | — |
| `compute_vol` | rolling annualised realised vol of every column | DataFrame, int -> DataFrame | — | as class | TC-RVC-001 |
| `compute_rank_pct` | trailing percentile of each value | Series -> Series | — | as class | TC-RVC-002 |

### `SmallCapWatchBuilder` — `quant_cn.portfolio.small_cap_watch_builder` (L5)
- **Purpose:** The daily 小盘观察 document (plan 30). Rows:
  - limit-down count (close ≤ stk_limit.down_limit > 0);
  - share of stocks at a `low_window` low and above their `ma_window` average (close_adj from derived.prices_adj, full windows only);
  - 中证1000 close vs each user level, and its drawdown from the year high;
  - realised vol (sample std × √252 × 100) of 中证1000 and 科创50 with percentile;
  - the 1000−300 gap with percentile and its exit line;
  - broad-ETF net flow (1 day, `flow_days`, own rows) via EtfFlowCalculator;
  - market financing balance (Σ curated.margin over exchanges; a day missing an exchange is dropped): drawdown from the `margin_high_days` high, `margin_turn_days` / `margin_ma_days` change, `margin_ma_days` mean, share of float cap (daily_basic) and its percentile (ph4, 2026-11-18).

  Each row is on / near / off / info. `triggered` and `new_triggered` (vs the previous document); `missing` lists keys without data; chart history. Percentile = share of the last `pct_window` values at or below the latest.
- **Base:** none. **Depends on (injected):** `SmallCapWatchSettings`, `LakeQuery`, `EtfFlowCalculator`, `SmallCapWatchRows`, `RealizedVolCalculator` (vol and percentiles, plan 31).
- **Used by:** `cli.ReportCommands` (`smallcap-watch`).
- **Tests:** `tests/portfolio/test_small_cap_watch_builder.py` (TC-SCW-001..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the watch document as of the last curated.daily session | previous: dict \| None -> dict (as_of, rows, history, triggered, new_triggered, missing) | LakeError | `write` | TC-SCW-001..007, 009, 010 |
| `write` | build against the previous file and write smallcap_watch.json | out_dir: Path -> Path | LakeError | `cli.ReportCommands._run_smallcap_watch` | TC-SCW-008 |

### `SmallCapWatchRows` — `quant_cn.portfolio.small_cap_watch_rows` (L5)
- **Purpose:** Turn the watch's daily frames (market panic, index vols, ETF flows) into display rows with a state against each trigger, and into the chart history. States:
  - count / share rows: near at `near_share` of the trigger;
  - percentile rows: near within `near_pct` points below the trigger;
  - level rows: on at or below the level, near within `near_level` above it;
  - info: rows without a trigger;
  - 杠杆 (ph4): 融资余额, 融资余额 / 流通市值 with percentile (info), 企稳 on when the drawdown is at or below `margin_dd_trigger` and the `margin_turn_days` change is ≥ 0.

  Rows: panic, leverage, levels and drawdown, vols and gap with exit line, ETF flows (plan 30).
- **Base:** none. **Depends on (injected):** `SmallCapWatchSettings`.
- **Used by:** `portfolio.SmallCapWatchBuilder`, `cli.ReportCommands` (wiring).
- **Tests:** `tests/portfolio/test_small_cap_watch_rows.py` (TC-SCR-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | all rows in display order and keys without data | market, vols, flows: DataFrame -> (list[dict], list[str]) | — | `portfolio.SmallCapWatchBuilder.build` | TC-SCR-001..004, 006 |
| `build_history` | chart rows from a start date | market, vols: DataFrame, start: str -> list[dict] | — | `portfolio.SmallCapWatchBuilder.build` | TC-SCR-005 |

### `HoldingsRiskBuilder` — `quant_cn.portfolio.holdings_risk_builder` (L5)
- **Purpose:** Value the PositionsBook at curated.daily closes of the last risk-model session on or before a date; weights over stocks + cash; RiskDecomposer against the benchmark's latest index_weight (tracking error); exposures with Shenwan L1 labels and shares of risk; per-stock own vol and Euler share of variance and model correlations from `RiskSnapshot.compute_stock_cov`; each stock's style exposures and Shenwan L1 industry (`stock_exposures`); codes without a close or forecast listed in `missing`. Writes `holdings_risk.json` and hands the session to HoldingsHistoryWriter (plan 15 ph7d, D-132).
- **Base:** none. **Depends on (injected):** `PositionsBook`, `LakeQuery`, `BaseRiskModel`, `RiskDecomposer`, `HoldingsHistoryWriter`; benchmark index_code; optional `PositionReviewer` (ph7f `reviews`).
- **Used by:** `cli.AppServiceBuilder` (wired for the `holdings-risk` command).
- **Tests:** `tests/portfolio/test_holdings_risk_builder.py` (TC-HRB-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the holdings risk document at the last risk session on or before trade_date | trade_date: str -> dict | LakeError | `write` | TC-HRB-001, 002, 004 |
| `write` | build, write `holdings_risk.json`, store the session in the lake | out_dir: Path, trade_date: str -> Path | LakeError | `cli.ResearchCommands._run_holdings_risk` | TC-HRB-003, 004 |
| `_build_risk` (private, > 20 lines) | decomposition rows into annualised risk and factor rows | snap, weights, session -> dict | — | `build` | TC-HRB-001 |

### `HoldingsHistoryWriter` — `quant_cn.portfolio.holdings_history_writer` (L5)
- **Purpose:** Replace one session's rows in derived/holdings_positions (positions + CASH row) and derived/holdings_risk (risk components, `x:` exposures, `c:` shares of risk), one year file each, so the book's history accumulates in the lake outside git (plan 15 ph7d, D-132).
- **Base:** none. **Depends on (injected):** `LakeQuery`, `ParquetWriter`.
- **Used by:** `portfolio.HoldingsRiskBuilder`, `cli.AppServiceBuilder`.
- **Tests:** `tests/portfolio/test_holdings_history_writer.py` (TC-HHW-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `write` | replace the session in both year files | doc: dict -> list[Path] | LakeError | `portfolio.HoldingsRiskBuilder.write` | TC-HHW-001 |

### `NotifyRecipient` — `quant_cn.core.message_sender` (L1)
- **Purpose:** One person who gets phone alerts: name and iMessage handle.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.NotifySettings`.
- **Tests:** `tests/core/test_message_sender.py` (TC-NS-001).

### `NotifySettings` — `quant_cn.core.message_sender` (L1)
- **Purpose:** Who gets phone alerts and which: recipients (unique names), triggers in TRIGGERS (volatility, watchlist, futures, macro), max alert lines per message; from git-ignored config/local.notify.yaml (template config/notify.example.yaml; missing file = no recipients).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/core/test_message_sender.py` (TC-NS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read config/local.notify.yaml (or another file under the repo) | repo_root: Path, file: Path -> NotifySettings | ConfigError | `cli.ReportCommands` | TC-NS-001 |
| `find_recipient` | recipient by name, case-insensitive | name: str -> NotifyRecipient | ConfigError | `cli.ReportCommands` | TC-NS-002 |

### `SentAlertLog` — `quant_cn.core.sent_alert_log` (L1)
- **Purpose:** The JSON list of phone-alert keys already sent and still active (`notify_sent.json` in the app data folder): `list_new` = active keys not yet sent; `write` keeps the active keys sent before or now, so a condition that clears is sent again when it returns.
- **Base:** none. **Depends on (injected):** path: Path.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/core/test_sent_alert_log.py` (TC-SAL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_keys` | keys recorded as sent | — -> set[str] | ConfigError | `list_new`, `write` | TC-SAL-001..002 |
| `list_new` | active keys not yet sent, in order | active: Iterable[str] -> list[str] | ConfigError | `cli.ReportCommands` | TC-SAL-001 |
| `write` | store the active keys that have been sent | active, sent: Iterable[str] -> Path | ConfigError | `cli.ReportCommands` | TC-SAL-001 |

### `MessageSender` — `quant_cn.core.message_sender` (L1)
- **Purpose:** Base of a channel that delivers one short text to one handle.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `core.IMessageSender` (subclass), `cli.ReportCommands` (typed as the base).
- **Tests:** `tests/core/test_message_sender.py` (TC-IMS-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | deliver text, then images, to handle (abstract) | handle: str, text: str, images: Sequence[Path] -> None | DataSourceError | `cli.ReportCommands` | TC-IMS-001 |

### `IMessageSender` — `quant_cn.core.message_sender` (L1)
- **Purpose:** Send an iMessage from this Mac's Messages app: osascript runs a fixed script with the handle and text as argv (never inside the script source), through the iMessage account. Needs Messages signed in and the Automation permission.
- **Base:** MessageSender. **Depends on (injected):** Runner | None (default subprocess.run), timeout_s.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/core/test_message_sender.py` (TC-IMS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | deliver text, then each image, by iMessage | handle: str, text: str, images: Sequence[Path] -> None | DataSourceError | `cli.ReportCommands` | TC-IMS-001..003 |

### `MailSettings` — `quant_cn.core.mail_sender` (L1)
- **Purpose:** Where the morning report goes: host, port (587), sender, recipients and the name of the env variable with the app password (never the password); loaded from git-ignored `config/local.mail.yaml`, empty when missing.
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `core.MailSender`, `cli.ReportCommands`.
- **Tests:** `tests/core/test_mail_sender.py` (TC-MS-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read the settings file | repo_root: Path -> MailSettings | ConfigError | `cli.ReportCommands` | TC-MS-001 |

### `FuturesFamily` — `quant_cn.core.futures_monitor_settings` (L1)
- **Purpose:** One watched futures family ("CU.SHF"), its Chinese name and display group.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.FuturesMonitorSettings`.
- **Tests:** `tests/core/test_futures_monitor_settings.py` (TC-FMS-001).

### `FuturesSpreadLeg` — `quant_cn.core.futures_monitor_settings` (L1)
- **Purpose:** One spread leg: family and coefficient on its dominant price.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.FuturesSpread`.
- **Tests:** `tests/core/test_futures_monitor_settings.py` (TC-FMS-001).

### `FuturesSpread` — `quant_cn.core.futures_monitor_settings` (L1)
- **Purpose:** A value-chain spread (key, name, unit): sum of coef x leg price, or kind "ratio" leg 1 / leg 2 (exactly two legs); `reversion` + `half_life_d` mark a tested mean-reverting spread (D-156).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.FuturesMonitorSettings`.
- **Tests:** `tests/core/test_futures_monitor_settings.py` (TC-FMS-002..003).

### `IndexFuturesProduct` — `quant_cn.core.futures_monitor_settings` (L1)
- **Purpose:** One CFFEX index-futures product (IF, IH, IC, IM), its name and index ts_code.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.FuturesMonitorSettings`.
- **Tests:** `tests/core/test_futures_monitor_settings.py` (TC-FMS-001).

### `FuturesMonitorSettings` — `quant_cn.core.futures_monitor_settings` (L1)
- **Purpose:** What the futures monitor watches: families, spreads (legs must be families), OI floor of a curve point, percentile flag bounds, OI z bound, reversion_z (D-156); loaded from config/futures_monitor.yaml (missing file = empty).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `calculation.FuturesMonitorBuilder`, `calculation.SpreadReversion`, `cli.ReportCommands`.
- **Tests:** `tests/core/test_futures_monitor_settings.py` (TC-FMS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read config/futures_monitor.yaml | repo_root: Path -> FuturesMonitorSettings | ConfigError | `cli.ReportCommands` | TC-FMS-001 |

### `VolatilityLine` — `quant_cn.core.volatility_monitor_settings` (L1)
- **Purpose:** One monitored volatility index: key, name, group, kind ("cboe" = curated.cboe_vix index_code, "option" = opt_basic opt_code), code, and optional alerts (level, one-day jump fraction, window percentile).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.VolatilityMonitorSettings`, `calculation.VolatilityMonitorBuilder`.
- **Tests:** `tests/core/test_volatility_monitor_settings.py` (TC-VMS-001).

### `VolatilityMonitorSettings` — `quant_cn.core.volatility_monitor_settings` (L1)
- **Purpose:** What the volatility monitor watches: lines (unique keys), percentile window in sessions, min_obs before a percentile alert, TermSelector min_days; loaded from config/volatility_monitor.yaml (missing file = no lines).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `calculation.VolatilityMonitorBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/core/test_volatility_monitor_settings.py` (TC-VMS-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read config/volatility_monitor.yaml | repo_root: Path -> VolatilityMonitorSettings | ConfigError | `cli.ReportCommands` | TC-VMS-001 |

### `RatesFxLine` — `quant_cn.core.rates_fx_monitor_settings` (L1)
- **Purpose:** One monitored rates / FX series: key, name, group, kind (curve: curve + field; us / shibor / fixing: field; fx / equity_ep: code; combo: op diff / mul / div / gap + earlier lines a, b), unit (yield, bp, rate, gap), show, optional alerts. A kind without its parameters is refused.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.RatesFxMonitorSettings`, `calculation.RatesFxSeriesReader`, `calculation.RatesFxMonitorBuilder`.
- **Tests:** `tests/core/test_rates_fx_monitor_settings.py` (TC-RFS-001).

### `RatesFxMonitorSettings` — `quant_cn.core.rates_fx_monitor_settings` (L1)
- **Purpose:** What the rates and RMB monitor shows: lines (unique keys; combos name earlier lines), pct_years, min_obs, history_start, stale_days and the curve snapshot (curve name, fields); loaded from config/rates_fx_monitor.yaml (missing file = no lines).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `calculation.RatesFxSeriesReader`, `calculation.RatesFxMonitorBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/core/test_rates_fx_monitor_settings.py` (TC-RFS-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read config/rates_fx_monitor.yaml | repo_root: Path -> RatesFxMonitorSettings | ConfigError | `cli.ReportCommands` | TC-RFS-001 |

### `SectorEarningsSignalSettings` — `quant_cn.core.sector_earnings_signal_settings` (L1)
- **Purpose:** Windows and thresholds of the earnings events and the sector earnings-season top signal (D-172); loaded from config/sector_earnings_signal.yaml (missing file = defaults).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `calculation.EarningsEventBuilder`, `portfolio.SectorEarningsSignalBuilder`, `cli.AppServiceBuilder`.
- **Tests:** `tests/core/test_sector_earnings_signal_settings.py` (TC-SES-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read config/sector_earnings_signal.yaml | repo_root: Path -> SectorEarningsSignalSettings | ConfigError | `cli.AppServiceBuilder` | TC-SES-001 |

### `MonitoredSecurity` — `quant_cn.core.sector_monitor_settings` (L1)
- **Purpose:** One company or index of a monitored sector: ts_code and Chinese name. Frozen pydantic model, no methods.
- **Used by:** `core.MonitoredSector`.
- **Tests:** `tests/core/test_sector_monitor_settings.py` (TC-SMS-001).

### `MonitoredSector` — `quant_cn.core.sector_monitor_settings` (L1)
- **Purpose:** One sector of the monitor: key, name, Shenwan index, companies (>= 1) and the chart metrics (Metric literal, >= 1). Frozen pydantic model, no methods.
- **Used by:** `core.SectorMonitorSettings`, `portfolio.SectorMonitorBuilder`.
- **Tests:** `tests/core/test_sector_monitor_settings.py` (TC-SMS-002).

### `SectorMonitorSettings` — `quant_cn.core.sector_monitor_settings` (L1)
- **Purpose:** Everything the sector monitor reads from config/sector_monitors.yaml (plan 31 ph4, D-168): 70-city tier lists (others are 三线), realised-vol windows, percentile window and minimum, chart lengths (sessions, quarters, months), App Store home market and top-list length (app_country, app_top), sectors.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `portfolio.SectorMonitorBuilder`, `portfolio.SectorMetricReader`, `cli.ReportCommands`.
- **Tests:** `tests/core/test_sector_monitor_settings.py` (TC-SMS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | (classmethod) read config/sector_monitors.yaml | Path -> SectorMonitorSettings | `ConfigError` | `cli.ReportCommands` | TC-SMS-001, TC-SMS-002 |

### `AppPublisher` — `quant_cn.core.app_publisher_settings` (L1)
- **Purpose:** One App Store seller account: artist_id, account name, company, listed code (None when not listed) (plan 19 ph2).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.AppPublisherSettings`.
- **Tests:** `tests/core/test_app_publisher_settings.py` (TC-APS-001).

### `AppPublisherSettings` — `quant_cn.core.app_publisher_settings` (L1)
- **Purpose:** The App Store publisher map of config/app_publishers.yaml (plan 19 ph2, D-137 update 1); artist ids unique.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `portfolio.AppRankReader`, `cli.AppServiceBuilder`.
- **Tests:** `tests/core/test_app_publisher_settings.py` (TC-APS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | (classmethod) read config/app_publishers.yaml | Path -> AppPublisherSettings | `ConfigError` | `cli.AppServiceBuilder` | TC-APS-001, TC-APS-002 |
| `get_by_artist` | map keyed by artist_id | — -> dict[str, AppPublisher] | — | `portfolio.AppRankReader` | TC-APS-001 |
| `get_a_share` | ts_code -> company of every A-share company (.SH/.SZ/.BJ) | — -> dict[str, str] | — | `portfolio.AppRankReader` | TC-APS-001 |

### `WatchIndex` — `quant_cn.core.small_cap_watch_settings` (L1)
- **Purpose:** One index of the small-cap watch: ts_code (curated.index_daily) and Chinese name.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.SmallCapWatchSettings`.
- **Tests:** `tests/core/test_small_cap_watch_settings.py` (TC-SCS-001).

### `WatchEtf` — `quant_cn.core.small_cap_watch_settings` (L1)
- **Purpose:** One broad ETF in the flow total: code, name, `own_row` (also shown on its own row).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.SmallCapWatchSettings`.
- **Tests:** `tests/core/test_small_cap_watch_settings.py` (TC-SCS-001).

### `SmallCapWatchSettings` — `quant_cn.core.small_cap_watch_settings` (L1)
- **Purpose:** What the 小盘观察 watches: small / large / star indices, user levels, panic limit-down count, low / MA / vol / percentile windows, vol and gap entry / exit percentiles, near rules (share, percentile points, level fraction), history and flow days, broad ETFs (unique codes), 融资余额 企稳 drawdown trigger and turn / high / mean windows (ph4). config/smallcap_watch.yaml, then the git-ignored config/local.smallcap_watch.yaml key by key; the indices are required (no ticker defaults), so no file raises ConfigError (plan 30).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `portfolio.SmallCapWatchBuilder`, `portfolio.SmallCapWatchRows`, `cli.ReportCommands`.
- **Tests:** `tests/core/test_small_cap_watch_settings.py` (TC-SCS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read the repo file, then the local override | repo_root: Path -> SmallCapWatchSettings | ConfigError | `cli.ReportCommands` | TC-SCS-001..003 |

### `MailContent` — `quant_cn.core.mail_sender` (L1)
- **Purpose:** One rendered e-mail: subject, HTML body, plain-text alternative.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.MailSender`, `visualization.MonitorReportRenderer`, `visualization.OpportunityReportRenderer`, `visualization.MorningReportBuilder`.
- **Tests:** `tests/core/test_mail_sender.py` (TC-MSN-001).

### `MailSender` — `quant_cn.core.mail_sender` (L1)
- **Purpose:** Multipart (plain + HTML) message; SMTP with STARTTLS and login; the password comes from the environment variable named in the settings, spaces removed, checked before connecting, never logged.
- **Base:** none. **Depends on (injected):** `MailSettings`, env mapping, SMTP factory.
- **Used by:** `visualization.MorningReportBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/core/test_mail_sender.py` (TC-MSN-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_message` | the message as it will be sent | content: MailContent -> EmailMessage | — | `run` | TC-MSN-001 |
| `run` | send one e-mail to every recipient | content: MailContent -> None | ConfigError, SMTPException, OSError | `visualization.MorningReportBuilder.run` | TC-MSN-002..003 |

### `PositionsBook` — `quant_cn.core.positions_book` (L1)
- **Purpose:** The user's holdings as one combined book (cash, positions with shares and cost) from git-ignored `config/local.positions.yaml`; missing file = empty book. Loaded here rather than by `Config` because config.py is at the 600-line limit (§2.6).
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `portfolio.HoldingsRiskBuilder`, `cli.ResearchCommands`, `core.docs.ContractLinter`, `cli.AppServiceBuilder`, `portfolio.PositionReviewer`.
- **Tests:** `tests/portfolio/test_holdings_risk_builder.py` (TC-PB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read the book from the repo root | repo_root: Path -> PositionsBook | ConfigError | `cli.ResearchCommands._run_holdings_risk` | TC-PB-001, 002 |
| `list_codes` | ts_codes in file order | () -> list[str] | — | `_check_codes`, callers | TC-PB-001 |

### `PositionNote` — `quant_cn.core.positions_book` (L1)
- **Purpose:** Why a position is held and what would make the user act: thesis, falsifier, stop (> 0), target (> 0), action, watch, reviewed (YYYYMMDD), conditions (plan 15 ph7f).
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `core.PositionsBook` (`notes`, `closed`), `portfolio.PositionReviewer`.
- **Tests:** `tests/portfolio/test_holdings_risk_builder.py` (TC-PB-003).

### `BookRules` — `quant_cn.core.positions_book` (L1)
- **Purpose:** Weight cap (0, 1] with named exceptions, before-buy checklist, review interval in days (plan 15 ph7f).
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `core.PositionsBook` (`rules`).
- **Tests:** `tests/portfolio/test_holdings_risk_builder.py` (TC-PB-003).

### `Condition` — `quant_cn.core.condition` (L1)
- **Purpose:** One structured condition `<metric> <op> <value>`; METRICS lists the metrics per kind, `series` takes any manual-series id; `manual` is a user flag (plan 15 ph7f).
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `core.WatchlistEntry`, `core.PositionNote`, `portfolio.ConditionEvaluator`.
- **Tests:** `tests/core/test_condition.py` (TC-CND-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `metric_key` | name of the compared value in the metrics frame | () -> str | — | `portfolio.ConditionEvaluator.compute_results` | TC-CND-002 |

### `MarginSignalReader` — `quant_cn.lake.margin_signal_reader` (L2)
- **Purpose:** Margin signals per stock from rows dated before as_of (published after the close): rz_chg_20d, rz_net_20d_pct, rq_pct_float, rq_max_ratio. Research 20261113_margin_signals: contrarian IC −0.03 to −0.06, weaker since 2024.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `portfolio.ConditionEvaluator`, `cli.AppServiceBuilder`.
- **Tests:** `tests/lake/test_margin_signal_reader.py` (TC-MSR-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read` | signals of codes before as_of | codes: list[str], as_of: str -> DataFrame | LakeError | `portfolio.ConditionEvaluator` | TC-MSR-001 |
| `compute` | signals from rows | rows: DataFrame -> DataFrame | — | `read` | TC-MSR-001 |

### `BuybackLedger` — `quant_cn.lake.buyback_ledger` (L2)
- **Purpose:** Buyback programmes from curated.repurchase in announcement order: 预案 opens; 股东大会通过 / 实施 / 完成 / 停止 attach to the newest open programme; executed amount = running max of the cumulative 实施 / 完成 amounts; 完成 / 停止 close; past expiry = expired; an 实施 without an open programme is seeded. Point in time by ann_date.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `lake.ShareholderYieldReader`, `portfolio.BuybackMonitorBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/lake/test_buyback_ledger.py` (TC-BBL-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_rows` | rows announced by as_of | as_of: str, codes: list[str] \| None -> DataFrame | LakeError | `read_programmes`, `read_executed` | — |
| `build_programmes` | programmes as known on as_of | rows: DataFrame, as_of: str -> DataFrame | — | callers | TC-BBL-001..004 |
| `read_programmes` | programmes from the lake | as_of: str, codes -> DataFrame | LakeError | callers | — |
| `compute_executed` | money executed in a window | rows, as_of: str, days: int -> Series | — | `read_executed` | TC-BBL-003 |
| `read_executed` | executed money from the lake | as_of: str, codes, days -> Series | LakeError | `lake.ShareholderYieldReader` | — |

### `ShareholderYieldReader` — `quant_cn.lake.shareholder_yield_reader` (L2)
- **Purpose:** Per stock on a date: dividend yield (dv_ttm / 100), buyback yield (12-month executed buybacks from BuybackLedger ÷ total market cap) and their sum; for conditions also the largest live buyback plan as % of market cap and the share executed (plans ≥ 2% predict +2% over 60 days, research 20261113_buyback_yield).
- **Base:** none. **Depends on (injected):** LakeQuery, BuybackLedger.
- **Used by:** `portfolio.ConditionEvaluator`, `cli.AppServiceBuilder`.
- **Tests:** `tests/lake/test_shareholder_yield_reader.py` (TC-SYR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read` | yields on the last session by as_of | as_of: str, codes -> DataFrame | LakeError | `read_metrics`, research | — |
| `compute` | combine dividend and buyback | basic: DataFrame, executed: Series -> DataFrame | — | `read` | TC-SYR-001 |
| `read_metrics` | condition metrics of codes | codes: list[str], as_of: str -> DataFrame | LakeError | `portfolio.ConditionEvaluator` | — |
| `compute_plans` | largest live plan and its done share | programmes: DataFrame, total_mv: Series -> DataFrame | — | `read_metrics` | TC-SYR-002 |

### `ChipStructureReader` — `quant_cn.lake.chip_structure_reader` (L2)
- **Purpose:** 筹码结构 signals as known on a date (rows announced or traded on or before it): holder count change, top-10 institutional change (pp), northbound change between the last two disclosures (pp; quarterly since 2024), margin 60-day change, large / small order weekly flows over 4 ISO weeks (亿), unlocks in 6 months and insider sales in 6 months (%), latest RetailGauge reading from derived.retail_gauge (≤ 45 days old: pct, expected change, avoid / avoid_strong / leaving flags, D-167 streaks; plan 21 ph5); winner rate and cost_lo_gap / cost_hi_gap (last cyq_perf session's close / cost_15pct, cost_85pct - 1; NaN without the dataset) (plan 21 ph1, ph4).
- **Base:** none. **Depends on (injected):** `LakeQuery`, gauge_max_age_days: int.
- **Used by:** `portfolio.ConditionEvaluator`, `cli.AppServiceBuilder`, `portfolio.SectorMonitorBuilder`, `portfolio.OpportunityScreen`, `cli.GaugeCommands`.
- **Tests:** `tests/lake/test_chip_structure_reader.py` (TC-CSR-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read` | all chip signals for codes on as_of | codes: list[str], as_of: str -> DataFrame | LakeError | `portfolio.ConditionEvaluator.read_metrics`, `portfolio.OpportunityScreen.build` | TC-CSR-001..005 |

### `FundamentalSignalReader` — `quant_cn.lake.fundamental_signal_reader` (L2)
- **Purpose:** From statement versions known on a date (D-092): latest reported quarter, its single-quarter GM and deducted-profit YoY (|base|), TTM OCF / TTM net profit; latest published manual-series values (plan 20) keyed `series:<id>`.
- **Base:** none. **Depends on (injected):** `StatementVersionReader`, `LakeQuery`.
- **Used by:** `portfolio.ConditionEvaluator`, `cli.AppServiceBuilder`.
- **Tests:** `tests/lake/test_fundamental_signal_reader.py` (TC-FSR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read` | statement signals for codes on as_of | codes: list[str], as_of: str -> DataFrame | LakeError | `portfolio.ConditionEvaluator.read_metrics` | TC-FSR-001..003 |
| `read_series` | latest published value per series | ids: list[str], as_of: str -> dict[str, float] | LakeError | `portfolio.ConditionEvaluator.read_metrics` | TC-FSR-003 |

### `ConditionResult` — `quant_cn.portfolio.condition_evaluator` (L5)
- **Purpose:** One condition with its threshold, the value found (None = unknown) and its state.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `portfolio.ConditionEvaluator`.
- **Tests:** `tests/portfolio/test_condition_evaluator.py` (TC-CE-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `to_record` | JSON-ready form | () -> dict | — | `portfolio.PositionReviewer`, `portfolio.WatchlistBuilder` | TC-CE-001 |

### `ConditionEvaluator` — `quant_cn.portfolio.condition_evaluator` (L5)
- **Purpose:** Gather the metrics conditions refer to and evaluate them to met / unmet / unknown; entry status buy (price met and k of n conditions met, all by default) / near (price met) / wait. Unknown is never met (plan 15 ph7f).
- **Base:** none. **Depends on (injected):** `ChipStructureReader`, `FundamentalSignalReader`.
- **Used by:** `portfolio.PositionReviewer`, `portfolio.WatchlistBuilder`, `cli.AppServiceBuilder`.
- **Tests:** `tests/portfolio/test_condition_evaluator.py` (TC-CE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_metrics` | one metrics row per code as known on as_of | closes: Mapping[str, float], as_of: str, series: Sequence[str] -> DataFrame | LakeError | `portfolio.PositionReviewer.build`, `portfolio.WatchlistBuilder.build` | TC-CE-003 |
| `compute_results` | evaluate conditions against one code's metrics | conditions: Sequence[Condition], metrics: Mapping -> list[ConditionResult] | — | same | TC-CE-001 |
| `compute_status` | buy / near / wait from price check and results | results, price_met: bool, needed: int \| None -> str | — | `portfolio.WatchlistBuilder` | TC-CE-002 |

### `PositionReviewer` — `quant_cn.portfolio.position_reviewer` (L5)
- **Purpose:** For every held stock: note, chip and statement row, latest statement period, condition results and flags — close ≤ stop, close ≥ target, weight above the cap (unless excepted), note never reviewed or older than the interval, missing note (plan 15 ph7f).
- **Base:** none. **Depends on (injected):** `PositionsBook`, `ConditionEvaluator`.
- **Used by:** `portfolio.HoldingsRiskBuilder`, `cli.AppServiceBuilder`.
- **Tests:** `tests/portfolio/test_position_reviewer.py` (TC-PRV-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | one review per held stock | held: DataFrame[code, close, weight], as_of: str -> dict[str, dict] | LakeError | `portfolio.HoldingsRiskBuilder.build` | TC-PRV-001..003 |

### `ReportCommands` — `quant_cn.report_commands` (L8)
- **Purpose:** CLI `morning-report [--data DIR] [--dry-run --out DIR] [--today YYYYMMDD]`: last trading session before today from the lake calendar (read-only catalog), mail settings and `os.environ`, then MorningReportBuilder; prints one line per e-mail. Separate from cli.py, which is at its size limit.
- **Base:** none. **Depends on (injected):** `Console`.
- **Used by:** `cli.QuantCnCli` (parser and dispatch).
- **Tests:** `tests/test_report_commands.py` (TC-RPC-001..012; TC-RPC-012 `smallcap-watch`, plan 30).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_parser` | add the subcommand | sub -> None | — | `cli.QuantCnCli` | TC-RPC-001 |

### `AppServiceBuilder` — `quant_cn.app_service_builder` (L8)
- **Purpose:** Composition root for the app's portfolio documents: the condition evaluator (RetailGauge file under the lake root until plan 21), the watchlist builder with it, the holdings-risk builder with history writer and position reviewer. Separate from `ServiceBuilder`, which is at its class size limit (plan 15 ph7f).
- **Base:** none. **Depends on (injected):** none (builds from Config and LakeCatalog).
- **Used by:** `cli.ResearchCommands` (`watchlist`, `holdings-risk`, `sector-monitor`, `sector-earnings-signal`).
- **Tests:** `tests/test_app_service_builder.py` (TC-ASB-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_evaluator` | condition evaluator over the lake | config, catalog -> ConditionEvaluator | — | `build_watchlist`, `build_holdings_risk` | TC-ASB-001 |
| `build_watchlist` | watchlist builder with evaluator | config, catalog -> WatchlistBuilder | — | `cli.ResearchCommands._run_watchlist` | TC-ASB-001 |
| `build_holdings_risk` | holdings-risk builder with reviewer | config, catalog, book, benchmark -> HoldingsRiskBuilder | ConfigError | `cli.ResearchCommands._run_holdings_risk` | TC-ASB-001 |
| `build_sector_monitor` | Sector monitor builder (plan 31 ph4) over the lake of `catalog`. | config, catalog -> SectorMonitorBuilder | `ConfigError` | `cli.ResearchCommands._run_sector_monitor` | TC-ASB-003 |
| `build_sector_earnings_signal` | 财报季信号 builder (plan 35, D-172) over the lake of `catalog`. | config, catalog -> SectorEarningsSignalBuilder | `ConfigError` | `cli.ResearchCommands._run_sector_earnings_signal` | TC-ASB-004 |

### `Position` — `quant_cn.core.positions_book` (L1)
- **Purpose:** One holding: code, name, shares (> 0), cost per share (diluted 摊薄成本; <= 0 allowed once paid back, D-166); broker snapshot fields ignored.
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `core.PositionsBook`.
- **Tests:** `tests/portfolio/test_holdings_risk_builder.py` (TC-PB-001).

### `EtfStyleHeat` — `quant_cn.portfolio.etf_style_heat` (L5)
- **Purpose:** Style ETF crowding (plan 15 ph7g): members per style via its own EtfFlowCalculator (indices = styles, core empty), then per style the `style_window`-day net flow, its share of today's AUM and the z-score against the previous `style_z_days` sessions (today excluded). Status 过热 at z ≥ style_hot_z, kept until z ≤ 0 (降温), else 正常.
- **Base:** none. **Depends on (injected):** EtfProxySettings.
- **Used by:** `portfolio.EtfProxyBuilder`.
- **Tests:** `tests/portfolio/test_etf_style_heat.py` (TC-ESH-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_members` | the ETFs of each style | funds: DataFrame -> DataFrame | — | `portfolio.EtfProxyBuilder` | TC-ESH-001 |
| `build` | one summary per style | prices, shares, members: DataFrame -> list[dict] | — | `portfolio.EtfProxyBuilder` | TC-ESH-002..003 |

### `EtfCtaGroup` — `quant_cn.core.etf_cta_settings` (L1)
- **Purpose:** One risk group (股票, 黄金, 商品) of the ETF CTA book: ETFs with inner capital weights; weights renormalise over the ETFs that have a price.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.EtfCtaSettings`.
- **Tests:** `tests/core/test_etf_cta_settings.py` (TC-ECS-001).

### `EtfCtaPremium` — `quant_cn.core.etf_cta_settings` (L1)
- **Purpose:** Premium guard: guarded codes, buy or add only below buy_below (3%), 很高 at high (10%), alternative shown at switch (20%).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.EtfCtaSettings`.
- **Tests:** `tests/core/test_etf_cta_settings.py` (TC-ECS-002).

### `EtfCtaSettings` — `quant_cn.core.etf_cta_settings` (L1)
- **Purpose:** The ETF CTA book (D-160 update): groups at equal risk scaled to risk_share (0.6), bonds (5y + 30y) at bond_share (0.4) x the bond switch, timed A股 ETFs, trend / switch windows, vol window, band (0.02), cost (15 bp), history_start, paper_start, group_step, names, premium.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `portfolio.EtfCtaBook`, `portfolio.EtfCtaWeights`, `cli.ReportCommands`, `core.EtfCtaViews`, `portfolio.EtfCtaViewTilt`.
- **Tests:** `tests/core/test_etf_cta_settings.py` (TC-ECS-001..004). Fields `subsets` (named view sets) and `views_file` (D-163).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_codes` | every ETF the book can hold, cash last | — -> list[str] | — | `portfolio.EtfCtaBook`, `portfolio.EtfCtaWeights`, `cli.ReportCommands` | TC-ECS-001 |
| `list_members` | the ETFs a view name stands for (group, 债券, subset, code) | name: str -> list[str] | ConfigError | `core.EtfCtaViews`, `portfolio.EtfCtaViewTilt` | TC-ECS-004 |
| `load` | read config/etf_cta.yaml (defaults when missing) | repo_root: Path -> EtfCtaSettings | ConfigError | `cli.ReportCommands` | TC-ECS-001 |

### `EtfCtaWhen` — `quant_cn.core.etf_cta_views` (L1)
- **Purpose:** Price condition of a view: exactly one of below / above for one ETF close; the view waits until a decision-date close meets it, then stays live until expiry.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.EtfCtaView`.
- **Tests:** `tests/core/test_etf_cta_views.py` (TC-ECV-002).

### `EtfCtaView` — `quant_cn.core.etf_cta_views` (L1)
- **Purpose:** One view (D-163): kind scale (target x multiplier 0.5–2) or relative (move points ≤ 0.05 from under to over); reason, start, expires ≤ start + 92 days; optional `when`.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.EtfCtaViews`, `portfolio.EtfCtaViewTilt`.
- **Tests:** `tests/core/test_etf_cta_views.py` (TC-ECV-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_names` | set names the view refers to, plus the condition code | — -> list[str] | — | `core.EtfCtaViews.load` | TC-ECV-001 |

### `EtfCtaViews` — `quant_cn.core.etf_cta_views` (L1)
- **Purpose:** The user's views and optional A股 floor, read from the git-ignored `views_file` of the settings; every name checked with `EtfCtaSettings.list_members`.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `portfolio.EtfCtaViewTilt`, `portfolio.EtfCtaBook`, `cli.ReportCommands`.
- **Tests:** `tests/core/test_etf_cta_views.py` (TC-ECV-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read and check the views file; missing = no views | repo_root: Path, settings: EtfCtaSettings -> EtfCtaViews | ConfigError | `cli.ReportCommands` | TC-ECV-001, TC-ECV-003 |

### `TrendPosition` — `quant_cn.calculation.trend_position` (L4)
- **Purpose:** Plan 24 rule on any price series: signal per window = price above its level n sessions ago; blend = share up; size = min(1, vol_target / annualised vol over vol_window); position = blend x size; vol_target None = blend only (bond switch).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `portfolio.EtfCtaWeights`.
- **Tests:** `tests/calculation/test_trend_position.py` (TC-TP-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_blend` | share of windows up | prices: DataFrame -> DataFrame | — | `portfolio.EtfCtaWeights` | TC-TP-001 |
| `compute_position` | blend x size | prices: DataFrame -> DataFrame | — | `portfolio.EtfCtaWeights` | TC-TP-002..003 |
| `build_summary` | last row: windows, blend, vol, size, position | prices: Series -> dict | — | `portfolio.EtfCtaWeights` | TC-TP-003 |

### `EtfCtaWeights` — `quant_cn.portfolio.etf_cta_weights` (L5)
- **Purpose:** Daily ETF returns -> target weights on the last session of each week: group returns from live ETFs; risk weights ∝ 1 / group vol (vol_window, vol_min_obs) set on the first session of a month; x risk_share; timed ETFs x TrendPosition (0 until known); bonds bond_share x switch (1 until known); the rest in cash.
- **Base:** none. **Depends on (injected):** `EtfCtaSettings`, `TrendPosition` | None (two, built from settings).
- **Used by:** `portfolio.EtfCtaBook`.
- **Tests:** `tests/portfolio/test_etf_cta_weights.py` (TC-ECW-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_targets` | target weights per decision date | returns: DataFrame -> DataFrame | KeyError | `portfolio.EtfCtaBook` | TC-ECW-001..005 |
| `list_decisions` | last session of each week | index: DatetimeIndex -> DatetimeIndex | — | `portfolio.EtfCtaWeights` | TC-ECW-005 |
| `build_summary` | group vols and risk weights, timed positions, bond switch | returns: DataFrame -> dict | KeyError | `portfolio.EtfCtaBook` | TC-ECW-006 |

### `EtfCtaPaperBook` — `quant_cn.portfolio.etf_cta_paper_book` (L5)
- **Purpose:** Paper account from all cash: holdings drift; at each decision a group is traded to target when its total or one ETF is off by band or more; a zero target is always sold; cash absorbs trades and earns its return; cost x traded weight; no-add codes are not bought on their date.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `portfolio.EtfCtaBook`.
- **Tests:** `tests/portfolio/test_etf_cta_paper_book.py` (TC-ECP-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | run the account from start | returns, cash, targets, start, no_add -> dict(nav, weights, trades) | ValueError | `portfolio.EtfCtaBook` | TC-ECP-001..007 |

### `EtfCtaBook` — `quant_cn.portfolio.etf_cta_book` (L5)
- **Purpose:** Read curated fund_daily (returns, ±20% clip) and fund_nav (premium on the latest common date); EtfCtaWeights targets; premium guard (no adds at or above buy_below); paper book from paper_start and back-test from history_start with EtfCtaPaperBook; per ETF target / last target / held / trade / action; groups; flags (group change ≥ group_step, premium); new_flags against the previous document; write `etf_cta.json`.
- **Base:** none. **Depends on (injected):** `EtfCtaSettings`, `LakeQuery`, `DateCodec`, `EtfCtaWeights` | None, `EtfCtaPaperBook` | None, `EtfCtaViews` | None; builds `EtfCtaViewTilt` and `EtfCtaRecord`. The `views` block holds the 含观点 track (D-163).
- **Used by:** `cli.ReportCommands` (`etf-cta` command).
- **Tests:** `tests/portfolio/test_etf_cta_book.py` (TC-ECB-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the document as of the last fund_daily session | previous: dict or None -> dict | LakeError | `portfolio.EtfCtaBook.write` | TC-ECB-001..004, TC-ECB-006 |
| `write` | build against the previous file and overwrite | out_dir: Path -> Path | LakeError | `cli.ReportCommands` | TC-ECB-004..005 |

### `EtfCtaViewTilt` — `quant_cn.portfolio.etf_cta_view_tilt` (L5)
- **Purpose:** The 含观点 targets (D-163): A股 floor; scale views (subset inside a group keeps the group total; combined per-ETF multiplier clipped 0.5–2); relative moves pro rata, capped by the source, skipped into a zero set; total capped at 100%. Views live start..expires, conditions latch.
- **Base:** none. **Depends on (injected):** `EtfCtaSettings`, `DateCodec`.
- **Used by:** `portfolio.EtfCtaBook`.
- **Tests:** `tests/portfolio/test_etf_cta_view_tilt.py` (TC-ECVT-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_targets` | tilted targets | targets, views, closes, full -> DataFrame | ConfigError | `portfolio.EtfCtaBook.build` | TC-ECVT-001..006 |
| `build_summary` | statuses, group effects, view flags for the last date | system, tilted, views, closes -> dict | — | `portfolio.EtfCtaBook.build` | TC-ECVT-007 |

### `EtfCtaRecord` — `quant_cn.portfolio.etf_cta_record` (L5)
- **Purpose:** Track record of a paper NAV: last nav, ann return, vol, Sharpe over cash (a year or more), max drawdown, calendar years, weekly points.
- **Base:** none. **Depends on (injected):** `DateCodec`.
- **Used by:** `portfolio.EtfCtaBook`.
- **Tests:** `tests/portfolio/test_etf_cta_record.py` (TC-ECR-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the record of one NAV | nav, cash: Series -> dict | — | `portfolio.EtfCtaBook.build` | TC-ECR-001 |

### `EtfProxyBuilder` — `quant_cn.portfolio.etf_proxy_builder` (L5)
- **Purpose:** Read fund_basic, fund_share and fund_daily from `start`, run `EtfFlowCalculator`, and summarise core (national-team ETFs) vs other: totals (AUM, position, recent and YTD flow, peak and trough since peak), recent daily flows, weekly flow and position, yearly flow, per-index table with weekly series and rhythm (peak, trough since peak, added since the trough, last `rhythm_weeks` weeks / week / day flows, reference drawdown from this year's high; 2026-11-17), and per index and total the 近3月 window (today's position percentile, low / high over the last `pct_window_days` sessions) plus total `flow_weeks`, with `rhythm_weeks` / `pct_window_days` / `matrix_weeks` echoed for the page (ph7o, 2026-11-18); write `etf_proxy.json` for the chain app (plan 15 ph7b, D-126).
- **Base:** none. **Depends on (injected):** `Config`, `LakeQuery`, `DateCodec`, `EtfFlowCalculator`, `EtfStyleHeat` | None (default built from the settings).
- **Used by:** `cli.ResearchCommands` (`etf-proxy` command).
- **Tests:** `tests/portfolio/test_etf_proxy_builder.py` (TC-EP-001..007). The document gains `styles` (ph7g) and the 近3月 `window` blocks (ph7o).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the proxy document from start to the last share day | () -> dict {as_of, price_as_of, start, n_members, totals, recent, weekly, yearly, indices} | LakeError | `write` | TC-EP-001, 002, 004 |
| `write` | build and write `etf_proxy.json` into the app data dir | out_dir: Path -> Path | LakeError | `cli.ResearchCommands._run_etf_proxy` | TC-EP-003 |
| `_build_summary` (private, > 20 lines) | group daily rows into totals, recent, weekly, yearly and per-index blocks | daily: DataFrame, as_of: str, prices: DataFrame -> dict | — | `build` | TC-EP-001 |
| `_build_rhythm` (private, > 20 lines) | per-index peak / trough, added since the trough, recent flows, reference drawdown, 近3月 window | daily, name, reference, prices, year -> dict | — | `_build_summary` | TC-EP-006, 007 |

### `ReleaseLagChecker` — `quant_cn.lake.release_lag_checker` (L2)
- **Purpose:** For every dataset with `known_on_rule: period_end_lag` and `release_dates` set, measure the observed lag (release date - period end) in that curated release-date dataset and count releases that came later than the rule. A rule earlier than any observed release is look-ahead; D-086 raises it to the observed maximum and `make check` warns if it recurs. The period of a release is the last month end before it, or its own month end when the release falls on/after day 25 (month-end PMI releases).
- **Base:** none. **Depends on (injected):** LakeQuery, Mapping[str, DatasetSpec], str.
- **Used by:** `cli.ResearchCommands`.
- **Tests:** `tests/lake/test_release_lag_checker.py` (TC-RLC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, Mapping[str, DatasetSpec], str -> None | — | callers of the class | — |
| `compute` | One row per checked dataset. | — -> pd.DataFrame | `LakeError` | as class | see class |
| `build_lines` | Human-readable lines of a compute() result. | pd.DataFrame -> list[str] | — | as class | see class |

### `RunLog` — `quant_cn.lake.run_log` (L2)
- **Purpose:** Append run and per-key events to `meta.run_log` (run_id, started_at, finished_at, kind, dataset, key, status, n_rows, duration_ms, message) and echo them to logging.
- **Base:** BaseRunLog. **Depends on (injected):** LakeCatalog, Clock.
- **Used by:** `cli.QuantCnCli`, `cli.ServiceBuilder`, `cli.ResearchCommands`.
- **Tests:** `tests/lake/test_run_log.py` (TC-RL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, Clock -> None | `LakeError` | callers of the class | — |
| `open_run` | Insert the run row (dataset and key NULL, status "running"). | str -> str | `LakeError` | as class | see class |
| `record_event` | Append one key event. | str, str, str, str, int, int, str -> None | `LakeError` | as class | see class |
| `close_run` | Set status, message and finished_at on the run row. | str, str, str -> None | `LakeError` | as class | see class |

### `StatementVersionReader` — `quant_cn.lake.statement_version_reader` (L2)
- **Purpose:** Read every company's statement values as known on one date: per (company, period, field) the version with the latest known_on <= as_of (D-092 versions), or the first version ever announced with its known_on (guidance outcomes, D-124); retired codes mapped to surviving codes (plan 16 ph1, plan 18 ph1).
- **Base:** none. **Depends on (injected):** LakeQuery, TickerAliasMap, DateCodec.
- **Used by:** (none yet; pipeline.DiscoveryStep plan 16 ph6, pipeline.GuidanceStep plan 18 ph6).
- **Tests:** `tests/lake/test_statement_version_reader.py` (TC-SVR-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, TickerAliasMap, DateCodec -> None | — | callers of the class | — |
| `read_versions` | statement values per (company, period, field) known on as_of | Sequence[str], str, str -> pd.DataFrame | `LakeError` | callers | TC-SVR-001..004 |
| `read_first_versions` | first announced value per (company, period, field) with its known_on | Sequence[str], str, str -> pd.DataFrame | `LakeError` | callers (ForecastTracker input) | TC-SVR-005 |

### `TickerAliasMap` — `quant_cn.lake.ticker_alias_map` (L2)
- **Purpose:** Map retired codes to their surviving codes so a company has one history. Tushare keeps a retired code's rows and back-fills the same history under the new code, but some datasets (stk_limit, moneyflow, margin_detail) exist only under the old code before the change. `refresh` builds `derived.ticker_alias`: pairs detected from the data (a code missing from stock_basic whose closes equal a listed code's on >= 20 shared dates, >= 99% equal) plus the config pairs; every candidate keeps its match statistics, and an old code matching more than one listed code is kept but not accepted. `normalize_codes` renames accepted old codes and, where both codes have a row for the same key, keeps the new code's row.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, Sequence[TickerAlias].
- **Used by:** `lake.DerivedViews`, `lake.LakeReader`, `cli.ServiceBuilder`, `lake.StatementVersionReader`.
- **Tests:** `tests/lake/test_ticker_alias_map.py` (TC-TAM-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, Sequence[TickerAlias] -> None | — | callers of the class | — |
| `refresh` | (Re)create `derived.ticker_alias`. | — -> str \| None | `LakeError` | as class | see class |
| `get_pairs` | Accepted old -> new pairs (read once per refresh). | — -> dict[str, str] | `LakeError` | as class | see class |
| `normalize_codes` | Rename accepted old codes to new codes; on a duplicate key the new code's row wins. | pd.DataFrame, Sequence[str] -> pd.DataFrame | `LakeError` | as class | see class |
| `list_codes` | `codes` plus the old codes of any requested new code, so a filter sees both. | Sequence[str] -> list[str] | `LakeError` | as class | see class |

### `TradingCalendar` — `quant_cn.lake.trading_calendar` (L2)
- **Purpose:** Answer trading-day questions (sessions in a range, is_open, next, prev) from the SSE calendar in the lake; loads lazily so it works after trade_cal is fetched in the same run.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `data_loading.DateSweepFetcher.list_keys`, `data_loading.FetcherFactory`, `cli.ServiceBuilder`, `lake.EffectiveDateResolver`, `lake.LakeReader`, `factor.FactorFactory`.
- **Tests:** `tests/lake/test_trading_calendar.py` (TC-TCA-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery -> None | — | callers of the class | — |
| `refresh` | Drop the cached calendar so the next call re-reads trade_cal. | — -> None | — | as class | see class |
| `list_sessions` | Trading days within [start, end]. | str, str -> list[str] | `LakeError` | as class | see class |
| `is_open` | True if `date` is a trading day. | str -> bool | `LakeError` | as class | see class |
| `get_next` | First trading day strictly after `date`. | str -> str | `LakeError` | as class | see class |
| `get_prev` | Last trading day strictly before `date`. | str -> str | `LakeError` | as class | see class |

### `CompactStep` — `quant_cn.pipeline.curate_pipeline` (L6)
- **Purpose:** Adapt Compactor to a pipeline step: one unit per dataset.
- **Base:** BaseStep. **Depends on (injected):** Compactor, Sequence[DatasetSpec].
- **Used by:** `pipeline.CuratePipeline`.
- **Tests:** `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Compactor, Sequence[DatasetSpec] -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | Datasets to compact. | — -> list[str] | — | as class | see class |
| `run` | Rebuild curated partitions for every dataset. | str, ProgressHook \| None -> StepReport | `SchemaError`, `LakeError` | as class | see class |

### `DeriveStep` — `quant_cn.pipeline.curate_pipeline` (L6)
- **Purpose:** Build the derived views and the PIT states view, then record a digest per derived view.
- **Base:** BaseStep. **Depends on (injected):** DerivedViews, PitAligner, LakeQuery, Path.
- **Used by:** `pipeline.CuratePipeline`, `pipeline.FeatureStep`, `cli.ServiceBuilder`, `pipeline.RiskModelStep`.
- **Tests:** `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DerivedViews, PitAligner, LakeQuery, Path -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | One unit: the derived layer. | — -> list[str] | — | as class | see class |
| `run` | Refresh derived views (and PIT states when fundamentals exist), write digests. | str, ProgressHook \| None -> StepReport | `LakeError` | as class | see class |
| `build_digests` | md5 over every row of each view, rows ordered by their text form; equal digests mean byte-identical derived data. | Sequence[str] -> dict[str, str] | `LakeError` | as class | see class |
| `refresh_digests` | Recompute the digests of views built after this step (derived.features) and merge them into meta/manifest/derived_digests.json. | Sequence[str] -> dict[str, str] | `LakeError` | as class | see class |

### `CuratePipeline` — `quant_cn.pipeline.curate_pipeline` (L6)
- **Purpose:** Rebuild everything below raw/: compact every dataset, create derived views and PIT states, regenerate lake indexes, and record digests in meta/manifest/derived_digests.json.
- **Base:** none. **Depends on (injected):** Config, Compactor, DerivedViews, PitAligner, LakeQuery, LakeCatalog, BaseRunner, BaseStep | None, DeriveStep | None, BaseStep | None.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, Compactor, DerivedViews, PitAligner, LakeQuery, LakeCatalog, BaseRunner, BaseStep \| None, DeriveStep \| None, BaseStep \| None -> None | — | callers of the class | — |
| `run` | Compact the datasets (default all), then derive and index. | Sequence[str] \| None -> PipelineReport | `ConfigError`, `SchemaError`, `LakeError` | as class | see class |

### `FetchStep` — `quant_cn.pipeline.download_pipeline` (L6)
- **Purpose:** Adapt one dataset's fetcher to a pipeline step: keys computed in list_units (so the calendar fetched earlier in the run is visible), catalog view refreshed after the run.
- **Base:** BaseStep. **Depends on (injected):** BaseFetcher, LakeCatalog, str, str, bool.
- **Used by:** `pipeline.DownloadPipeline.run`.
- **Tests:** `tests/pipeline/test_download_pipeline.py` (TC-DP-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseFetcher, LakeCatalog, str, str, bool -> None | — | callers of the class | — |
| `name` | The dataset name. | — -> str | — | as class | see class |
| `list_units` | Compute the dataset's keys for the range. | — -> list[str] | `LakeError` | as class | see class |
| `run` | Fetch the prepared keys, then refresh the dataset's catalog views. | str, ProgressHook \| None -> StepReport | `DataSourceError`, `PermissionDeniedError`, `SchemaError`, `LakeError` | as class | see class |

### `DownloadPipeline` — `quant_cn.pipeline.download_pipeline` (L6)
- **Purpose:** Resolve which datasets and date ranges to download, run one FetchStep per dataset through the runner, and regenerate the lake indexes; `dry_run` lists pending keys without calling the API.
- **Base:** none. **Depends on (injected):** Config, FetcherFactory, BaseRunner, LakeCatalog, BaseFetchLog, Clock, DateCodec.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_download_pipeline.py` (TC-DP-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, FetcherFactory, BaseRunner, LakeCatalog, BaseFetchLog, Clock, DateCodec -> None | — | callers of the class | — |
| `run` | Download the requested datasets (default: config.download.order). | Sequence[str] \| None, str \| None, str \| None, bool, bool -> PipelineReport | `ConfigError`, `ValueError`, `DataSourceError` | as class | see class |

### `EvaluationStep` — `quant_cn.pipeline.evaluation_step` (L6)
- **Purpose:** Evaluate every factor in derived.features (FactorEvaluator, one factor at a time to bound memory, forward returns from the open of t+1 on dense prices), apply the campaign-level adjustment once over all factor x horizon tests, and write derived/reports/<campaign>/ ic_series, ic_test and quantiles; the campaign's TrialLog (meta/trials/<campaign>.parquet) is resumed and saved, so re-running the same variants does not inflate N.
- **Base:** BaseStep. **Depends on (injected):** LakeQuery, LakeReader, FactorEvaluator, ParquetWriter, str, Mapping[str, Mapping[str, object]], str.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_evaluation_step.py` (TC-ES-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, LakeReader, FactorEvaluator, ParquetWriter, str, Mapping[str, Mapping[str, object]], str -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | Factors to evaluate. | — -> list[str] | `LakeError` | as class | see class |
| `run` | Evaluate, adjust, write reports and the trial log. | str, ProgressHook \| None -> StepReport | `LakeError`, `SchemaError` | as class | see class |

### `FeatureStep` — `quant_cn.pipeline.feature_step` (L6)
- **Purpose:** Build derived/features, one file per year from the campaign start: the six library factors (FactorFactory, PIT inputs from LakeReader), restricted to universe members, preprocessed (winsorise -> standardise -> neutralise on Shenwan L1 + log market cap, D-093) and the combined "score" (SignalCombiner), as FACTOR_PANEL. Runs inside curate after the derived views; then refreshes derived.features and merges its digest so `make lake-rebuild` proves the features byte-identical.
- **Base:** BaseStep. **Depends on (injected):** LakeQuery, LakeReader, FactorFactory, ExposureReader, FactorPreprocessor, SignalCombiner, ParquetWriter, DerivedViews, DeriveStep, str.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_feature_step.py` (TC-FS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, LakeReader, FactorFactory, ExposureReader, FactorPreprocessor, SignalCombiner, ParquetWriter, DerivedViews, DeriveStep, str -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | Years from the campaign start to the last universe session. | — -> list[str] | `LakeError` | as class | see class |
| `run` | Build and write every year, then refresh the view and its digest. | str, ProgressHook \| None -> StepReport | `LakeError`, `SchemaError`, `ConfigError` | as class | see class |

### `PrefectRunner` — `quant_cn.pipeline.prefect_runner` (L6)
- **Purpose:** Same contract as LocalRunner, executed as a Prefect flow named "quant_cn <kind>" whose run name is the RunLog run id; every step is a Prefect task with a progress artifact over its units (keys). RunLog stays the source of truth (D-022); steps and fetchers never import Prefect. A permission failure marks the step blocked and continues; any other project error fails the flow, closes the run as failed and re-raises.
- **Base:** BaseRunner. **Depends on (injected):** BaseRunLog, int.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_prefect_runner.py` (TC-PFR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseRunLog, int -> None | — | callers of the class | — |
| `run` | See BaseRunner.run; the flow appears in the Prefect UI while it runs. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

### `PipelineReport` — `quant_cn.pipeline.runner` (L6)
- **Purpose:** Result of one pipeline run: its id, overall status and one StepReport per step.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.BaseRunner`, `pipeline.CuratePipeline`, `pipeline.PrefectRunner`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_blocked` | Names of steps blocked by missing permissions. | — -> list[str] | — | as class | see class |
| `to_frame` | One row per step for display or logging. | — -> pd.DataFrame | — | as class | see class |

### `BaseRunner` — `quant_cn.pipeline.runner` (L6)
- **Purpose:** Extension point for how steps are executed (local now, Prefect later, D-022); steps never import the runner's backend.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `pipeline.LocalRunner`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`, `pipeline.PrefectRunner`, `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | Execute steps in order under one run id. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

### `LocalRunner` — `quant_cn.pipeline.runner` (L6)
- **Purpose:** Run steps serially in this process with a rich progress bar per step; a permission failure marks the step blocked and continues; any other project error closes the run as failed and re-raises (finished keys stay done).
- **Base:** BaseRunner. **Depends on (injected):** BaseRunLog, Console | None, bool.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseRunLog, Console \| None, bool -> None | — | callers of the class | — |
| `run` | See BaseRunner.run. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

### `UniverseStep` — `quant_cn.pipeline.universe_step` (L6)
- **Purpose:** Build UNIVERSE_PANEL: one row per stock listed on each session (list_date <= t < delist_date; retired alias codes are absent from stock_basic, D-053), in_universe = 1 when no rule excludes it, and every failing rule kept in `reason` (comma-joined): exchange (not in config, BJ by default, D-054), st (name in effect at t contains ST or starts with PT, from namechange start dates), delisting (name contains 退, 退市整理期), new_listing (fewer than min_sessions sessions since the first session on/after list_date), suspended (no daily bar at t). Delisted stocks stay in history (no survivorship). Point in time: the name at t is the namechange row with the latest start_date <= t (FACTOR_TESTING_DESIGN §11). One unit per calendar year, written to derived/universe/year=YYYY.
- **Base:** BaseStep. **Depends on (injected):** LakeQuery, ParquetWriter, UniverseConfig.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_contract_checker.py`, `tests/pipeline/test_universe_step.py` (TC-US-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, ParquetWriter, UniverseConfig -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | Years to build: from rules.start to the last daily session. | — -> list[str] | `LakeError` | as class | see class |
| `run` | Build and write every year. | str, ProgressHook \| None -> StepReport | `LakeError`, `SchemaError` | as class | see class |

### `ServiceBuilder` — `quant_cn.service_builder` (L8)
- **Purpose:** Wire services for the CLI commands (the composition root's constructors): download and curate pipelines with the chosen runner, and the project catalog.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `cli.QuantCnCli`, `cli.ResearchCommands`.
- **Tests:** `tests/test_cli.py` (TC-QCC-002..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_download_pipeline` | DownloadPipeline wired to the lake, Tushare client and chosen runner. | Config, LakeCatalog, bool, str -> DownloadPipeline | — | as class | see class |
| `build_curate_pipeline` | CuratePipeline wired to compactor, derived views, PIT aligner and chosen runner. | Config, LakeCatalog, bool, str -> CuratePipeline | — | as class | see class |
| `build_features` | FeatureStep wired from config/factors.yaml (factors and campaign settings). | Config, LakeCatalog, LakeQuery, DerivedViews, DeriveStep -> FeatureStep | — | as class | see class |
| `build_runner` | LocalRunner, or PrefectRunner for name "prefect" (optional extra "flows", D-022). | RunLog, str, bool -> BaseRunner | `ModuleNotFoundError` | as class | see class |
| `build_reader` | The lake read API (D-089): PIT aligner, alias map, calendar and an optional cache. | Config, LakeCatalog, bool -> LakeReader | — | as class | see class |
| `build_evaluation` | EvaluationStep for the configured campaign (2,000 seeded block-bootstrap resamples). | Config, LakeCatalog -> EvaluationStep | — | as class | see class |
| `build_risk_model` | RiskModelStep for config/risk_model.yaml (plan 05, D-127): loader, model, validation report, view refresh and digests. | Config, LakeCatalog -> RiskModelStep | — | as class | see class |
| `build_project_catalog` | ProjectCatalog over the repository with the contract linter. | Config, LakeCatalog -> ProjectCatalog | — | as class | see class |

### `BlockBootstrap` — `quant_cn.statistic.block_bootstrap` (L4)
- **Purpose:** Resample a time series (or several aligned series with the same draws) in blocks so serial correlation survives: stationary bootstrap with geometric block lengths (Politis & Romano 1994) or circular block bootstrap with fixed blocks (Politis & Romano 1992); both wrap around. Seeded, so reports reproduce byte for byte.
- **Base:** none. **Depends on (injected):** int, int, Method.
- **Used by:** `statistic.IcSignificance`, `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_block_bootstrap.py` (TC-BB-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int, int, Method -> None | `ValueError` | callers of the class | — |
| `compute_block` | Expected block length for a horizon. | int -> int | — | as class | see class |
| `build_indices` | B resampled index vectors of length T. | int, int -> np.ndarray | — | as class | see class |
| `compute_distribution` | The statistic recomputed on every resample. | Values, Callable[[np.ndarray], float], int -> np.ndarray | `ValueError` | as class | see class |
| `compute_interval` | Percentile confidence interval and bootstrap p-value of H0: statistic = 0. | Values, Callable[[np.ndarray], float], int, float -> dict[str, float] | `ValueError` | as class | see class |

### `HacVariance` — `quant_cn.statistic.hac_variance` (L4)
- **Purpose:** Heteroskedasticity- and autocorrelation-consistent variance of a sample mean with the Bartlett kernel (Newey & West 1987; lag rule of Newey & West 1994), for series whose observations overlap (IC_t at horizon h is serially correlated by construction). By default the series is AR(1)-prewhitened before the kernel and recoloured after (Andrews & Monahan 1992): with the plain rule-of-thumb lag, 95% intervals covered only 89.8% on AR(1) phi = 0.6 and 88.4% on an overlapping 20-session MA(19), against 95.1% and 99.0% prewhitened (D-090). Used for the NW t on mean IC and by every HAC test.
- **Base:** none. **Depends on (injected):** int | None, bool.
- **Used by:** `statistic.IcSignificance`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_hac_variance.py` (TC-HAC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int \| None, bool -> None | `ValueError` | callers of the class | — |
| `compute_lag` | Bartlett truncation lag. | int, int -> int | — | as class | see class |
| `compute_long_run_variance` | Bartlett-kernel long-run variance of a series. | Values, int -> float | `ValueError` | as class | see class |
| `compute_hac_variance` | Long-run variance used for inference: prewhitened (default) or plain Bartlett. | Values, int -> float | `ValueError` | as class | see class |
| `compute_t` | Newey-West t statistic of the mean. | Values, int -> dict[str, float] | `ValueError` | as class | see class |

### `IcCalculator` — `quant_cn.statistic.ic_calculator` (L4)
- **Purpose:** Per-date information coefficient between factor values and forward returns across the universe: IC_t = corr_rank(f_{i,t}, r_{i,t->t+h}) (Spearman; Pearson on the values as a variant). Forward returns are tradeable (FACTOR_TESTING_DESIGN §10, §11): the factor known at the close of t is traded at the next open, r = P_adj close(t+h) / P_adj open(t+1) - 1; close-to-close is available for comparison only.
- **Base:** none. **Depends on (injected):** Method, int.
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_ic_calculator.py` (TC-ICC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Method, int -> None | `ValueError` | callers of the class | — |
| `build_forward_returns` | Forward returns per stock, session and horizon from dense adjusted prices. | pd.DataFrame, Sequence[int], Entry -> pd.DataFrame | `SchemaError`, `ValueError` | as class | see class |
| `compute` | IC_t per date, factor and horizon. | pd.DataFrame, pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |

### `IcSignificance` — `quant_cn.statistic.ic_significance` (L4)
- **Purpose:** The §2 tests for one factor at one horizon: Newey-West t on mean IC (Newey & West 1987, 1994, prewhitened per D-090), stationary block-bootstrap CI of mean IC and ICIR (Politis & Romano 1994), Fisher-z / Stouffer screen, sign consistency per sub-period, single break in mean (Bai & Perron 1998; sup-F critical values of Andrews 1993), plus Pesaran-Timmermann directional accuracy (1992, 2009) and an exponential decay fit across horizons.
- **Base:** none. **Depends on (injected):** HacVariance, BlockBootstrap, Mapping[str, tuple[str, str]].
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_ic_significance.py` (TC-ICS-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | HacVariance, BlockBootstrap, Mapping[str, tuple[str, str]] -> None | — | callers of the class | — |
| `compute` | IC_TEST rows for one factor and horizon. | pd.DataFrame -> pd.DataFrame | `SchemaError`, `ValueError` | as class | see class |
| `compute_break` | Single structural break in mean IC. | pd.DataFrame, int -> dict[str, object] | `ValueError` | as class | see class |
| `compute_pesaran_timmermann` | Directional accuracy of sign(signal) for sign(outcome) beyond chance. | Values, Values -> dict[str, float] | `ValueError` | as class | see class |
| `compute_decay` | Horizon profile of mean IC (D-095): peak horizon, exponential decay beyond the peak, accumulation ratio. | Mapping[int, float] -> dict[str, float] | `ValueError` | as class | see class |
| `_build_full_rows` (private) | internal helper over 20 lines | pd.DataFrame, str, int, int -> list[dict[str, object]] | — | internal | — |
| `_build_row` (private) | internal helper over 20 lines | str, int, str, str, float, float \| None, float \| None, float \| None, tuple[float, float] \| None -> dict[str, object] | — | internal | — |

### `MultipleTestingAdjuster` — `quant_cn.statistic.multiple_testing_adjuster` (L4)
- **Purpose:** Adjust the p-values of many factor tests run in one campaign: Holm step-down FWER (Holm 1979), Benjamini-Hochberg FDR (1995), Benjamini-Hochberg-Yekutieli FDR under arbitrary dependence (2001), Romano-Wolf bootstrap step-down FWER (Romano & Wolf 2005, 2016), and the Harvey-Liu-Zhu (2016) /t/ >= 3.0 hurdle. Pure arithmetic on arrays.
- **Base:** none. **Depends on (injected):** float.
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_multiple_testing_adjuster.py` (TC-MTA-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | float -> None | — | callers of the class | — |
| `compute_holm` | Holm step-down adjusted p-values (family-wise error). | Values -> np.ndarray | — | as class | see class |
| `compute_bh` | Benjamini-Hochberg adjusted p-values (false discovery rate). | Values, float -> np.ndarray | — | as class | see class |
| `compute_bhy` | Benjamini-Hochberg-Yekutieli adjusted p-values (FDR under arbitrary dependence). | Values -> np.ndarray | — | as class | see class |
| `compute_romano_wolf` | Romano-Wolf step-down adjusted p-values from bootstrap null statistics. | Values, np.ndarray -> np.ndarray | `ValueError` | as class | see class |
| `build_adjusted` | Fill adjusted p-values and the HLZ flag on one metric (and window) across factors. | pd.DataFrame, str, str \| None, np.ndarray \| None -> pd.DataFrame | `SchemaError`, `ValueError` | as class | see class |

### `Neutralizer` — `quant_cn.statistic.neutralizer` (L4)
- **Purpose:** Remove what industry membership and numeric exposures (e.g. log market cap) explain in a factor, date by date: the residual of OLS x_i = a + sum_g d_{ig} b_g + sum_k z_{ik} c_k + e_i, so the factor's IC is not an industry or size bet in disguise.
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `factor.FactorPreprocessor`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_neutralizer.py` (TC-NEU-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | — | callers of the class | — |
| `compute` | Replace `column` by its per-date OLS residual. | pd.DataFrame, str, Sequence[str], Sequence[str], str -> pd.DataFrame | `KeyError` | as class | see class |

### `QuantileReturns` — `quant_cn.statistic.quantile_returns` (L4)
- **Purpose:** Sort names into n quantiles of the factor within each date and horizon, and report each quantile's equal-weighted mean forward return plus the long-short spread (top minus bottom, stored as quantile 0): the monotone "ladder" that complements the IC.
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_quantile_returns.py` (TC-QR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | `ValueError` | callers of the class | — |
| `compute` | Mean forward return per quantile, date, factor and horizon. | pd.DataFrame, pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |

### `ReturnStats` — `quant_cn.statistic.return_stats` (L4)
- **Purpose:** Summarise a series of period returns: annualised mean and volatility, Sharpe (per period and annualised with sqrt(244 / h)), maximum drawdown of the compounded path, hit rate, skewness and non-excess kurtosis (the PSR / DSR inputs of Bailey & López de Prado 2012).
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_return_stats.py` (TC-RS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | — | callers of the class | — |
| `compute` | Statistics of non-overlapping returns of length h sessions. | Values, int -> dict[str, float] | `ValueError` | as class | see class |

### `Standardizer` — `quant_cn.statistic.standardizer` (L4)
- **Purpose:** Put factor values on a common scale within each date: z = (x - m) / s with m the equal-weighted mean (or a weighted mean, e.g. cap weights as in Barra-style exposures) and s the equal-weighted standard deviation, so the cross-section has unit dispersion.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `factor.FactorPreprocessor`, `factor.SignalCombiner`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_standardizer.py` (TC-STD-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute` | z-score one column within each group. | pd.DataFrame, str, str, str \| None -> pd.DataFrame | `KeyError` | as class | see class |

### `TrialLog` — `quant_cn.statistic.trial_log` (L4)
- **Purpose:** Record every factor / parameter / horizon variant evaluated in a campaign, including the failures, because the deflated Sharpe ratio (Bailey & López de Prado 2014) and the multiple-testing adjusters need the number and dispersion of all trials, not just the winners. Append-only: trials get sequential ids and can never be edited or removed. No I/O: the caller persists `build_frame()` and resumes with `from_frame()`.
- **Base:** none. **Depends on (injected):** str.
- **Used by:** `factor.FactorEvaluator`, `pipeline.EvaluationStep`.
- **Tests:** `tests/statistic/test_trial_log.py` (TC-TL-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str -> None | `ValueError` | callers of the class | — |
| `n_trials` | Number of trials recorded (N for the deflated Sharpe ratio). | — -> int | — | as class | see class |
| `add_trial` | Append one evaluated variant. | str, Mapping[str, object], int, float \| None, float \| None -> str | `TypeError` | as class | see class |
| `find_trial` | The id of an already recorded identical variant (re-running a campaign does not inflate N). | str, Mapping[str, object], int -> str \| None | `TypeError` | as class | see class |
| `build_frame` | The log as a TRIAL_LOG frame (a copy). | — -> pd.DataFrame | — | as class | see class |
| `from_frame` | Resume a campaign's log from a saved TRIAL_LOG frame. | str, pd.DataFrame -> TrialLog | `ValueError`, `SchemaError` | as class | see class |

### `Winsorizer` — `quant_cn.statistic.winsorizer` (L4)
- **Purpose:** Clip extreme factor values within each date so a few outliers do not dominate ranks, z-scores or regressions: median +- k * 1.4826 * MAD (robust default) or the q / 1 - q cross-sectional quantiles.
- **Base:** none. **Depends on (injected):** Method, float, float.
- **Used by:** `factor.FactorPreprocessor`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_winsorizer.py` (TC-WZ-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Method, float, float -> None | `ValueError` | callers of the class | — |
| `compute` | Winsorise one column within each group. | pd.DataFrame, str, str -> pd.DataFrame | `KeyError` | as class | see class |

### `BaseChart` — `quant_cn.visualization.base_chart` (L7)
- **Purpose:** Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never objects from other packages); the base applies theme, size, hover and export.
- **Base:** ABC. **Depends on (injected):** ChartTheme, int, int.
- **Used by:** `visualization.PriceChart`, `visualization.FactorChart`.
- **Tests:** `tests/visualization/test_charts.py` (TC-BCA-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ChartTheme, int, int -> None | `TypeError` | callers of the class | — |
| `build_figure` | Build the unthemed figure from the input frame. | pd.DataFrame -> go.Figure | `ValueError`, `SchemaError` | as class | see class |
| `render` | Build the figure and apply the theme: surfaces, ink, recessive grid, unified hover. | pd.DataFrame -> go.Figure | `ValueError`, `SchemaError` | as class | see class |
| `to_html` | The themed chart as an HTML fragment (plotly.js from its CDN). | pd.DataFrame -> str | `ValueError`, `SchemaError` | as class | see class |
| `write_html` | Save the themed chart as a standalone HTML page. | pd.DataFrame, Path -> Path | `ValueError`, `SchemaError`, `OSError` | as class | see class |

### `ChartTheme` — `quant_cn.visualization.chart_theme` (L7)
- **Purpose:** The colour and font tokens every chart reads, so charts are written against roles, never raw hex. Values follow the dataviz reference palette; `up`/`down` are its red and green slots (A-share convention: red up, green down), validated per mode; the light pair sits in the CVD 6-8 band, so up candles are hollow as the secondary encoding.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `visualization.BaseChart`, `visualization.PriceChart`, `visualization.FactorChart`.
- **Tests:** `tests/visualization/test_charts.py` (TC-CT-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `from_mode` | The theme for a display mode. | Mode -> ChartTheme | `ValueError` | as class | see class |

### `FactorChart` — `quant_cn.visualization.factor_chart` (L7)
- **Purpose:** The four views of a factor campaign (plan 04 phase 6), one single-series chart each so identity never rests on colour: "ic_series" (IC_SERIES) the rolling mean IC of one factor and horizon with a band of +/- 1.96 sd / sqrt(window / h), the effective number of non-overlapping observations; "icir" (IC_TEST) full-window ICIR per factor at one horizon with its bootstrap CI; "quantiles" (QUANTILE_RETURNS) mean forward return per quantile of one factor and horizon, long-short mean in the title; "horizon" (IC_TEST) full-window mean IC of one factor by horizon with its CI, peak horizon and half-life in the title (D-095).
- **Base:** BaseChart. **Depends on (injected):** ChartTheme, Kind, str | None, int, int, DateCodec | None, int, int.
- **Used by:** `research_space/notebooks/20260930_factor_campaign_01.ipynb`, `plan 06 ReportBuilder`.
- **Tests:** `tests/visualization/test_factor_chart.py` (TC-FC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ChartTheme, Kind, str \| None, int, int, DateCodec \| None, int, int -> None | `ValueError` | callers of the class | — |
| `build_figure` | The figure for `kind`. | pd.DataFrame -> go.Figure | `SchemaError`, `ValueError` | as class | see class |
| `_build_ic_series` (private) | internal helper over 20 lines | pd.DataFrame -> go.Figure | — | internal | — |
| `_build_horizon` (private) | internal helper over 20 lines | pd.DataFrame -> go.Figure | — | internal | — |

### `PriceChart` — `quant_cn.visualization.price_chart` (L7)
- **Purpose:** Daily candles (backward-adjusted by default: OHLC x adj_factor) over a volume panel for one ticker. Two stacked panels with their own y-axes (never a dual axis); x is a category axis of trading days so non-trading days leave no gaps. Up candles hollow, down candles filled.
- **Base:** BaseChart. **Depends on (injected):** ChartTheme, str, DateCodec, bool, int, int.
- **Used by:** `research_space/main.ipynb`.
- **Tests:** `tests/visualization/test_charts.py` (TC-PC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ChartTheme, str, DateCodec, bool, int, int -> None | — | callers of the class | — |
| `build_figure` | Candles and volume for `ts_code`. | pd.DataFrame -> go.Figure | `SchemaError`, `ValueError` | as class | see class |

### `DocumentRule` — `quant_cn.core.document_source` (L1)
- **Purpose:** One title rule: a title matching `include` and not `exclude` (regular expressions) is a document of `doc_type`.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.DocumentSource`, `data_loading.DocumentClassifier`.
- **Tests:** `tests/core/test_document_source.py` (TC-DSR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DocumentSource` — `quant_cn.core.document_source` (L1)
- **Purpose:** One document source of config/documents.yaml: the curated metadata dataset listing the documents, its key columns, the PDF URL and file-name templates (`{column}` placeholders), the folder under `documents/`, and how a row gets its doc type (a fixed `doc_type` or title `rules`, first match wins).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `data_loading.DocumentClassifier`, `data_loading.DocumentDownloader`.
- **Tests:** `tests/core/test_document_source.py` (TC-DSR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DocumentViews` — `quant_cn.lake.document_views` (L2)
- **Purpose:** Expose the document manifest in the catalog. `meta.document_attempts` holds every manifest row (one per download attempt). `meta.documents` holds the latest attempt per doc_id, so `WHERE status = 'ok'` lists the PDFs present under `documents/`.
- **Base:** none. **Depends on (injected):** Path, duckdb.DuckDBPyConnection.
- **Used by:** `lake.LakeCatalog.refresh_views`, `cli.DocumentCommands`.
- **Tests:** `tests/lake/test_document_views.py` (TC-DOV-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, duckdb.DuckDBPyConnection -> None | — | callers of the class | — |
| `refresh` | (Re)create both views, or drop them when no manifest file exists. | — -> None | `LakeError` | as class | see class |

### `RequestPacer` — `quant_cn.data_loading.request_pacer` (L3)
- **Purpose:** Run one request callable at a time-spaced rate with retries: request starts are at least `min_interval_s` apart across all threads sharing the pacer, and a call raising OSError, ValueError or KeyError is retried after `retry_sleep_s` up to `retries` times.
- **Base:** none. **Depends on (injected):** Clock, str, float, int, float.
- **Used by:** `data_loading.BaseWebClient`, `data_loading.DocumentDownloader`.
- **Tests:** `tests/data_loading/test_document_downloader.py` (TC-RP-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, str, float, int, float -> None | — | callers of the class | — |
| `run` | Wait for this request's turn, run `call`, retry on transport errors. | str, Callable[[], T] -> T | `DataSourceError` | as class | see class |
| `record_throttle` | Record that the site throttled us: no request (from any thread) starts for `cooldown_s` seconds from now. | float -> None | — | as class | TC-RP-003 |

### `BaseWebClient` — `quant_cn.data_loading.base_web_client` (L3)
- **Purpose:** Base for vendor clients that page a public website's JSON API (CNINFO, Eastmoney). It holds the transport, the timeout and a RequestPacer. Every request is spaced by `min_interval_s` and transport failures are retried after `retry_sleep_s`, so a long sweep survives short outages without hammering the site.
- **Base:** BaseApiClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float, float.
- **Used by:** `data_loading.CninfoClient`, `data_loading.EastmoneyReportClient`, `data_loading.AppStoreClient`, `data_loading.CboeClient`, `data_loading.BaseHtmlListClient`.
- **Tests:** `tests/data_loading/test_web_clients.py` (TC-BWC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, HttpTransport \| None, float, int, float, float -> None | — | callers of the class | — |
| `get_vendor_name` | Short vendor name used in error messages. | — -> str | — | as class | see class |

### `CninfoClient` — `quant_cn.data_loading.cninfo_client` (L3)
- **Purpose:** List CNINFO announcements for the whole A-share market (`column=szse` covers SZ, SH and BJ) over a date range, optionally one category (e.g. "category_ndbg_szsh" annual reports), following `pageNum` until `totalpages`. Rows are de-duplicated on (ann_id, sec_code) because the list can shift while a busy day is paged; `<em>` highlight tags are removed from titles; `announcementTime` (epoch ms) becomes `ann_time` "YYYYMMDD HH:MM:SS" and `ann_date` YYYYMMDD in Beijing time.
- **Base:** BaseWebClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_web_clients.py` (TC-CNC-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, HttpTransport \| None, float, int, float -> None | — | callers of the class | — |
| `get_vendor_name` | Vendor name for messages. | — -> str | — | as class | see class |
| `query` | Every announcement in the date range (and category), all pages. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | as class | see class |

### `EastmoneyReportClient` — `quant_cn.data_loading.eastmoney_report_client` (L3)
- **Purpose:** List Eastmoney (东方财富) broker research reports published in a date range for one report kind (`q_type` "0" stock, "1" industry, "2" strategy), following `pageNo` until `TotalPage`. The PDF of a row is https://pdf.dfcfw.com/pdf/H3_<info_code>_1.pdf. `publishDate` carries no time of day, so `publish_date` is YYYYMMDD and the lake rule makes it usable from the next session.
- **Base:** BaseWebClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_web_clients.py` (TC-EMR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, HttpTransport \| None, float, int, float -> None | — | callers of the class | — |
| `get_vendor_name` | Vendor name for messages. | — -> str | — | as class | see class |
| `query` | Every report of one kind published in [start_date, end_date]. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | as class | see class |


### `AppStoreClient` — `quant_cn.data_loading.app_store_client` (L3)
- **Purpose:** One country's App Store top charts as rows: for each chart GET the legacy iTunes RSS JSON feed (Apple caps it at 100 entries) and flatten every entry to COLUMNS (rank = feed position, app_id, artist_id from the artist link, release_date YYYYMMDD, price and currency, captured_at from the Clock). A store that does not exist (HTTP 400 / 404) or an empty feed gives zero rows (D-137).
- **Base:** BaseWebClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_web_clients.py` (TC-ASC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, HttpTransport \| None, float, int, float -> None | — | callers of the class | — |
| `get_vendor_name` | Vendor name for messages. | — -> str | — | as class | see class |
| `query` | Every chart in `params["charts"]` for one country, flattened. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | `core.BaseFetcher.fetch_one` | TC-ASC-001..003 |

### `CboeClient` — `quant_cn.data_loading.cboe_client` (L3)
- **Purpose:** The full daily history of one CBOE index (default VIX) from CBOE's public CSV (DATE MM/DD/YYYY, OPEN, HIGH, LOW, CLOSE): YYYYMMDD dates, float prices, one row per date, sorted; bad-date rows dropped with a log line (D-152).
- **Base:** BaseWebClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_cboe_client.py` (TC-CBC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, HttpTransport \| None, float, int, float -> None | — | callers of the class | — |
| `get_vendor_name` | Vendor name for messages. | — -> str | — | as class | see class |
| `query` | Every day of one index. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | `core.BaseFetcher.fetch_one` | TC-CBC-001..002 |

### `BaseHtmlListClient` — `quant_cn.data_loading.base_html_list_client` (L3)
- **Purpose:** Base for clients of sites that list monthly releases on paged HTML index pages (`<list_url>`, `index_1.html`, ...) and publish each release as HTML tables (国家统计局, 国家新闻出版署; plan 31 ph1). Pages the index until a page has no link, answers 404, `max_pages`, or all its links are older than `since`; keeps links passing `is_wanted`; reads a release into (caption, rows), dropping repeated tables with the same caption (PC and mobile copies).
- **Base:** BaseWebClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float.
- **Used by:** `data_loading.NbsHousePriceClient`, `data_loading.NppaGameClient` (subclasses).
- **Tests:** `tests/data_loading/test_nbs_house_price_client.py` (TC-BHL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, HttpTransport \| None, float, int, float -> None | — | callers of the class | — |
| `is_wanted` | Whether a list-page link with this title is a release the client reads. | str -> bool | — | subclasses | see class |
| `fetch_text` | GET one page as text, paced and retried. | str -> str | `DataSourceError` | subclasses | see class |
| `list_links` | Wanted release links of the list pages, newest first, no duplicates. | str, int, str -> list[PageLink] | `DataSourceError` | subclasses | TC-BHL-001 |
| `read_tables` | The tables of one release as (caption, rows). | str -> list[tuple[str, list[list[str]]]] | `DataSourceError` | `NbsHousePriceClient` | TC-BHL-002 |
| `build_tables` | Parse page text into (caption, rows) pairs. | str -> list[tuple[str, list[list[str]]]] | — | `NppaGameClient` | TC-BHL-002 |
| `get_text` | Visible text of an HTML fragment without whitespace. | str -> str | — | as class | see class |

### `PageLink` — `quant_cn.data_loading.base_html_list_client` (L3)
- **Purpose:** One release linked from a list page: absolute url, title text, publication date from the url (YYYYMMDD). Frozen dataclass, no methods.
- **Used by:** `data_loading.BaseHtmlListClient.list_links`, `data_loading.NppaGameClient`.
- **Tests:** `tests/data_loading/test_nbs_house_price_client.py` (TC-BHL-001).

### `NbsHousePriceClient` — `quant_cn.data_loading.nbs_house_price_client` (L3)
- **Purpose:** The 70-city price indices from the 国家统计局 monthly release "YYYY年M月份70个大中城市商品住宅销售价格变动情况": tables 1 (新建商品住宅) and 2 (二手住宅), two cities per row; one row per (month YYYYMM, city, house_type new / second_hand) with mom / yoy indices (= 100 base), `published` from the url. Tier averages are left to plan 31 ph4.
- **Base:** BaseHtmlListClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float.
- **Used by:** `cli.ServiceBuilder` (source "nbs", dataset `house_price_70`).
- **Tests:** `tests/data_loading/test_nbs_house_price_client.py` (TC-NHP-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_vendor_name` | Vendor name for messages ("nbs"). | — -> str | — | as class | see class |
| `is_wanted` | The 70-city price release, not its 解读. | str -> bool | — | as class | TC-NHP-002 |
| `query` | Every city index of the releases from `start_date` on. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | `core.BaseFetcher.fetch_one` | TC-NHP-001..003 |

### `NppaGameClient` — `quant_cn.data_loading.nppa_game_client` (L3)
- **Purpose:** Game approvals (版号) from the 国家新闻出版署 lists 国产 / 进口网络游戏审批信息: one row per approval number with name, category (from the page's `_sblb` script), publisher, operator, ISBN, approved_on, published (list date from the url), origin domestic / imported.
- **Base:** BaseHtmlListClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float.
- **Used by:** `cli.ServiceBuilder` (source "nppa", dataset `game_license`).
- **Tests:** `tests/data_loading/test_nppa_game_client.py` (TC-NGC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_vendor_name` | Vendor name for messages ("nppa"). | — -> str | — | as class | see class |
| `is_wanted` | A game approval list. | str -> bool | — | as class | see class |
| `query` | Every approval of the lists published from `start_date` on. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | `core.BaseFetcher.fetch_one` | TC-NGC-001..002 |

### `ManualSeriesClient` — `quant_cn.data_loading.manual_series_client` (L3)
- **Purpose:** Serve the hand-entered series in `config/manual_series.yaml` (public, committed) and `config/local.manual_series.yaml` (licensed exports, git-ignored) as one validated vendor frame, so download / compact write curated `alt/manual_series` with known_on = published; every row keeps its source URL (plan 20, D-139).
- **Base:** BaseApiClient. **Depends on (injected):** Path.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_manual_series_client.py` (TC-MSC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `query` | All observations of both files, validated, one row per (series, date, published). | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `ConfigError` | `core.BaseFetcher.fetch_one` | TC-MSC-001..003 |

### `ManualSeriesDef` — `quant_cn.data_loading.manual_series_client` (L3)
- **Purpose:** One manual series definition: id, name, unit, freq (daily / weekly / monthly / quarterly), kind (index / price / spread / count), linked ts_codes.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `data_loading.ManualSeriesClient`, `data_loading.ManualSeriesFile`.
- **Tests:** `tests/data_loading/test_manual_series_client.py` (TC-MSC-001).

### `ManualObservation` — `quant_cn.data_loading.manual_series_client` (L3)
- **Purpose:** One manual value: series, date, value, published (>= date, the PIT date), http(s) source URL, note, revision flag.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `data_loading.ManualSeriesClient`, `data_loading.ManualSeriesFile`.
- **Tests:** `tests/data_loading/test_manual_series_client.py` (TC-MSC-002).

### `ManualSeriesFile` — `quant_cn.data_loading.manual_series_client` (L3)
- **Purpose:** The content of one manual-series YAML file: series definitions and observations.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `data_loading.ManualSeriesClient`.
- **Tests:** `tests/data_loading/test_manual_series_client.py` (TC-MSC-001).

### `SnapshotFetcher` — `quant_cn.data_loading.snapshot_fetcher` (L3)
- **Purpose:** Capture a source that only serves the current state: one key per value for today, "<today>_<value>", today from the injected Clock; the run range is ignored so past dates are never requested; `sweep.key_field` (capture date) is filled from the key's date part (D-137).
- **Base:** EnumFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, Sequence[str].
- **Used by:** `data_loading.FetcherFactory.build` (sweep kind "snapshot").
- **Tests:** `tests/data_loading/test_snapshot_fetcher.py` (TC-SNF-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_keys` | Today's keys, one per value. | str, str -> list[str] | — | `core.BaseFetcher.run` | TC-SNF-001 |
| `build_params` | The value part of the key under the sweep parameter, plus constant parameters. | str, str, str -> dict[str, str] | — | `core.BaseFetcher.fetch_one` | TC-SNF-002 |
### `DocumentClassifier` — `quant_cn.data_loading.document_classifier` (L3)
- **Purpose:** Give each listed document its type: the source's fixed `doc_type`, or the first title rule whose `include` matches and whose `exclude` does not (e.g. "2025年年度报告" → annual; "2025年年度报告摘要" → none; "2025年半年度报告" → semiannual because that rule comes first).
- **Base:** none. **Depends on (injected):** DocumentSource.
- **Used by:** `data_loading.DocumentDownloader`.
- **Tests:** `tests/data_loading/test_document_downloader.py` (TC-DCL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DocumentSource -> None | — | callers of the class | — |
| `compute_doc_types` | Document type per title. | pd.Series -> pd.Series | — | as class | see class |

### `DocumentManifestWriter` — `quant_cn.data_loading.document_manifest_writer` (L3)
- **Purpose:** Write one manifest part file (MANIFEST_COLUMNS, zstd parquet, tmp + rename) under `<lake_root>/meta/document_manifest/`. Rows are never rewritten: a later row for the same doc_id (later `downloaded_at`) supersedes the earlier one for readers.
- **Base:** none. **Depends on (injected):** Path.
- **Used by:** `data_loading.DocumentDownloader`, `data_loading.DocumentRetyper`.
- **Tests:** `tests/data_loading/test_document_retyper.py` (TC-DMW-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_glob` | The glob of every part file, for read_parquet. | — -> str | — | as class | TC-DMW-001 |
| `has_parts` | Whether any part file exists. | — -> bool | — | as class | TC-DMW-001 |
| `write_part` | Persist rows as part-<name>.parquet; None when no rows. | Sequence[Mapping], str -> Path \| None | `LakeError` | as class | TC-DMW-001 |

### `DocumentRetyper` — `quant_cn.data_loading.document_retyper` (L3)
- **Purpose:** After the title rules change, re-classify the latest `ok` manifest row of every document of a source; a new type moves the file to that type's folder and appends a manifest row, a title no rule matches appends `excluded` (file kept); unchanged documents untouched (plan 18 ph2, D-149).
- **Base:** none. **Depends on (injected):** Path, LakeQuery, Mapping[str, DocumentSource], Clock, DocumentManifestWriter.
- **Used by:** (none yet).
- **Tests:** `tests/data_loading/test_document_retyper.py` (TC-DRT-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | Re-type every downloaded document of one source. | str -> StepReport | `ConfigError`, `LakeError` | as class | TC-DRT-001 |

### `DocumentDownloader` — `quant_cn.data_loading.document_downloader` (L3)
- **Purpose:** Download the PDFs listed in a document source's curated metadata (config/documents.yaml) into `documents/<folder>/<doc_type>/<YYYY>/<MM>/<file>` (D-101). Rows are typed by DocumentClassifier, optionally limited to A-share codes (`curated.stock_basic.symbol`), de-duplicated on the document id, and skipped when the manifest already holds an `ok` attempt whose file exists. Each file is written atomically (tmp + rename) after its body is checked to start with %PDF-; one manifest row per attempt (sha256, bytes, status ok | not_pdf | failed) is appended to `meta/document_manifest/part-*.parquet` every `flush_every` documents, so an interrupted run resumes where it stopped.
- **Base:** none. **Depends on (injected):** Path, LakeQuery, Mapping[str, DocumentSource], Clock, HttpTransport | None, int, float, int, float, int.
- **Used by:** `cli.DocumentCommands`.
- **Tests:** `tests/data_loading/test_document_downloader.py` (TC-DD-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, LakeQuery, Mapping[str, DocumentSource], Clock, HttpTransport \| None, int \| None, int, float, int -> None | — | callers of the class | — |
| `list_candidates` | Every wanted document of a source, typed and with its URL and target path. | str, Sequence[str] \| None, str \| None, str \| None -> pd.DataFrame | `ConfigError`, `LakeError` | as class | see class |
| `list_todo` | Candidates without an `ok` manifest attempt whose file exists: the work of `run`. | str, Sequence[str] \| None, str \| None, str \| None -> pd.DataFrame | `ConfigError`, `LakeError` | as class | see class |
| `run` | Download the documents of `todo` (from list_todo); no catalog access. | pd.DataFrame, int \| None, Progress \| None -> StepReport | `LakeError` | as class | see class |

### `DocumentCommands` — `quant_cn.document_commands` (L8)
- **Purpose:** The document-side CLI commands: `download-docs` (plan 12 phase 2, D-101) prints candidate counts per doc type (`--dry-run`) or downloads the PDFs not yet in the manifest; `import-labels` (plan 28 ph0) imports config/label_sources.yaml into derived/labels via LegacyLabelImporter and LabelStore.
- **Base:** none. **Depends on (injected):** Console.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/test_cli.py` (TC-QCC-010, 015).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Console -> None | — | callers of the class | — |
| `build_parser` | Add the `download-docs` and `import-labels` subcommands and their options to the CLI parser. | argparse._SubParsersAction -> None | — | as class | see class |

### `ReportPages` — `quant_cn.quant_cn.industry_graph.pdf_text_extractor` (L4)
- **Purpose:** The text of one report PDF, page by page, plus its outline (bookmarks) when present.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.PdfTextExtractor`, `industry_graph.SectionDetector`, `industry_graph.AnnualReportParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-PTE-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `n_chars` | Characters over all pages (for section-share statistics). | — -> int | — | as class | see class |

### `PdfTextExtractor` — `quant_cn.quant_cn.industry_graph.pdf_text_extractor` (L4)
- **Purpose:** Read the native text layer of a PDF page by page (no OCR; D-102) and remove the running header and footer: a line with at least four letters or CJK characters that, with digits ignored, appears on at least `header_share` of the pages (e.g. "牧原食品股份有限公司2025 年年度报告全文"), and bare page numbers ("31", "36 / 251"). Tables that cross a page break then read as one block, which the top-5 table parser needs (a header inside the table split rows in the hog-sector prototype).
- **Base:** none. **Depends on (injected):** float.
- **Used by:** `industry_graph.AnnualReportParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-PTE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | float -> None | — | callers of the class | — |
| `read_pages` | Text and outline of one PDF, headers and footers removed. | Path -> ReportPages | `DataSourceError` | as class | see class |
| `normalize_pages` | Remove running headers/footers and page-number lines from raw page texts. | list[str] -> list[str] | — | as class | see class |

### `Section` — `quant_cn.quant_cn.industry_graph.section_detector` (L4)
- **Purpose:** One located section: its key, the heading-matched start page and the page before the next section (or the chapter end), 1-based, inclusive.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.SectionDetector`, `industry_graph.ParsedReport`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-SD-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `SectionDetector` — `quant_cn.quant_cn.industry_graph.section_detector` (L4)
- **Purpose:** Locate the MD&A chapter (管理层讨论与分析, 第三节 in the 2021 standard; 第二节/第四节 in older or exchange-specific layouts) and the chain sections inside it by heading text, not by number, so SSE, SZSE and BSE layouts all work. A chapter heading must stand on its own line (body text often cites "第三节管理层讨论与分析"). A table-of-contents page (dot leaders, or three or more 第X节 headings) never counts as a chapter start. Only these pages go to later steps (D-102); in the prototype the chapter was 12-19% of a report's text.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.AnnualReportParser`, `industry_graph.GuidanceExtractor` (outlook section, plan 18 ph3).
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-SD-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `find_chapter` | First and last page (1-based, inclusive) of the MD&A chapter. | ReportPages -> tuple[int, int] \| None | — | as class | see class |
| `list_sections` | The MD&A chapter and every chain section found in it. | ReportPages -> list[Section] | — | as class | see class |
| `find_heading_page` | First non-TOC page (1-based) anywhere in the report that carries a section's heading, for reports whose MD&A chapter is missing or named differently. | ReportPages, str -> int \| None | KeyError | `industry_graph.AnnualReportParser` | TC-SD-005 |

### `CounterpartyRow` — `quant_cn.quant_cn.industry_graph.counterparty_table_parser` (L4)
- **Purpose:** One ranked customer or supplier of a top-5 table.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.CounterpartyTable`, `industry_graph.CounterpartyTableParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-CTP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `is_anonymous` | True when the report hides the name ("客户一", "供应商A", "第三名"). | — -> bool | — | as class | see class |

### `CounterpartyTable` — `quant_cn.quant_cn.industry_graph.counterparty_table_parser` (L4)
- **Purpose:** The top-5 customers or suppliers of one report: stated totals and the ranked rows (empty when only the totals sentence is disclosed, as on the SSE main board).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.CounterpartyTableParser`, `industry_graph.ParsedReport`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-CTP-004..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `is_consistent` | Rows complete and their shares add up to the stated total. | — -> bool | — | as class | see class |

### `CounterpartyTableParser` — `quant_cn.quant_cn.industry_graph.counterparty_table_parser` (L4)
- **Purpose:** Parse the "主要销售客户和主要供应商情况" block into a customer and a supplier CounterpartyTable. Three layouts are covered (prototype on 10 FY2025 reports): SZSE (totals as label + value, table in 元 or 千元 with % signs), STAR (totals sentence in 万元, table in 万元 without % and with a related-party column), SSE main board (totals sentence only, no table). Amounts are converted to CNY. Text is expected without running headers (PdfTextExtractor), so a table crossing a page break reads as one block.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.AnnualReportParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-CTP-001..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `parse_tables` | Customer and supplier tables from the block text. | str -> tuple[CounterpartyTable, CounterpartyTable] | — | as class | see class |

### `ParsedReport` — `quant_cn.quant_cn.industry_graph.annual_report_parser` (L4)
- **Purpose:** What the rule-based pass extracts from one annual report.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.AnnualReportParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-ARP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_section` | The section with this key, if located. | str -> Section \| None | — | as class | see class |

### `AnnualReportParser` — `quant_cn.quant_cn.industry_graph.annual_report_parser` (L4)
- **Purpose:** Run the rule-based pass of plan 12 phase 3 on one annual report: read the pages (PdfTextExtractor), locate the MD&A chapter and chain sections (SectionDetector), and parse the top-5 customer and supplier tables (CounterpartyTableParser). Nothing here calls an LLM; the located section pages are what phase 4 sends to DeepSeek.
- **Base:** none. **Depends on (injected):** PdfTextExtractor, SectionDetector, CounterpartyTableParser.
- **Used by:** `research_space`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-ARP-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | PdfTextExtractor, SectionDetector, CounterpartyTableParser -> None | — | callers of the class | — |
| `parse_report` | Read and parse one PDF. | Path -> ParsedReport | `DataSourceError` | as class | see class |
| `parse_pages` | Parse already-read pages (lets callers reuse or synthesise ReportPages). | Path, ReportPages -> ParsedReport | — | as class | see class |

### `LlmReply` — `quant_cn.quant_cn.core.base_llm_client` (L1)
- **Purpose:** One LLM answer as parsed JSON, with the model and token usage, and whether it came from the response cache (a cached reply costs nothing and makes rebuilds deterministic).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.BaseLlmClient`, `data_loading.DeepSeekClient`.
- **Tests:** `tests/data_loading/test_deep_seek_client.py` (TC-DSC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BaseLlmClient` — `quant_cn.quant_cn.core.base_llm_client` (L1)
- **Purpose:** Abstract chat-completion client that returns a JSON object: one system prompt, one user message, an optional model override. Vendors subclass it; extractors depend on this.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `data_loading.DeepSeekClient`, `industry_graph.ApplicationExtractor`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `fetch_json` | Ask the model and return its answer parsed as a JSON object. | str, str, str \| None, Sequence[str] -> LlmReply | `DataSourceError`, `ConfigError` | as class | see class |

### `LlmConfig` — `quant_cn.quant_cn.core.config` (L1)
- **Purpose:** The LLM endpoint used for extraction (D-098): OpenAI-compatible chat completions URL, default model, limits, and the API key, which comes from env DEEPSEEK_API_KEY only.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `data_loading.DeepSeekClient`.
- **Tests:** `tests/core/test_config.py` (TC-C-014..014).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DeepSeekClient` — `quant_cn.quant_cn.data_loading.deep_seek_client` (L3)
- **Purpose:** Call the DeepSeek (OpenAI-compatible) chat-completions endpoint with JSON output and temperature 0 and model reasoning off unless LlmConfig.thinking, paced and retried by RequestPacer. Every reply is cached on disk under `cache_dir/<hash[:2]>/<hash>.json`, keyed by model + system + user + stop, so a re-run costs nothing and gives the same graph (D-098). The key comes from LlmConfig (env only).
- **Base:** BaseLlmClient. **Depends on (injected):** LlmConfig, Clock, Path | None, HttpTransport | None.
- **Used by:** `research_space`.
- **Tests:** `tests/data_loading/test_deep_seek_client.py` (TC-DSC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LlmConfig, Clock, Path \| None, HttpTransport \| None -> None | — | callers of the class | — |
| `fetch_json` | One JSON answer, from the cache when the same request was made before. | str, str, str \| None, Sequence[str] -> LlmReply | `ConfigError`, `DataSourceError` | as class | see class |
| `get_usage` | Calls, local-cache hits, tokens and money spent since construction. | — -> dict[str, float] | — | as class | see class |
| `record_usage` | Append this client's usage so far as one JSON line to the cost ledger. | Path, str -> dict[str, Any] | `OSError` | as class | see class |
| `compute_cost` | CNY cost of one call at the configured peak prices, halved off-peak (Beijing time). | str, int, int, int -> float | — | as class | see class |

### `Evidence` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** A verbatim quote and the page it was found on (after the quote check).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationResult`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ApplicationResult` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** What the model found in one report, after validation: per revenue line the downstream applications (taxonomy node or proposed name, main/secondary, evidence) and customer types; named counterparties with role and evidence; and the items dropped because their quote was not in the text.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationExtractor`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ApplicationExtractor` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** Send the business / industry pages of one report, its revenue lines and the candidate downstream taxonomy nodes to the LLM, and keep only answers whose verbatim quote is found in the supplied pages (whitespace ignored). A quote found on another page than claimed is kept with the page corrected. Unknown node ids become proposals (node_id None). Roles outside ROLES (customer, supplier, partner, competitor, subsidiary, mention) are dropped; competitor mentions are peer evidence (D-102).
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `research_space`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `fetch_applications` | Ask the model about one report and validate the answer against the text. | str, Sequence[tuple[int, str]], Sequence[str], Sequence[tuple[str, str]] -> ApplicationResult | `DataSourceError` | as class | see class |

### `ApplicationItem` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** One downstream application of a revenue line as the LLM returned it.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.LineItem`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `LineItem` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** One revenue line with its applications and customer types as returned.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationReply`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `CounterpartyItem` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** One company named in the text, with its role, as returned.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationReply`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ApplicationReply` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** The whole LLM reply of one report, validated before the quote check.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationExtractor`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `QuoteChecker` — `quant_cn.quant_cn.industry_graph.quote_checker` (L4)
- **Purpose:** Hold the pages sent to an LLM and accept a returned quote only if it occurs verbatim (whitespace ignored) on one of them. The claimed page is preferred; a quote found on another sent page is kept with that page. Also assembles the page-tagged text ("[第N页]") sent to the model, truncated in page order to a character budget, so the checked pages are exactly the sent pages.
- **Base:** none. **Depends on (injected):** Sequence[tuple[int, str]].
- **Used by:** `industry_graph.ApplicationExtractor`, `industry_graph.ValuationExtractor`, `industry_graph.BaseQuotedExtractor`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-QC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Sequence[tuple[int, str]] -> None | — | callers of the class | — |
| `build_prompt_text` | Page-tagged text for the prompt and the pages it contains. | Sequence[tuple[int, str]], int -> tuple[str, list[tuple[int, str]]] | — | as class | see class |
| `find_evidence` | Accept a quote if it occurs on a sent page. | str, int -> Evidence \| None | — | as class | see class |

### `ValuationItem` — `quant_cn.quant_cn.industry_graph.valuation_extractor` (L4)
- **Purpose:** Base of the reply shapes: unknown keys ignored, so a richer reply still validates.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ValuationReply`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-VE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ValuationReply` — `quant_cn.quant_cn.industry_graph.valuation_extractor` (L4)
- **Purpose:** The LLM reply for one broker report, before the quote check: rating, target price, methods (multiple, implied or target, base year), forecasts, comparables, assumptions.
- **Base:** ValuationItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.ValuationExtractor`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-VE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ValuationResult` — `quant_cn.quant_cn.industry_graph.valuation_extractor` (L4)
- **Purpose:** One report's valuation after validation: only quote-checked target price, methods and assumptions; methods carry `multiple_kind` (D-109) and a base year; comparables carry a ts_code when it could be resolved.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ValuationExtractor`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-VE-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ValuationExtractor` — `quant_cn.quant_cn.industry_graph.valuation_extractor` (L4)
- **Purpose:** Extract how a broker values a company (plan 13, D-105, D-109). Pages sent: the first LEAD_PAGES plus every page matching KEYWORDS, within a character budget. Kept: a target price and methods whose quotes are on a sent page; methods with a multiple must have a base year and a multiple_kind of "implied_at_price" or "target" (otherwise dropped); assumptions with a checked quote. Comparables are resolved to ts_codes through an injected name → code map when the report gives no code.
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `research_space`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-VE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `list_pages` | The pages of a report worth sending, as (page number, text). | Sequence[str] -> list[tuple[int, str]] | — | as class | see class |
| `fetch_valuation` | Ask the model about one report and keep only what the text supports. | str, Sequence[tuple[int, str]], Mapping[str, str] \| None -> ValuationResult | `DataSourceError` | as class | see class |

### `QuarterlyNoteItem` — `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` (L4)
- **Purpose:** One fact the LLM found in the notes, before the quote check.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.QuarterlyNoteReply`.
- **Tests:** `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `QuarterlyNoteReply` — `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` (L4)
- **Purpose:** The LLM reply for one quarterly report.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.QuarterlyNoteExtractor`.
- **Tests:** `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `QuarterlyNoteResult` — `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` (L4)
- **Purpose:** The quote-checked facts of one quarterly report.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.QuarterlyNoteExtractor`.
- **Tests:** `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `QuarterlyNoteExtractor` — `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` (L4)
- **Purpose:** Q1 and Q3 reports carry no business chapter; their only narrative is the "主要会计数据、 财务指标发生变动的情况及原因" table and the "其他提醒事项" note. `list_note_pages` cuts those pages (from the first NOTE_START page up to the statements), `compute_note_chars` measures the text so the caller can skip near-empty notes, and `fetch_notes` asks the LLM for orders and contracts, customers won, capacity changes, profit drivers and new products, keeping only items whose verbatim quote is on a sent page and whose kind is in KINDS (plan 12 phase 4, user request 2026-11-07).
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `list_note_pages` | The narrative pages (1-based) of a quarterly report. | Sequence[str] -> list[tuple[int, str]] | — | as class | see class |
| `compute_note_chars` | Characters of real note text: "□适用 √不适用" placeholders and whitespace removed. | Sequence[tuple[int, str]] -> int | — | as class | see class |
| `fetch_notes` | Ask the model about one report's notes and validate the answer against the text. | str, str, Sequence[tuple[int, str]] -> QuarterlyNoteResult | `DataSourceError` | as class | see class |

### `LenientItem` — `quant_cn.quant_cn.industry_graph.lenient_item` (L4)
- **Purpose:** Base for one item of an LLM JSON reply: unknown keys ignored; every float field also accepts text, taking its first number after removing thousands separators; text with no number becomes None.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.GuidanceItem`, `industry_graph.ContractItem`, `industry_graph.QuotedItem`.
- **Tests:** `tests/industry_graph/test_lenient_item.py` (TC-LI-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `GuidanceItem` — `quant_cn.quant_cn.industry_graph.guidance_extractor` (L4)
- **Purpose:** One guidance statement the LLM found (metric, metric_class, segment, period, basis, value_low / value_high, unit, base_period, kind, condition, quote, page), before the checks.
- **Base:** LenientItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.GuidanceReply`.
- **Tests:** `tests/industry_graph/test_guidance_extractor.py` (TC-GE-003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `GuidanceReply` — `quant_cn.quant_cn.industry_graph.guidance_extractor` (L4)
- **Purpose:** The LLM reply for one guidance document.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.GuidanceExtractor`.
- **Tests:** `tests/industry_graph/test_guidance_extractor.py` (TC-GE-003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `GuidanceResult` — `quant_cn.quant_cn.industry_graph.guidance_extractor` (L4)
- **Purpose:** The checked guidance items of one document: period normalized (YYYY, YYYYH1, YYYYQ3, YYYY-YYYY), evidence in place of quote / page.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.GuidanceExtractor`.
- **Tests:** `tests/industry_graph/test_guidance_extractor.py` (TC-GE-002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `GuidanceExtractor` — `quant_cn.quant_cn.industry_graph.guidance_extractor` (L4)
- **Purpose:** Turn a company document into quote-checked quantitative guidance rows, one prompt per doc type (annual_plan: outlook heading to MD&A end; ir_record: all pages; incentive_plan: 业绩考核 pages and the next). Kept only with a found quote, a known kind, a value, and a period not before the announcement year minus one.
- **Base:** none. **Depends on (injected):** BaseLlmClient, SectionDetector, int, Mapping[str, str] \| None.
- **Used by:** `lake` meta/runs/guidance_pilot.py.
- **Tests:** `tests/industry_graph/test_guidance_extractor.py` (TC-GE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, SectionDetector, int, Mapping[str, str] \| None -> None | — | callers of the class | — |
| `list_source_pages` | The pages of one document to send, 1-based, in order. | str, ReportPages -> list[tuple[int, str]] | `DataSourceError` | as class | TC-GE-001 |
| `fetch_guidance` | Ask the model for one document's guidance and check every item against the text. | str, str, str, Sequence[tuple[int, str]] -> GuidanceResult | `DataSourceError` | as class | TC-GE-002, TC-GE-003 |

### `ContractItem` — `quant_cn.quant_cn.industry_graph.contract_extractor` (L4)
- **Purpose:** One contract, bid win or period order total the LLM found (kind, counterparty, project, amount, unit, currency, share_of_revenue, term, status, segment, period, is_framework, quote, page), before the checks.
- **Base:** LenientItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.ContractReply`.
- **Tests:** `tests/industry_graph/test_contract_extractor.py` (TC-CEX-002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ContractReply` — `quant_cn.quant_cn.industry_graph.contract_extractor` (L4)
- **Purpose:** The LLM reply for one announcement.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ContractExtractor`.
- **Tests:** `tests/industry_graph/test_contract_extractor.py` (TC-CEX-002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ContractResult` — `quant_cn.quant_cn.industry_graph.contract_extractor` (L4)
- **Purpose:** The checked contract rows of one announcement; amount_value = amount times the unit's multiplier (UNIT_SCALES).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ContractExtractor`.
- **Tests:** `tests/industry_graph/test_contract_extractor.py` (TC-CEX-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ContractExtractor` — `quant_cn.quant_cn.industry_graph.contract_extractor` (L4)
- **Purpose:** Turn a 重大合同 / 中标 / 经营数据 announcement into quote-checked rows: single contracts or bids with status 预中标 / 中标 / 签约 / 进展 / 终止, or period order totals; amounts scaled by the unit word; framework agreements flagged.
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str \| None.
- **Used by:** `lake` meta/runs/guidance_pilot.py.
- **Tests:** `tests/industry_graph/test_contract_extractor.py` (TC-CEX-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `fetch_contracts` | Ask the model about one announcement and check every row against the text. | str, str, Sequence[tuple[int, str]] -> ContractResult | `DataSourceError` | as class | TC-CEX-001, TC-CEX-002 |


### `QuotedItem` — `quant_cn.quant_cn.industry_graph.base_quoted_extractor` (L4)
- **Purpose:** Base of one reply item of a plan 28 extractor: the subclass fields plus the verbatim quote and the page it is on.
- **Base:** LenientItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.BaseQuotedExtractor`, `industry_graph.InquiryCounterpartyItem`, `industry_graph.InquiryCustomerExtractor`.
- **Tests:** `tests/industry_graph/test_base_quoted_extractor.py` (TC-BQE-002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `QuotedResult` — `quant_cn.quant_cn.industry_graph.base_quoted_extractor` (L4)
- **Purpose:** The checked items of one document: items with evidence {quote, page}, dropped, tokens, cached, pages sent.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.BaseQuotedExtractor`.
- **Tests:** `tests/industry_graph/test_base_quoted_extractor.py` (TC-BQE-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BaseQuotedExtractor` — `quant_cn.quant_cn.industry_graph.base_quoted_extractor` (L4)
- **Purpose:** Base of the plan 28 phase 2 extractors (D-161 update 6). Sends the chosen pages with a header and the subclass's prompt file, validates each reply item with the subclass's item model (a malformed item is dropped, not the reply), keeps it when its quote is on a sent page, is_item_anchored holds and check_item accepts it.
- **Base:** ABC. **Depends on (injected):** BaseLlmClient.
- **Used by:** `industry_graph.InquiryCustomerExtractor`, `industry_graph.IrCustomerExtractor`, `industry_graph.DealExtractor`, `industry_graph.OperatingDataExtractor`, `industry_graph.BuybackTermsExtractor`.
- **Tests:** `tests/industry_graph/test_base_quoted_extractor.py` (TC-BQE-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `item_model` | (abstract property) the pydantic model of one reply item | — -> type[QuotedItem] | — | as class | TC-BQE-001 |
| `list_pages` | (abstract) the pages of a document to send | Sequence[str] -> list[tuple[int, str]] | — | as class | TC-BQE-003 |
| `check_item` | (abstract) stored fields of one quote-checked item, or None to drop it | QuotedItem -> dict[str, Any] \| None | — | as class | TC-BQE-001 |
| `fetch_items` | Ask the model about one document and check every item against the text. | Mapping[str, str], Sequence[tuple[int, str]] -> QuotedResult | `DataSourceError` | as class | TC-BQE-001, TC-BQE-002 |
| `build_checked_text` | the part of a sent page a quote may come from (default the whole page) | str -> str | — | as class | TC-BQE-004 |
| `is_item_anchored` | whether a quote-checked item is tied to its quote (default True) | QuotedItem, str -> bool | — | as class | TC-BQE-005 |
| `list_top_pages` | (static) the pages with the most pattern hits, at most max_pages, in page order | Sequence[str], re.Pattern[str], int -> list[tuple[int, str]] | — | as class | TC-BQE-003 |

### `InquiryCounterpartyItem` — `quant_cn.quant_cn.industry_graph.inquiry_customer_extractor` (L4)
- **Purpose:** One customer or supplier named in an inquiry reply (role, name, alias, period, rank, amount, unit, share, share_base, product, region, is_related_party, quote, page), before the checks.
- **Base:** QuotedItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.InquiryCustomerExtractor`.
- **Tests:** `tests/industry_graph/test_inquiry_customer_extractor.py` (TC-ICE-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `InquiryCustomerExtractor` — `quant_cn.quant_cn.industry_graph.inquiry_customer_extractor` (L4)
- **Purpose:** Turn an exchange inquiry reply into quote-checked customer and supplier rows (plan 28 ph2): real names behind 客户一…, amounts, shares, products, region of foreign suppliers. Sends the MAX_PAGES pages with the most customer / supplier words; is_named (CounterpartyName) False for numbered (客户一), hidden (某) or class (境外客户) names; a row whose name and alias are not in its quote is dropped.
- **Base:** BaseQuotedExtractor. **Depends on (injected):** BaseLlmClient.
- **Used by:** `industry_graph.ProspectusExtractor`, `lake` (meta/runs/plan28_pilot.py).
- **Tests:** `tests/industry_graph/test_inquiry_customer_extractor.py` (TC-ICE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `item_model` | InquiryCounterpartyItem | — -> type[QuotedItem] | — | as class | TC-ICE-001 |
| `list_pages` | the MAX_PAGES pages with the most customer / supplier words | Sequence[str] -> list[tuple[int, str]] | — | as class | TC-ICE-002 |
| `is_item_anchored` | name or alias in the quote | QuotedItem, str -> bool | — | as class | TC-ICE-003 |
| `check_item` | known role and a name; adds is_named | QuotedItem -> dict[str, Any] \| None | — | as class | TC-ICE-001 |

### `CounterpartyName` — `quant_cn.quant_cn.industry_graph.counterparty_name` (L4)
- **Purpose:** The two checks plan 28 applies to every counterparty name an LLM returns (D-161 update 8): is_named (not a number like 客户一 / 供应商A / 客商9, not hidden with 某, not a class like 头部车企; a bare letter name such as GE is a real name) and is_in_text (name or alias in a text, whitespace and case ignored, also suffix-stripped or as its first 4 characters).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.InquiryCustomerExtractor`, `industry_graph.IrCustomerExtractor`, `industry_graph.CompanyEdgeBuilder`.
- **Tests:** `tests/industry_graph/test_counterparty_name.py` (TC-CPN-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `is_named` | (static) the name identifies one counterparty (not numbered, ranked, hidden, a class or a placeholder) | str -> bool | — | InquiryCustomerExtractor.check_item, IrCustomerExtractor.check_item, CompanyEdgeBuilder | TC-CPN-001, TC-CPN-003 |
| `is_in_text` | (static) the name, alias or short form occurs in the text | str, str \| None, str -> bool | — | InquiryCustomerExtractor.is_item_anchored, IrCustomerExtractor.is_item_anchored | TC-CPN-002 |

### `EntityMatch` — `quant_cn.quant_cn.industry_graph.entity_resolver` (L4)
- **Purpose:** Where one counterparty name resolved to (name, entity_id "a:<ts_code>" / alias id / "x:<key>", ts_code, method alias / full / short / prefix / code / unresolved, is_group_member).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.EntityResolver`.
- **Tests:** `tests/industry_graph/test_entity_resolver.py` (TC-ER-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `EntityResolver` — `quant_cn.quant_cn.industry_graph.entity_resolver` (L4)
- **Purpose:** Give every customer / supplier / partner name one entity id across documents and periods (plan 28 ph3, D-161 update 9). Key = whitespace, punctuation, case, brackets and legal suffix folded; lookup: alias map, A-share full names, A-share short names current and former (ST marks removed), the same without a bracketed region, then an A-share short name of ≥ 4 characters as prefix (group member). Ambiguous hits do not resolve. Group tails (及其关联方, 子公司4, 分公司) are cut and mark a member. Unresolved names get "x:<key>".
- **Base:** none. **Depends on (injected):** — (name lists and alias map passed in).
- **Used by:** `lake` (meta/runs/plan28_entities.py), `industry_graph.CompanyEdgeBuilder`, `industry_graph.GameCompanyBuilder`.
- **Tests:** `tests/industry_graph/test_entity_resolver.py` (TC-ER-001..008).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire name lists (full, short in use, former), aliases and member alias names | Iterable[tuple[str, str]], Iterable[tuple[str, str]], Mapping[str, str] \| None, Iterable[str], Iterable[tuple[str, str]] -> None | — | callers of the class | — |
| `build_key` | (static) the lookup key of a name | str -> str | — | as class | TC-ER-003 |
| `find_entity` | resolve one name | str -> EntityMatch | — | as class | TC-ER-001, TC-ER-002 |
| `find_by_code` | confirm a proposed A-share code: known, and a short name (share class removed) or full name starts with the name; with is_member a known code is enough (member_code) | str, str, bool -> EntityMatch \| None | — | as class | TC-ER-004, TC-ER-007 |
| `find_by_alias` | resolve a name through an alias proposal, checked by rule: canonical name, proposed A-share code, or a member of a parent that resolves by full / short name (member_code) | str, str, str \| None, str \| None -> EntityMatch \| None | — | `industry_graph.GameCompanyBuilder` | TC-ER-008 |

### `AliasItem` — `quant_cn.quant_cn.industry_graph.entity_alias_extractor` (L4)
- **Purpose:** One reply row of EntityAliasExtractor (name, canonical, kind, is_member, listed, parent), before the checks.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.EntityAliasExtractor`.
- **Tests:** `tests/industry_graph/test_entity_alias_extractor.py` (TC-EAX-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `EntityAlias` — `quant_cn.quant_cn.industry_graph.entity_alias_extractor` (L4)
- **Purpose:** The entity one name stands for as the model proposed it (name, canonical, kind, is_member, listed code checked for format only, parent short name).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.EntityAliasExtractor`.
- **Tests:** `tests/industry_graph/test_entity_alias_extractor.py` (TC-EAX-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `EntityAliasExtractor` — `quant_cn.quant_cn.industry_graph.entity_alias_extractor` (L4)
- **Purpose:** Ask the model which entity each of a batch of counterparty names stands for (plan 28 ph3, D-161 update 9): common short name, kind (company / government / university / institute / hospital / person / generic / unknown), member of a group, security code hint. Keeps rows whose name was asked, kind known, canonical not empty; a malformed code becomes None. The caller resolves the canonical name against the A-share list itself.
- **Base:** none. **Depends on (injected):** BaseLlmClient.
- **Used by:** `lake` (meta/runs/plan28_entities.py).
- **Tests:** `tests/industry_graph/test_entity_alias_extractor.py` (TC-EAX-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, str \| None -> None | — | callers of the class | — |
| `fetch_aliases` | the entity of every name in one batch | Sequence[tuple[str, str]] -> list[EntityAlias] | `DataSourceError` | as class | TC-EAX-001, TC-EAX-002 |

### `EdgeItem` — `quant_cn.quant_cn.industry_graph.base_edge_reader` (L4)
- **Purpose:** One raw edge a document states (name, relation, stage, period, known_on, amount, share, share_base, product, quote, page), before resolution.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.BaseEdgeReader`, `industry_graph.CounterpartyEdgeReader`, `industry_graph.TopFiveEdgeReader`, `industry_graph.DealEdgeReader`, `industry_graph.CompanyEdgeBuilder`.
- **Tests:** `tests/industry_graph/test_edge_readers.py` (TC-BER-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BaseEdgeReader` — `quant_cn.quant_cn.industry_graph.base_edge_reader` (L4)
- **Purpose:** Base of the plan 28 ph4 readers that list the raw edges of one label-store row; build_period parses an item's own period text.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `industry_graph.CounterpartyEdgeReader`, `industry_graph.TopFiveEdgeReader`, `industry_graph.DealEdgeReader`, `industry_graph.CompanyEdgeBuilder`.
- **Tests:** `tests/industry_graph/test_edge_readers.py` (TC-BER-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_items` | (abstract) the raw edges of one label-store row | Mapping[str, Any] -> list[EdgeItem] | — | as class | TC-CER-001, TC-TFR-001, TC-DER-001 |
| `build_period` | (static) period end of an item's own period text | Any -> str \| None | — | as class | TC-BER-001 |

### `CounterpartyEdgeReader` — `quant_cn.quant_cn.industry_graph.counterparty_edge_reader` (L4)
- **Purpose:** Raw edges of a counterparty-list row (plan 28 sets under items, applications under counterparties); roles mapped, subsidiary → holds; IR Q&A item date from dates[page-1].
- **Base:** BaseEdgeReader. **Depends on (injected):** —.
- **Used by:** `lake` (meta/runs/plan28_edges.py).
- **Tests:** `tests/industry_graph/test_edge_readers.py` (TC-CER-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | set the payload list key | str -> None | — | callers of the class | — |
| `list_items` | the named counterparties of one row | Mapping[str, Any] -> list[EdgeItem] | — | as class | TC-CER-001, TC-CER-002 |

### `TopFiveEdgeReader` — `quant_cn.quant_cn.industry_graph.top_five_edge_reader` (L4)
- **Purpose:** Raw edges of the rule-parsed annual top-5 customer and supplier tables (named rows; share of revenue / purchases).
- **Base:** BaseEdgeReader. **Depends on (injected):** —.
- **Used by:** `lake` (meta/runs/plan28_edges.py).
- **Tests:** `tests/industry_graph/test_edge_readers.py` (TC-TFR-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_items` | the named top-5 rows of one annual report | Mapping[str, Any] -> list[EdgeItem] | — | as class | TC-TFR-001 |

### `DealEdgeReader` — `quant_cn.quant_cn.industry_graph.deal_edge_reader` (L4)
- **Purpose:** Raw invests_in edges of outward deals (new company, capital increase, stake purchase, acquisition, JV, fund) with status and stake.
- **Base:** BaseEdgeReader. **Depends on (injected):** —.
- **Used by:** `lake` (meta/runs/plan28_edges.py).
- **Tests:** `tests/industry_graph/test_edge_readers.py` (TC-DER-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_items` | the outward deals of one row | Mapping[str, Any] -> list[EdgeItem] | — | as class | TC-DER-001 |

### `CompanyEdgeBuilder` — `quant_cn.quant_cn.industry_graph.company_edge_builder` (L4)
- **Purpose:** company_edge rows: one per stated edge, counterparty resolved (EntityResolver), oriented seller → buyer, item period / known_on, non-flow shares cleared (plan 28 ph4, D-161 update 7).
- **Base:** none. **Depends on (injected):** EntityResolver, BaseEdgeReader (readers).
- **Used by:** `lake` (meta/runs/plan28_edges.py).
- **Tests:** `tests/industry_graph/test_company_edge_builder.py` (TC-CEB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire resolver, readers, skipped names | EntityResolver, Mapping[str, BaseEdgeReader], Collection[str] -> None | — | callers of the class | — |
| `build_edges` | the edges of the rows of one label set | str, DataFrame -> DataFrame (EDGE_COLUMNS) | `KeyError` | as class | TC-CEB-001..003 |

### `EdgeSpanBuilder` — `quant_cn.quant_cn.industry_graph.edge_span_builder` (L4)
- **Purpose:** edge_span rows: observations of one (src, dst, kind) joined into first / last seen, stage path, status active / ended / denied / silent, shares and amounts per period and base; point in time with as_of (plan 28 ph4, D-161 update 7).
- **Base:** none. **Depends on (injected):** DateCodec.
- **Used by:** `lake` (meta/runs/plan28_edges.py).
- **Tests:** `tests/industry_graph/test_edge_span_builder.py` (TC-ESB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire DateCodec | DateCodec -> None | — | callers of the class | — |
| `build_spans` | the spans of all edges as known on a date | DataFrame, str \| None -> DataFrame (SPAN_COLUMNS) | `SchemaError` | as class | TC-ESB-001..003 |

### `GraphBuilder` — `quant_cn.quant_cn.industry_graph.graph_builder` (L4)
- **Purpose:** Rebuild the company graph tables (plan 28 ph4, D-161 updates 7, 9–11): each label set with a reader is read from the LabelStore, edges built by CompanyEdgeBuilder with an EntityResolver over A-share names and the entity_map (aliases, member names, kinds generic / unknown / person skipped), joined into spans by EdgeSpanBuilder; writes company_edge (sorted src, dst, known_on, doc_key) and edge_span. No LLM call.
- **Base:** none. **Depends on (injected):** LabelStore, GraphStore, BaseEdgeReader (readers), EdgeSpanBuilder.
- **Used by:** `cli.DocumentCommands`.
- **Tests:** `tests/industry_graph/test_graph_builder.py` (TC-GB-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LabelStore, GraphStore, Mapping[str, BaseEdgeReader], EdgeSpanBuilder, CompanyPeriodBuilder -> None | — | callers of the class | — |
| `build_resolver` | resolver over A-share names and entity_map, plus names to skip | NamePairs ×3 -> tuple[EntityResolver, set[str]] | — | as class | TC-GB-001 |
| `build` | rebuild company_edge, edge_span and company_period | NamePairs ×3, str \| None -> dict[str, int] | `SchemaError`, `LakeError` | as class | TC-GB-001..004 |

### `CompanyPeriodBuilder` — `quant_cn.quant_cn.industry_graph.company_period_builder` (L4)
- **Purpose:** Build company_period, the company leaf of plan 28 (D-161; CompanyCard of D-104 per period): one row per (company, period, label set, document) over every set of the LabelStore with doc type, known_on and n_items (length of the payload's first list among items / counterparties / claims / lines); the payload stays in the LabelStore. Sorted ts_code, period, label_set, known_on, doc_key.
- **Base:** none. **Depends on (injected):** LabelStore.
- **Used by:** `industry_graph.GraphBuilder`, `cli.DocumentCommands`.
- **Tests:** `tests/industry_graph/test_company_period_builder.py` (TC-CPB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire LabelStore | LabelStore -> None | — | callers of the class | — |
| `build_leaf` | the leaf rows of all companies | list[str] \| None -> DataFrame (LEAF_COLUMNS) | `SchemaError` | as class | TC-CPB-001, TC-CPB-002 |

### `GraphQuery` — `quant_cn.quant_cn.industry_graph.graph_query` (L4)
- **Purpose:** Plan 28 point-in-time questions from the GraphStore tables, never using a fact before it was public: find_leaf (latest period per label set among rows known on as_of), list_spans (spans of the company's edges rebuilt from observations known on as_of), list_timeline (company_period rows and the company's stated edges ordered by known_on in [start, end]); industry nodes from node_member / node_edge / node_lineage as built (plan 28 ph4d).
- **Base:** none. **Depends on (injected):** GraphStore, EdgeSpanBuilder, DateCodec.
- **Used by:** (none yet; plan 28 ph5 app).
- **Tests:** `tests/industry_graph/test_graph_query.py` (TC-GQ-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | GraphStore, EdgeSpanBuilder, DateCodec -> None | — | callers of the class | — |
| `find_leaf` | the company's label rows as known on a date, latest period per set | str, str -> DataFrame | `SchemaError` | as class | TC-GQ-001 |
| `list_spans` | spans of the company's edges as known on a date | str, str -> DataFrame (SPAN_COLUMNS) | `SchemaError` | as class | TC-GQ-002 |
| `list_timeline` | labels and edge observations ordered by known_on | str, str, str -> DataFrame (TIMELINE_COLUMNS) | `SchemaError` | as class | TC-GQ-003 |
| `list_node_members` | companies of a segment in a period by sales | str, str -> DataFrame (MEMBER_COLUMNS) | `SchemaError` | as class | TC-GQ-004 |
| `list_node_neighbours` | upstream / downstream segments of a node by weight | str, str, str -> DataFrame (NEIGHBOUR_COLUMNS) | `SchemaError` | as class | TC-GQ-005 |
| `list_node_history` | members, sales and evidenced edges per annual period | str -> DataFrame (HISTORY_COLUMNS) | — | as class | TC-GQ-006 |
| `list_node_lineage` | node_lineage rows naming the node | str -> DataFrame | — | as class | TC-GQ-006 |

### `NodeMemberBuilder` — `quant_cn.quant_cn.industry_graph.node_member_builder` (L4)
- **Purpose:** Build node_member (plan 28 ph3b-1, D-161): for each company and period, the taxonomy nodes its 主营构成 product lines map to through ProductMatcher, with segment, sector, sales and weight in revenue (over the kept lines; totals, adjustments and sub-lines of a parent line dropped; compound lines split equally; sector-fallback lines get their segment); unmatched and generic lines kept with node_id None. known_on = the annual report's date when given, else period end + 120 days.
- **Base:** none. **Depends on (injected):** ProductMatcher, ProductTaxonomy, DateCodec.
- **Used by:** `cli.DocumentCommands` (`build-graph`).
- **Tests:** `tests/industry_graph/test_node_member_builder.py` (TC-NMB-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ProductMatcher, ProductTaxonomy, DateCodec -> None | — | callers of the class | — |
| `build_members` | the node members of every company and period in a revenue table | DataFrame, Mapping[str, list[str]], Mapping[tuple[str, str], str] \| None -> DataFrame (MEMBER_COLUMNS) | — | as class | TC-NMB-001..003 |

### `NodeStatsBuilder` — `quant_cn.quant_cn.industry_graph.node_stats_builder` (L4)
- **Purpose:** Turn node_member rows into the material Opus curates nodes from (plan 28 ph3b-2): build_stats (per segment: companies, sales, top companies), build_diff (two periods: counts, sales change, joined / left companies), build_unmapped (unmatched lines by the company's main sector and item).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `lake` (meta/runs/plan28_nodes.py).
- **Tests:** `tests/industry_graph/test_node_stats_builder.py` (TC-NSB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_stats` | per-segment statistics of one period | DataFrame, str -> DataFrame (STAT_COLUMNS) | — | as class | TC-NSB-001, TC-NSB-003 |
| `build_diff` | per-segment change between two periods | DataFrame, str, str -> DataFrame (DIFF_COLUMNS) | — | as class | TC-NSB-002, TC-NSB-003 |
| `build_unmapped` | unmatched revenue lines by sector and item | DataFrame, str -> DataFrame (UNMAPPED_COLUMNS) | — | as class | TC-NSB-003 |

### `TaxonomyChange` — `quant_cn.quant_cn.industry_graph.taxonomy_change_set` (L4)
- **Purpose:** One change of a taxonomy version (plan 28 ph3b-4): upsert a node (new, or name / segment / parent of an existing one; aliases added, drop_aliases removed; optional sw_l3 codes) or retire a node into a successor; kind and split_from feed the lineage; sector for a new node.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.TaxonomyChangeSet`, `industry_graph.ProductTaxonomy`, `industry_graph.NodeLineageBuilder`.
- **Tests:** `tests/industry_graph/test_taxonomy_change_set.py` (TC-TCS-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `node_id` | (property) the id the change is about | — -> str | — | as class | TC-TCS-001 |

### `TaxonomyChangeSet` — `quant_cn.quant_cn.industry_graph.taxonomy_change_set` (L4)
- **Purpose:** One accepted taxonomy version (plan 28 ph3b-4, D-161): changes Opus proposed and the user accepted, effective from effective_period; stored as config/industry_chain/_changes/<version>.yaml and applied in name order on top of the v0 files.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ProductTaxonomy`, `industry_graph.NodeLineageBuilder`, `cli.DocumentCommands`.
- **Tests:** `tests/industry_graph/test_taxonomy_change_set.py` (TC-TCS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_all` | (classmethod) every version under folder/_changes, in name order | Path -> list[TaxonomyChangeSet] | `ConfigError` | as class | TC-TCS-001, TC-TCS-002 |

### `NodeLineageBuilder` — `quant_cn.quant_cn.industry_graph.node_lineage_builder` (L4)
- **Purpose:** node_lineage rows (plan 28 ph3b-4): compare the taxonomy before and after each accepted change — new / split (from the split source), rename (old → new name), move (segment change), alias (+added -dropped), merge / retire (to the successor); a missing successor or a retire loop raises ConfigError.
- **Base:** none. **Depends on (injected):** — (v0 folder path).
- **Used by:** `cli.DocumentCommands` (`build-graph`).
- **Tests:** `tests/industry_graph/test_node_lineage_builder.py` (TC-NLB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | the v0 folder | Path -> None | — | callers of the class | — |
| `build_lineage` | lineage rows of every version, in order | Sequence[TaxonomyChangeSet] -> DataFrame (LINEAGE_COLUMNS) | `ConfigError` | as class | TC-NLB-001, TC-NLB-002 |

### `NodeEdgeBuilder` — `quant_cn.quant_cn.industry_graph.node_edge_builder` (L4)
- **Purpose:** node_edge (plan 28 ph4d, D-161 update 18): one row per year (YYYY1231), supplier segment, buyer segment and kind (sales / invests). Evidence = company_edge rows between two A-share companies, one observation per (year, src, dst, kind); each side spread over its node_member segment weights (annual of the year, else interim, else latest earlier, else earliest later); weight = Σ w_src × w_dst. Prior = taxonomy edges upstream_of / component_of / used_in / uses_material (reversed) mapped to segments; prior-only pairs get weight-0 rows in every year with members. as_of drops later edges and members.
- **Base:** none. **Depends on (injected):** ProductTaxonomy, DateCodec.
- **Used by:** `cli.DocumentCommands` (`build-graph`).
- **Tests:** `tests/industry_graph/test_node_edge_builder.py` (TC-NEB-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | taxonomy and date codec | ProductTaxonomy, DateCodec -> None | — | callers of the class | — |
| `build_node_edges` | node_edge from company_edge and node_member | DataFrame, DataFrame, str \| None -> DataFrame (NODE_EDGE_COLUMNS, sorted by period, kind, src_node, dst_node) | `SchemaError` (bad as_of) | as class | TC-NEB-001..004 |

### `GameCompanyBuilder` — `quant_cn.industry_graph.game_company_builder` (L4)
- **Purpose:** Link every approved game (dataset `game_license`) to the companies behind it (plan 31 ph2): one row per (approval, role operator / publisher). A holder resolves by rule (full / short name, or prefix when no proposal contradicts it) or through its model proposal in the `game_alias` table (`EntityResolver.find_by_alias`, e.g. 上海巨人网络科技 → 巨人网络 as a group member). Publishing houses (出版 / 音像) get method publishing_house; known_on = the list's publication date.
- **Base:** none. **Depends on (injected):** EntityResolver, Mapping[str, Mapping[str, Any]] (alias proposals).
- **Used by:** `cli.DocumentCommands` (`build-graph`).
- **Tests:** `tests/industry_graph/test_game_company_builder.py` (TC-GCB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | resolver and alias proposals | EntityResolver, Mapping[str, Mapping[str, Any]] -> None | — | callers of the class | — |
| `build_links` | one row per (approval, role) with the resolved company | DataFrame -> DataFrame (GAME_COMPANY_COLUMNS) | — | as class | TC-GCB-001, TC-GCB-002 |
| `list_unresolved` | holders without a company, most games first | DataFrame -> DataFrame (UNRESOLVED_COLUMNS) | — | as class | TC-GCB-002 |

### `IrCounterpartyItem` — `quant_cn.quant_cn.industry_graph.ir_customer_extractor` (L4)
- **Purpose:** One customer, supplier or partner the company names in an IR answer or meeting record (name, role, product, stage, detail, quote, page), before the checks.
- **Base:** QuotedItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.IrCustomerExtractor`.
- **Tests:** `tests/industry_graph/test_ir_customer_extractor.py` (TC-IRC-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `IrCustomerExtractor` — `quant_cn.quant_cn.industry_graph.ir_customer_extractor` (L4)
- **Purpose:** Turn IR Q&A (one 问 / 答 pair per page) or an IR meeting record into quote-checked customer / supplier / partner rows with the stage reached (contact, sample, qualified, designated, small_batch, volume, ended, denied). Only the answer of a Q&A page may be quoted. Unnamed rows (CounterpartyName.is_named) are dropped; the name must be in the quote, or the quote refers back (该公司, 上述, 您所说) and the name is on the page.
- **Base:** BaseQuotedExtractor. **Depends on (injected):** BaseLlmClient.
- **Used by:** `industry_graph.BrokerCustomerExtractor`, `lake` (meta/runs/plan28_pilot.py).
- **Tests:** `tests/industry_graph/test_ir_customer_extractor.py` (TC-IRC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `item_model` | IrCounterpartyItem | — -> type[QuotedItem] | — | as class | TC-IRC-001 |
| `list_pages` | the MAX_PAGES pages with the most customer / supply-chain words | Sequence[str] -> list[tuple[int, str]] | — | as class | TC-IRC-002 |
| `build_checked_text` | the answer part of a Q&A page | str -> str | — | as class | TC-IRC-001 |
| `is_item_anchored` | name in the quote, or referred back and on the page | QuotedItem, str -> bool | — | as class | TC-IRC-003 |
| `check_item` | known role and stage and a real name | QuotedItem -> dict[str, Any] \| None | — | as class | TC-IRC-001, TC-IRC-003 |

### `ProspectusExtractor` — `quant_cn.quant_cn.industry_graph.prospectus_extractor` (L4)
- **Purpose:** Turn an IPO prospectus into quote-checked rows of its named top customers and suppliers per reported year and its named competitors / comparable companies; InquiryCustomerExtractor with its own prompt, ROLES (adds competitor), page words and MAX_PAGES.
- **Base:** InquiryCustomerExtractor. **Depends on (injected):** BaseLlmClient.
- **Used by:** `lake` (meta/runs/plan28_pilot.py).
- **Tests:** `tests/industry_graph/test_prospectus_extractor.py` (TC-PRE-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DealItem` — `quant_cn.quant_cn.industry_graph.deal_extractor` (L4)
- **Purpose:** One investment, acquisition, disposal or restructuring the company announces (kind, target, target_business, counterparty, stake, amount, unit, is_related_party, status, quote, page), before the checks.
- **Base:** QuotedItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.DealExtractor`.
- **Tests:** `tests/industry_graph/test_deal_extractor.py` (TC-DEX-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DealExtractor` — `quant_cn.quant_cn.industry_graph.deal_extractor` (L4)
- **Purpose:** Turn an outside-investment announcement or a restructuring report into quote-checked deal rows: kind (KINDS), target and its business, counterparty, stake, amount, status (proposed / approved / completed / terminated). Finance / invest edges of the chain graph.
- **Base:** BaseQuotedExtractor. **Depends on (injected):** BaseLlmClient.
- **Used by:** `lake` (meta/runs/plan28_pilot.py).
- **Tests:** `tests/industry_graph/test_deal_extractor.py` (TC-DEX-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `item_model` | DealItem | — -> type[QuotedItem] | — | as class | TC-DEX-001 |
| `list_pages` | the MAX_PAGES pages with the most deal words | Sequence[str] -> list[tuple[int, str]] | — | as class | TC-DEX-002 |
| `check_item` | known kind and status and a target | QuotedItem -> dict[str, Any] \| None | — | as class | TC-DEX-001 |

### `OperatingDataItem` — `quant_cn.quant_cn.industry_graph.operating_data_extractor` (L4)
- **Purpose:** One operating figure of the announcement's own period (metric_class, metric, product, segment, period, value, unit, yoy, quote, page), before the checks.
- **Base:** QuotedItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.OperatingDataExtractor`.
- **Tests:** `tests/industry_graph/test_operating_data_extractor.py` (TC-ODX-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `OperatingDataExtractor` — `quant_cn.quant_cn.industry_graph.operating_data_extractor` (L4)
- **Purpose:** Turn a 主要经营数据 announcement into quote-checked figures of its own period: revenue, output, sales volume, price, orders, backlog, capacity per product, channel or region, with yoy. Covers volumes and prices, which ContractExtractor's period totals do not.
- **Base:** BaseQuotedExtractor. **Depends on (injected):** BaseLlmClient.
- **Used by:** `lake` (meta/runs/plan28_pilot.py).
- **Tests:** `tests/industry_graph/test_operating_data_extractor.py` (TC-ODX-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `item_model` | OperatingDataItem | — -> type[QuotedItem] | — | as class | TC-ODX-001 |
| `list_pages` | the MAX_PAGES pages with the most figure words | Sequence[str] -> list[tuple[int, str]] | — | as class | TC-ODX-002 |
| `check_item` | known metric class and a metric | QuotedItem -> dict[str, Any] \| None | — | as class | TC-ODX-001 |

### `BuybackTermsItem` — `quant_cn.quant_cn.industry_graph.buyback_terms_extractor` (L4)
- **Purpose:** The terms of one buyback or 增持 plan as the model read them (kind, purpose, holder_type, holders, funding, loan_bank, loan_amount / loan_unit, amount_low / amount_high / amount_unit, shares and ratio range, price_cap, period_months, method, quote, page), before the checks.
- **Base:** QuotedItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.BuybackTermsExtractor`.
- **Tests:** `tests/industry_graph/test_buyback_terms_extractor.py` (TC-BTX-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BuybackTermsExtractor` — `quant_cn.quant_cn.industry_graph.buyback_terms_extractor` (L4)
- **Purpose:** Turn a buyback plan (回购方案 / 预案 / 回购报告书) or a holder 增持计划 announcement into quote-checked terms (plan 32 ph2, D-169). Amounts are scaled to yuan in code from the stated unit; labels outside the allowed lists become 其他; the other kind's fields are emptied; an item needs an amount, share or ratio range. Pages: the first 3 plus up to 2 later loan pages.
- **Base:** BaseQuotedExtractor. **Depends on (injected):** BaseLlmClient.
- **Used by:** `lake` (meta/runs/plan32_terms.py).
- **Tests:** `tests/industry_graph/test_buyback_terms_extractor.py` (TC-BTX-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `item_model` | BuybackTermsItem | — -> type[QuotedItem] | — | as class | TC-BTX-001 |
| `list_pages` | first 3 pages plus up to 2 later loan pages, in order | Sequence[str] -> list[tuple[int, str]] | — | as class | TC-BTX-002 |
| `check_item` | known kind and a range; amounts in yuan; labels mapped | QuotedItem -> dict[str, Any] \| None | — | as class | TC-BTX-001, TC-BTX-003 |

### `BrokerCustomerExtractor` — `quant_cn.quant_cn.industry_graph.broker_customer_extractor` (L4)
- **Purpose:** Turn a broker stock report into quote-checked customers, suppliers and partners of the covered company with the stage reached; IrCustomerExtractor with its own prompt (no investees, peers or forecasts), page words and MAX_PAGES.
- **Base:** IrCustomerExtractor. **Depends on (injected):** BaseLlmClient.
- **Used by:** `lake` (meta/runs/plan28_pilot.py).
- **Tests:** `tests/industry_graph/test_broker_customer_extractor.py` (TC-BCE-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `TaxonomyNode` — `quant_cn.quant_cn.industry_graph.product_taxonomy` (L4)
- **Purpose:** One node of the taxonomy as the matcher and views need it.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ProductTaxonomy`, `industry_graph.ProductMatcher`.
- **Tests:** `tests/industry_graph/test_product_matcher.py` (TC-PT-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `labels` | Name and aliases. | — -> tuple[str, ...] | — | as class | see class |

### `ProductTaxonomy` — `quant_cn.quant_cn.industry_graph.product_taxonomy` (L4)
- **Purpose:** Load config/industry_chain/*.yaml once: nodes (names and aliases always strings, even when YAML reads "1,4-丁二醇" style values as numbers), the merged-id map, and the Shenwan L3 → segment map (`sw_l3_map`). Answers which segments and products belong to a company's Shenwan codes, which is the context ProductMatcher uses.
- **Base:** none. **Depends on (injected):** Path.
- **Used by:** `industry_graph.ProductMatcher`, `research_space`, `industry_graph.NodeEdgeBuilder`.
- **Tests:** `tests/industry_graph/test_product_matcher.py` (TC-PT-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | load v0 files and apply accepted change sets | Path, Sequence[TaxonomyChangeSet] -> None | `ConfigError` | callers of the class | TC-PT-004 |
| `version` | (property) the taxonomy version loaded (v0 or the last change set) | — -> str | — | as class | TC-PT-004 |
| `get_node` | The node for an id, after translating a merged id. | str -> TaxonomyNode \| None | — | as class | see class |
| `get_surviving_id` | Translate an id removed by the cross-sector merge to its surviving id. | str -> str | — | as class | see class |
| `list_nodes` | Nodes of the given types, in file order. | tuple[str, ...] -> list[TaxonomyNode] | — | as class | see class |
| `list_edges` | prior edges of the given relations, ends translated to successors, unknown ends and duplicates dropped | tuple[str, ...] -> list[tuple[str, str, str]] | — | `industry_graph.NodeEdgeBuilder` | TC-PT-006 |
| `get_segment_id` | the segment of a node (itself for a segment); None without one | str -> str \| None | — | `industry_graph.NodeEdgeBuilder` | TC-PT-006 |
| `list_context_ids` | Segments mapped to the company's Shenwan codes (with their child segments) and the products in those segments. | list[str] -> set[str] | — | as class | see class |

### `ProductMatch` — `quant_cn.quant_cn.industry_graph.product_matcher` (L4)
- **Purpose:** One taxonomy node a revenue line maps to, with how it was found.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ProductMatcher`.
- **Tests:** `tests/industry_graph/test_product_matcher.py` (TC-PM-001..009).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ProductMatcher` — `quant_cn.quant_cn.industry_graph.product_matcher` (L4)
- **Purpose:** Map a company's revenue line to taxonomy nodes without the LLM. Order: generic lines (其他, 投资收益, 抵销, ...) map to nothing and `is_generic` says so, so callers can drop them from the denominator; the name is normalized (parentheses and suffixes such as 收入/业务/产品 removed; for "A:B:C" the leaf is tried first, then the top level); each product, segment or material label scores exact 1.0, contains 0.6-0.9 by length share, character-bigram overlap up to 0.6; labels inside the company's Shenwan context (ProductTaxonomy.list_context_ids) get CONTEXT_BONUS; the best label at or above MIN_SCORE wins (products before segments on ties). A compound line ("A、B及C") is split first; when two or more parts match, each part is a match, otherwise the whole line (or its one matching part) is matched. Last resort: a company whose Shenwan codes map to exactly one segment gets that segment with how="sector".
- **Base:** none. **Depends on (injected):** ProductTaxonomy.
- **Used by:** `research_space`.
- **Tests:** `tests/industry_graph/test_product_matcher.py` (TC-PM-001..009).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ProductTaxonomy -> None | — | callers of the class | — |
| `is_generic` | True for lines that name no product (residuals, accounting items, eliminations). | str -> bool | — | as class | see class |
| `find_sector_segment` | the one root segment of the company's Shenwan context (sector fallback) or None | list[str] -> str \| None | — | NodeMemberBuilder | TC-PM-009 |
| `find_matches` | Taxonomy nodes for one revenue line. | str, list[str] -> list[ProductMatch] | — | as class | see class |

### `ReportDigest` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** One broker report reduced to what the synthesis needs: the quote-checked fields of a ValuationExtractor result (plan 13), tagged with a short id the model must cite.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.BrokerViewSynthesizer`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `format_text` | The digest as one prompt block. | — -> str | — | as class | see class |

### `ViewPoint` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** One synthesized point with the report refs it rests on.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BrokerViewReply`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BrokerViewReply` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** The LLM reply before the citation check.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BrokerViewSynthesizer`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BrokerView` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** The synthesized view after the citation check.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.BrokerViewSynthesizer`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BrokerViewSynthesizer` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** Synthesize the broker view of one product, Shenwan L3 industry or company from many report digests (user, 2026-11-08: the broker part must be the pattern across reports, not a list). The model may use only the digests; every point must cite digest refs, and refs not among the digests are removed; a point left without a valid ref is dropped (the citation check plays the role QuoteChecker plays for single documents). Digests are sent newest first within a character budget.
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `fetch_view` | Ask the model for the synthesized view and check its citations. | str, str, Sequence[ReportDigest] -> BrokerView | `DataSourceError` | as class | see class |

### `ModeClaim` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** One quoted answer: a value (variant id, pricing mode, pass-through) with its evidence.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BusinessModeReply`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `PriceAction` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** A stated price move: direction, what, magnitude, evidence.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BusinessModeReply`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BusinessModeReply` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** The LLM reply for one report before validation.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BusinessModeExtractor`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BusinessModeResult` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** The quote-checked reading: each claim is a dict {value, reason, evidence} or None.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.BusinessModeExtractor`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BusinessModeExtractor` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** Read the business-section pages of one annual report for the business-model fields that only the text can give (BUSINESS_MODEL_DESIGN §4.5 T1, §4b.7): which candidate variant of the company's archetype fits (or a proposed new one), the pricing mode, the cost pass-through and the stated price actions. Kept: claims whose verbatim quote is on a sent page and whose value is allowed (variant among the candidates, pricing in PRICING, pass-through in PASS_THROUGH, direction in DIRECTIONS); the rest is dropped and counted.
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `fetch_mode` | Ask the model about one report and validate the answer against the text. | str, str, Sequence[tuple[str, str, str]], Sequence[tuple[int, str]] -> BusinessModeResult | `DataSourceError` | as class | see class |

### `Reason` — `quant_cn.quant_cn.industry_graph.pricing_adjudicator` (L4)
- **Purpose:** One reason for the verdict with the evidence keys it rests on.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.AdjudicationReply`.
- **Tests:** `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `AdjudicationReply` — `quant_cn.quant_cn.industry_graph.pricing_adjudicator` (L4)
- **Purpose:** The LLM reply before validation.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.PricingAdjudicator`.
- **Tests:** `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `Adjudication` — `quant_cn.quant_cn.industry_graph.pricing_adjudicator` (L4)
- **Purpose:** The validated verdict.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.PricingAdjudicator`.
- **Tests:** `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `PricingAdjudicator` — `quant_cn.quant_cn.industry_graph.pricing_adjudicator` (L4)
- **Purpose:** For a company whose rule-based pricing-power label is insufficient or whose archetype check is inconsistent (BUSINESS_MODEL_DESIGN §4.5, §4b.7), give the model every measured signal, the annual-report claims and the broker-view summary, each under a key, and ask for one label, a confidence, whether the default archetype holds (or which allowed archetype fits) and the reasons. The citation check: reasons must cite supplied keys (unknown keys removed; a reason left with none is dropped); a label, confidence or archetype outside the allowed values raises (label) or is cleared (archetype) so nothing unverifiable is stored.
- **Base:** none. **Depends on (injected):** BaseLlmClient, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, str \| None -> None | — | callers of the class | — |
| `fetch_verdict` | Ask for the verdict and validate it. | str, str, Mapping[str, str], Mapping[str, str] -> Adjudication | `DataSourceError` | as class | see class |

### `MoatClaim` — `quant_cn.quant_cn.industry_graph.moat_extractor` (L4)
- **Purpose:** One claimed advantage: its moat type, a short statement, the figure the company gives (if any) and the evidence.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.MoatReply`, `industry_graph.MoatExtractor`.
- **Tests:** `tests/industry_graph/test_moat_extractor.py` (TC-ME-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `MoatReply` — `quant_cn.quant_cn.industry_graph.moat_extractor` (L4)
- **Purpose:** The LLM reply before validation.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.MoatExtractor`.
- **Tests:** `tests/industry_graph/test_moat_extractor.py` (TC-ME-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `MoatResult` — `quant_cn.quant_cn.industry_graph.moat_extractor` (L4)
- **Purpose:** The quote-checked claims of one report.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.MoatExtractor`.
- **Tests:** `tests/industry_graph/test_moat_extractor.py` (TC-ME-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `MoatExtractor` — `quant_cn.quant_cn.industry_graph.moat_extractor` (L4)
- **Purpose:** Read the 核心竞争力分析 pages of one annual report and list the advantages the company claims, each classified as one of MOAT_TYPES (cost, switching costs, intangibles, network effects, efficient scale) with the figure it cites. These are claims, not proof: the rule layer tests them against ROIC, margins and share (§4.4). Kept: claims with an allowed type and a verbatim quote on a sent page.
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_moat_extractor.py` (TC-ME-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `fetch_claims` | Ask the model about one report and validate the answer against the text. | str, Sequence[tuple[int, str]] -> MoatResult | `DataSourceError` | as class | see class |

### `IndexFuturesMonitor` — `quant_cn.calculation.index_futures_monitor` (L4)
- **Purpose:** 股指期货 part of the futures monitor: per configured product, FuturesPositioning (plan 09) over 5 years from derived.fut_daily_one_sided, derived.fut_holding_brokers and the index close; last-day basis (raw, annualised to the third-Friday expiry) and top-20 net with 5-year percentiles, OI change and regime, weekly histories; flags at the percentile bounds. Without the derived views every product is missing.
- **Base:** none. **Depends on (injected):** FuturesMonitorSettings, LakeQuery.
- **Used by:** `calculation.FuturesMonitorBuilder`.
- **Tests:** `tests/calculation/test_index_futures_monitor.py` (TC-IFM-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the 股指期货 part | start: str -> dict | LakeError | `calculation.FuturesMonitorBuilder` | TC-IFM-002 |
| `build_product` | one product's summary | product, name, index: str, frame: DataFrame -> dict | — | `build` | TC-IFM-001 |
| `list_flags` | basis / net signals | row: dict -> list[dict] | — | `build` | TC-IFM-002 |

### `FuturesBrokerNets` — `quant_cn.calculation.futures_broker_nets` (L4)
- **Purpose:** Top-20 broker longs and shorts summed per commodity family and day in SQL (family contracts on its exchange only; category rows already dropped, D-079); net, gross, net share (long − short)/(long + short), its 5-day change and 5-year percentile; a flag at the bounds naming the extreme side, never under MIN_GROSS lots. {} without the derived view.
- **Base:** none. **Depends on (injected):** FuturesMonitorSettings, LakeQuery.
- **Used by:** `calculation.FuturesMonitorBuilder`.
- **Tests:** `tests/calculation/test_futures_broker_nets.py` (TC-FBN-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | broker-net metrics per family | start: str -> dict | LakeError | `calculation.FuturesMonitorBuilder` | TC-FBN-001, TC-FBN-003 |
| `list_flags` | net-share signal | family, name: str, metrics: dict \| None -> list[dict] | — | `calculation.FuturesMonitorBuilder` | TC-FBN-002 |

### `SpreadReversion` — `quant_cn.calculation.spread_reversion` (L4)
- **Purpose:** One-year z of a spread (latest vs mean / std of the last 250 values, at least 120) and "reversion" flags for spreads marked `reversion` whose |z| reaches `reversion_z`, with side and half-life in the message (D-156).
- **Base:** none. **Depends on (injected):** FuturesMonitorSettings.
- **Used by:** `calculation.FuturesMonitorBuilder`.
- **Tests:** `tests/calculation/test_spread_reversion.py` (TC-SRV-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_z` | one-year z of the latest value | series: pd.Series -> float \| None | — | `calculation.FuturesMonitorBuilder` | TC-SRV-001 |
| `list_flags` | reversion flags of the built spreads | spreads: list[dict] -> list[dict] | — | `calculation.FuturesMonitorBuilder` | TC-SRV-002 |

### `FuturesMonitorBuilder` — `quant_cn.calculation.futures_monitor_builder` (L4)
- **Purpose:** Futures monitor from curated fut_basic + fut_daily over 5 years: per watched family the dominant (max-OI) contract price with 1- / 5-year percentile and 1-week / 3-month change on the same contract; front (nearest unexpired, OI ≥ min_oi) vs the 4th listed month and vs ~12 months later, each with a 5-year percentile; total OI with 5-day change and z vs one year; today's curve and shape via `FuturesCurve`. Spreads from the legs' dominant prices with 5-year percentile and one-year z. Flags at the percentile bounds, |OI z| ≥ bound, or |z| ≥ reversion_z on reversion spreads (D-156); new_flags vs the previous document. A family without contracts is listed in `missing`.
- **Base:** none. **Depends on (injected):** FuturesMonitorSettings, LakeQuery (builds IndexFuturesMonitor, FuturesBrokerNets, SpreadReversion).
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/calculation/test_futures_monitor_builder.py` (TC-FUM-001..008).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the monitor document | previous: dict \| None -> dict | LakeError | `write` | TC-FUM-001..005, TC-FUM-007..008 |
| `write` | build against the previous file and overwrite futures_monitor.json | out_dir: Path -> Path | LakeError | `cli.ReportCommands` | TC-FUM-006 |

### `VolatilityMonitorBuilder` — `quant_cn.calculation.volatility_monitor_builder` (L4)
- **Purpose:** Volatility monitor over the last `window` sessions: US VIX read from curated.cboe_vix; A-share VIX computed by `VixCalculator` (trading clock, D-052; building blocks made in `build` from that day's shibor and trade_cal) from opt_basic / opt_daily. Per line: latest value and date, one-day change, window percentile (None under min_obs), median / low / high, quality_flag, history. Level / jump / percentile flags; new_flags vs the previous document; lines without data in `missing`.
- **Base:** none. **Depends on (injected):** VolatilityMonitorSettings, LakeQuery.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/calculation/test_volatility_monitor_builder.py` (TC-VMB-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the monitor document | previous: dict \| None -> dict | LakeError | `write` | TC-VMB-001..004, TC-VMB-006 |
| `write` | build against the previous file and overwrite volatility_monitor.json | out_dir: Path -> Path | LakeError | `cli.ReportCommands` | TC-VMB-005 |

### `RatesFxSeriesReader` — `quant_cn.calculation.rates_fx_series_reader` (L4)
- **Purpose:** One dated series per configured line from `start`: curated.cn_bond_yield (curve + field), us_treasury_yield, shibor, fx_daily (bid / ask close mid), cny_fixing (÷ 100: per unit), an index earnings yield (members of the last index_weight date on or before each day, Σ mv / pe_ttm ÷ Σ mv in percent; losses count in mv only) and combos of earlier lines on a's dates with b carried forward (diff, ×100 to bp for unit bp; mul; div; gap a / b − 1). An unreadable table gives an empty series.
- **Base:** none. **Depends on (injected):** RatesFxMonitorSettings, LakeQuery.
- **Used by:** `calculation.RatesFxMonitorBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/calculation/test_rates_fx_monitor_builder.py` (TC-RFR-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_series` | every line's series from start | start: str -> dict[str, pd.Series] | — | `calculation.RatesFxMonitorBuilder` | TC-RFR-001..004 |

### `ConsensusPanelBuilder` — `quant_cn.calculation.consensus_panel_builder` (L4)
- **Purpose:** The analyst consensus known on each given date (D-173): report_rc notes with report_date in (date − window_days, date) (visible from the next session), one value per broker and fiscal year (latest note), median FY1 / FY2 / FY3 net profit (10k CNY) and the brokers behind FY1; FY1 = the year from May, else the year before.
- **Base:** none. **Depends on (injected):** LakeQuery, DateCodec.
- **Used by:** `factor.FactorFactory`, `risk.RiskInputLoader`, `cli.ServiceBuilder`.
- **Tests:** `tests/calculation/test_consensus_panel_builder.py` (TC-CNS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | consensus FY1-FY3 per stock on each date | dates: Sequence[str], window_days: int -> DataFrame (CONSENSUS_COLUMNS) | LakeError | `factor.FactorFactory` | TC-CNS-001..003 |
| `get_fy1` | first unreported fiscal year on a date | day: str -> int | — | `build` | TC-CNS-002 |

### `EarningsEventBuilder` — `quant_cn.calculation.earnings_event_builder` (L4)
- **Purpose:** Earnings events (plan 35, D-172): first disclosure = earliest ann_date of forecast_vip / express_vip / income_vip (a preview before the quarter end counts); SUE = single-quarter parent profit yoy change ÷ std of the prior 8 changes (≥ 4), first versions; SUE decile within the quarter among events with a pre window; excess vs the equal-weight market (|log return| ≥ 0.25 dropped), windows pre [-60,-1], react [0,+1], post [+2,+21] in %, NaN until complete; nothing after as_of read.
- **Base:** none. **Depends on (injected):** SectorEarningsSignalSettings, LakeQuery, DateCodec.
- **Used by:** `portfolio.SectorEarningsSignalBuilder`, `cli.AppServiceBuilder`.
- **Tests:** `tests/calculation/test_earnings_event_builder.py` (TC-EEB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | all events from start to as_of with SUE, decile, windows | as_of: str -> DataFrame (EVENT_COLUMNS) | LakeError | `portfolio.SectorEarningsSignalBuilder` | TC-EEB-003 |
| `compute_sue` | SUE per company and quarter from YTD profit | profit: DataFrame, window: int, min_obs: int -> DataFrame | — | `build` | TC-EEB-001 |
| `compute_windows` | day 0 and pre / react / post excess sums | events: DataFrame, cum: DataFrame, pre_window: int, react_window: int -> DataFrame | — | `build` | TC-EEB-002 |

### `RetailGaugeMatrices` — `quant_cn.calculation.retail_gauge_matrices` (L4)
- **Purpose:** Hold the daily matrices (px adjusted close, tov turnover_rate_f, cmv circ_mv, lg / elg / sm net order flow in 万元, rz financing balance) and compute the v3 / v4 path features over (a, b] and the v5 multi-scale features at b; flows / circ_mv are unitless; only rows on or before b are read (plan 21 ph2, D-142).
- **Base:** none. **Depends on (injected):** RetailGaugeSettings, dict[str, DataFrame].
- **Used by:** `calculation.RetailGaugeFeatureBuilder`.
- **Tests:** `tests/calculation/test_retail_gauge_matrices.py` (TC-RGM-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_path` | v3 / v4 path features over the quarter window | a: str, b: str -> DataFrame (empty when the window is too short) | — | `calculation.RetailGaugeFeatureBuilder` | TC-RGM-001 |
| `compute_scale` | v5 multi-scale, EWMA and slope features | b: str -> DataFrame | — | `calculation.RetailGaugeFeatureBuilder` | TC-RGM-002 |

### `HolderCountPanel` — `quant_cn.calculation.holder_count_panel` (L4)
- **Purpose:** Quarter-end shareholder counts from curated.stk_holdernumber announced by `end` (latest value, first ann_date): y = ln(n_q / n_{q-1}) with ann_y; prev / prev2 = changes of q-1 / q-2 visible only when announced on or before the row's as_of (plan 21, D-142).
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `calculation.RetailGaugeFeatureBuilder`, `calculation.RetailGaugeNowcaster`, `cli.GaugeCommands`.
- **Tests:** `tests/calculation/test_holder_count_panel.py` (TC-HCP-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read counts announced by end | end: str -> None | LakeError | `calculation.RetailGaugeFeatureBuilder` | TC-HCP-001 |
| `compute_labels` | y and ann_y of each row's quarter | rows: DataFrame -> DataFrame | — | `calculation.RetailGaugeNowcaster` | TC-HCP-001 |
| `compute_lags` | prev / prev2, point in time | rows: DataFrame -> DataFrame | — | `calculation.RetailGaugeFeatureBuilder` | TC-HCP-002 |
| `get_quarter_before` | quarter end k quarters earlier | q: str, k: int -> str | ValueError | `calculation.RetailGaugeFeatureBuilder` | TC-HCP-002 |

### `RetailGaugeFeatureBuilder` — `quant_cn.calculation.retail_gauge_feature_builder` (L4)
- **Purpose:** The 83 v5 features for any as-of session (quarter window from the previous quarter end): path / multi-scale (RetailGaugeMatrices), chips from cyq_perf at the last snapshot on or before as_of and on or before the previous quarter end, PIT holder lags, quarter number, `<f>_lag1` of the configured features from the previous quarter-end row (NaN for the first quarter), dtov_prev; rows = stocks with a turnover in the window; writes derived/retail_gauge_features by as_of (plan 21 ph2, D-142).
- **Base:** none. **Depends on (injected):** RetailGaugeSettings, LakeQuery, HolderCountPanel, DatedTableStore.
- **Used by:** `calculation.RetailGaugeNowcaster`, `cli.GaugeCommands`.
- **Tests:** `tests/calculation/test_retail_gauge_feature_builder.py` (TC-RGF-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read the matrices and holder counts up to end | end: str -> None | LakeError | `cli.GaugeCommands` | TC-RGF-001 |
| `build` | feature rows for as-of dates (loads when needed) | as_ofs: Sequence[str] -> DataFrame | LakeError | `calculation.RetailGaugeNowcaster` | TC-RGF-001..002 |
| `build_quarter_ends` | rows at every quarter end up to end | end: str -> DataFrame | LakeError | `calculation.RetailGaugeNowcaster` | TC-RGF-001 |
| `list_quarter_ends` | quarter ends after first_quarter | end: str -> list[str] | — | `build_quarter_ends` | TC-RGF-001 |
| `write` | store rows by as_of | frame: DataFrame -> list[Path] | LakeError | `cli.GaugeCommands` | TC-RGF-003 |
| `sessions` | loaded sessions (property) | — -> Index | — | `calculation.RetailGaugeNowcaster`, `cli.GaugeCommands` | TC-RGF-001 |

### `RetailGaugeModel` — `quant_cn.calculation.retail_gauge_model` (L4)
- **Purpose:** v5 LightGBM model (D-142): training medians fill NaN, features ranked within quarter (training) or within the scored set, target = within-quarter rank of y (|y| < label_abs_max); predict returns the pct rank of the score; saved as model.txt + meta.json.
- **Base:** none. **Depends on (injected):** RetailGaugeSettings.
- **Used by:** `calculation.RetailGaugeNowcaster`, `cli.GaugeCommands`.
- **Tests:** `tests/calculation/test_retail_gauge_model.py` (TC-RGMD-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | train on labelled quarter-end rows | rows: DataFrame, features: Sequence[str] -> None | LakeError | `calculation.RetailGaugeNowcaster` | TC-RGMD-001 |
| `compute_pct` | pct rank of the score | rows: DataFrame -> Series | LakeError | `calculation.RetailGaugeNowcaster` | TC-RGMD-001..002 |
| `save` | write the booster and medians | folder: Path -> None | LakeError | `calculation.RetailGaugeNowcaster` | TC-RGMD-002 |
| `load` | read a saved model | folder: Path -> None | LakeError | `calculation.RetailGaugeNowcaster` | TC-RGMD-002 |
| `is_fitted` | fitted flag (property) | — -> bool | — | callers | TC-RGMD-002 |

### `RetailGaugeNowcaster` — `quant_cn.calculation.retail_gauge_nowcaster` (L4)
- **Purpose:** Daily RetailGauge readings (plan 21 ph3, D-142, D-155, D-167): model per retrain key (1st of a retrain month; quarter-end rows of earlier quarters announced by the key; saved under model_root/<version>/<key>); expanding walk-forward at quarter ends -> derived/reports/retail_gauge/backtest.parquet; calibration deciles -> expected change and IQR relative to the quarter median; avoid = pct >= avoid_pct; lo / hi streaks over checkpoints t, t - step, ... in the same quarter (a missing checkpoint ends it); retail_leaving / avoid_strong at persist_n; writes derived/retail_gauge.
- **Base:** none. **Depends on (injected):** RetailGaugeSettings, RetailGaugeFeatureBuilder, HolderCountPanel, ParquetWriter, DatedTableStore, Path, Callable[[], RetailGaugeModel].
- **Used by:** `cli.GaugeCommands`.
- **Tests:** `tests/calculation/test_retail_gauge_nowcaster.py` (TC-RGN-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_model` | fit or load the model of a retrain key | key: str -> RetailGaugeModel | LakeError | `run` | TC-RGN-003 |
| `run_walk_forward` | out-of-sample quarter-end readings | end: str -> DataFrame | LakeError | `cli.GaugeCommands` | TC-RGN-003 |
| `compute_calibration` | decile -> quantiles of y minus the quarter median | backtest: DataFrame, key: str -> DataFrame | LakeError | `run` | TC-RGN-004 |
| `run` | daily readings written to derived/retail_gauge | as_ofs: Sequence[str] -> DataFrame | LakeError | `cli.GaugeCommands` | TC-RGN-002 |
| `get_retrain_key` | retrain key of an as-of date | as_of: str -> str | — | `run` | TC-RGN-001 |
| `compute_streaks` | avoid, streaks, retail_leaving, avoid_strong | frame: DataFrame, sessions: Sequence[str], settings -> DataFrame | — | `run` | TC-RGN-002 |

### `RetailGaugeEvaluator` — `quant_cn.calculation.retail_gauge_evaluator` (L4)
- **Purpose:** Per walk-forward quarter: rank IC of pct vs y, top-decile hit (pct >= 0.9 and y rank >= 0.7), bottom-decile hit, avoid names' 60-session excess vs the equal-weight mean of scored names (%), ic_low (< 0.4); writes derived/reports/retail_gauge/evaluation.parquet (plan 21 ph3).
- **Base:** none. **Depends on (injected):** RetailGaugeSettings, LakeQuery, ParquetWriter.
- **Used by:** `cli.GaugeCommands`.
- **Tests:** `tests/calculation/test_retail_gauge_evaluator.py` (TC-RGE-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | score a walk-forward table and store the report | backtest: DataFrame -> DataFrame | LakeError | `cli.GaugeCommands` | TC-RGE-001 |
| `compute_scores` | per-quarter scores | backtest: DataFrame, fwd: DataFrame, avoid_pct: float -> DataFrame | — | `run` | TC-RGE-001 |

### `RatesFxMonitorBuilder` — `quant_cn.calculation.rates_fx_monitor_builder` (L4)
- **Purpose:** The 利率与汇率 document as of the last date of any line (or as_of; nothing later used). Per shown line: latest value and date, 1w / 1m / 3m / 1y changes (bp for yield / bp, fraction for rate, fraction points for gap), 5-year percentile (None under min_obs), 1-year low / high, stale, alerts, history (daily over the last year, every 5th observation before). Flags: week_move, week_widen, extreme, pct_above, abs_above, below / above; new_flags vs the previous document; curve snapshot today / 1 month / 1 year earlier.
- **Base:** none. **Depends on (injected):** RatesFxMonitorSettings, RatesFxSeriesReader, LakeQuery.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/calculation/test_rates_fx_monitor_builder.py` (TC-RFM-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the monitor document | previous: dict \| None, as_of: str \| None -> dict | LakeError | `write` | TC-RFM-001..004 |
| `write` | build against the previous file and overwrite rates_fx_monitor.json | out_dir: Path -> Path | LakeError | `cli.ReportCommands` | TC-RFM-004 |

### `MacroSeries` — `quant_cn.calculation.macro_monitor_builder` (L4)
- **Purpose:** One monitored macro line: key, Chinese name, group (价格 / 景气 / 货币 / 社融), unit and the merged-frame column it reads.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `calculation.MacroMonitorBuilder`.
- **Tests:** `tests/calculation/test_macro_monitor_builder.py` (TC-MMB-001).

### `MacroMonitorBuilder` — `quant_cn.calculation.macro_monitor_builder` (L4)
- **Purpose:** Read curated cn_cpi, cn_ppi, cn_pmi, cn_m, sf_month into one monthly frame, add PPI − CPI, M1 − M2, 社融 stock yoy and new 社融 vs the same month last year, and per line give latest, previous, change, percentile in the last 60 prints and new_print (month not in the previous document). A missing table is listed, never zero-filled.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/calculation/test_macro_monitor_builder.py` (TC-MMB-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the monitor document | previous: dict \| None -> dict | LakeError | `write` | TC-MMB-001..004, TC-MMB-006 |
| `write` | build against the previous file and overwrite macro_monitor.json | out_dir: Path -> Path | LakeError | `cli.ReportCommands` | TC-MMB-005 |

### `CurveSummary` — `quant_cn.quant_cn.calculation.futures_curve` (L4)
- **Purpose:** The shape of one contract family's curve on one date: front, most-held, 6- and 12-month and last prices, and the slope from the most-held month to 12 months after it (or to the last later month when the curve is shorter).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `calculation.FuturesCurve`.
- **Tests:** `tests/calculation/test_futures_curve.py` (TC-FCV-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `FuturesCurve` — `quant_cn.quant_cn.calculation.futures_curve` (L4)
- **Purpose:** Back-month futures curve per contract family (e.g. "AL.SHF") and per material node (config/material_prices.yaml maps MAT_* ids to families), for the commodity price the market implies against the curve (plan 16 phase 2). A curve on a date is every listed month of the family that has a quote that day and has not expired (delivery month >= the trade month), priced at settle (close when settle is missing), with months ahead counted from the trade month. PIT: only quotes of that trade date are used.
- **Base:** none. **Depends on (injected):** pd.DataFrame, Mapping[str, Sequence[str]].
- **Used by:** `plan`.
- **Tests:** `tests/calculation/test_futures_curve.py` (TC-FCV-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | pd.DataFrame, Mapping[str, Sequence[str]] -> None | — | callers of the class | — |
| `list_families` | Contract families mapped to a material node. | str -> list[str] | — | as class | see class |
| `build_curve` | The family's curve on one date. | pd.DataFrame, str, str -> pd.DataFrame | `ValueError` | as class | see class |
| `compute_summary` | Front, dominant, 6m, 12m and last prices and the curve shape. | pd.DataFrame, str, str -> CurveSummary | — | as class | see class |
| `list_material_summaries` | One summary per family of a material. | pd.DataFrame, str, str -> list[CurveSummary] | `ValueError` | as class | see class |
| `build_dominant_series` | Daily price of the most-held unexpired month (regressor for profit sensitivity). | pd.DataFrame, str -> pd.DataFrame | `ValueError` | research checks; `ImpliedExpectations.compute_sensitivity` input | TC-FCV-006 |

### `ImpliedExpectations` — `quant_cn.quant_cn.calculation.implied_expectations` (L4)
- **Purpose:** Turn a market cap into what it already pays for (D-121: "priced in", not "cheap"). Years priced: the market cap above a normal value V0 is read as an annuity of excess profit E = TTM profit - 10-year median profit, discounted at `discount_rate`; n = -ln(1 - r*(MC - V0)/E) / ln(1 + r), 0 when MC ≤ V0, `max_years` when the market pays more than a perpetuity of E, NaN when E ≤ 0. Three bases, always shown side by side: V0 = median profit x `normal_pe` (primary), x the stock's own median PE, and the pre-cycle market cap. Each on net profit and on deducted net profit. Reverse DCF: the constant growth g of TTM profit over `dcf_years`, exiting at `normal_pe` x final profit, that makes the discounted value equal the market cap (bisection in GROWTH_BOUNDS, clamped). Pure: the caller loads market caps and PEs.
- **Base:** none. **Depends on (injected):** DiscoverySettings.
- **Used by:** `plan`.
- **Tests:** `tests/calculation/test_implied_expectations.py` (TC-IE-001..007). Inputs from `calculation.CompanyCyclePanel.list_quarters` and `calculation.FuturesCurve.build_dominant_series` (passed in by the caller).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DiscoverySettings -> None | — | callers of the class | — |
| `compute_years` | Years of excess profit the market cap pays for above a base value. | float, float, float -> float | — | as class | see class |
| `compute_implied_growth` | Annual profit growth over dcf_years that justifies the market cap (reverse DCF). | float, float -> float | — | as class | see class |
| `compute_sensitivity` | Annual profit change per unit commodity price (OLS of quarterly profit on quarterly mean futures price, x4; NaN below 8 quarters or R² 0.3). | pd.DataFrame, pd.DataFrame -> dict[str, float] | — | as class | TC-IE-006 |
| `compute_implied_price` | Commodity price at which normal_pe x profit(p) equals the market cap. | float, float, float, float -> float | — | as class | TC-IE-007 |
| `build` | Years priced on three bases and implied growth for every company with a market cap. | pd.DataFrame, pd.DataFrame -> pd.DataFrame | `ValueError` | as class | see class |
### `BaseRiskModel` — `quant_cn.risk.base_risk_model` (L5)
- **Purpose:** Abstract risk model: produces the RISK_EXPOSURE / FACTOR_RETURN / FACTOR_COV / SPECIFIC_RISK frames for a pipeline step and answers portfolio-risk questions for a session from those frames. A statistical (PCA) model would be another subclass (D-045).
- **Base:** ABC. **Depends on (injected):** str.
- **Used by:** `risk.RiskModel`, `risk.RiskModelValidator`, `portfolio.HoldingsRiskBuilder`.
- **Tests:** `tests/risk/test_base_risk_model.py` (TC-BRM-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str -> None | — | callers of the class | — |
| `load_snapshot` | The fitted model as of a session. | str -> RiskSnapshot | `LakeError` | as class | see class |
| `compute_portfolio_risk` | Forecast daily volatility of a portfolio held from the close of `trade_date`. | pd.Series, str -> float | `LakeError` | as class | see class |

### `BayesianShrinker` — `quant_cn.risk.bayesian_shrinker` (L5)
- **Purpose:** Pull each stock's specific vol toward the cap-weighted mean of its size group, more so the further it is from it: sigma_sh = v sigma_bar + (1 - v) sigma with v = q \|sigma - sigma_bar\| / (delta + q \|sigma - sigma_bar\|), delta the root mean square deviation inside the group. Corrects the over-prediction of extreme historical vols (mean reversion of specific risk).
- **Base:** none. **Depends on (injected):** float, int.
- **Used by:** `risk.SpecificRiskEstimator`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_bayesian_shrinker.py` (TC-BS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | float, int -> None | — | callers of the class | — |
| `compute` | Shrunk specific vol for one session. | np.ndarray, np.ndarray -> np.ndarray | — | as class | see class |

### `DescriptorBuilder` — `quant_cn.risk.descriptor_builder` (L5)
- **Purpose:** One row per universe member and session in [start, end] with its Shenwan L1 group, circulating market cap (regression weight base, CNY) and every raw CNE5 descriptor: LNCAP = ln(total market cap in CNY), NLSIZE = cube of the cap-weighted standardised LNCAP, the price descriptors (PriceDescriptors on the dense return matrix; market = previous-day circ_mv weighted return of all stocks), the value / leverage descriptors, the growth descriptors from the latest monthly snapshot on or before the session, the analyst descriptors EPFWD / EGRSF / EGRLF (AnalystDescriptors; NaN without a consensus, plan 37), and one partial beta per configured external series (the foreign return that closed between the previous and the current China close, e.g. S&P 500 or USDCNH; D-128, D-134) and per theme basket (circ_mv-weighted return of the concept's members excluding the stock itself, from the concept's start; D-130), with the China market as control (FundamentalDescriptors). Stocks whose code ends with an excluded suffix are dropped.
- **Base:** none. **Depends on (injected):** PriceDescriptors, FundamentalDescriptors, Standardizer, Sequence[str], AnalystDescriptors | None.
- **Used by:** `risk.RiskModel`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_descriptor_builder.py` (TC-DB-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | PriceDescriptors, FundamentalDescriptors, Standardizer, Sequence[str], AnalystDescriptors \| None -> None | — | callers of the class | — |
| `compute` | The descriptor table of the window. | RiskInputs -> pd.DataFrame | `KeyError` | as class | see class |
| `compute_theme_return` | Weighted theme-basket return seen by every stock: members get the basket without themselves, non-members the whole basket. | np.ndarray, np.ndarray, np.ndarray -> np.ndarray | — | as class | see class |
| `compute_overnight_return` | Foreign index return aligned to China sessions: for session t with previous session p, the compounded return of every foreign close dated d with p <= d < t (a US close dated d happens on the morning of d + 1 Beijing time, between the two China closes). | list[str], pd.DataFrame -> np.ndarray | `KeyError` | as class | see class |

### `EigenfactorAdjuster` — `quant_cn.risk.eigenfactor_adjuster` (L5)
- **Purpose:** Remove the systematic underestimation of risk of the smallest-variance eigenportfolios of a sample covariance. For the matrix F0 = U0 D0 U0^T: simulate `sims` histories of `n_obs` returns from N(0, F0), estimate each sample covariance F_m = U_m D_m U_m^T with the estimation weights, compare the true variance of the simulated eigenportfolios diag(U_m^T F0 U_m) with the estimated D_m, and form the bias v(k) = sqrt(mean_m ratio) per eigen rank k. The adjusted matrix is U0 diag(gamma^2 D0) U0^T with gamma = scale (v - 1) + 1. The bias profile (gamma by rank) can be reused across nearby dates (`compute_adjusted`): it depends on the spectrum shape and sample length.
- **Base:** none. **Depends on (injected):** int, float.
- **Used by:** `risk.FactorCovarianceEstimator`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_eigenfactor_adjuster.py` (TC-EFA-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int, float -> None | — | callers of the class | — |
| `compute_gamma` | The eigen-rank scaling gamma for a covariance estimated with `weights`. | np.ndarray, np.ndarray, int -> np.ndarray | `np.linalg.LinAlgError` | as class | see class |
| `compute_adjusted` | Scale the eigenvalues of `cov` by gamma^2 (ascending rank order). | np.ndarray, np.ndarray -> np.ndarray | `ValueError` | as class | see class |

### `EwmWindow` — `quant_cn.risk.ewm_window` (L5)
- **Purpose:** The trailing-window kernel of every Barra descriptor and covariance estimate: weight w_k = 0.5^(k / half_life) on the observation k sessions before the current one (k = lag .. lag + window - 1), normalised to sum 1. Sums are exact finite-window convolutions along axis 0 (scipy.signal.lfilter with an FIR kernel), so a value at row t uses rows t - lag - window + 1 .. t - lag only.
- **Base:** none. **Depends on (injected):** int, float, int.
- **Used by:** `risk.PriceDescriptors`, `risk.FactorCovarianceEstimator`, `risk.SpecificRiskEstimator`, `risk.VolatilityRegimeAdjuster`.
- **Tests:** `tests/risk/test_ewm_window.py` (TC-EW-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int, float, int -> None | — | callers of the class | — |
| `weights` | The normalised weights, most recent first (without the lag zeros). | — -> np.ndarray | — | as class | see class |
| `compute_sum` | Weighted trailing sum per row and column; NaN counts as 0. | np.ndarray -> np.ndarray | — | as class | see class |
| `compute_count` | Number of valid observations inside each trailing window. | np.ndarray -> np.ndarray | — | as class | see class |

### `ExposureStandardizer` — `quant_cn.risk.exposure_standardizer` (L5)
- **Purpose:** Turn the descriptor table into RISK_EXPOSURE, per session: each descriptor is standardised (circ_mv-weighted mean 0, equal-weighted sd 1), then clipped at +-winsor_sd and standardised again until no value exceeds the bound (at most 20 rounds); a style is the weighted mean of its descriptors' z-scores (weights renormalised over the descriptors a stock has), restandardised and clipped, then orthogonalised to its configured styles (OLS residual, Neutralizer) and restandardised; a style with raw coverage below `min_coverage` of the session's names is dropped for that session. Missing exposures of a kept style are filled with the prediction of an OLS of the style on Shenwan L1 dummies and size (is_filled = 1). Industry rows: factor "ind_<l1_code>", exposure 1, is_filled = industry_backfilled (D-071). Monitor styles (D-130) are built the same way after the model styles.
- **Base:** none. **Depends on (injected):** RiskModelSettings, Standardizer, Neutralizer.
- **Used by:** `risk.RiskModel`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_exposure_standardizer.py` (TC-EXS-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | RiskModelSettings, Standardizer, Neutralizer -> None | — | callers of the class | — |
| `compute` | Style and industry exposures for every row of the descriptor table. | pd.DataFrame -> pd.DataFrame | `KeyError` | as class | see class |

### `FactorCovarianceEstimator` — `quant_cn.risk.factor_covariance_estimator` (L5)
- **Purpose:** For every session t, the factor covariance forecast for t+1 from factor returns up to t over the last `cov_window` sessions: zero-mean exponentially weighted covariances with pairwise missing-data normalisation and Newey-West autocorrelation terms (Bartlett weights, `cov_nw_lags`), volatilities with `vol_half_life` and correlations with `corr_half_life` (CNE5 90 / 480), combined as D C D and made PSD (cov_raw); then the eigenfactor adjustment (gamma profile refitted every `eigen_refit_days` sessions or when the factor set changes) and the volatility regime multiplier lambda^2 (cov). Units: daily variance; horizon_days records the NW horizon. A factor enters a session's matrix only with >= min_factor_obs observations in its window.
- **Base:** none. **Depends on (injected):** RiskModelSettings, EigenfactorAdjuster, VolatilityRegimeAdjuster.
- **Used by:** `risk.RiskModel`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_factor_covariance_estimator.py` (TC-FCE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | RiskModelSettings, EigenfactorAdjuster, VolatilityRegimeAdjuster -> None | — | callers of the class | — |
| `compute` | FACTOR_COV for every session of the factor-return history (from `start` if given). | pd.DataFrame, str \| None -> pd.DataFrame | `SchemaError` | as class | see class |
| `compute_raw` | EWMA + Newey-West covariance of one window (last row = most recent). | np.ndarray -> np.ndarray | — | as class | see class |

### `FactorMonitorBuilder` — `quant_cn.risk.factor_monitor_builder` (L5)
- **Purpose:** Turn the stored risk-model frames into the factor monitor: for every factor (country, Shenwan L1 industries, styles) its compounded return over 1 d / 1 w / 1 m / 3 m / YTD / 1 y, forecast volatility (sqrt of the covariance diagonal, annualised with 252), realized volatility over 21 and 63 sessions, their ratio, and today's return in units of the forecast daily sigma made at the previous close; plus daily series of the cumulative return, forecast vol and 21-session realized vol for the last `series_days` sessions. No model math: only derived.risk_factor_return and derived.risk_factor_cov are read.
- **Base:** none. **Depends on (injected):** LakeQuery, str, int.
- **Used by:** `cli.ResearchCommands`.
- **Tests:** `tests/risk/test_factor_monitor_builder.py` (TC-FMB-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, str, int -> None | — | callers of the class | — |
| `build` | The factor monitor document as of the last factor-return session. | — -> dict[str, Any] | `LakeError` | as class | see class |
| `write` | Build the document and write it as `factor_monitor.json` for the app's data dir. | Path -> Path | `LakeError` | as class | see class |

### `FactorReturnEstimator` — `quant_cn.risk.factor_return_estimator` (L5)
- **Purpose:** For each return session t, regress stock returns from the close of t-1 to the close of t on exposures known at the close of t-1: r = f_c + sum_i X_i f_i + sum_s X_s f_s + u, weights sqrt(circ_mv at t-1) capped at the `weight_cap_quantile` cross-sectional quantile. Country and industry factors are identified by the constraint sum_i w_i f_i = 0 with w_i the industry's share of circ_mv, imposed by the restriction f = R g (the largest industry is expressed through the others), so the country factor is the cap-weighted market. Styles with no exposure on a session are left out of it. R^2 is the weighted uncentred R^2 1 - sum w u^2 / sum w r^2 (Barra convention).
- **Base:** none. **Depends on (injected):** Sequence[str], float, int.
- **Used by:** `risk.RiskModel`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_factor_return_estimator.py` (TC-FRE-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Sequence[str], float, int -> None | — | callers of the class | — |
| `compute` | Factor returns and residuals for every session of the panel. | pd.DataFrame -> tuple[pd.DataFrame, pd.DataFrame] | `KeyError` | as class | see class |
| `compute_monitor` | Returns of monitor styles (D-130): per session the constrained WLS is rerun with one monitor style added to the model's styles, and only that style's coefficient, t-stat and the R^2 gain are kept, so the risk model itself is unchanged. | pd.DataFrame, Sequence[str] -> pd.DataFrame | `KeyError` | as class | see class |
| `compute_date` | The constrained WLS of one session. | pd.DataFrame, Sequence[str] -> tuple[pd.DataFrame, pd.DataFrame] \| None | `KeyError` | as class | see class |

### `AnalystDescriptors` — `quant_cn.risk.analyst_descriptors` (L5)
- **Purpose:** CNE5 analyst descriptors per stock and session from the latest consensus reading on or before it (ConsensusPanelBuilder month ends): EPFWD = (w × FY1 + (1 − w) × FY2) / total_mv with w = whole months left in FY1 after the session's month / 12 (0 once FY1 has ended); EGRSF = FY2 / FY1 − 1; EGRLF = (FY3 / FY1)^½ − 1; growth needs FY1 > 0 (and FY3 > 0); NaN without a consensus (plan 37).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `risk.DescriptorBuilder`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_analyst_descriptors.py` (TC-AND-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute` | EPFWD, EGRSF, EGRLF for every (trade_date, ts_code) of keys | keys: DataFrame, consensus: DataFrame -> DataFrame | — | `risk.DescriptorBuilder` | TC-AND-001..003 |

### `FundamentalDescriptors` — `quant_cn.risk.fundamental_descriptors` (L5)
- **Purpose:** CNE5 descriptors from statements already aligned point in time (FUNDAMENTALS_PIT for balance and TTM fields; StatementVersionReader snapshots for annual history): BTOP = common equity / market cap; ETOP, CETOP = TTM net profit (parent) and operating cash flow / market cap; MLEV = (ME + LD) / ME, DTOA = total liabilities / total assets, FCFP = (TTM operating cash flow - TTM capex, c_pay_acq_const_fiolta) / market cap (D-131); BLEV = (BE + LD) / BE with LD = long-term borrowings + bonds payable (preferred equity is not reported separately and taken as 0); EGRO, SGRO = slope of the last up to `years` annual EPS / revenue on time divided by their mean absolute value (revenue instead of revenue per share: a constant share count cancels in slope / mean).
- **Base:** none. **Depends on (injected):** int, int.
- **Used by:** `risk.DescriptorBuilder`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_fundamental_descriptors.py` (TC-FD-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int, int -> None | — | callers of the class | — |
| `compute_value_leverage` | Value and leverage descriptors per (trade_date, ts_code). | pd.DataFrame -> pd.DataFrame | `KeyError` | as class | see class |
| `compute_growth` | EGRO and SGRO per (as_of, ts_code) from the annual reports known on each as_of. | pd.DataFrame -> pd.DataFrame | `KeyError` | as class | see class |

### `PriceDescriptors` — `quant_cn.risk.price_descriptors` (L5)
- **Purpose:** The CNE5 descriptors that need only daily returns and turnover, computed for every session and stock at once on wide matrices (rows = sessions in order, columns = stocks): BETA and HSIGMA (exponentially weighted regression on the cap-weighted market, 252 d, half-life 63), RSTR (weighted sum of log returns over 504 d, half-life 126, lag 21), DASTD (weighted sd of returns, 252 d, half-life 42), CMRA (range of cumulative log returns over the last 12 months), STOM / STOQ / STOA (log share turnover over 1 / 3 / 12 months). Values at row t use rows <= t only.
- **Base:** none. **Depends on (injected):** int, int, int, int, int, int, int, int.
- **Used by:** `risk.DescriptorBuilder`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_price_descriptors.py` (TC-PD-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int, int, int, int, int, int, int, int -> None | — | callers of the class | — |
| `compute_beta` | BETA (slope) and HSIGMA (residual sd) of the weighted regression r = a + b m + e. | np.ndarray, np.ndarray -> tuple[np.ndarray, np.ndarray] | — | as class | see class |
| `compute_partial_beta` | Slope on an external return in the weighted regression r = a + b m + c x + e (same window and half-life as BETA): the sensitivity to x beyond the home market m, e.g. | np.ndarray, np.ndarray, np.ndarray -> np.ndarray | — | as class | see class |
| `compute_rstr` | RSTR: weighted sum of ln(1 + r) over the window, skipping the most recent `lag`. | np.ndarray -> np.ndarray | — | as class | see class |
| `compute_dastd` | DASTD: exponentially weighted standard deviation of daily returns. | np.ndarray -> np.ndarray | — | as class | see class |
| `compute_cmra` | CMRA: max minus min over T = 1..months of the cumulative log return of the last T months (Z(T) = sum of ln(1 + r) over the last 21 T sessions), i.e. | np.ndarray, int -> np.ndarray | — | as class | see class |
| `compute_liquidity` | STOM, STOQ, STOA from daily share turnover (a fraction of free-float shares). | np.ndarray -> dict[str, np.ndarray] | — | as class | see class |

### `RiskDecomposer` — `quant_cn.risk.risk_decomposer` (L5)
- **Purpose:** Euler decomposition of a portfolio's forecast volatility at one session: total, factor and specific risk, each factor's contribution b_k (F b)_k / sigma (contributions plus the specific part h' D h / sigma sum to sigma), and the portfolio's factor exposures. With a benchmark, the same for active weights h - h_b (tracking error). Daily units; annualise with sqrt(252) when presenting.
- **Base:** none. **Depends on (injected):** none.
- **Used by:** `research_space/notebooks/20261111_risk_model_validation.ipynb`, `portfolio.HoldingsRiskBuilder`, `cli.ResearchCommands`.
- **Tests:** `tests/risk/test_risk_decomposer.py` (TC-RD-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute` | RISK_DECOMP rows of one portfolio (and its active version against a benchmark). | RiskSnapshot, pd.Series, str, pd.Series \| None -> pd.DataFrame | `QuantCnError` | as class | see class |

### `RiskInputs` — `quant_cn.risk.risk_input_loader` (L5)
- **Purpose:** Everything the descriptors need for exposures on [start, end], all point in time: dense prices and daily_basic from PRICE_HISTORY sessions before start (descriptor windows), universe members with their Shenwan L1 group (EXPOSURE_PANEL), balance and TTM fields (FUNDAMENTALS_PIT), month-end snapshots of annual EPS and revenue, and the analyst consensus on those month ends (plan 37; empty when not loaded).
- **Base:** none. **Depends on (injected):** none.
- **Used by:** `risk.RiskInputLoader`, `risk.DescriptorBuilder`, `risk.RiskModel`.
- **Tests:** `tests/risk/test_risk_input_loader.py` (TC-RIL-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `RiskInputLoader` — `quant_cn.risk.risk_input_loader` (L5)
- **Purpose:** Read RiskInputs for one exposure window through the lake readers only (no parquet paths): LakeReader for prices, daily_basic and FUNDAMENTALS_PIT, ExposureReader for universe members with Shenwan L1 (D-093), StatementVersionReader for the annual reports known on each month-end session (growth descriptors refresh monthly, PIT at the snapshot date; D-127).
- **Base:** none. **Depends on (injected):** LakeReader, ExposureReader, StatementVersionReader, TradingCalendar, DateCodec, LakeQuery, Sequence[ExternalSeriesSpec], Sequence[ThemeBasketSpec], ConsensusPanelBuilder | None, int.
- **Used by:** `pipeline.RiskModelStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/risk/test_risk_input_loader.py` (TC-RIL-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeReader, ExposureReader, StatementVersionReader, TradingCalendar, DateCodec, LakeQuery, Sequence[ExternalSeriesSpec], Sequence[ThemeBasketSpec], ConsensusPanelBuilder \| None, int -> None | — | callers of the class | — |
| `load` | All panels for exposures on [start, end]. | str, str -> RiskInputs | `ValueError`, `LakeError` | as class | see class |
| `list_snapshot_dates` | Month-end sessions used as growth snapshots: the last session of each month in [start, end] plus the last session before start. | str, str -> list[str] | — | as class | see class |

### `RiskModel` — `quant_cn.risk.risk_model` (L5)
- **Purpose:** CNE5-style model for A-shares (country + Shenwan L1 + configured styles) as a sequence of pure stages the pipeline step runs year by year: exposures from RiskInputs (DescriptorBuilder -> ExposureStandardizer), factor returns and residuals (exposures at t-1, returns t-1 -> t, circ_mv at t-1; FactorReturnEstimator), the factor covariance over the whole factor-return history (FactorCovarianceEstimator) and specific risk (SpecificRiskEstimator). Reads the stored frames back from derived.risk_* views for portfolio questions.
- **Base:** BaseRiskModel. **Depends on (injected):** RiskModelSettings, DescriptorBuilder, ExposureStandardizer, FactorReturnEstimator, FactorCovarianceEstimator, SpecificRiskEstimator, LakeQuery.
- **Used by:** `risk.RiskModelFactory`, `pipeline.RiskModelStep`.
- **Tests:** `tests/risk/test_risk_model.py` (TC-RM-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | RiskModelSettings, DescriptorBuilder, ExposureStandardizer, FactorReturnEstimator, FactorCovarianceEstimator, SpecificRiskEstimator, LakeQuery -> None | — | callers of the class | — |
| `compute_exposures` | RISK_EXPOSURE for the inputs' window. | RiskInputs -> pd.DataFrame | `KeyError` | as class | see class |
| `compute_factor_returns` | FACTOR_RETURN and SPECIFIC_RETURN for the sessions of [inputs.start, inputs.end]. | pd.DataFrame, RiskInputs -> tuple[pd.DataFrame, pd.DataFrame] | `KeyError` | as class | see class |
| `compute_monitor_returns` | Daily returns of the monitor styles (D-130), estimated beside the model. | pd.DataFrame, RiskInputs -> pd.DataFrame | `KeyError` | as class | see class |
| `build_regression_panel` | One row per stock and return session t: ret (t-1 -> t), circ_mv (CNY at t-1), l1_code and style exposures at t-1. | pd.DataFrame, RiskInputs -> pd.DataFrame | `KeyError` | as class | see class |
| `compute_covariance` | FACTOR_COV from the factor-return history. | pd.DataFrame, str \| None -> pd.DataFrame | `SchemaError` | as class | see class |
| `compute_specific_session` | Pre-regime specific vol of one session's members. | pd.Series, pd.Series, pd.DataFrame, pd.Series -> pd.DataFrame | `KeyError` | as class | see class |
| `compute_specific_time_series` | Time-series specific vol and residual counts (SpecificRiskEstimator). | pd.DataFrame -> tuple[pd.DataFrame, pd.DataFrame] | — | as class | see class |
| `compute_specific_final` | SPECIFIC_RISK after the specific volatility regime adjustment. | pd.DataFrame, pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |
| `load_snapshot` | The stored model of one session. | str -> RiskSnapshot | `LakeError` | as class | see class |

### `RiskModelFactory` — `quant_cn.risk.risk_model_factory` (L5)
- **Purpose:** Wire a RiskModel and all its estimators from one RiskModelSettings (config/ risk_model.yaml), so variants (six styles vs ten, other half-lives) are config only.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `cli.ServiceBuilder`, `research_space/notebooks/20261111_risk_model_validation.ipynb`, `cli.ResearchCommands`.
- **Tests:** `tests/risk/test_risk_model_factory.py` (TC-RMF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery -> None | — | callers of the class | — |
| `build` | The model for these settings. | RiskModelSettings -> RiskModel | — | as class | see class |

### `RiskModelValidator` — `quant_cn.risk.risk_model_validator` (L5)
- **Purpose:** Test whether forecasts match realised risk. Bias statistic of a series of forecasts: B = sd(z) with z_t = r_{t+1} / sigma_t (forecast at the close of t, return over t+1); B ~ 1 when unbiased, with a 95% band of about 1 +- sqrt(2 / T). Applied to every factor (FACTOR_COV diagonal vs FACTOR_RETURN), to random long-only portfolios (snapshots of the model vs realised stock returns) and to any named portfolio (e.g. CSI 300 weights). Also reports the cross-sectional fit (median / mean R^2) and the q-statistic mean(z^2 - ln z^2) when asked.
- **Base:** none. **Depends on (injected):** BaseRiskModel, int.
- **Used by:** `research_space/notebooks/20261111_risk_model_validation.ipynb`, `pipeline.RiskValidationWriter`, `cli.ServiceBuilder`.
- **Tests:** `tests/risk/test_risk_model_validator.py` (TC-RMV-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseRiskModel, int -> None | — | callers of the class | — |
| `compute_bias` | Bias statistic and q-statistic per scope. | pd.DataFrame, str -> pd.DataFrame | `KeyError` | as class | see class |
| `compute_factor_bias` | Bias statistic of every factor's variance forecast over forecasts made in [start, end]. | pd.DataFrame, pd.DataFrame, str, str -> pd.DataFrame | `SchemaError` | as class | see class |
| `build_random_portfolios` | Random long-only portfolios: `size` names drawn without replacement, Dirichlet(1) weights. | Sequence[str], int, int -> pd.DataFrame | `ValueError` | as class | see class |
| `compute_portfolio_forecasts` | Forecast vol at each session and the realised return over the next session for each portfolio (fixed weights, renormalised over names with a return). | pd.DataFrame, Sequence[str], pd.DataFrame -> pd.DataFrame | `LakeError` | as class | see class |
| `compute_fit` | Cross-sectional fit summary: median and mean R^2 and median adjusted R^2 of the daily regressions (adjusted R^2 compares models with different factor counts). | pd.DataFrame, str, str -> pd.DataFrame | `KeyError` | as class | see class |

### `RiskSnapshot` — `quant_cn.risk.risk_snapshot` (L5)
- **Purpose:** The model as of one session's close, ready for portfolio arithmetic: X (stocks x factors, country column = 1), F (factors x factors, daily variance) and specific vol. Portfolio variance = h^T X F X^T h + sum h^2 sigma^2.
- **Base:** none. **Depends on (injected):** none.
- **Used by:** `risk.RiskModel`, `risk.RiskDecomposer`, `risk.BaseRiskModel`, `risk.RiskModelValidator`, `portfolio.HoldingsRiskBuilder`.
- **Tests:** `tests/risk/test_risk_snapshot.py` (TC-RSN-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_covered_weights` | Restrict weights to stocks with exposures and specific risk. | pd.Series -> tuple[pd.Series, float] | — | as class | see class |
| `compute_variance` | Factor and specific variance of a portfolio (daily). | pd.Series -> tuple[float, float] | `QuantCnError` | as class | see class |
| `compute_exposure_vector` | Portfolio factor exposures b = X^T h. | pd.Series -> pd.Series | — | as class | see class |
| `compute_stock_cov` | Daily covariance between stocks implied by the model: X F X^T + diag(sigma^2). | list[str] -> pd.DataFrame | `KeyError` | as class | see class |
| `build_matrix` | Dense K x K matrix from FACTOR_COV rows of one session. | pd.DataFrame, list[str] -> np.ndarray | — | as class | see class |

### `SpecificRiskEstimator` — `quant_cn.risk.specific_risk_estimator` (L5)
- **Purpose:** Specific (idiosyncratic) volatility forecasts in three steps. (1) Time series: zero-mean EWMA of residual variance (specific_window, specific_half_life) with Newey-West lags (specific_nw_lags), and the residual count h in the window. (2) Per session: blend sigma = g sigma_ts + (1 - g) sigma_str with g = clip((h - min_obs) / (full_obs - min_obs), 0, 1) and sigma_str from StructuralSpecificRisk fitted on stocks with g = 1; then BayesianShrinker toward size-group means. (3) Volatility regime: lambda from the cap-weighted bias of residuals over the previous session's forecast; sigma = lambda x shrunk. method = ewma (g = 1), blended (0 < g < 1) or structural (g = 0).
- **Base:** none. **Depends on (injected):** RiskModelSettings, StructuralSpecificRisk, BayesianShrinker, VolatilityRegimeAdjuster.
- **Used by:** `risk.RiskModel`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_specific_risk_estimator.py` (TC-SRE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | RiskModelSettings, StructuralSpecificRisk, BayesianShrinker, VolatilityRegimeAdjuster -> None | — | callers of the class | — |
| `compute_time_series` | EWMA + Newey-West residual vol and residual counts for every session and stock. | pd.DataFrame -> tuple[pd.DataFrame, pd.DataFrame] | — | as class | see class |
| `compute_session` | Blended and shrunk specific vol of one session (before the regime multiplier). | np.ndarray, np.ndarray, np.ndarray, np.ndarray -> tuple[np.ndarray, np.ndarray] | — | as class | see class |
| `compute_final` | Apply the specific volatility regime multiplier and build SPECIFIC_RISK. | pd.DataFrame, pd.DataFrame, str \| None -> pd.DataFrame | `SchemaError` | as class | see class |

### `StructuralSpecificRisk` — `quant_cn.risk.structural_specific_risk` (L5)
- **Purpose:** Predict specific volatility from exposures (USE4 / CNE5 structural model): regress ln(sigma_ts) on the factor exposures (industry dummies and styles) over stocks with a full residual history, weighted by cap, then sigma_str = E0 exp(X b) with E0 = sum w sigma_ts / sum w exp(X b) over the fit set (removes the log-retransformation bias). Used for stocks whose residual history is shorter than `specific_full_obs`.
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `risk.SpecificRiskEstimator`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_structural_specific_risk.py` (TC-SSR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | — | callers of the class | — |
| `compute` | Structural specific vol for every stock of one session. | np.ndarray, np.ndarray, np.ndarray, np.ndarray -> np.ndarray | — | as class | see class |

### `VolatilityRegimeAdjuster` — `quant_cn.risk.volatility_regime_adjuster` (L5)
- **Purpose:** Scale risk forecasts by lambda_t so they track the current volatility regime: the cross-sectional bias statistic B_t^2 = weighted mean of (x_t / sigma_{t-1})^2 (factor returns over their forecast vol, equal weights; or specific returns over specific risk, cap weights) is averaged with an exponential kernel (half-life h, window 6 h) and lambda_t = sqrt(of that average). Multiplying variances by lambda_t^2 (vols by lambda_t) removes the bias a slow EWMA has right after a regime change. lambda at t uses B up to t.
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `risk.FactorCovarianceEstimator`, `risk.SpecificRiskEstimator`, `risk.RiskModelFactory`.
- **Tests:** `tests/risk/test_volatility_regime_adjuster.py` (TC-VRA-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | — | callers of the class | — |
| `compute_bias` | B_t^2 per session. | np.ndarray, np.ndarray, np.ndarray \| None -> np.ndarray | — | as class | see class |
| `compute_lambda` | lambda_t from the B_t^2 series. | pd.Series -> pd.Series | — | as class | see class |

### `StyleSpec` — `quant_cn.core.risk_model_settings` (L1)
- **Purpose:** One style factor: its descriptors with CNE5 weights and the factors it is orthogonalised against (RISK_FACTOR_LIST §1).
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `core.RiskModelSettings`, `risk.ExposureStandardizer`.
- **Tests:** `tests/core/test_risk_model_settings.py` (TC-RMS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `validate_weights` | Refuse non-positive descriptor weights. | — -> StyleSpec | `ValueError` | as class | see class |

### `ExternalSeriesSpec` — `quant_cn.core.risk_model_settings` (L1)
- **Purpose:** One external daily series behind a partial-beta descriptor (D-128, D-134): where it is in the lake and how its dates map to China sessions.
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `core.RiskModelSettings`, `risk.RiskInputLoader`.
- **Tests:** `tests/core/test_risk_model_settings.py` (TC-RMS-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ThemeBasketSpec` — `quant_cn.core.risk_model_settings` (L1)
- **Purpose:** A theme basket behind a partial-beta descriptor (D-130): the circ_mv-weighted return of a concept's current members (excluding the stock itself), from the concept's list date on.
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `core.RiskModelSettings`, `risk.RiskInputLoader`.
- **Tests:** `tests/core/test_risk_model_settings.py` (TC-RMS-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `RiskModelSettings` — `quant_cn.core.risk_model_settings` (L1)
- **Purpose:** Every tunable of the risk model in one typed object, CNE5 defaults (RISK_MODEL_DESIGN §1): estimation universe, style set, regression weights, covariance and specific-risk half-lives and lags, eigenfactor and volatility-regime adjustments.
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `core.Config`, `risk.ExposureStandardizer`, `risk.FactorCovarianceEstimator`, `risk.SpecificRiskEstimator`, `risk.RiskModelFactory`, `risk.RiskModel`, `pipeline.RiskModelStep`, `pipeline.RiskValidationWriter`.
- **Tests:** `tests/core/test_risk_model_settings.py` (TC-RMS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `validate_styles` | Orthogonalisation may only target styles listed earlier; full_obs > min_obs. | — -> RiskModelSettings | `ValueError` | as class | see class |
| `style_names` | Style factor names in configured order. | — -> list[str] | — | as class | see class |

### `RiskModelStep` — `quant_cn.pipeline.risk_model_step` (L6)
- **Purpose:** Fit the configured RiskModel from `settings.start` to the last universe session and write one file per year of each frame (derived/risk_exposure, risk_factor_return, risk_specific_return, risk_factor_cov, risk_specific_risk). Stage A per year: inputs (from the session before the year so the first regression has exposures at t-1) -> exposures -> factor returns and residuals. Stage B: factor covariance over the whole factor-return history. Stage C: specific risk from the residual history and each session's exposures (read back from derived.risk_exposure). Then refreshes the views, merges their digests (rebuilds are checked like features), writes the validation report (RiskValidationWriter) and the monitor-style returns (derived/reports/risk_<name>/monitor_returns.parquet, D-130). A full refit; seeded, so reruns are byte-identical.
- **Base:** BaseStep. **Depends on (injected):** LakeQuery, RiskInputLoader, RiskModel, TradingCalendar, ParquetWriter, DerivedViews, DeriveStep, RiskValidationWriter, RiskModelSettings.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_risk_model_step.py` (TC-RMST-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, RiskInputLoader, RiskModel, TradingCalendar, ParquetWriter, DerivedViews, DeriveStep, RiskValidationWriter, RiskModelSettings -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | Years from the model start to the last universe session. | — -> list[str] | `LakeError` | as class | see class |
| `run` | Refit the model over every year and write all frames. | str, ProgressHook \| None -> StepReport | `LakeError` | as class | see class |

### `RiskValidationWriter` — `quant_cn.pipeline.risk_validation_writer` (L6)
- **Purpose:** After a fit, test the stored model over the last `validation_sessions` forecast sessions and write derived/reports/risk_<name>/validation.parquet (RISK_VALIDATION): median / mean R^2 (whole history and window), the bias statistic of every factor, of `validation_portfolios` random long-only portfolios of `validation_names` stocks drawn from the names with a forecast on the first window session, and of each benchmark index (index_weight weights on or before the window start, held fixed), plus the summary rows share_in_band and median_bias over the random portfolios.
- **Base:** none. **Depends on (injected):** LakeQuery, LakeReader, RiskModelValidator, ParquetWriter, RiskModelSettings.
- **Used by:** `pipeline.RiskModelStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_risk_validation_writer.py` (TC-RVW-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, LakeReader, RiskModelValidator, ParquetWriter, RiskModelSettings -> None | — | callers of the class | — |
| `write` | Compute and persist the validation report. | pd.DataFrame, str -> pd.DataFrame | `LakeError` | as class | see class |

### `EmailFormat` — `quant_cn.visualization.email_format` (L7)
- **Purpose:** Display text of report numbers: YYYY-MM-DD, date with the Chinese weekday, signed %, vol %, CNY with separators, σ; colour of a signed number (red up, green down).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `visualization.MonitorReportRenderer`, `visualization.OpportunityReportRenderer`.
- **Tests:** `tests/visualization/test_email_html.py` (TC-EH-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `format_ymd` | YYYYMMDD -> YYYY-MM-DD | d: str \| None -> str | — | renderers | TC-EH-001 |
| `format_day` | header date with the Chinese weekday | d: str -> str | ValueError | renderers | TC-EH-001 |
| `format_pct` | signed percentage | v: float \| None, digits: int -> str | — | renderers | TC-EH-001 |
| `format_vol` | unsigned percentage, one decimal | v: float \| None -> str | — | renderers | TC-EH-001 |
| `format_yuan` | CNY with separators | v: float \| None -> str | — | renderers | TC-EH-001 |
| `format_sigma` | signed move in σ | v: float \| None -> str | — | renderers | TC-EH-001 |
| `get_color` | colour of a signed number | v: float \| None -> str | — | renderers | TC-EH-001 |

### `EmailHtml` — `quant_cn.visualization.email_html` (L7)
- **Purpose:** HTML that renders in Gmail and Apple Mail: escaped cells, header cells, tables, titled sections, missing-data sections, two-column pairs, signed bars drawn with cells, KPI tiles and the 960 px page shell (D-136).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `visualization.MonitorReportRenderer`, `visualization.OpportunityReportRenderer`, `visualization.SmallCapReportSection`.
- **Tests:** `tests/visualization/test_email_html.py` (TC-EH-002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_td` | one escaped cell | text, align, color, bold, mono, bg -> str | — | renderers | TC-EH-002 |
| `build_th` | one header cell | text, align -> str | — | renderers | TC-EH-002 |
| `build_table` | full-width table | head, rows -> str | — | renderers | TC-EH-002 |
| `build_section` | titled section rows | title, sub, body -> str | — | renderers | TC-EH-002 |
| `build_missing` | section saying the input is missing | title, file_name -> str | — | renderers | TC-EH-002 |
| `build_pair` | two sections side by side | left, right -> str | — | `visualization.MonitorReportRenderer` | TC-EH-002 |
| `build_bar` | signed bar from cells | v: float \| None, scale -> str | — | `visualization.MonitorReportRenderer` | TC-EH-002 |
| `build_tile` | KPI tile | label, value, note, color -> str | — | `visualization.MonitorReportRenderer` | TC-EH-002 |
| `build_page` | complete document | kicker, day, sub, summary, rows -> str | — | renderers | TC-EH-002 |

### `MonitorReportRenderer` — `quant_cn.visualization.monitor_report_renderer` (L7)
- **Purpose:** The 持仓监测 e-mail from holdings_risk / factor_monitor / etf_proxy: alerts first (position flags, RetailGauge ≥ 0.8, conditions met with the statement period, factor 2σ moves or vol ratio ≥ 1.5), tiles, positions by share of risk, style exposures, factor table, industries, national-team ETF; a missing document gives 数据缺失 sections.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `visualization.MorningReportBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/visualization/test_monitor_report_renderer.py` (TC-MRR-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `render` | the e-mail for a day | docs: Mapping, today: str -> MailContent | — | `visualization.MorningReportBuilder` | TC-MRR-001..004 |

### `ReportSection` — `quant_cn.visualization.report_section` (L7)
- **Purpose:** Abstract optional block of the 持仓监测 e-mail; subclasses set DOC (the app document they read) and build a summary line and section rows.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `visualization.MonitorReportRenderer`, `visualization.MacroReportSection`, `visualization.FuturesReportSection`.
- **Tests:** `tests/visualization/test_monitor_report_renderer.py` (TC-MRR-003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | summary-box line | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-MRR-003 |
| `build_rows` | section rows | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-MRR-003 |

### `FuturesReportSection` — `quant_cn.visualization.futures_report_section` (L7)
- **Purpose:** The 期货 block from futures_monitor.json: summary line with the signal count and the new ones named; a table of new signals only; 数据缺失 without the document.
- **Base:** ReportSection. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands` (passed to `MonitorReportRenderer` as a section).
- **Tests:** `tests/visualization/test_futures_report_section.py` (TC-FRS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | one-line summary | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-FRS-001 |
| `build_rows` | new-signal rows | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-FRS-002 |

### `VolatilityReportSection` — `quant_cn.visualization.volatility_report_section` (L7)
- **Purpose:** The 波动率 block from volatility_monitor.json: summary line with each index's value and 1-year percentile and the alert count (new ones named); a table of every index (value, change, percentile, range, date) with alerting lines in amber and the alert messages; 数据缺失 without the document.
- **Base:** ReportSection. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands` (passed to `MonitorReportRenderer` as a section).
- **Tests:** `tests/visualization/test_volatility_report_section.py` (TC-VRS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | one-line summary | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-VRS-001 |
| `build_rows` | every index plus alert rows | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-VRS-002 |

### `SmallCapReportSection` — `quant_cn.visualization.small_cap_report_section` (L7)
- **Purpose:** The 小盘观察 block from smallcap_watch.json: summary line naming triggered rows (new ones marked) and rows near their trigger; a table of every signal (group, name, value by unit, 3-year percentile, trigger, state, note) with triggered rows first in red and near rows amber; 数据缺失 without the document.
- **Base:** ReportSection. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands` (passed to `MonitorReportRenderer` as a section).
- **Tests:** `tests/visualization/test_small_cap_report_section.py` (TC-SRS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | one-line summary | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-SRS-001 |
| `build_rows` | every signal, triggered first | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-SRS-002 |

### `RatesFxReportSection` — `quant_cn.visualization.rates_fx_report_section` (L7)
- **Purpose:** The 利率汇率 block from rates_fx_monitor.json: summary line (10Y and USDCNH with one-week change and 5-year percentile, then alerts with new ones marked, or 没有提醒) and a table of the key rows (10Y, 30Y, term and credit spreads, 股债性价比, USDCNH, fixing gap, EUR/CNH, CNH/JPY, 中美利差) with alerting rows red; 数据缺失 without the document.
- **Base:** ReportSection. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands` (passed to `MonitorReportRenderer` as a section).
- **Tests:** `tests/visualization/test_rates_fx_report_section.py` (TC-RRS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | one-line summary | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-RRS-001 |
| `build_rows` | key rows, alerting red | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-RRS-002 |

### `SectorEarningsReportSection` — `quant_cn.visualization.sector_earnings_report_section` (L7)
- **Purpose:** The 财报季信号 block from sector_earnings_signal.json: summary line (season, firing sectors with pre / reaction / prior rally, new ones marked, record after a rally; 没有行业触发 when none) and a table of firing (red) and provisional sectors; "" when none shown; 数据缺失 without the document.
- **Base:** ReportSection. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands` (passed to `MonitorReportRenderer` as a section).
- **Tests:** `tests/visualization/test_sector_earnings_report_section.py` (TC-SER-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | one-line summary | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-SER-001 |
| `build_rows` | firing and provisional sectors | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-SER-002 |

### `BuybackMarketReportSection` — `quant_cn.visualization.buyback_market_report_section` (L7)
- **Purpose:** From buyback_monitor.json, the market side of buybacks and 增持, kinds apart: a summary line per kind (new programmes in the window by purpose or holder type, 专项贷款 count, live planned and executed totals) and a table of each kind's largest new programmes (at most 8) with purpose / holder type, funding, planned range and % of market cap.
- **Base:** ReportSection. **Depends on (injected):** none.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/visualization/test_buyback_market_report_section.py` (TC-BMR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | the summary-box line | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-BMR-001 |
| `build_rows` | the section rows | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-BMR-002 |

### `BuybackReportSection` — `quant_cn.visualization.buyback_report_section` (L7)
- **Purpose:** The 回购 block from buybacks.json: summary line (book events, count of new plans ≥ 2% of market cap) and a table of both; nothing without events.
- **Base:** ReportSection. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands` (passed to `MonitorReportRenderer` as a section).
- **Tests:** `tests/visualization/test_buyback_report_section.py` (TC-BRS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | one-line summary | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-BRS-001 |
| `build_rows` | section rows | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-BRS-002 |

### `EtfReportSection` — `quant_cn.visualization.etf_report_section` (L7)
- **Purpose:** The ETF 资金强度 summary line (per style: 过热 / 降温 / 正常, z, 20-day flow share of AUM); no rows (the ETF table is MonitorReportRenderer's).
- **Base:** ReportSection. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands` (passed to `MonitorReportRenderer` as a section).
- **Tests:** `tests/visualization/test_etf_report_section.py` (TC-ERS-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | one-line summary | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-ERS-001 |
| `build_rows` | no rows | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-ERS-001 |

### `CardShot` — `quant_cn.visualization.alert_message_builder` (L7)
- **Purpose:** Where an alert's picture is in the app: page hash (e.g. "#volatility"), CSS selector of the card, file stem of the screenshot.
- **Base:** none (frozen dataclass). **Depends on (injected):** —.
- **Used by:** `visualization.Alert`, `visualization.AlertMessageBuilder`, `visualization.CardScreenshotter`, `cli.ReportCommands`.
- **Tests:** `tests/visualization/test_alert_message_builder.py` (TC-AMB-001).

### `Alert` — `quant_cn.visualization.alert_message_builder` (L7)
- **Purpose:** One phone alert line: stable key (sent once per episode), trigger, plain-language text, optional CardShot.
- **Base:** none (frozen dataclass). **Depends on (injected):** —.
- **Used by:** `visualization.AlertMessageBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/visualization/test_alert_message_builder.py` (TC-AMB-001).

### `AlertMessageBuilder` — `quant_cn.visualization.alert_message_builder` (L7)
- **Purpose:** Plain-language phone alerts (D-153: no jargon or English abbreviations, numbers against their normal level): volatility flags (one line per index, its card), watchlist names in the buy range or with buy conditions met (their card), new futures signals (one line naming up to 3 families; a reversion spread far from normal gets its own line, D-156), new CPI / PPI / PMI prints (their card); only triggers switched on. `build_message` joins the new alerts under a day header with an overflow note.
- **Base:** none. **Depends on (injected):** triggers (Sequence[str]).
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/visualization/test_alert_message_builder.py` (TC-AMB-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_alerts` | every active alert in DOCS order | docs: Mapping[str, dict \| None] -> list[Alert] | — | `cli.ReportCommands` | TC-AMB-001..002, TC-AMB-004..006 |
| `build_message` | one phone message from the new alerts | alerts, day: str, limit: int -> str | — | `cli.ReportCommands` | TC-AMB-003 |

### `CardScreenshotter` — `quant_cn.visualization.card_screenshotter` (L7)
- **Purpose:** One PNG per CardShot by running `apps/chain_web/tests/shot_cards.mjs` with Node (Playwright against the running app, phone style that hides small print, 3x scale); pictures are optional, so failures are logged and give no file.
- **Base:** none. **Depends on (injected):** node: Path, script: Path, out_dir: Path, base_url: str, runner | None.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/visualization/test_card_screenshotter.py` (TC-CSS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | screenshot every card, return the saved files | shots: Sequence[CardShot] -> list[Path] | — | `cli.ReportCommands` | TC-CSS-001..002 |

### `MacroReportSection` — `quant_cn.visualization.macro_report_section` (L7)
- **Purpose:** The 宏观 block of the 持仓监测 e-mail from macro_monitor.json: one summary line (CPI, PPI, 制造业 PMI, M1 − M2, 社融存量) daily; the full table (latest, previous, change, 5-year percentile, extremes in amber, new marker) only on days with a new print; 数据缺失 without the document.
- **Base:** ReportSection. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands` (passed to `MonitorReportRenderer` as a section).
- **Tests:** `tests/visualization/test_macro_report_section.py` (TC-MRS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | one-line summary | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-MRS-001 |
| `build_rows` | section rows | doc: dict \| None -> str | — | `visualization.MonitorReportRenderer` | TC-MRS-002 |

### `OpportunityReportRenderer` — `quant_cn.visualization.opportunity_report_renderer` (L7)
- **Purpose:** The 机会清单 e-mail: plan 21's list (new first, near-misses with what is missing; "not live" until opportunities.json exists) and the watchlist sorted buy / near / wait with one mark per condition.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `visualization.MorningReportBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/visualization/test_opportunity_report_renderer.py` (TC-ORR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `render` | the e-mail for a day | docs: Mapping, today: str -> MailContent | — | `visualization.MorningReportBuilder` | TC-ORR-001..002 |

### `ReportOutcome` — `quant_cn.visualization.morning_report_builder` (L7)
- **Purpose:** What happened to one e-mail: written (path), sent (subject) or skipped (reason).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `visualization.MorningReportBuilder.run`.
- **Tests:** `tests/visualization/test_morning_report_builder.py` (TC-MRB-002).

### `MorningReportBuilder` — `quant_cn.visualization.morning_report_builder` (L7)
- **Purpose:** Read the app's JSON documents (missing = None), render both e-mails, skip an e-mail whose data is older than the last trading session (log line, no send), and write the HTML (dry run) or send through MailSender.
- **Base:** none. **Depends on (injected):** data folder, `MonitorReportRenderer`, `OpportunityReportRenderer`, `MailSender` | None.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/visualization/test_morning_report_builder.py` (TC-MRB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_documents` | parsed documents by name | () -> dict | LakeError | `build`, `run` | TC-MRB-001 |
| `build` | both e-mails, no freshness check | today: str -> dict[str, MailContent] | LakeError | callers | TC-MRB-001 |
| `run` | freshness check, then write or send | today, last_session: str, out_dir: Path \| None -> list[ReportOutcome] | LakeError, ConfigError | `cli.ReportCommands` | TC-MRB-001..003 |

### `RiskChart` — `quant_cn.visualization.risk_chart` (L7)
- **Purpose:** Three views of the risk model (plan 05 phase 5), over frames only: "cumulative" (FACTOR_RETURN) compounded returns of the chosen factors, one line each, labelled at the line end so identity does not rest on colour; "correlation" (FACTOR_COV) the factor correlation matrix of one session as a diverging heatmap (-1..1); "decomposition" (RISK_DECOMP) each factor's contribution to a portfolio's annualised volatility as horizontal bars (specific risk as its own bar), total in the title.
- **Base:** BaseChart. **Depends on (injected):** ChartTheme, Kind, Sequence[str], str | None, str | None, DateCodec | None, int, int.
- **Used by:** `research_space/notebooks/20261111_risk_model_validation.ipynb`.
- **Tests:** `tests/visualization/test_risk_chart.py` (TC-RC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ChartTheme, Kind, Sequence[str], str \| None, str \| None, DateCodec \| None, int, int -> None | — | callers of the class | — |
| `build_figure` | The figure for `kind`. | pd.DataFrame -> go.Figure | `SchemaError`, `ValueError` | as class | see class |

### `LabelSource` — `quant_cn.core.label_source` (L1)
- **Purpose:** One existing label file to import into the parquet label store: which set it feeds, the period it describes, where each record's document key and public date come from (plan 28 ph0, D-161).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `cli.DocumentCommands`, `industry_graph.LegacyLabelImporter`.
- **Tests:** `tests/core/test_label_source.py` (TC-LSR-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `is_parquet` | Whether the file is parquet (else jsonl). | — -> bool | — | `industry_graph.LegacyLabelImporter` | TC-LSR-001 |
| `read_all` | The sources listed in a label-sources YAML file, in file order. | Path -> list[LabelSource] | `ConfigError` | `cli.DocumentCommands._run_import_labels` | TC-LSR-003 |

### `GraphStore` — `quant_cn.lake.graph_store` (L2)
- **Purpose:** Hold the plan 28 graph tables (entity_map, company_edge, edge_span) as one parquet file each under derived/graph/; a write replaces the table atomically through ParquetWriter, rows in the order given (same frame → same file); only TABLES allowed.
- **Base:** none. **Depends on (injected):** ParquetWriter.
- **Used by:** `industry_graph.GraphBuilder`, `cli.DocumentCommands`, `lake` (meta/runs/plan28_entities.py).
- **Tests:** `tests/lake/test_graph_store.py` (TC-GS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire writer and lake root | ParquetWriter, Path -> None | — | callers of the class | — |
| `write` | replace one graph table | str, DataFrame -> Path | `SchemaError`, `LakeError` | as class | TC-GS-001, TC-GS-003 |
| `read` | one graph table (empty when not written) | str, list[str] \| None -> DataFrame | `SchemaError` | as class | TC-GS-002, TC-GS-003 |
| `list_tables` | the graph tables written so far | — -> list[str] | — | as class | TC-GS-003 |

### `LabelStore` — `quant_cn.lake.label_store` (L2)
- **Purpose:** Hold every label set as parquet under `derived/labels/<label_set>/year=<YYYY>/part-0.parquet`; one row per (company, document) with period, known_on, event_date, taxonomy_version, source and the record as JSON payload; writes upsert on (ts_code, doc_key).
- **Base:** none. **Depends on (injected):** ParquetWriter, Path, DateCodec.
- **Used by:** `industry_graph.LegacyLabelImporter`, `cli.DocumentCommands`, `portfolio.BuybackMonitorBuilder`, `cli.ReportCommands`.
- **Tests:** `tests/lake/test_label_store.py` (TC-LBS-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ParquetWriter, Path, DateCodec -> None | — | callers of the class | — |
| `write` | Upsert rows of one label set into year partitions of the period; `replace_source` first removes that source's earlier rows from every partition. | str, pd.DataFrame, str \| None -> list[Path] | `SchemaError`, `LakeError` | `industry_graph.LegacyLabelImporter.run` | TC-LBS-001, 002, 004, 005 |
| `read` | Rows of one label set, optionally for some codes and as known on a date (known_on <= as_of). | str, list[str] \| None, str \| None -> pd.DataFrame | `SchemaError` | as class | TC-LBS-001, 003 |
| `list_sets` | Names of the label sets on disk. | — -> list[str] | — | as class | TC-LBS-001 |

### `LegacyLabelImporter` — `quant_cn.industry_graph.legacy_label_importer` (L4)
- **Purpose:** Turn the label files of earlier runs (config/label_sources.yaml) into LabelStore rows: ts_code, doc_key, doc_type, period ("2026Q3" -> 20260930), known_on (document list date or the record's date field), taxonomy_version, JSON payload; company-only records take their anchor set's document; bad codes and documents public before their period ended are skipped.
- **Base:** none. **Depends on (injected):** LabelStore, LakeQuery, Path, TickerNormalizer.
- **Used by:** `cli.DocumentCommands`.
- **Tests:** `tests/industry_graph/test_legacy_label_importer.py` (TC-LLI-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LabelStore, LakeQuery, Path, TickerNormalizer -> None | — | callers of the class | — |
| `run` | Import every source in order into the store; each source replaces its own earlier rows. | Sequence[LabelSource] -> dict[str, int] | `LakeError`, `SchemaError`, `FileNotFoundError` | `cli.DocumentCommands._run_import_labels` | TC-LLI-004, 007 |
| `read_dates` | Public date of every listed document id (CNINFO ann_id, Eastmoney info_code) from the curated catalog views; missing views skipped. | — -> dict[str, str] | `LakeError` | as class | TC-LLI-006 |
| `read_records` | The records of one label file, without the keys listed in its exclude_file. | LabelSource -> list[dict] | `FileNotFoundError` | as class | TC-LLI-004, 007 |
| `build_rows` | LabelStore rows of one source's records. | LabelSource, list[dict], dict, dict -> pd.DataFrame | — | as class | TC-LLI-001..003, 005 |

### `RetailGaugeSettings` — `quant_cn.core.retail_gauge_settings` (L1)
- **Purpose:** RetailGauge feature windows, LightGBM params, label clip, training minimum, avoid / leaving / inflow thresholds, D-167 streak rule (persist_n, persist_step), retrain months and model version from config/retail_gauge.yaml (plan 21).
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `calculation.RetailGaugeMatrices`, `calculation.RetailGaugeFeatureBuilder`, `calculation.RetailGaugeModel`, `calculation.RetailGaugeNowcaster`, `calculation.RetailGaugeEvaluator`, `cli.GaugeCommands`.
- **Tests:** `tests/core/test_retail_gauge_settings.py` (TC-RGS-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read config/retail_gauge.yaml (defaults when missing) | repo_root: Path -> RetailGaugeSettings | ConfigError | `cli.GaugeCommands` | TC-RGS-001 |

### `DatedTableStore` — `quant_cn.lake.dated_table_store` (L2)
- **Purpose:** Own derived/<name>/year=YYYY/part-0.parquet tables keyed by a YYYYMMDD column, read and written without the DuckDB catalog (a read-only session can update them): written dates replace their stored rows, other dates are kept; read some years; read one whole derived report (plan 21).
- **Base:** none. **Depends on (injected):** ParquetWriter.
- **Used by:** `calculation.RetailGaugeFeatureBuilder`, `calculation.RetailGaugeNowcaster`, `cli.GaugeCommands`, `portfolio.OpportunityScreen`, `factor.FactorFactory`, `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_dated_table_store.py` (TC-DTW-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `write` | replace the frame's dates in the year files | name: str, frame: DataFrame, date_column: str -> list[Path] | LakeError | `calculation.RetailGaugeFeatureBuilder`, `calculation.RetailGaugeNowcaster` | TC-DTW-001 |
| `read` | stored rows of some years (empty when none) | name: str, years: Sequence[str] -> DataFrame | LakeError | `calculation.RetailGaugeNowcaster` | TC-DTW-001..002 |
| `read_report` | one whole table under derived/ | rel_path: str -> DataFrame | LakeError | `calculation.RetailGaugeNowcaster` | TC-DTW-002 |

### `GaugeCommands` — `quant_cn.gauge_commands` (L8)
- **Purpose:** CLI commands `retail-gauge` (daily readings for every session in [start, end], one quarter at a time, models trained on first use), `retail-gauge-backtest` (walk-forward + evaluation, summary printed) (plan 21 ph3) and `opportunity-list` (OpportunityScreen on a date, holdings from PositionsBook, prints the list) (ph4); all refresh the derived views.
- **Base:** none. **Depends on (injected):** Console.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/test_cli.py` (TC-QCC-019..020).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_parser` | add the three subcommands | sub -> None | — | `cli.QuantCnCli` | TC-QCC-019..020 |

### `OpportunitySettings` — `quant_cn.core.opportunity_settings` (L1)
- **Purpose:** Universe (min_circ_mv 亿, exclude_st, gauge_max_age_days), rule thresholds (inflow_weeks, np_yoy_min, np_qoq_min, valuation_field / years, fit_weight / styles), required rules and list sizes (top_n, near_n) from config/discovery_rules.yaml section `opportunity` (plan 21 ph4).
- **Base:** BaseModel. **Depends on (injected):** none.
- **Used by:** `portfolio.OpportunityRules`, `portfolio.OpportunityScreen`, `portfolio.StyleFitChecker`, `cli.GaugeCommands`.
- **Tests:** `tests/core/test_opportunity_settings.py` (TC-OPS-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read the `opportunity` section (defaults when file or section missing) | repo_root: Path -> OpportunitySettings | ConfigError | `cli.GaugeCommands` | TC-OPS-001 |
| `validate_required` | refuse unknown required rule names | value: list[str] -> list[str] | ValueError | pydantic | TC-OPS-001 |

### `ValuationHistoryReader` — `quant_cn.lake.valuation_history_reader` (L2)
- **Purpose:** Latest pb or pe_ttm on or before a date (0 when empty, i.e. a loss) and the median / count of its positive values over [start, as_of] (plan 21 ph4).
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `portfolio.OpportunityScreen`, `cli.GaugeCommands`.
- **Tests:** `tests/lake/test_valuation_history_reader.py` (TC-VHR-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read` | latest value and median per code | codes, field, start, as_of -> DataFrame (value, median, n_days) | LakeError | `portfolio.OpportunityScreen` | TC-VHR-001 |

### `OpportunityRules` — `quant_cn.portfolio.opportunity_rules` (L5)
- **Purpose:** Evaluate the opportunity rules on a metrics frame and rank: listed (every rule, top_n, lowest gauge pct first), near (one non-required rule missing, near_n); avoid dropped first; NaN never hits; is_new vs the previous list (plan 21 ph4).
- **Base:** none. **Depends on (injected):** OpportunitySettings.
- **Used by:** `portfolio.OpportunityScreen`, `cli.GaugeCommands`.
- **Tests:** `tests/portfolio/test_opportunity_rules.py` (TC-OPR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_hits` | bool hit per rule | metrics: DataFrame -> DataFrame[RULES] | KeyError | `portfolio.OpportunityScreen` | TC-OPR-001 |
| `build_list` | ranked listed + near-miss rows | metrics: DataFrame, previous: set[str] -> DataFrame | KeyError | `portfolio.OpportunityScreen` | TC-OPR-002..003 |

### `StyleFitChecker` — `quant_cn.portfolio.style_fit_checker` (L5)
- **Purpose:** b = X'h over styles (no industries / country); candidate at weight a gives (1 - a) b + a x_c; fits when no top-`fit_styles` |b_k| grows; empty book fits all; uncovered candidate NaN (plan 21 ph4).
- **Base:** none. **Depends on (injected):** OpportunitySettings.
- **Used by:** `portfolio.OpportunityScreen`, `cli.GaugeCommands`.
- **Tests:** `tests/portfolio/test_style_fit_checker.py` (TC-SFC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute` | fit, styles checked, delta per candidate | snap: RiskSnapshot, weights: Series, codes: list[str] -> DataFrame | — | `portfolio.OpportunityScreen` | TC-SFC-001..002 |

### `OpportunityDocument` — `quant_cn.portfolio.opportunity_document` (L5)
- **Purpose:** Turn one session's opportunity list and the previous stored list into opportunities.json: rows ordered new listed, stayed listed, near (rules_hit / missing as lists, numbers None when unknown), dropped names, the rule thresholds (plan 21 ph5).
- **Base:** none. **Depends on (injected):** OpportunitySettings.
- **Used by:** `cli.GaugeCommands`.
- **Tests:** `tests/portfolio/test_opportunity_document.py` (TC-OPD-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the document | frame: DataFrame, previous: DataFrame, as_of: str -> dict | — | `cli.GaugeCommands` | TC-OPD-001 |
| `write` | write opportunities.json | doc: dict, out_dir: Path -> Path | LakeError | `cli.GaugeCommands` | TC-OPD-002 |

### `OpportunityScreen` — `quant_cn.portfolio.opportunity_screen` (L5)
- **Purpose:** Daily opportunity list on the last daily_basic session: universe (free-float cap, ST, holdings, recent RetailGauge reading; only leaving names when required), signal row (ChipStructureReader), profit YoY / QoQ (CompanyCyclePanel on StatementVersionReader versions), valuation vs its own median (ValuationHistoryReader), fit (StyleFitChecker on the latest risk snapshot), OpportunityRules ranking -> derived/opportunity_list (plan 21 ph4).
- **Base:** none. **Depends on (injected):** OpportunitySettings, LakeQuery, ChipStructureReader, ValuationHistoryReader, StatementVersionReader, CompanyCyclePanel, BaseRiskModel, OpportunityRules, StyleFitChecker, DatedTableStore.
- **Used by:** `cli.GaugeCommands`.
- **Tests:** `tests/portfolio/test_opportunity_screen.py` (TC-OSC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the list on a session | as_of: str, book: PositionsBook -> DataFrame (OUTPUT_COLUMNS) | LakeError | `cli.GaugeCommands` | TC-OSC-001..002 |
| `write` | store into derived/opportunity_list | frame: DataFrame -> list[Path] | LakeError | `cli.GaugeCommands` | TC-OSC-001 |
| `read_previous` | the last stored list before a session | session: str -> DataFrame | LakeError | `cli.GaugeCommands` | TC-OSC-001 |

### `UpdateStep` — `quant_cn.core.update_all_settings` (L1)
- **Purpose:** One update-all step: name, make target, `needs` (steps that must succeed first), optional output JSON in APP_DATA whose `as_of` is recorded, timeout in minutes, extra attempts (0–3).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.UpdateAllSettings`, `pipeline.UpdateAllRunner`.
- **Tests:** `tests/core/test_update_all_settings.py` (TC-UAS-001).

### `UpdateAllSettings` — `quant_cn.core.update_all_settings` (L1)
- **Purpose:** The ordered steps of `update-all` from config/update_all.yaml; unique names, each need names an earlier step; default timeout, output lines kept for a failed step, runs per step in task_status.json (plan 38, D-181).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `pipeline.UpdateAllRunner`, `cli.UpdateCommands`.
- **Tests:** `tests/core/test_update_all_settings.py` (TC-UAS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | read config/update_all.yaml | repo_root: Path -> UpdateAllSettings | ConfigError | `cli.UpdateCommands` | TC-UAS-001..002 |
| `find_missing_targets` | step targets the Makefile does not define | makefile: Path -> list[str] | ConfigError | `cli.UpdateCommands` | TC-UAS-001 |
| `list_steps` | all steps, only some, or from one on, config order | only, start -> list[UpdateStep] | ConfigError | `cli.UpdateCommands` | TC-UAS-003 |
| `get_timeout_s` | step time limit in seconds | step -> int | — | `pipeline.UpdateAllRunner` | TC-UAS-003 |

### `TaskLog` — `quant_cn.lake.task_log` (L2)
- **Purpose:** The update task ledger (D-181): one zstd parquet part per step, `meta/task_log/part-<run_id>-<seq>.parquet`, written tmp + rename without the DuckDB catalog so the steps keep the writer lock; rows never rewritten; `meta.task_log` view over all parts.
- **Base:** none. **Depends on (injected):** lake root.
- **Used by:** `pipeline.UpdateAllRunner`, `lake.LakeCatalog`, `pipeline.TaskStatusBuilder`, `cli.UpdateCommands`.
- **Tests:** `tests/lake/test_task_log.py` (TC-TKL-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_glob` | glob of the part files | -> str | — | `lake.TaskLog.refresh_view` | TC-TKL-003 |
| `write_row` | persist one step row | row: Mapping -> Path | LakeError | `pipeline.UpdateAllRunner` | TC-TKL-001 |
| `read_rows` | every row in (run_id, seq) order | -> DataFrame | LakeError | `pipeline.TaskStatusBuilder` | TC-TKL-002 |
| `refresh_view` | (re)create or drop meta.task_log | connection -> None | LakeError | `lake.LakeCatalog`, `cli.UpdateCommands` | TC-TKL-003 |

### `TargetRunner` — `quant_cn.pipeline.update_all_runner` (L6)
- **Purpose:** Structural type of the process runner UpdateAllRunner calls (MakeTargetRunner or a test fake).
- **Base:** Protocol. **Depends on (injected):** —.
- **Used by:** `pipeline.UpdateAllRunner`.
- **Tests:** `tests/pipeline/test_update_all_runner.py` (TC-UAR-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run_target` | run one make target | target, timeout_s, tail_lines -> (int or None, list[str]) | — | `pipeline.UpdateAllRunner` | TC-UAR-001 |

### `MakeTargetRunner` — `quant_cn.pipeline.make_target_runner` (L6)
- **Purpose:** `make <target>` in the repo root as a subprocess (fixed argv, no shell), stdout and stderr merged and echoed line by line, last lines kept; killed by a timer at the limit (exit None); a make that cannot start returns 127.
- **Base:** none. **Depends on (injected):** repo root, make executable, echo stream.
- **Used by:** `cli.UpdateCommands`.
- **Tests:** `tests/pipeline/test_update_all_runner.py` (TC-MKR-001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run_target` | run one target to the end or the limit | target, timeout_s, tail_lines -> (int or None, list[str]) | — | `pipeline.UpdateAllRunner` | TC-MKR-001 |

### `UpdateAllRunner` — `quant_cn.pipeline.update_all_runner` (L6)
- **Purpose:** Run the selected steps in config order (D-181): a failed step does not stop the run; a step whose needs failed or were skipped in this run is skipped (needs outside the selection count as met); `retry` extra attempts; one ledger row per step right after it ends, with the output JSON `as_of` of an ok step.
- **Base:** none. **Depends on (injected):** UpdateAllSettings, TaskLog, TargetRunner, Clock, app data dir.
- **Used by:** `cli.UpdateCommands`.
- **Tests:** `tests/pipeline/test_update_all_runner.py` (TC-UAR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | run and record the steps | steps, trigger -> list[dict] | LakeError | `cli.UpdateCommands` | TC-UAR-001..003 |

### `TaskStatusBuilder` — `quant_cn.pipeline.task_status_builder` (L6)
- **Purpose:** task_status.json for the app panel and e-mail line: latest run (id, trigger, start, end, counts, steps with exit code, as_of, last message line) and per configured step its last status, last success time, last as_of, recent history.
- **Base:** none. **Depends on (injected):** TaskLog, history length.
- **Used by:** `cli.UpdateCommands`.
- **Tests:** `tests/pipeline/test_task_status_builder.py` (TC-TSB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the status document | task_names -> dict | LakeError | `cli.UpdateCommands` | TC-TSB-001..002 |
| `write` | write task_status.json atomically | out_dir, task_names -> Path | LakeError | `cli.UpdateCommands` | TC-TSB-002 |

### `UpdateCommands` — `quant_cn.update_commands` (L8)
- **Purpose:** CLI `update-all --out [--only] [--from] [--dry-run] [--with-report] [--trigger]`: check targets against the Makefile, run the steps (UpdateAllRunner + MakeTargetRunner), print a summary, write task_status.json, refresh meta.task_log (a held lock only warns); exit 1 when a step failed.
- **Base:** none. **Depends on (injected):** Console, repo root.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/test_update_commands.py` (TC-UPC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_parser` | add the `update-all` subcommand | sub -> None | — | `cli.QuantCnCli` | TC-UPC-001..002 |

### `TaskStatusReportSection` — `quant_cn.visualization.task_status_report_section` (L7)
- **Purpose:** From task_status.json: summary line "数据更新 <time>（自动/手动）：n/m 成功；失败：…；跳过 k。" and, only when a step failed or was skipped, a 数据更新 table (failed first, last output line); nothing without a run.
- **Base:** ReportSection. **Depends on (injected):** —.
- **Used by:** `cli.ReportCommands`.
- **Tests:** `tests/visualization/test_task_status_report_section.py` (TC-TSR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_summary` | the 数据更新 line | doc -> str | — | `visualization.MonitorReportRenderer` | TC-TSR-001 |
| `build_rows` | failed / skipped steps table | doc -> str | — | `visualization.MonitorReportRenderer` | TC-TSR-002 |

## C. Abstract base classes / extension points

| Class | Module | Layer | Purpose | Abstract methods (purpose each) | Known subclasses | Added |
|---|---|---|---|---|---|---|
| `BaseApiClient` | `quant_cn.core.base_api_client` | 1 | Abstract vendor client: one logical query returns all pages as one DataFrame. | `query`: Run one query and return every row across pages. | `AkshareClient`, `BaostockClient`, `TushareClient`, `BaseWebClient` | 2026-09-27 |
| `BaseFetchLog` | `quant_cn.core.base_fetch_log` | 1 | Abstract record of which (dataset, key) pairs are fully downloaded. | `read_done_keys`: All keys recorded as done for a dataset.; `mark_done`: Record a finished key, replacing any earlier record for it.; `save`: Make recorded keys durable (e.g. write the parquet mirror). | `FetchLog` | 2026-09-27 |
| `BaseFetcher` | `quant_cn.core.base_fetcher` | 1 | Download one dataset as a sequence of keys | `list_keys`: All fetch keys for [start, end], ascending.; `build_params`: API parameters for one key. | `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher`, `DateWindowFetcher` | 2026-09-27 |
| `BaseRunLog` | `quant_cn.core.base_run_log` | 1 | Abstract append-only log of runs and per-key events | `open_run`: Open a run and return its id.; `record_event`: Append one event (fetched / skipped / empty / failed / blocked).; `close_run`: Close a run with its final status. | `RunLog` | 2026-09-27 |
| `BaseStep` | `quant_cn.core.base_step` | 1 | Abstract unit of pipeline work: list its units, then run and report. | `name`: Step name shown in progress and reports.; `list_units`: Compute the work units (e.g. keys) just before running.; `run`: Do the work listed by `list_units`. | `CompactStep`, `DeriveStep`, `FetchStep`, `EvaluationStep`, `FeatureStep`, `UniverseStep`, `RiskModelStep` | 2026-09-27 |
| `BaseStore` | `quant_cn.core.base_store` | 1 | Abstract sink for raw fetch results and curated partitions. | `write_raw`: Persist one fetch key's rows atomically.; `write_curated`: Replace one curated partition atomically after validating its schema. | `ParquetWriter` | 2026-09-27 |
| `MessageSender` | `quant_cn.core.message_sender` | 1 | Abstract channel for one short text to one handle (plan 22). | `run`: Deliver `text` to `handle`. | `IMessageSender` | 2026-11-13 |
| `BaseChecker` | `quant_cn.core.docs.base_checker` | 1 | Abstract repository check: inspect the tree, return findings (empty = pass). | `run`: Run the check over the repository. | `ContractChecker`, `IndexChecker`, `NameChecker`, `PlanStatusChecker`, `ResearchLogChecker`, `SizeChecker` | 2026-09-27 |
| `BaseFactor` | `quant_cn.factor.base_factor` | 5 | Abstract factor: declares which inputs, fundamentals fields and daily_basic columns it needs and how many sessions of price history before the first output date | `compute_raw`: The raw factor value per stock and session. | `EarningsYieldFactor`, `MomentumFactor`, `ProfitGrowthFactor`, `ReversalFactor`, `RoeFactor`, `TurnoverFactor`, `PricingGapFactor`, `RetailGaugeFactor` | 2026-09-27 |
| `BaseRunner` | `quant_cn.pipeline.runner` | 6 | Extension point for how steps are executed (local now, Prefect later, D-022) | `run`: Execute steps in order under one run id. | `PrefectRunner`, `LocalRunner` | 2026-09-27 |
| `BaseChart` | `quant_cn.visualization.base_chart` | 7 | Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never objects from other packages) | `build_figure`: Build the unthemed figure from the input frame. | `FactorChart`, `PriceChart`, `RiskChart` | 2026-09-27 |
| `BaseWebClient` | `quant_cn.data_loading.base_web_client` | 3 | Base for vendor clients that page a public website's JSON API (CNINFO, Eastmoney). | `get_vendor_name`: Short vendor name used in error messages. | `CninfoClient`, `EastmoneyReportClient` | 2026-11-07 |
| `BaseHtmlListClient` | `quant_cn.data_loading.base_html_list_client` | 3 | Base for clients of sites that list monthly releases on paged HTML pages and publish them as HTML tables. | `is_wanted`: whether a list link is a release to read. | `NbsHousePriceClient`, `NppaGameClient` | 2026-11-17 |
| `BaseEdgeReader` | `quant_cn.quant_cn.industry_graph.base_edge_reader` | 4 | Base of the plan 28 ph4 readers that list the raw edges of one label-store row. | `list_items`: the raw edges of one label-store row. | `CounterpartyEdgeReader`, `TopFiveEdgeReader`, `DealEdgeReader` | 2026-11-16 |
| `BaseLlmClient` | `quant_cn.quant_cn.core.base_llm_client` | 1 | Abstract chat-completion client that returns a JSON object: one system prompt, one user message, an optional model override. | `fetch_json`: Ask the model and return its answer parsed as a JSON object. |  | 2026-11-07 |
| `ReportSection` | `quant_cn.visualization.report_section` | 7 | Optional block of the 持仓监测 e-mail fed by one app document (DOC). | `build_summary`: The block's line for the summary box.; `build_rows`: The block's section rows. | `MacroReportSection`, `FuturesReportSection`, `EtfReportSection`, `BuybackReportSection`, `BuybackMarketReportSection` | 2026-11-13 |
| `BaseRiskModel` | `quant_cn.risk.base_risk_model` | 5 | Abstract risk model: produces the RISK_EXPOSURE / FACTOR_RETURN / FACTOR_COV / SPECIFIC_RISK frames for a pipeline step and answers portfolio-risk questions for a session from those frames. | `load_snapshot`: The fitted model as of a session. | `RiskModel` | 2026-11-11 |
| `BaseQuotedExtractor` | `quant_cn.industry_graph.base_quoted_extractor` | 4 | Base of the plan 28 ph2 document extractors: prompt, per-item validation, quote check. | `item_model`: the pydantic model of one reply item.; `list_pages`: the pages of a document to send.; `check_item`: stored fields of one checked item, or None to drop it. | `InquiryCustomerExtractor`, `IrCustomerExtractor`, `ProspectusExtractor`, `DealExtractor`, `OperatingDataExtractor`, `BrokerCustomerExtractor` | 2026-11-15 |

## D. Exceptions

| Class | Module | Parent | Purpose / raised when | Raised by | Added |
|---|---|---|---|---|---|
| `QuantCnError` | `quant_cn.core.exceptions` | `Exception` | Root of every exception the package raises, so callers catch project errors in one place. | `pipeline.LocalRunner.run`, `cli.QuantCnCli.run`, `core.ConfigError`, `core.DataSourceError`, `core.LakeError`, `core.SchemaError`, `pipeline.PrefectRunner` | 2026-09-27 |
| `ConfigError` | `quant_cn.core.exceptions` | `QuantCnError` | Configuration is missing, malformed or unsafe (e.g. lake root inside the repository). | `core.Config.load`, `core.Config.get_dataset`, `data_loading.TushareClient`, `data_loading.FetcherFactory.build`, `pipeline.DownloadPipeline.run`, `pipeline.CuratePipeline`, `factor.FactorFactory`, `data_loading.DocumentDownloader`, `core.SmallCapWatchSettings.load` | 2026-09-27 |
| `SchemaError` | `quant_cn.core.exceptions` | `QuantCnError` | A DataFrame does not satisfy its declared Schema (columns, dtypes, primary key). | `core.Schema.normalize`, `core.Schema.validate` | 2026-09-27 |
| `DataSourceError` | `quant_cn.core.exceptions` | `QuantCnError` | The external data source failed: API error code, retries exhausted, malformed response. | `data_loading.TushareClient.query`, `core.BaseFetcher.run`, `core.PermissionDeniedError`, `data_loading.AkshareClient`, `data_loading.BaostockClient`, `data_loading.DocumentDownloader`, `data_loading.RequestPacer` | 2026-09-27 |
| `PermissionDeniedError` | `quant_cn.core.exceptions` | `DataSourceError` | The account lacks permission (points) for an endpoint; the dataset is blocked, not broken. | `data_loading.TushareClient.query`, `pipeline.LocalRunner.run`, `pipeline.PrefectRunner` | 2026-09-27 |
| `LakeError` | `quant_cn.core.exceptions` | `QuantCnError` | The local lake cannot be read or written: missing dataset, failed atomic write, bad catalog. | `lake.ParquetWriter`, `lake.TradingCalendar`, `lake.LakeQuery.sql`, `portfolio.SmallCapWatchBuilder`, `cli.QuantCnCli`, `lake.Compactor`, `pipeline.DownloadPipeline`, `lake.FetchLog`, `lake.LakeCatalog`, `lake.RunLog`, `pipeline.DeriveStep`, `lake.DerivedViews`, `lake.PitAligner`, `lake.ProjectCatalog`, `lake.QualityViews`, `lake.RebuildAudit`, `lake.LakeReader`, `lake.TickerAliasMap`, `data_loading.DocumentDownloader`, `lake.DocumentViews`, `cli.DocumentCommands`, `portfolio.EtfProxyBuilder`, `portfolio.BuybackMonitorBuilder` | 2026-09-27 |

## E. Schemas (DataFrame / typed records)

| Schema | Module | Purpose | Index | Columns (dtype) | Invariants | Produced by | Consumed by | Added |
|---|---|---|---|---|---|---|---|---|
| `PRICE_PANEL` | `quant_cn.core.frames` | daily bars with adjustment factor and adjusted close | long; key (trade_date, ts_code) | trade_date (string), ts_code (string), open (float64), high (float64), low (float64), close (float64), pre_close (float64), vol (float64), amount (float64), adj_factor (float64), close_adj (float64) | key unique and non-null | `lake.LakeQuery.read_prices` | `visualization.PriceChart`, factors, engine | 2026-09-27 |
| `FUNDAMENTALS_PIT` | `quant_cn.core.frames` | point-in-time fundamentals, one value per field per trading day | long; key (trade_date, ts_code, field) | trade_date (string), ts_code (string), field (string), value (float64), end_date (string), ann_date (string) | key unique and non-null | `lake.PitAligner.read_aligned` | factors (plan 04) | 2026-09-27 |
| `VIX_PANEL` | `quant_cn.core.frames` | CBOE-method volatility index per day and option underlying, with per-term inputs | long; key (trade_date, underlying) | trade_date (string), underlying (string), clock (string), vix (float64), var_near (float64), var_next (float64), days_near (float64), days_next (float64), t_near (float64), t_next (float64), f_near (float64), f_next (float64), k0_near (float64), k0_next (float64), n_options_near (float64), n_options_next (float64), rate_near (float64), rate_next (float64), quality_flag (string) | key unique and non-null | `calculation.VixCalculator.compute` | VIX notebook; `pipeline.CalculationStep` (plan 03 ph4) | 2026-09-27 |
| `GEX_PANEL` | `quant_cn.core.frames` | dealer gamma exposure per option (sign assumption D-057) | long; key (trade_date, maturity_date, strike, call_put) | trade_date (string), maturity_date (string), days (float64), strike (float64), call_put (string), oi (float64), price (float64), forward (float64), rate (float64), t (float64), iv (float64), gamma (float64), sign (float64), multiplier (float64), gex (float64) | key unique and non-null | `calculation.GammaExposureCalculator.compute` | positioning notebook; plan 09 event study | 2026-09-27 |
| `FUTURES_POSITIONING` | `quant_cn.core.frames` | index-futures OI regime, top-20 net and basis per product and day | long; key (trade_date, product) | trade_date (string), product (string), main_contract (string), price (float64), price_change (float64), oi_total (float64), oi_change (float64), regime (string), top20_long (float64), top20_short (float64), top20_net (float64), spot (float64), basis_pct (float64), basis_annualised (float64) | key unique and non-null | `calculation.FuturesPositioning.compute` | positioning notebook; plan 09 event study | 2026-09-27 |
| `MARGIN_VINTAGES` | `quant_cn.core.frames` | FIFO margin-financing vintages with liquidation prices (D-058) | long; key (ts_code, entry_date, seeded) | ts_code (string), entry_date (string), entry_price (float64), debt (float64), liquidation_price (float64), price (float64), distance_pct (float64), seeded (float64) | key unique and non-null | `calculation.MarginLadderEstimator.compute_ladder` | `calculation.MarginLadderEstimator.compute_curve` | 2026-09-27 |
| `MARGIN_LADDER` | `quant_cn.core.frames` | financing debt reaching forced sale per market drawdown | long; key (drawdown_pct) | drawdown_pct (float64), debt_forced (float64), share_of_debt (float64) | key unique and non-null | `calculation.MarginLadderEstimator.compute_curve` | positioning notebook | 2026-09-27 |
| `UNIVERSE_PANEL` | `quant_cn.core.frames` | tradeable universe per session with exclusion reason | long; key (trade_date, ts_code) | trade_date (string), ts_code (string), in_universe (float64), reason (string) | key unique and non-null | `pipeline.UniverseStep` (plan 04 ph3) | constructors, `factor.FactorEvaluator` | 2026-09-27 |
| `FACTOR_PANEL` | `quant_cn.core.frames` | factor value (processed and raw) per stock and session | long; key (trade_date, ts_code, factor) | trade_date (string), ts_code (string), factor (string), value (float64), value_raw (float64) | key unique and non-null | `factor.BaseFactor`, `factor.FactorPreprocessor` (plan 04 ph4-5) | `factor.FactorEvaluator`, constructors | 2026-09-27 |
| `IC_SERIES` | `quant_cn.core.frames` | information coefficient per date, factor and horizon with N | long; key (trade_date, factor, horizon) | trade_date (string), factor (string), horizon (float64), ic (float64), n (float64) | key unique and non-null | `statistic.ICCalculator` (plan 04 ph2) | `statistic.ICSignificance` | 2026-09-27 |
| `IC_TEST` | `quant_cn.core.frames` | significance results per factor, horizon, metric and window incl. adjusted p | long; key (factor, horizon, metric, window) | factor (string), horizon (float64), metric (string), value (float64), se (float64), t (float64), p (float64), ci_lo (float64), ci_hi (float64), window (string), p_adj_holm (float64), p_adj_bhy (float64), p_adj_romano_wolf (float64), hlz_pass (float64) | key unique and non-null | `statistic.ICSignificance`, `statistic.MultipleTestingAdjuster` (plan 04 ph2) | `factor.FactorEvaluator` reports | 2026-09-27 |
| `TRIAL_LOG` | `quant_cn.core.frames` | every factor/parameter variant evaluated in a campaign | long; key (campaign, trial_id) | campaign (string), trial_id (string), factor (string), params (string), horizon (float64), sr (float64), ic_mean (float64) | key unique and non-null | `statistic.TrialLog` (plan 04 ph2) | `statistic.MultipleTestingAdjuster`, DSR (plan 06) | 2026-09-27 |
| `FORWARD_RETURN` | `quant_cn.core.frames` | tradeable forward return per stock, session and horizon | long; key (trade_date, ts_code, horizon) | trade_date (string), ts_code (string), horizon (float64), fwd_return (float64) | key unique and non-null | `statistic.ICCalculator.build_forward_returns` | `statistic.ICCalculator`, `statistic.QuantileReturns` | 2026-09-27 |
| `QUANTILE_RETURNS` | `quant_cn.core.frames` | mean forward return per factor quantile and date (0 = long-short) | long; key (trade_date, factor, horizon, quantile) | trade_date (string), factor (string), horizon (float64), quantile (float64), ret (float64), n (float64) | key unique and non-null | `statistic.QuantileReturns.compute` | `factor.FactorEvaluator`, `FactorChart` | 2026-09-27 |
| `EXPOSURE_PANEL` | `quant_cn.core.frames` | industry (Shenwan L1 grouping) and log market cap per universe member and session | long; key (trade_date, ts_code) | trade_date (string), ts_code (string), l1_code (string), industry_backfilled (float64), log_mcap (float64) | key unique and non-null | `lake.ExposureReader.read_exposures` | `factor.FactorPreprocessor` (neutralisation, D-093) | 2026-09-27 |
| `RISK_EXPOSURE` | `quant_cn.core.frames` | style and industry exposures per stock and session (risk model) | long; key (trade_date, ts_code, factor) | trade_date (string), ts_code (string), factor (string), exposure (float64), exposure_raw (float64), is_filled (float64) | key unique and non-null | `risk.ExposureStandardizer.compute` | `risk.RiskModel`, `pipeline.RiskModelStep`; later `factor` neutralisation | 2026-11-11 |
| `FACTOR_RETURN` | `quant_cn.core.frames` | daily factor returns of the constrained WLS with t-stat and R^2 | long; key (trade_date, factor) | trade_date (string), factor (string), ret (float64), t_stat (float64), r2 (float64), n_obs (float64) | key unique and non-null | `risk.FactorReturnEstimator.compute` | `risk.FactorCovarianceEstimator`, `risk.RiskModelValidator` | 2026-11-11 |
| `SPECIFIC_RETURN` | `quant_cn.core.frames` | regression residual and weight per stock and session (D-127) | long; key (trade_date, ts_code) | trade_date (string), ts_code (string), resid (float64), weight (float64) | key unique and non-null | `risk.FactorReturnEstimator.compute` | `risk.SpecificRiskEstimator` via `pipeline.RiskModelStep` | 2026-11-11 |
| `FACTOR_COV` | `quant_cn.core.frames` | factor covariance forecast per session (daily units; raw and adjusted) | long; key (trade_date, factor_i, factor_j) | trade_date (string), factor_i (string), factor_j (string), cov (float64), cov_raw (float64), horizon_days (float64) | key unique and non-null | `risk.FactorCovarianceEstimator.compute` | `risk.RiskModel.load_snapshot`, `risk.RiskModelValidator`; plan 06 optimiser | 2026-11-11 |
| `SPECIFIC_RISK` | `quant_cn.core.frames` | specific volatility forecast per stock and session | long; key (trade_date, ts_code) | trade_date (string), ts_code (string), sigma (float64), sigma_raw (float64), method (string) | key unique and non-null | `risk.SpecificRiskEstimator.compute_final` | `risk.RiskModel.load_snapshot`; plan 06 optimiser | 2026-11-11 |
| `RISK_DECOMP` | `quant_cn.core.frames` | portfolio risk attribution (total, factor, specific, contributions, exposures, active) | long; key (trade_date, portfolio, component) | trade_date (string), portfolio (string), component (string), risk (float64), pct (float64), kind (string) | key unique and non-null | `risk.RiskDecomposer.compute` | notebooks; later `back_testing` | 2026-11-11 |
| `RISK_VALIDATION` | `quant_cn.core.frames` | bias statistics and fit of the risk model | long; key (trade_date, metric, scope) | trade_date (string), metric (string), scope (string), value (float64), window (string), notes (string) | key unique and non-null | `risk.RiskModelValidator`, `pipeline.RiskValidationWriter` | validation notebook | 2026-11-11 |

## F. Allowed standalone functions (`core/utils` only, with justification)

| Function | Module | Purpose | Input -> Output | Why not a class method | Used by | Tests | Added |
|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | |
