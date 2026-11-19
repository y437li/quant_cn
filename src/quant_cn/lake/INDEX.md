# src/quant_cn/lake/

L2: parquet writer, DuckDB catalog, fetch log, compactor, query API, PIT aligner. May import from: L1.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `compactor.py` | raw/ -> curated/: typed, deduplicated, yearly partitions with manifests (D-012) | `Compactor` |
| `derived_views.py` | Derived DuckDB views over curated/ (D-015c): prices, fundamentals, futures, industry | `DerivedViews` |
| `document_views.py` | catalog views over the document download manifest (D-101) | `DocumentViews` |
| `effective_date_resolver.py` | First trading session a row may be used, from its known-on column and rule (D-063, §11) | `EffectiveDateResolver` |
| `exposure_reader.py` | Industry and size exposures of universe members (D-093): the neutralisation inputs | `ExposureReader` |
| `fetch_log.py` | Done-keys for resumable downloads: `meta.fetch_log` + a durable parquet mirror (D-012) | `FetchLog` |
| `lake_catalog.py` | The DuckDB catalog over the lake: views per dataset and zone, metadata, generated indexes | `LakeCatalog` |
| `lake_query.py` | The read API over the lake: SQL through the catalog connection (D-009) | `LakeQuery` |
| `lake_reader.py` | The lake read API above raw SQL (D-041, D-089): panels, prices, PIT fundamentals, reference | `LakeReader` |
| `panel_cache.py` | In-memory cache of read panels (SRC_DESIGN §2.2b): repeated notebook reads skip DuckDB | `PanelCache` |
| `parquet_writer.py` | Atomic, hive-named parquet writes into the lake (FOLDER_STRUCTURE §2 conventions) | `ParquetWriter` |
| `label_store.py` | every label set as parquet under derived/labels/<set>/year=<YYYY>/, keyed by company and document, with period and known_on (plan 28, D-161) | `LabelStore` |
| `dated_table_store.py` | derived year tables keyed by a date: replace dates, read years, read a report (plan 21) | `DatedTableStore` |
| `task_log.py` | update task ledger: one parquet part per step under meta/task_log/, view meta.task_log (plan 38, D-181) | `TaskLog` |
| `valuation_history_reader.py` | latest pb / pe_ttm and the median of its positive values over a window (plan 21 ph4) | `ValuationHistoryReader` |
| `pit_aligner.py` | The only point-in-time join (D-006): fundamentals visible the trading day after announcement | `PitAligner` |
| `project_catalog.py` | The repository as SQL: schema `project` in the lake catalog, rebuilt from docs + code (D-017) | `ProjectCatalog` |
| `quality_views.py` | Cross-source quality views (schema `quality`): verification never overwrites primary data | `QualityViews` |
| `rebuild_audit.py` | What `rebuild` confirms: fetch-log orphans (D-073) and rewritten raw files (D-083) | `RebuildAudit` |
| `release_lag_checker.py` | Checks release-lag rules against observed official release dates (D-086) | `ReleaseLagChecker` |
| `run_log.py` | Run history for monitoring: `meta.run_log` in DuckDB, mirrored to logging (D-022) | `RunLog` |
| `statement_version_reader.py` | Statement values per (company, period, field) as known on a date, or first announced (plans 16, 18) | `StatementVersionReader` |
| `ticker_alias_map.py` | Retired codes mapped to their surviving codes (D-053, D-089): one company, one history | `TickerAliasMap` |
| `trading_calendar.py` | Trading-day arithmetic from the downloaded `trade_cal` (SRC_DESIGN §2.2) | `TradingCalendar` |
| `chip_structure_reader.py` | 筹码结构 and order-flow signals per stock as known on a date: holders, institutions, northbound, margin, weekly flows, unlocks, insiders, RetailGauge (plan 15 ph7f) | `ChipStructureReader` |
| `fundamental_signal_reader.py` | statement signals (single-quarter GM, deducted-profit YoY, OCF / NP) and manual-series values as known on a date (plan 15 ph7f) | `FundamentalSignalReader` |
| `buyback_ledger.py` | buyback programmes and executed amounts from curated.repurchase, point in time (plan 23 ph2) | `BuybackLedger` |
| `shareholder_yield_reader.py` | dividend + buyback yield per stock on a date (plan 23 ph3) | `ShareholderYieldReader` |
| `margin_signal_reader.py` | margin-trading signals per stock for conditions (plan 15 ph7m) | `MarginSignalReader` |
| `graph_store.py` | plan 28 graph tables (entity_map, company_edge, edge_span) as parquet under derived/graph | `GraphStore` |
