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
| `QuantCnCli` | `quant_cn.cli` | 6 | none | `python -m quant_cn.cli <command>`: doctor, download, compact, rebuild, backup | 1 | `Makefile targets doctor, download, compact, lake-rebuild, lake-backup` | `tests/test_cli.py` (TC-QCC-001..002) | 2026-09-27 |
| `BaseApiClient` | `quant_cn.core.base_api_client` | 1 | ABC | Abstract vendor client: one logical query returns all pages as one DataFrame. | 1 | `data_loading.TushareClient`, `core.BaseFetcher`, `data_loading.FetcherFactory` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `BaseFetchLog` | `quant_cn.core.base_fetch_log` | 1 | ABC | Abstract record of which (dataset, key) pairs are fully downloaded. | 5 | `lake.FetchLog`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline` | `tests/lake/test_fetch_log.py` (TC-FL-001..003) | 2026-09-27 |
| `BaseFetcher` | `quant_cn.core.base_fetcher` | 1 | ABC | Download one dataset as a sequence of keys | 5 | `data_loading.SingleCallFetcher`, `data_loading.EnumFetcher`, `data_loading.DateSweepFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.FetcherFactory.build`, `pipeline.FetchStep`, `pipeline.DownloadPipeline.run` | `tests/core/test_base_fetcher.py` (TC-BF-001..006) | 2026-09-27 |
| `BaseRunLog` | `quant_cn.core.base_run_log` | 1 | ABC | Abstract append-only log of runs and per-key events | 3 | `lake.RunLog`, `core.BaseFetcher.run`, `pipeline.LocalRunner`, `data_loading.FetcherFactory` | `tests/lake/test_run_log.py` (TC-RL-001..001) | 2026-09-27 |
| `BaseStep` | `quant_cn.core.base_step` | 1 | ABC | Abstract unit of pipeline work: list its units, then run and report. | 3 | `pipeline.FetchStep`, `pipeline.BaseRunner.run`, `pipeline.LocalRunner.run` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `BaseStore` | `quant_cn.core.base_store` | 1 | ABC | Abstract sink for raw fetch results and curated partitions. | 2 | `lake.ParquetWriter`, `core.BaseFetcher`, `lake.Compactor`, `data_loading.FetcherFactory` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `Clock` | `quant_cn.core.clock` | 1 | none | The single source of wall time, monotonic time and sleeping | 4 | `data_loading.TushareClient`, `core.BaseFetcher.run`, `lake.RunLog`, `lake.Compactor.rebuild`, `pipeline.DownloadPipeline`, `cli.QuantCnCli` | `tests/core/test_clock.py` (TC-CL-001..002) | 2026-09-27 |
| `LakeConfig` | `quant_cn.core.config` | 1 | BaseModel | Where the lake lives and whether it may sit inside the repository. | 0 | `core.Config`, `cli.QuantCnCli` | `tests/core/test_config.py` (TC-C-001..001) | 2026-09-27 |
| `TushareConfig` | `quant_cn.core.config` | 1 | BaseModel | Tushare endpoint, paging, retry and rate-limit settings | 0 | `core.Config`, `data_loading.TushareClient` | `tests/core/test_config.py` (TC-C-002..002) | 2026-09-27 |
| `DownloadConfig` | `quant_cn.core.config` | 1 | BaseModel | Which datasets to download, in what order, and from which start dates (D-015b). | 0 | `core.Config`, `pipeline.DownloadPipeline.run` | `tests/core/test_config.py` (TC-C-004..004) | 2026-09-27 |
| `Config` | `quant_cn.core.config` | 1 | BaseModel | The typed configuration injected everywhere: YAML defaults, machine overrides, environment. | 3 | `cli.QuantCnCli`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline` | `tests/core/test_config.py` (TC-C-001..008) | 2026-09-27 |
| `SweepSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | How a dataset is swept so each call returns the whole market for one key. | 1 | `core.DatasetSpec`, `data_loading.FetcherFactory.build`, `core.BaseFetcher.run` | `tests/core/test_dataset_spec.py` (TC-DS-001..001) | 2026-09-27 |
| `CuratedSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Where a dataset lands in `curated/` and which date column drives its yearly partition. | 0 | `core.DatasetSpec`, `lake.ParquetWriter.write_curated`, `lake.Compactor.rebuild`, `lake.LakeCatalog.refresh_view` | `tests/core/test_dataset_spec.py` (TC-DS-001..001) | 2026-09-27 |
| `DatasetSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Everything the lake and the fetchers need to know about one dataset, as data (D-012). | 2 | `core.Config`, `core.BaseFetcher`, `core.BaseStore`, `lake.ParquetWriter`, `lake.LakeCatalog`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory.build` | `tests/core/test_dataset_spec.py` (TC-DS-001..004) | 2026-09-27 |
| `DateCodec` | `quant_cn.core.date_codec` | 1 | none | Validate and convert Tushare `YYYYMMDD` date strings and generate date keys for sweeps. | 5 | `core.Config.load`, `data_loading.DateSweepFetcher.list_keys`, `data_loading.PeriodSweepFetcher.list_keys`, `pipeline.DownloadPipeline.run` | `tests/core/test_date_codec.py` (TC-DC-001..005) | 2026-09-27 |
| `Schema` | `quant_cn.core.schema` | 1 | none | Declare and enforce a DataFrame shape: text columns are pandas `string`, all other declared columns are `float64`, and the primary key is unique and non-null. | 4 | `core.DatasetSpec.build_schema`, `lake.ParquetWriter.write_raw`, `lake.ParquetWriter.write_curated`, `lake.Compactor.rebuild` | `tests/core/test_schema.py` (TC-S-001..006) | 2026-09-27 |
| `StepReport` | `quant_cn.core.step_report` | 1 | none | Counts and status of one step (usually one dataset's fetch) so runs can be summarised. | 0 | `core.BaseFetcher.run`, `core.BaseStep.run`, `lake.Compactor.rebuild`, `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run` | `tests/core/test_base_fetcher.py` (TC-BF-001..001) | 2026-09-27 |
| `TickerNormalizer` | `quant_cn.core.ticker_normalizer` | 1 | none | Turn common A-share ticker spellings into Tushare `ts_code` and check `ts_code` validity. | 2 | (none yet) | `tests/core/test_ticker_normalizer.py` (TC-TN-001..004) | 2026-09-27 |
| `FetcherFactory` | `quant_cn.data_loading.fetcher_factory` | 3 | none | Build the right fetcher for a DatasetSpec and inject the shared dependencies. | 1 | `pipeline.DownloadPipeline`, `cli.QuantCnCli` | `tests/data_loading/test_fetcher_factory.py` (TC-FF-001..002) | 2026-09-27 |
| `SingleCallFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Datasets fetched in one (paged) call, key "all": trade_cal, namechange. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-SCF-001..001) | 2026-09-27 |
| `EnumFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Datasets swept over an enumerated list: stock_basic by list_status (L, D, P), index_daily by index ts_code. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-EF-001..001) | 2026-09-27 |
| `DateSweepFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Whole-market daily sweeps: trade_date keys are trading days (daily, adj_factor, daily_basic, moneyflow, stk_limit) | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-DSF-001..002) | 2026-09-27 |
| `PeriodSweepFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Whole-market report-period sweeps (the *_vip fundamentals): one key per quarter end. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-PSF-001..001) | 2026-09-27 |
| `HttpTransport` | `quant_cn.data_loading.http_transport` | 3 | none | Send one JSON POST and return the decoded JSON object. | 1 | `data_loading.TushareClient` | `tests/data_loading/test_tushare_client.py` (TC-TC-001..001) | 2026-09-27 |
| `TushareClient` | `quant_cn.data_loading.tushare_client` | 3 | BaseApiClient | Query Tushare Pro: one logical query follows limit/offset paging until a short page and returns all rows | 1 | `data_loading.FetcherFactory`, `cli.QuantCnCli` | `tests/data_loading/test_tushare_client.py` (TC-TC-001..007) | 2026-09-27 |
| `Compactor` | `quant_cn.lake.compactor` | 2 | none | Rebuild a dataset's curated partitions from its raw files: select declared fields, cast dtypes, drop duplicate primary keys (keeping one), sort by partition date then key, validate, write, and record a manifest in `meta/manifest/<dataset>.json`. | 1 | `cli.QuantCnCli` | `tests/lake/test_compactor.py` (TC-CO-001..005) | 2026-09-27 |
| `FetchLog` | `quant_cn.lake.fetch_log` | 2 | BaseFetchLog | Record finished (dataset, key) pairs in `meta.fetch_log`, mirror them to `meta/fetch_log.parquet` on save, and rebuild the table after the DuckDB file is lost. | 5 | `core.BaseFetcher.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli` | `tests/lake/test_fetch_log.py` (TC-FL-001..005) | 2026-09-27 |
| `LakeCatalog` | `quant_cn.lake.lake_catalog` | 2 | none | Own the lake's single DuckDB connection (`meta/quant_cn.duckdb`): schemas `raw`, `curated`, `meta` | 8 | `lake.FetchLog`, `lake.RunLog`, `lake.LakeQuery`, `lake.Compactor`, `pipeline.FetchStep.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli` | `tests/lake/test_lake_catalog.py` (TC-LC-001..004) | 2026-09-27 |
| `LakeQuery` | `quant_cn.lake.lake_query` | 2 | none | Run read queries against the catalog views | 2 | `lake.TradingCalendar`, `lake.Compactor.rebuild`, `cli.QuantCnCli` | `tests/lake/test_lake_query.py` (TC-LQ-001..003) | 2026-09-27 |
| `ParquetWriter` | `quant_cn.lake.parquet_writer` | 2 | BaseStore | Write raw fetch results and curated partitions as zstd parquet, atomically (write `.tmp`, fsync, rename), so a crash never leaves a half-written file. | 4 | `core.BaseFetcher.run`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory`, `cli.QuantCnCli` | `tests/lake/test_parquet_writer.py` (TC-PW-001..005) | 2026-09-27 |
| `RunLog` | `quant_cn.lake.run_log` | 2 | BaseRunLog | Append run and per-key events to `meta.run_log` (run_id, started_at, finished_at, kind, dataset, key, status, n_rows, duration_ms, message) and echo them to logging. | 3 | `core.BaseFetcher.run`, `pipeline.LocalRunner`, `cli.QuantCnCli` | `tests/lake/test_run_log.py` (TC-RL-001..002) | 2026-09-27 |
| `TradingCalendar` | `quant_cn.lake.trading_calendar` | 2 | none | Answer trading-day questions (sessions in a range, is_open, next, prev) from the SSE calendar in the lake | 5 | `data_loading.DateSweepFetcher.list_keys`, `data_loading.FetcherFactory`, `cli.QuantCnCli` | `tests/lake/test_trading_calendar.py` (TC-TCA-001..004) | 2026-09-27 |
| `FetchStep` | `quant_cn.pipeline.download_pipeline` | 4 | BaseStep | Adapt one dataset's fetcher to a pipeline step: keys computed in list_units (so the calendar fetched earlier in the run is visible), catalog view refreshed after the run. | 3 | `pipeline.DownloadPipeline.run` | `tests/pipeline/test_download_pipeline.py` (TC-DP-002..002) | 2026-09-27 |
| `DownloadPipeline` | `quant_cn.pipeline.download_pipeline` | 4 | none | Resolve which datasets and date ranges to download, run one FetchStep per dataset through the runner, and regenerate the lake indexes | 1 | `cli.QuantCnCli` | `tests/pipeline/test_download_pipeline.py` (TC-DP-001..005) | 2026-09-27 |
| `PipelineReport` | `quant_cn.pipeline.runner` | 4 | none | Result of one pipeline run: its id, overall status and one StepReport per step. | 2 | `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli` | `tests/pipeline/test_runner.py` (TC-LR-001..001) | 2026-09-27 |
| `BaseRunner` | `quant_cn.pipeline.runner` | 4 | ABC | Extension point for how steps are executed (local now, Prefect later, D-022) | 1 | `pipeline.LocalRunner`, `pipeline.DownloadPipeline` | `tests/pipeline/test_runner.py` (TC-LR-001..001) | 2026-09-27 |
| `LocalRunner` | `quant_cn.pipeline.runner` | 4 | BaseRunner | Run steps serially in this process with a rich progress bar per step | 1 | `pipeline.DownloadPipeline`, `cli.QuantCnCli` | `tests/pipeline/test_runner.py` (TC-LR-001..003) | 2026-09-27 |

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

### `QuantCnCli` — `quant_cn.cli` (L6)
- **Purpose:** `python -m quant_cn.cli <command>`: doctor, download, compact, rebuild, backup. Builds every service from Config (the only place objects are wired together) and prints summaries.
- **Base:** none. **Depends on (injected):** Config | None, Console | None.
- **Used by:** `Makefile targets doctor, download, compact, lake-rebuild, lake-backup`.
- **Tests:** `tests/test_cli.py` (TC-QCC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config \| None, Console \| None -> None | — | callers of the class | — |
| `run` | Parse arguments and dispatch to a command. | Sequence[str] \| None -> int | `SystemExit` | as class | see class |

### `BaseApiClient` — `quant_cn.core.base_api_client` (L1)
- **Purpose:** Abstract vendor client: one logical query returns all pages as one DataFrame.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `core.BaseFetcher`, `data_loading.FetcherFactory`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `query` | Run one query and return every row across pages. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError`, `PermissionDeniedError` | as class | see class |

### `BaseFetchLog` — `quant_cn.core.base_fetch_log` (L1)
- **Purpose:** Abstract record of which (dataset, key) pairs are fully downloaded.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.FetchLog`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`.
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
- **Used by:** `data_loading.SingleCallFetcher`, `data_loading.EnumFetcher`, `data_loading.DateSweepFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.FetcherFactory.build`, `pipeline.FetchStep`, `pipeline.DownloadPipeline.run`.
- **Tests:** `tests/core/test_base_fetcher.py` (TC-BF-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock -> None | `TypeError` | callers of the class | — |
| `list_keys` | All fetch keys for [start, end], ascending. | str, str -> list[str] | `LakeError`, `ValueError` | as class | see class |
| `build_params` | API parameters for one key. | str, str, str -> dict[str, str] | — | as class | see class |
| `list_due_keys` | Keys that must be fetched: all if forced or overwrite, else pending plus the newest `refetch_recent` keys. | Sequence[str], bool -> list[str] | `LakeError` | as class | see class |
| `fetch_one` | Query the endpoint for one key. | str, str, str -> pd.DataFrame | `DataSourceError`, `PermissionDeniedError` | as class | see class |
| `run` | Fetch every key that needs fetching, writing and logging each before the next. | str, str, str, Sequence[str] \| None, bool, ProgressHook \| None -> StepReport | `DataSourceError`, `PermissionDeniedError`, `SchemaError`, `LakeError` | as class | see class |

### `BaseRunLog` — `quant_cn.core.base_run_log` (L1)
- **Purpose:** Abstract append-only log of runs and per-key events; the source of truth for "what happened".
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.RunLog`, `core.BaseFetcher.run`, `pipeline.LocalRunner`, `data_loading.FetcherFactory`.
- **Tests:** `tests/lake/test_run_log.py` (TC-RL-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `open_run` | Open a run and return its id. | str -> str | `LakeError` | as class | see class |
| `record_event` | Append one event (fetched / skipped / empty / failed / blocked). | str, str, str, str, int, int, str -> None | `LakeError` | as class | see class |
| `close_run` | Close a run with its final status. | str, str, str -> None | `LakeError` | as class | see class |

### `BaseStep` — `quant_cn.core.base_step` (L1)
- **Purpose:** Abstract unit of pipeline work: list its units, then run and report.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `pipeline.FetchStep`, `pipeline.BaseRunner.run`, `pipeline.LocalRunner.run`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `name` | Step name shown in progress and reports. | — -> str | — | as class | see class |
| `list_units` | Compute the work units (e.g. keys) just before running. | — -> list[str] | `QuantCnError` | as class | see class |
| `run` | Do the work listed by `list_units`. | str, ProgressHook \| None -> StepReport | `QuantCnError` | as class | see class |

### `BaseStore` — `quant_cn.core.base_store` (L1)
- **Purpose:** Abstract sink for raw fetch results and curated partitions.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.ParquetWriter`, `core.BaseFetcher`, `lake.Compactor`, `data_loading.FetcherFactory`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `write_raw` | Persist one fetch key's rows atomically. | DatasetSpec, str, pd.DataFrame -> Path \| None | `SchemaError`, `LakeError` | as class | see class |
| `write_curated` | Replace one curated partition atomically after validating its schema. | DatasetSpec, int \| None, pd.DataFrame -> Path | `SchemaError`, `LakeError` | as class | see class |

### `Clock` — `quant_cn.core.clock` (L1)
- **Purpose:** The single source of wall time, monotonic time and sleeping; tests inject a fake subclass.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `core.BaseFetcher.run`, `lake.RunLog`, `lake.Compactor.rebuild`, `pipeline.DownloadPipeline`, `cli.QuantCnCli`.
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
- **Used by:** `core.Config`, `cli.QuantCnCli`.
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
- **Used by:** `core.Config`, `pipeline.DownloadPipeline.run`.
- **Tests:** `tests/core/test_config.py` (TC-C-004..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `Config` — `quant_cn.core.config` (L1)
- **Purpose:** The typed configuration injected everywhere: YAML defaults, machine overrides, environment.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `cli.QuantCnCli`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`.
- **Tests:** `tests/core/test_config.py` (TC-C-001..008).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | Build the configuration from `config/base.yaml`, `config/datasets.yaml`, optional `config/local.yaml`, the repo `.env` and the process environment. | Path \| None, Mapping[str, str] \| None -> Config | `ConfigError` | as class | see class |
| `get_dataset` | Look up one dataset spec by name. | str -> DatasetSpec | `ConfigError` | as class | see class |
| `get_start` | Download start date for a dataset: its own `start`, else long-history start if listed, else the default start. | str -> str | `ConfigError` | as class | see class |

### `SweepSpec` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** How a dataset is swept so each call returns the whole market for one key.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.DatasetSpec`, `data_loading.FetcherFactory.build`, `core.BaseFetcher.run`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `param` | API parameter name carrying the key (None for single-call datasets). | — -> str \| None | — | as class | see class |

### `CuratedSpec` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** Where a dataset lands in `curated/` and which date column drives its yearly partition.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.DatasetSpec`, `lake.ParquetWriter.write_curated`, `lake.Compactor.rebuild`, `lake.LakeCatalog.refresh_view`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DatasetSpec` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** Everything the lake and the fetchers need to know about one dataset, as data (D-012).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `core.BaseFetcher`, `core.BaseStore`, `lake.ParquetWriter`, `lake.LakeCatalog`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory.build`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_raw_filename` | Hive-style raw file name for one fetch key. | str -> str | — | as class | see class |
| `build_schema` | The dataset's Schema (fields, text fields, primary key). | — -> Schema | `SchemaError` | as class | see class |

### `DateCodec` — `quant_cn.core.date_codec` (L1)
- **Purpose:** Validate and convert Tushare `YYYYMMDD` date strings and generate date keys for sweeps.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.Config.load`, `data_loading.DateSweepFetcher.list_keys`, `data_loading.PeriodSweepFetcher.list_keys`, `pipeline.DownloadPipeline.run`.
- **Tests:** `tests/core/test_date_codec.py` (TC-DC-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `validate` | Return `value` unchanged if it is a valid `YYYYMMDD` date string. | str -> str | `ValueError` | as class | see class |
| `to_date` | Parse a `YYYYMMDD` string. | str -> dt.date | `ValueError` | as class | see class |
| `to_str` | Format a date as `YYYYMMDD`. | dt.date -> str | — | as class | see class |
| `list_quarter_ends` | Report periods (Mar 31, Jun 30, Sep 30, Dec 31) within [start, end]. | str, str -> list[str] | `ValueError` | as class | see class |
| `list_weekdays` | Monday-to-Friday dates within [start, end], for announcement-date sweeps. | str, str -> list[str] | `ValueError` | as class | see class |

### `Schema` — `quant_cn.core.schema` (L1)
- **Purpose:** Declare and enforce a DataFrame shape: text columns are pandas `string`, all other declared columns are `float64`, and the primary key is unique and non-null.
- **Base:** none. **Depends on (injected):** str, Sequence[str], Collection[str], Sequence[str].
- **Used by:** `core.DatasetSpec.build_schema`, `lake.ParquetWriter.write_raw`, `lake.ParquetWriter.write_curated`, `lake.Compactor.rebuild`.
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
- **Used by:** `core.BaseFetcher.run`, `core.BaseStep.run`, `lake.Compactor.rebuild`, `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`.
- **Tests:** `tests/core/test_base_fetcher.py` (TC-BF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `TickerNormalizer` — `quant_cn.core.ticker_normalizer` (L1)
- **Purpose:** Turn common A-share ticker spellings into Tushare `ts_code` and check `ts_code` validity.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** (none yet).
- **Tests:** `tests/core/test_ticker_normalizer.py` (TC-TN-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `normalize` | Convert `code` to `ts_code`. | str -> str | `ValueError` | as class | see class |
| `is_valid` | True if `code` is already a well-formed `ts_code`. | str -> bool | — | as class | see class |

### `FetcherFactory` — `quant_cn.data_loading.fetcher_factory` (L3)
- **Purpose:** Build the right fetcher for a DatasetSpec and inject the shared dependencies.
- **Base:** none. **Depends on (injected):** Config, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec.
- **Used by:** `pipeline.DownloadPipeline`, `cli.QuantCnCli`.
- **Tests:** `tests/data_loading/test_fetcher_factory.py` (TC-FF-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec -> None | — | callers of the class | — |
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
- **Purpose:** Datasets swept over an enumerated list: stock_basic by list_status (L, D, P), index_daily by index ts_code.
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, Sequence[str].
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-EF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, Sequence[str] -> None | — | callers of the class | — |
| `list_keys` | The enumerated values. | str, str -> list[str] | — | as class | see class |
| `build_params` | Key parameter plus constants and optional date range. | str, str, str -> dict[str, str] | — | as class | see class |

### `DateSweepFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Whole-market daily sweeps: trade_date keys are trading days (daily, adj_factor, daily_basic, moneyflow, stk_limit); ann_date keys are weekdays (event datasets).
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-DSF-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec -> None | — | callers of the class | — |
| `list_keys` | Trading days (trade_date) or weekdays (ann_date) in [start, end]. | str, str -> list[str] | `LakeError`, `ValueError` | as class | see class |
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

### `HttpTransport` — `quant_cn.data_loading.http_transport` (L3)
- **Purpose:** Send one JSON POST and return the decoded JSON object.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`.
- **Tests:** `tests/data_loading/test_tushare_client.py` (TC-TC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `fetch_json` | POST `payload` as JSON to `url`. | str, Mapping[str, Any], float -> dict[str, Any] | `OSError`, `ValueError` | as class | see class |

### `TushareClient` — `quant_cn.data_loading.tushare_client` (L3)
- **Purpose:** Query Tushare Pro: one logical query follows limit/offset paging until a short page and returns all rows; rate-limit replies wait and retry without spending retries; permission replies fail fast as PermissionDeniedError; other failures retry up to `retries`.
- **Base:** BaseApiClient. **Depends on (injected):** TushareConfig, Clock, HttpTransport | None.
- **Used by:** `data_loading.FetcherFactory`, `cli.QuantCnCli`.
- **Tests:** `tests/data_loading/test_tushare_client.py` (TC-TC-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | TushareConfig, Clock, HttpTransport \| None -> None | — | callers of the class | — |
| `query` | Fetch every page of one query. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `ConfigError`, `PermissionDeniedError`, `DataSourceError` | as class | see class |
| `_fetch_page` (private) | internal helper over 20 lines | str, Mapping[str, object], Sequence[str] -> dict[str, Any] | — | internal | — |

### `Compactor` — `quant_cn.lake.compactor` (L2)
- **Purpose:** Rebuild a dataset's curated partitions from its raw files: select declared fields, cast dtypes, drop duplicate primary keys (keeping one), sort by partition date then key, validate, write, and record a manifest in `meta/manifest/<dataset>.json`.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, BaseStore, Clock.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_compactor.py` (TC-CO-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, BaseStore, Clock -> None | — | callers of the class | — |
| `rebuild` | Replace the curated partitions of `spec` (all years, or only `years`). | DatasetSpec, set[int] \| None -> StepReport | `SchemaError`, `LakeError` | as class | see class |

### `FetchLog` — `quant_cn.lake.fetch_log` (L2)
- **Purpose:** Record finished (dataset, key) pairs in `meta.fetch_log`, mirror them to `meta/fetch_log.parquet` on save, and rebuild the table after the DuckDB file is lost.
- **Base:** BaseFetchLog. **Depends on (injected):** LakeCatalog.
- **Used by:** `core.BaseFetcher.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_fetch_log.py` (TC-FL-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog -> None | `LakeError` | callers of the class | — |
| `mirror_path` | Location of the durable parquet copy. | — -> Path | — | as class | see class |
| `read_done_keys` | Keys recorded for `dataset`. | str -> set[str] | `LakeError` | as class | see class |
| `mark_done` | Upsert one finished key. | str, str, int, Path \| None -> None | `LakeError` | as class | see class |
| `save` | Atomically rewrite `meta/fetch_log.parquet` from the table. | — -> Path | `LakeError` | as class | see class |
| `rebuild_from_mirror` | Rebuild the table from the parquet mirror, then add raw files the mirror does not know. | — -> int | `LakeError` | as class | see class |

### `LakeCatalog` — `quant_cn.lake.lake_catalog` (L2)
- **Purpose:** Own the lake's single DuckDB connection (`meta/quant_cn.duckdb`): schemas `raw`, `curated`, `meta`; one view per dataset and zone; `meta.dataset_meta`; generated INDEX.md files. The DuckDB file is disposable: `rebuild()` recreates it from the parquet files.
- **Base:** none. **Depends on (injected):** Path, Mapping[str, DatasetSpec].
- **Used by:** `lake.FetchLog`, `lake.RunLog`, `lake.LakeQuery`, `lake.Compactor`, `pipeline.FetchStep.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_lake_catalog.py` (TC-LC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, Mapping[str, DatasetSpec] -> None | `LakeError` | callers of the class | — |
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
- **Used by:** `lake.TradingCalendar`, `lake.Compactor.rebuild`, `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_lake_query.py` (TC-LQ-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog -> None | — | callers of the class | — |
| `sql` | Execute a query and return the result as a DataFrame. | str, Sequence[object] \| None -> pd.DataFrame | `LakeError` | as class | see class |
| `has_view` | True if `schema.view` exists in the catalog. | str -> bool | `LakeError` | as class | see class |

### `ParquetWriter` — `quant_cn.lake.parquet_writer` (L2)
- **Purpose:** Write raw fetch results and curated partitions as zstd parquet, atomically (write `.tmp`, fsync, rename), so a crash never leaves a half-written file.
- **Base:** BaseStore. **Depends on (injected):** Path.
- **Used by:** `core.BaseFetcher.run`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory`, `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_parquet_writer.py` (TC-PW-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `get_raw_path` | Target path of one raw fetch key. | DatasetSpec, str -> Path | — | as class | see class |
| `get_curated_path` | Target path of one curated partition. | DatasetSpec, int \| None -> Path | — | as class | see class |
| `write_raw` | Persist one fetch key's rows, dtypes coerced by the dataset schema (dates stay strings). | DatasetSpec, str, pd.DataFrame -> Path \| None | `SchemaError`, `LakeError` | as class | see class |
| `write_curated` | Replace one curated partition after validating it against the dataset schema. | DatasetSpec, int \| None, pd.DataFrame -> Path | `SchemaError`, `LakeError` | as class | see class |

### `RunLog` — `quant_cn.lake.run_log` (L2)
- **Purpose:** Append run and per-key events to `meta.run_log` (run_id, started_at, finished_at, kind, dataset, key, status, n_rows, duration_ms, message) and echo them to logging.
- **Base:** BaseRunLog. **Depends on (injected):** LakeCatalog, Clock.
- **Used by:** `core.BaseFetcher.run`, `pipeline.LocalRunner`, `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_run_log.py` (TC-RL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, Clock -> None | `LakeError` | callers of the class | — |
| `open_run` | Insert the run row (dataset and key NULL, status "running"). | str -> str | `LakeError` | as class | see class |
| `record_event` | Append one key event. | str, str, str, str, int, int, str -> None | `LakeError` | as class | see class |
| `close_run` | Set status, message and finished_at on the run row. | str, str, str -> None | `LakeError` | as class | see class |

### `TradingCalendar` — `quant_cn.lake.trading_calendar` (L2)
- **Purpose:** Answer trading-day questions (sessions in a range, is_open, next, prev) from the SSE calendar in the lake; loads lazily so it works after trade_cal is fetched in the same run.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `data_loading.DateSweepFetcher.list_keys`, `data_loading.FetcherFactory`, `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_trading_calendar.py` (TC-TCA-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery -> None | — | callers of the class | — |
| `refresh` | Drop the cached calendar so the next call re-reads trade_cal. | — -> None | — | as class | see class |
| `list_sessions` | Trading days within [start, end]. | str, str -> list[str] | `LakeError` | as class | see class |
| `is_open` | True if `date` is a trading day. | str -> bool | `LakeError` | as class | see class |
| `get_next` | First trading day strictly after `date`. | str -> str | `LakeError` | as class | see class |
| `get_prev` | Last trading day strictly before `date`. | str -> str | `LakeError` | as class | see class |

### `FetchStep` — `quant_cn.pipeline.download_pipeline` (L4)
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

### `DownloadPipeline` — `quant_cn.pipeline.download_pipeline` (L4)
- **Purpose:** Resolve which datasets and date ranges to download, run one FetchStep per dataset through the runner, and regenerate the lake indexes; `dry_run` lists pending keys without calling the API.
- **Base:** none. **Depends on (injected):** Config, FetcherFactory, BaseRunner, LakeCatalog, BaseFetchLog, Clock, DateCodec.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/pipeline/test_download_pipeline.py` (TC-DP-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, FetcherFactory, BaseRunner, LakeCatalog, BaseFetchLog, Clock, DateCodec -> None | — | callers of the class | — |
| `run` | Download the requested datasets (default: config.download.order). | Sequence[str] \| None, str \| None, str \| None, bool, bool -> PipelineReport | `ConfigError`, `ValueError`, `DataSourceError` | as class | see class |

### `PipelineReport` — `quant_cn.pipeline.runner` (L4)
- **Purpose:** Result of one pipeline run: its id, overall status and one StepReport per step.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_blocked` | Names of steps blocked by missing permissions. | — -> list[str] | — | as class | see class |
| `to_frame` | One row per step for display or logging. | — -> pd.DataFrame | — | as class | see class |

### `BaseRunner` — `quant_cn.pipeline.runner` (L4)
- **Purpose:** Extension point for how steps are executed (local now, Prefect later, D-022); steps never import the runner's backend.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `pipeline.LocalRunner`, `pipeline.DownloadPipeline`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | Execute steps in order under one run id. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

### `LocalRunner` — `quant_cn.pipeline.runner` (L4)
- **Purpose:** Run steps serially in this process with a rich progress bar per step; a permission failure marks the step blocked and continues; any other project error closes the run as failed and re-raises (finished keys stay done).
- **Base:** BaseRunner. **Depends on (injected):** BaseRunLog, Console | None, bool.
- **Used by:** `pipeline.DownloadPipeline`, `cli.QuantCnCli`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseRunLog, Console \| None, bool -> None | — | callers of the class | — |
| `run` | See BaseRunner.run. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

## C. Abstract base classes / extension points

| Class | Module | Layer | Purpose | Abstract methods (purpose each) | Known subclasses | Added |
|---|---|---|---|---|---|---|
| `BaseApiClient` | `quant_cn.core.base_api_client` | 1 | Abstract vendor client: one logical query returns all pages as one DataFrame. | `query`: Run one query and return every row across pages. | `TushareClient` | 2026-09-27 |
| `BaseFetchLog` | `quant_cn.core.base_fetch_log` | 1 | Abstract record of which (dataset, key) pairs are fully downloaded. | `read_done_keys`: All keys recorded as done for a dataset.; `mark_done`: Record a finished key, replacing any earlier record for it.; `save`: Make recorded keys durable (e.g. write the parquet mirror). | `FetchLog` | 2026-09-27 |
| `BaseFetcher` | `quant_cn.core.base_fetcher` | 1 | Download one dataset as a sequence of keys | `list_keys`: All fetch keys for [start, end], ascending.; `build_params`: API parameters for one key. | `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher` | 2026-09-27 |
| `BaseRunLog` | `quant_cn.core.base_run_log` | 1 | Abstract append-only log of runs and per-key events | `open_run`: Open a run and return its id.; `record_event`: Append one event (fetched / skipped / empty / failed / blocked).; `close_run`: Close a run with its final status. | `RunLog` | 2026-09-27 |
| `BaseStep` | `quant_cn.core.base_step` | 1 | Abstract unit of pipeline work: list its units, then run and report. | `name`: Step name shown in progress and reports.; `list_units`: Compute the work units (e.g. keys) just before running.; `run`: Do the work listed by `list_units`. | `FetchStep` | 2026-09-27 |
| `BaseStore` | `quant_cn.core.base_store` | 1 | Abstract sink for raw fetch results and curated partitions. | `write_raw`: Persist one fetch key's rows atomically.; `write_curated`: Replace one curated partition atomically after validating its schema. | `ParquetWriter` | 2026-09-27 |
| `BaseRunner` | `quant_cn.pipeline.runner` | 4 | Extension point for how steps are executed (local now, Prefect later, D-022) | `run`: Execute steps in order under one run id. | `LocalRunner` | 2026-09-27 |

## D. Exceptions

| Class | Module | Parent | Purpose / raised when | Raised by | Added |
|---|---|---|---|---|---|
| `QuantCnError` | `quant_cn.core.exceptions` | `Exception` | Root of every exception the package raises, so callers catch project errors in one place. | `pipeline.LocalRunner.run`, `cli.QuantCnCli.run` | 2026-09-27 |
| `ConfigError` | `quant_cn.core.exceptions` | `QuantCnError` | Configuration is missing, malformed or unsafe (e.g. lake root inside the repository). | `core.Config.load`, `core.Config.get_dataset`, `data_loading.TushareClient`, `data_loading.FetcherFactory.build`, `pipeline.DownloadPipeline.run` | 2026-09-27 |
| `SchemaError` | `quant_cn.core.exceptions` | `QuantCnError` | A DataFrame does not satisfy its declared Schema (columns, dtypes, primary key). | `core.Schema.normalize`, `core.Schema.validate` | 2026-09-27 |
| `DataSourceError` | `quant_cn.core.exceptions` | `QuantCnError` | The external data source failed: API error code, retries exhausted, malformed response. | `data_loading.TushareClient.query`, `core.BaseFetcher.run` | 2026-09-27 |
| `PermissionDeniedError` | `quant_cn.core.exceptions` | `DataSourceError` | The account lacks permission (points) for an endpoint; the dataset is blocked, not broken. | `data_loading.TushareClient.query`, `pipeline.LocalRunner.run` | 2026-09-27 |
| `LakeError` | `quant_cn.core.exceptions` | `QuantCnError` | The local lake cannot be read or written: missing dataset, failed atomic write, bad catalog. | `lake.ParquetWriter`, `lake.TradingCalendar`, `lake.LakeQuery.sql`, `cli.QuantCnCli` | 2026-09-27 |

## E. Schemas (DataFrame / typed records)

| Schema | Module | Purpose | Index | Columns (dtype) | Invariants | Produced by | Consumed by | Added |
|---|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | | |

## F. Allowed standalone functions (`core/utils` only, with justification)

| Function | Module | Purpose | Input -> Output | Why not a class method | Used by | Tests | Added |
|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | |
