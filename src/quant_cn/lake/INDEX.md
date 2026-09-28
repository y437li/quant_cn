# src/quant_cn/lake/

L2: parquet writer, DuckDB catalog, fetch log, compactor, query API, PIT aligner. May import from: L1.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `compactor.py` | raw/ -> curated/: typed, deduplicated, yearly partitions with manifests (D-012) | `Compactor` |
| `derived_views.py` | Derived DuckDB views over curated/ (D-015c, views first): adjusted prices, fundamentals | `DerivedViews` |
| `fetch_log.py` | Done-keys for resumable downloads: `meta.fetch_log` + a durable parquet mirror (D-012) | `FetchLog` |
| `lake_catalog.py` | The DuckDB catalog over the lake: views per dataset and zone, metadata, generated indexes | `LakeCatalog` |
| `lake_query.py` | The read API over the lake: SQL through the catalog connection (D-009) | `LakeQuery` |
| `parquet_writer.py` | Atomic, hive-named parquet writes into the lake (FOLDER_STRUCTURE §2 conventions) | `ParquetWriter` |
| `pit_aligner.py` | The only point-in-time join (D-006): fundamentals visible the trading day after announcement | `PitAligner` |
| `project_catalog.py` | The repository as SQL: schema `project` in the lake catalog, rebuilt from docs + code (D-017) | `ProjectCatalog` |
| `run_log.py` | Run history for monitoring: `meta.run_log` in DuckDB, mirrored to logging (D-022) | `RunLog` |
| `trading_calendar.py` | Trading-day arithmetic from the downloaded `trade_cal` (SRC_DESIGN §2.2) | `TradingCalendar` |
