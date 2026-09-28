# Data Loading Design (v1.2, 2026-09-27; D-021, D-022; execution adjustments D-026; method names per D-031)

Design for plan 01 phases 1–4: where the data lives on this machine, how bytes get from Tushare into the
lake, and how a run is monitored. No code until approved.

---

## 1. Local environment: the lake lives outside the repo

Goal: the repository never contains data; the code finds the lake through configuration that is itself
never committed.

### 1.1 Resolution order for the lake root
```
1. env  QUANT_CN_LAKE_ROOT                (highest; set in .env or the shell)
2. file config/local.yaml  lake.root      (git-ignored, machine-specific)
3. file config/base.yaml   lake.root      (committed default: ~/quant_cn_lake, OUTSIDE the repo)
```
`Config.load()` applies this order and resolves `~` and relative paths (relative = relative to repo root).
The committed default is deliberately outside the repo so a fresh clone can never write data into git.

### 1.2 Files on this machine
| Path | Committed | Content |
|---|---|---|
| `.env` (repo root) | **no** (`.gitignore`) | `TUSHARE_TOKEN=…`, `QUANT_CN_LAKE_ROOT=/Volumes/Treasury/quant_cn_lake` (approved location) |
| `.env.example` | yes | same keys, empty values, comments |
| `config/local.yaml` | **no** | optional overrides (`lake.root`, `download.default_start`, thread count) |
| `config/base.yaml` | yes | defaults; `lake.root: ~/quant_cn_lake` |
| `/Volumes/Treasury/quant_cn_lake/` | n/a | the lake (zones per FOLDER_STRUCTURE §2), sibling of the repo, not inside it |

Loading `.env`: `uv run --env-file .env <cmd>` for CLI/Make targets (uv feature, no extra dependency);
`Config.load()` also reads `.env` via `python-dotenv` when present, so notebooks work without the flag.

### 1.3 Guards (belt and braces)
- `.gitignore` still lists `data/`, `.env`, `config/local.yaml`, `*.parquet`, `*.duckdb` so even a wrong
  `lake.root` inside the repo cannot be committed.
- `Config` refuses a `lake.root` that is inside the repository unless `lake.allow_inside_repo: true` is set
  explicitly in `local.yaml` (tests use `tmp_path`, never the repo).
- `make doctor`: prints resolved lake root, checks it exists and is writable, checks free space, checks
  `TUSHARE_TOKEN` is set (not its value), and warns if the root is under a git working tree.
- pre-commit hook `check-added-large-files` (500 kB) as a last line of defence.

### 1.4 Backup
`raw/` and `meta/fetch_log.parquet` are the only irreplaceable parts. `make lake-backup` runs
`rsync -a --delete <root>/raw <root>/meta/fetch_log.parquet <backup_target>/` where `backup_target` comes
from `local.yaml` (`lake.backup_target`). Everything else is rebuilt with `make lake-rebuild`.

---

## 2. Data loading architecture (`data_loading` L3 writing into `lake` L2)

### 2.1 One run, end to end
```
DownloadPipeline.run(datasets?, start?, end?)
  for each dataset in config.download.order:
     spec     = config.dataset(name)                     # DatasetSpec from datasets.yaml
     fetcher  = FetcherFactory.build(spec)               # by spec.sweep.kind
     keys     = fetcher.list_keys(start, end)            # e.g. trading days from TradingCalendar
     for key in keys:                                    # BaseFetcher.run() template
        if fetch_log.is_done(name, key): skip
        df   = fetcher.fetch_one(key)                    # TushareClient.query(...), paged
        path = parquet_writer.write_raw(spec, key, df)   # atomic; empty df -> no file
        fetch_log.mark_done(name, key, len(df), path)
        run_log.record_event(...)                        # progress / monitoring (§3)
  lake_catalog.refresh_views(); lake_catalog.write_indexes()
```

### 2.2 Classes and contracts (summary; full docstrings at build time)

| Class | Purpose | Input → Output | Raises | Notes |
|---|---|---|---|---|
| `TushareClient` (`BaseApiClient`) | one JSON POST per call; paging; retry; rate-limit sleep | `query(api_name, params, fields) → DataFrame` (all pages concatenated, Tushare column names) | `DataSourceError` on `code != 0` after retries, permission errors, exhausted retries | token from env only; `page_size`, `retries`, `retry_sleep_s`, `rate_limit_sleep_s`, `rate_limit_markers` from `config.tushare`; injected `Clock` for sleeps so tests run instantly |
| `FakeTushareClient` (`BaseApiClient`, tests) | canned responses, scripted errors (rate-limit once, permission denied, short page) | same as above | same | drives every fetcher/pipeline test; no network in tests |
| `BaseFetcher` (core) | template: `keys()` → loop → `fetch_one()` → write → log | `run(start, end, keys=None) → FetchReport(fetched, skipped, empty, failed)`; `list_keys(start, end)`; `fetch_one(key)` | re-raises `DataSourceError` after logging the key as failed | one subclass **per sweep pattern**, not per endpoint |
| `SingleCallFetcher` | `sweep.kind: none` (trade_cal, namechange) | one key `"all"` | | overwrites the single raw file on refresh |
| `EnumFetcher` | `sweep.kind: list_status | ts_code` (stock_basic L/D/P, index_daily) | one key per enumerated value | | values from `spec.sweep.values` or `values_from` config path |
| `DateSweepFetcher` | `sweep.kind: trade_date | ann_date` (daily, adj_factor, daily_basic, moneyflow, stk_limit, stk_holdertrade) | keys = trading days (or weekdays for `ann_date`) in [start, end] from `TradingCalendar` | | one raw file per day (~5.5k rows) |
| `PeriodSweepFetcher` | `sweep.kind: period` (`*_vip` fundamentals) | keys = quarter ends via `DateCodec.list_quarter_ends` | | one raw file per quarter |
| `MonthWindowFetcher` | `sweep.kind: month` (share_float; offset paging broken) | keys = `YYYYMM`; passes `start_date`/`end_date` of the month | | plan 05 |
| `FetcherFactory` | map `sweep.kind` → fetcher class, inject client/writer/log/calendar | `build(spec) → BaseFetcher` | `ConfigError` unknown kind | adding a dataset with a known kind needs **no code** |
| `ParquetWriter` (lake) | atomic hive-named write (`tmp` → fsync → rename), zstd | `write_raw(spec, key, df) → Path`; `write_curated(spec, year, df) → Path` | `LakeError` | dtypes coerced by `Schema` only in curated; raw keeps Tushare dtypes with dates as strings |
| `FetchLog` (lake, `BaseFetchLog`) | done-keys; DuckDB table + `meta/fetch_log.parquet` mirror | `is_done(dataset, key) → bool`; `mark_done(dataset, key, n_rows, path)`; `list_pending(dataset, keys) → list`; `save()`; `rebuild_from_mirror()` | `LakeError` | rebuilt from `raw/` listing if the DuckDB file is lost |
| `RunLog` (lake) | append-only run/step/key events for monitoring (§3) | `open_run(kind) → run_id`; `record_event(run_id, dataset, key, status, n_rows, ms, msg)`; `close_run` | | DuckDB table `meta.run_log`, also streamed to logging |
| `DownloadPipeline` (pipeline) | order datasets, resolve date ranges (default vs long-history), run fetchers, refresh catalog | `run(datasets=None, start=None, end=None, dry_run=False) → PipelineReport` | propagates `DataSourceError`; partial progress is preserved by `FetchLog` | `dry_run` lists keys per dataset without calling the API |

### 2.3 Behaviour rules
- **Sweep by date, never by stock** (DATA_CATALOG rule 1). Per-stock endpoints only for `index_daily`.
- **Resumable at key granularity**: a crash loses at most one in-flight key; rerun = same command.
- **Empty result is not an error**: non-trading day or no events → `mark_done(n_rows=0)`, no file.
- **Rate limit**: message contains a marker (`每分钟`, `频率`) → sleep `rate_limit_sleep_s`, retry without
  counting against `retries`; other errors → `retry_sleep_s`, up to `retries`.
- **Permission error** (points): raise `DataSourceError` with the endpoint name; pipeline marks the dataset
  `blocked` and continues with the next dataset; report lists blocked datasets.
- **Paging**: `limit = page_size`, `offset += page_size` until a short page; concatenated before writing so a
  key is all-or-nothing.
- **Refresh semantics**: `trade_cal`, `stock_basic`, `namechange` are overwritten on every run (small,
  whole-history); sweep datasets are append-only, re-fetch a key only with `--force key`.
- **Long history**: datasets in `download.long_history_datasets` start at `long_history_start`, others at
  `default_start` (D-015b).
- **Concurrency**: single-threaded first (D-015g). The key loop stays inside `BaseFetcher.run` (core cannot import
  `pipeline`); a `KeyExecutor` seam is introduced only when concurrency is added (D-026).
- **Late filers**: period datasets re-fetch their most recent `sweep.refetch_recent` quarters on every run so
  restatements and late annual reports are captured; older quarters stay append-only (D-026).
- **Dedupe**: `Compactor` drops duplicate primary keys (keeps the last) and records the dropped count in the
  partition manifest (D-026).
- **Permission failures**: `PermissionDeniedError(DataSourceError)` lets the pipeline mark a dataset `blocked`
  in its `StepReport` and continue (D-026).

### 2.4 Configuration touched
`config/base.yaml` gains `download.order` (list of dataset names in dependency order) and
`download.force: []`; `config/datasets.yaml` as already specified; `tushare.*` as specified.

### 2.5 Tests (all offline)
| Area | Cases |
|---|---|
| `TushareClient` | short-page paging stops; two pages concatenate; rate-limit marker → sleep via fake clock then success; `code != 0` → `DataSourceError`; retries exhausted; permission message surfaced |
| fetchers | keys per kind (trading days from a fixture calendar, quarter ends, enum values); skip when done; empty result → done with 0 rows and no file; failure leaves earlier keys done |
| `FetchLog` | mark/is_done round trip; parquet mirror rebuilt into DuckDB; `pending()` ordering |
| `ParquetWriter` | atomic rename (no `.tmp` left on simulated crash); hive filename; readable by DuckDB with `hive_partitioning` |
| `DownloadPipeline` | dry run lists keys; crash-resume (fake client fails on 3rd key, rerun fetches only remaining); blocked dataset does not stop others; long-history start applied |
| config | env > local.yaml > base.yaml precedence; refusal of a lake root inside the repo; `~` expansion |

---

## 3. Monitoring the flows (third party, not Airflow or Dagster)

The pipeline is a single-machine, run-when-asked job. It needs run history, progress, per-key failures
and retry visibility, not a scheduler cluster.

| Option | What you get | Cost | Fit |
|---|---|---|---|
| **Built-in**: `RunLog` table in DuckDB + `rich` progress bars + `logging` | run/step/key history queryable with SQL, live progress in terminal, zero services | one dependency (`rich`) | baseline, always on |
| **Prefect 3** (open source, local) | web UI with run history, task states, retries, logs, timings; `prefect server start` runs locally on SQLite; decorators wrap our step methods | `prefect` dep, one local process | **recommended optional adapter** |
| **Hamilton + Hamilton UI** | dataflow graph visualisation and run tracking; function-based DAG | pushes toward functional style, conflicts with OOP standard | not recommended |
| **Kestra / Windmill** | full workflow platforms with UI, YAML flows | Java/Deno server, Docker | heavier than the problem |
| **Grafana + Loki** | dashboards over our logs/metrics | Docker, config | later, if the pipeline runs unattended on a server |
| **Logfire (Pydantic)** | hosted tracing with pydantic integration | SaaS, data leaves the machine | not for now |

Decision proposed (D-022): the built-in `RunLog` + `rich` is the baseline and the source of truth for
"what happened". Prefect is added as an **adapter**, not a dependency of the engine: `PrefectRunner`
implements the same `BaseRunner` interface as `LocalRunner` and wraps each `BaseStep.run`/fetch key as a
Prefect task, so the UI shows the same runs. Steps and fetchers never import Prefect. `make download`
uses `LocalRunner`; `make download RUNNER=prefect` uses the adapter with a local Prefect server.

The `RunLog` schema (`meta.run_log`): `run_id, started_at, finished_at, kind, dataset, key, status
(fetched|skipped|empty|failed|blocked), n_rows, duration_ms, message`. `project`/`meta` queries and the
research notebook read it directly; the Prefect UI is a convenience view over the same events.

---

## 3b. Implementation notes (from execution, 2026-09-27, commit a62bef1)
- `DatasetSpec.schema()` is named `build_schema()`: pydantic's `BaseModel.schema` occupies the name (was `frame_schema` before the D-031 rename).
- The token is read at query time, not at construction, so dry runs and tests need no `TUSHARE_TOKEN`.
- `TushareClient` delegates I/O to an `HttpTransport`; tests script the transport instead of mocking HTTP.
- Curated partitions are sorted by partition date first, then primary key.
- The three statement datasets (`income_vip`, `balancesheet_vip`, `cashflow_vip`) carry an original and a corrected version per filing, distinguished by `update_flag`; it is part of their primary key and must be requested in every backfill (D-038). `fina_indicator_vip` already included it.

## 4. Changes applied to other documents on approval (2026-09-27)
- `config/base.yaml`: `lake.root: ~/quant_cn_lake`, `lake.allow_inside_repo: false`, `lake.backup_target`, `download.order`.
- `FOLDER_STRUCTURE.md`: `data/` folder removed from the repo tree; lake shown as a sibling path; `.env` and `local.yaml` rows.
- `SRC_DESIGN.md` §2.4: `BaseRunner`, `LocalRunner`, `PrefectRunner`, `RunLog`, `KeyExecutor`.
- Plan 01: phase 1 adds `python-dotenv`, `rich`, `make doctor`, `BaseRunLog`, `StepReport`, `PermissionDeniedError`; phase 3 adds `RunLog`; phase 4 adds `FetcherFactory`, `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `LocalRunner`, `TradingCalendar` (moved from phase 5); `KeyExecutor` and `PrefectRunner` deferred.

## 5. Open questions
None. Closed 2026-09-27 (user approved the recommendations):
- Lake path on this machine: `/Volumes/Treasury/quant_cn_lake` (sibling of the repo, same disk); moving it later is a one-line change in `.env`.
- Prefect adapter deferred to a later plan; `RunLog` + `rich` first.
- `.env` loaded in code via `python-dotenv` (notebooks work); `uv run --env-file .env` also supported.
