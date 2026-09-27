# src/quant_cn/core/

L1: base classes, exceptions, Config, Schema, DateCodec, TickerNormalizer, logging. May import from: stdlib, pandas, pyarrow, duckdb.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `base_api_client.py` | Extension point for data vendors | `BaseApiClient` |
| `base_fetch_log.py` | Extension point for resumable-download bookkeeping | `BaseFetchLog` |
| `base_fetcher.py` | Template for downloading a dataset key by key: skip done, fetch, write, log | `BaseFetcher` |
| `base_run_log.py` | Extension point for run monitoring events (D-022) | `BaseRunLog` |
| `base_step.py` | Extension point for pipeline steps run by a runner | `BaseStep` |
| `base_store.py` | Extension point for where fetched data is written | `BaseStore` |
| `clock.py` | Injectable time source so sleeps and "today" are controllable in tests (SRC_DESIGN §2.1) | `Clock` |
| `config.py` | Typed configuration: `config/*.yaml` merged with machine overrides and environment (D-021) | `LakeConfig`, `TushareConfig`, `DownloadConfig`, `Config` |
| `dataset_spec.py` | Typed view of one `config/datasets.yaml` entry: endpoint, sweep, keys, curated layout | `SweepSpec`, `CuratedSpec`, `DatasetSpec` |
| `date_codec.py` | The only place that converts between `YYYYMMDD` strings and dates (D-005) | `DateCodec` |
| `exceptions.py` | Project exception hierarchy; every raised error is a `QuantCnError` (CODING_STANDARD §2.5) | `QuantCnError`, `ConfigError`, `SchemaError`, `DataSourceError`, `PermissionDeniedError`, `LakeError` |
| `schema.py` | DataFrame contract: columns, dtypes and primary key, enforced at lake boundaries | `Schema` |
| `step_report.py` | Outcome record of one pipeline step or fetcher run | `StepReport` |
| `ticker_normalizer.py` | The only place that converts other ticker spellings to Tushare `ts_code` (CODING_STANDARD §4) | `TickerNormalizer` |
