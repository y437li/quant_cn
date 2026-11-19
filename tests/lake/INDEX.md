# tests/lake/

Tests for `quant_cn.lake`. No network, no files outside `tmp_path`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `test_compactor.py` | tests for `compactor`, one function per TC ID |  |
| `test_derived_views.py` | tests for `derived_views`, one function per TC ID |  |
| `test_document_views.py` | tests for `document_views`, one function per TC ID |  |
| `test_effective_date_resolver.py` | tests for `effective_date_resolver`, one function per TC ID |  |
| `test_fetch_log.py` | tests for `fetch_log`, one function per TC ID |  |
| `test_lake_catalog.py` | tests for `lake_catalog`, one function per TC ID |  |
| `test_lake_query.py` | tests for `lake_query`, one function per TC ID |  |
| `test_lake_reader.py` | tests for `lake_reader`, one function per TC ID |  |
| `test_panel_cache.py` | tests for `panel_cache`, one function per TC ID |  |
| `test_parquet_writer.py` | tests for `parquet_writer`, one function per TC ID |  |
| `test_label_store.py` | tests for `label_store`, one function per TC ID |  |
| `test_dated_table_store.py` | tests for `dated_table_store`, one function per TC ID |  |
| `test_task_log.py` | tests for `task_log`, one function per TC ID | |
| `test_valuation_history_reader.py` | tests for `valuation_history_reader`, one function per TC ID |  |
| `test_pit_aligner.py` | tests for `pit_aligner`, one function per TC ID |  |
| `test_project_catalog.py` | tests for `project_catalog`, one function per TC ID |  |
| `test_quality_views.py` | tests for `quality_views`, one function per TC ID |  |
| `test_rebuild_audit.py` | tests for `rebuild_audit`, one function per TC ID |  |
| `test_release_lag_checker.py` | tests for `release_lag_checker`, one function per TC ID |  |
| `test_run_log.py` | tests for `run_log`, one function per TC ID |  |
| `test_statement_version_reader.py` | tests for `statement_version_reader`, one function per TC ID |  |
| `test_ticker_alias_map.py` | tests for `ticker_alias_map`, one function per TC ID |  |
| `test_trading_calendar.py` | tests for `trading_calendar`, one function per TC ID |  |
| `test_chip_structure_reader.py` | tests for `chip_structure_reader`, one function per TC ID |  |
| `test_fundamental_signal_reader.py` | tests for `fundamental_signal_reader`, one function per TC ID | `FakeVersions` |
| `test_buyback_ledger.py` | tests for `buyback_ledger`, one function per TC ID | |
| `test_shareholder_yield_reader.py` | tests for `shareholder_yield_reader`, one function per TC ID | |
| `test_margin_signal_reader.py` | tests for `margin_signal_reader`, one function per TC ID | `RowsQuery` |
| `test_graph_store.py` | tests for `graph_store` (TC-GS-001..003) | — |
