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
| `pit_aligner.py` | The only point-in-time join (D-006): fundamentals visible the trading day after announcement | `PitAligner` |
| `project_catalog.py` | The repository as SQL: schema `project` in the lake catalog, rebuilt from docs + code (D-017) | `ProjectCatalog` |
| `quality_views.py` | Cross-source quality views (schema `quality`): verification never overwrites primary data | `QualityViews` |
| `rebuild_audit.py` | What `rebuild` confirms: fetch-log orphans (D-073) and rewritten raw files (D-083) | `RebuildAudit` |
| `release_lag_checker.py` | Checks release-lag rules against observed official release dates (D-086) | `ReleaseLagChecker` |
| `run_log.py` | Run history for monitoring: `meta.run_log` in DuckDB, mirrored to logging (D-022) | `RunLog` |
| `ticker_alias_map.py` | Retired codes mapped to their surviving codes (D-053, D-089): one company, one history | `TickerAliasMap` |
| `trading_calendar.py` | Trading-day arithmetic from the downloaded `trade_cal` (SRC_DESIGN §2.2) | `TradingCalendar` |
