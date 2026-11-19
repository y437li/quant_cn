# src/quant_cn/core/

L1: base classes, exceptions, Config, Schema, DateCodec, TickerNormalizer, logging. May import from: stdlib, pandas, pyarrow, duckdb.

## Folders
| Folder | Purpose |
|---|---|
| [`docs/`](docs/INDEX.md) | core.docs: parsers and checkers for code, docstrings, indexes, registry |

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `base_api_client.py` | Extension point for data vendors | `BaseApiClient` |
| `base_fetch_log.py` | Extension point for resumable-download bookkeeping | `BaseFetchLog` |
| `base_fetcher.py` | Template for downloading a dataset key by key: skip done, fetch, write, log | `BaseFetcher` |
| `base_llm_client.py` | extension point for LLM vendors used by extraction (D-098) | `LlmReply`, `BaseLlmClient` |
| `base_run_log.py` | Extension point for run monitoring events (D-022) | `BaseRunLog` |
| `base_step.py` | Extension point for pipeline steps run by a runner | `BaseStep` |
| `base_store.py` | Extension point for where fetched data is written | `BaseStore` |
| `clock.py` | Injectable time source so sleeps and "today" are controllable in tests (SRC_DESIGN §2.1) | `Clock` |
| `config.py` | Typed configuration: `config/*.yaml` merged with machine overrides and environment (D-021) | `LakeConfig`, `TushareConfig`, `DownloadConfig`, `FactorSpec`, `CampaignConfig`, `UniverseConfig`, `FuturesCategory`, `TickerAlias`, `LlmConfig`, `Config` |
| `etf_cta_settings.py` | groups, shares, trend / switch windows, band, costs and premium guard of the ETF CTA book from config/etf_cta.yaml (plan 27, D-160) | `EtfCtaGroup`, `EtfCtaPremium`, `EtfCtaSettings` |
| `etf_cta_views.py` | the user's views on the ETF CTA book (scale, relative, price condition, A股 floor) from the git-ignored views file (plan 27 ph5, D-163) | `EtfCtaWhen`, `EtfCtaView`, `EtfCtaViews` |
| `positions_book.py` | The user's holdings (one combined book) from git-ignored config/local.positions.yaml (plan 15 ph7d) | `BookRules`, `Position`, `PositionNote`, `PositionsBook` |
| `update_all_settings.py` | ordered update-all steps from config/update_all.yaml: needs, outputs, timeouts, retries (plan 38) | `UpdateStep`, `UpdateAllSettings` |
| `watchlist_entry.py` | the user's watchlist targets and the watchlist page settings (D-120) | `WatchlistEntry`, `WatchlistSettings` |
| `etf_proxy_settings.py` | members, start and window of the national-team ETF proxy (config/etf_proxies.yaml, D-126) | `EtfProxyIndex`, `EtfProxyStyle`, `EtfProxySettings` |
| `label_source.py` | one existing label file to import into the parquet label store (config/label_sources.yaml, plan 28, D-161) | `LabelSource` |
| `dataset_spec.py` | Typed view of one `config/datasets.yaml` entry: endpoint, sweep, keys, curated layout | `ValuesFromDataset`, `SweepSpec`, `CuratedSpec`, `DatasetSpec` |
| `date_codec.py` | The only place that converts between `YYYYMMDD` strings and dates (D-005) | `DateCodec` |
| `discovery_settings.py` | settings of the opportunity-discovery pipeline (plan 16, D-121) | `DiscoverySettings` |
| `guidance_settings.py` | settings of company guidance tracking (plan 18, D-124) | `GuidanceSettings` |
| `risk_model_settings.py` | Settings of the Barra-style risk model (config/risk_model.yaml, D-127) | `StyleSpec`, `ExternalSeriesSpec`, `ThemeBasketSpec`, `RiskModelSettings` |
| `document_source.py` | which documents are downloaded and where they land, as data (config/documents.yaml, D-101) | `DocumentRule`, `DocumentSource` |
| `exceptions.py` | Project exception hierarchy; every raised error is a `QuantCnError` (CODING_STANDARD §2.5) | `QuantCnError`, `ConfigError`, `SchemaError`, `DataSourceError`, `PermissionDeniedError`, `LakeError` |
| `frames.py` | Shared panel schemas that cross package boundaries (SRC_DESIGN §3); long format, YYYYMMDD dates | `PRICE_PANEL`, `FUNDAMENTALS_PIT`, `VIX_PANEL`, `GEX_PANEL`, `FUTURES_POSITIONING`, `MARGIN_VINTAGES`, `MARGIN_LADDER`, `UNIVERSE_PANEL`, `FACTOR_PANEL`, `IC_SERIES`, `IC_TEST`, `TRIAL_LOG`, `FORWARD_RETURN`, `QUANTILE_RETURNS`, `EXPOSURE_PANEL` |
| `schema.py` | DataFrame contract: columns, dtypes and primary key, enforced at lake boundaries | `Schema` |
| `step_report.py` | Outcome record of one pipeline step or fetcher run | `StepReport` |
| `ticker_normalizer.py` | The only place that converts other ticker spellings to Tushare `ts_code` (CODING_STANDARD §4) | `TickerNormalizer` |
| `condition.py` | structured buy / falsifier condition on a watchlist entry or position note; allowed metrics per kind (plan 15 ph7f) | `Condition` |
| `futures_monitor_settings.py` | families, spreads and flag bounds of the futures monitor from config/futures_monitor.yaml (plan 15 ph7i) | `FuturesFamily`, `FuturesSpreadLeg`, `FuturesSpread`, `IndexFuturesProduct`, `FuturesMonitorSettings` |
| `volatility_monitor_settings.py` | lines, window and alerts of the volatility monitor from config/volatility_monitor.yaml (plan 03 ph6) | `VolatilityLine`, `VolatilityMonitorSettings` |
| `rates_fx_monitor_settings.py` | lines, sources, units and alerts of the rates and RMB monitor from config/rates_fx_monitor.yaml (plan 34) | `RatesFxLine`, `RatesFxMonitorSettings` |
| `sector_earnings_signal_settings.py` | windows and thresholds of the earnings events and the 财报季信号 from config/sector_earnings_signal.yaml (plan 35) | `SectorEarningsSignalSettings` |
| `retail_gauge_settings.py` | RetailGauge windows, model params, thresholds and streak rule from config/retail_gauge.yaml (plan 21) | `RetailGaugeSettings` |
| `opportunity_settings.py` | daily opportunity list universe, rule thresholds and list sizes from config/discovery_rules.yaml (plan 21 ph4) | `OpportunitySettings` |
| `small_cap_watch_settings.py` | indices, triggers, windows and ETFs of the 小盘观察 from config/smallcap_watch.yaml plus the local override (plan 30) | `WatchIndex`, `WatchEtf`, `MarginEpisode`, `SmallCapWatchSettings` |
| `app_publisher_settings.py` | App Store seller accounts → company and listed code from config/app_publishers.yaml (plan 19 ph2) | `AppPublisher`, `AppPublisherSettings` |
| `sector_monitor_settings.py` | tiers, vol windows, chart lengths and sectors of the 行业监控 from config/sector_monitors.yaml (plan 31) | `MonitoredSecurity`, `MonitoredSector`, `SectorMonitorSettings` |
| `message_sender.py` | phone alerts by iMessage: recipients from config/local.notify.yaml and the osascript sender (plan 22) | `NotifyRecipient`, `NotifySettings`, `MessageSender`, `IMessageSender` |
| `sent_alert_log.py` | phone-alert keys already sent and still active, so each alert goes out once per episode (plan 22) | `SentAlertLog` |
| `mail_sender.py` | mail settings from git-ignored config/local.mail.yaml and an SMTP STARTTLS sender; password only from the environment (plan 15 ph7e) | `MailSettings`, `MailContent`, `MailSender` |
