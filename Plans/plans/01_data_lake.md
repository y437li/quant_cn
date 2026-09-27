# 01 — Data lake and Tushare download

| | |
|---|---|
| Status | approved 2026-09-27, not started; design: DATA_LOADING_DESIGN.md v1.0 |
| Owner | user (approve) / agent (execute) |
| Created | 2026-09-27 |
| Notion | pending (auth not completed) |
| Decisions | D-003, D-005, D-006, D-007, D-009, D-010, D-011, D-012, D-013, D-014, D-015, D-018, D-019, D-021, D-022 |
| Depends on plans | 00 (model roles) |

## Goal
A local lake (`FOLDER_STRUCTURE.md` §2: raw/curated/meta/external zones) holding the DATA_CATALOG core datasets as parquet, queryable through DuckDB with point-in-time-safe views, filled by a resumable Tushare download pipeline and a raw-to-curated compaction step.

## Scope
- In: `core` base classes; Tushare client; fetchers for trade_cal, stock_basic, namechange, daily, adj_factor, daily_basic, moneyflow, stk_limit, index_daily, fina_indicator_vip, income_vip, balancesheet_vip, cashflow_vip; parquet writer; DuckDB catalog, fetch log, query API; PIT aligner; `main.ipynb` smoke.
- Out: events datasets (forecast, express, holdertrade, share_float), intraday, features/factors, backtesting, portfolio. Follow-up plans.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Scaffold + toolchain + core | `pyproject.toml` (src layout, dependencies and dev group added via `uv add`, ruff/mypy/import-linter config), `uv.lock`, `.python-version` (3.12), `Makefile` (`setup`, `lint`, `check`, `doctor`, `lake-backup`, all via `uv run --env-file .env`), `.env.example`, `python-dotenv` + `rich` deps, `Config` lake-root resolution (env > local.yaml > base) with inside-repo guard, `.pre-commit-config.yaml`, `scripts/lint_contracts.py` (incl. `--index`) + `tests/test_contracts.py`, `INDEX.md` for every new folder at every depth (`src/`, `src/quant_cn/`, each of the eight packages incl. `visualization`, `tests/` and each test folder, `config/`, `scripts/`), optional `.claude/settings.json` ruff hook, `core` classes, `config/base.yaml` + `Config` | `uv sync --all-extras` ok from a clean clone; `make check` green including contract linter on the `core` classes; registry rows added | — | todo |
| 2 | Tushare client | `TushareClient` (POST, paging, retry, rate-limit sleep via injected `Clock`) + `FakeTushareClient` (canned pages, scripted rate-limit/permission errors) | TC pass against fake incl. paging and rate-limit; one live `trade_cal` call returns rows | 1 | todo |
| 3 | Lake core | `lake` package: `ParquetWriter` (atomic, hive-named raw files), `LakeCatalog` (DuckDB views over raw/ and curated/, `dataset_meta` from `config/datasets.yaml`), `FetchLog` (DuckDB table + `meta/fetch_log.parquet`), `RunLog` (`meta.run_log`), `Compactor` (raw -> curated yearly partitions with `Schema` check, manifests), `LakeQuery`; `LakeCatalog.write_indexes()` generating `INDEX.md` in every lake zone folder | test lake in tmp_path: raw write → compact → `LakeQuery.sql()` roundtrip; delete `.duckdb` → `rebuild()` restores views and fetch_log; resume skips logged keys; schema violation refuses partition | 1 | todo |
| 4 | Fetchers + pipeline | `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher`, `FetcherFactory`, `KeyExecutor` (serial), `BaseRunner`/`LocalRunner` (rich progress + RunLog), `DownloadPipeline` (`dry_run`, blocked datasets, long-history starts) | dry run lists keys; crash-resume on fake client; blocked dataset does not stop the run; live pull of 2026-08 daily datasets and 2026Q2 fundamentals lands in `/Volumes/Treasury/quant_cn_lake` | 2, 3 | todo |
| 5 | Derived + PIT | `curated/derived/prices_adj` (`close*adj_factor`), `fundamentals` (report_type=1, all ann_date versions), `PitAligner` building `derived/fundamentals_pit` via DuckDB ASOF JOIN; `CuratePipeline` | synthetic restatement test proves no row visible before its `ann_date`; suspended days absent unless dense=True; `make lake-rebuild` reproduces derived byte-identical | 3, 4 | todo |
| 6 | Research entry | `research_space/main.ipynb` querying lake through `LakeQuery` and plotting adjusted prices with `visualization.PriceChart` (`BaseChart`, `PriceChart` built here); `config/README.md` | notebook runs top to bottom on the phase-4 sample; `make check` green across the whole tree | 5 | todo |

## Classes (with planned Used by, D-010)

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `ContractLinter` (+ `DocstringParser`, `RegistryReader`, `UsageScanner`) | new | scripts/lint_contracts.py | 1 | `make lint`, pre-commit, `tests/test_contracts.py` |
| `Config` | new | core | 1 | every class via injection; `DownloadPipeline`, `LakeCatalog`, `main.ipynb`; resolves lake root env > local.yaml > base and refuses roots inside the repo (D-021) |
| `QuantCnError` + `DataSourceError`, `SchemaError`, `ConfigError`, `LakeError` | new | core | 1 | raised by `TushareClient`, `Schema`, `Config`, `LakeCatalog` |
| `BaseFetcher` | new | core | 1 | all `*Fetcher`; `DownloadPipeline` (type contract) |
| `BaseStore` | new | core | 1 | `ParquetWriter`, `LakeCatalog`, `Compactor` |
| `Schema` | new | core | 1 | `Compactor.write_partition` (validate), `LakeCatalog` (views), `PitAligner` |
| `DateCodec` | new | core | 1 | `TradeCalFetcher`, `DailySweepFetcher` (date sweeps), `PitAligner`, `main.ipynb` |
| `TickerNormalizer` | new | core | 1 | `StockBasicFetcher`, `LakeQuery` (input checks) |
| `TushareClient` | new | data_loading | 2 | all `*Fetcher` |
| `FakeTushareClient` | new | tests | 2 | fetcher and pipeline tests (paging, rate-limit, permission, crash scripts) |
| `ParquetWriter` | new | lake | 3 | all `*Fetcher` (via `BaseFetcher.persist`), `Compactor` |
| `LakeCatalog` | new | lake | 3 | `LakeQuery`, `FetchLog`, `Compactor`, `PitAligner`, `DownloadPipeline`, `CuratePipeline`; `write_indexes()` used by `DownloadPipeline` and `CuratePipeline` after each run |
| `Compactor` | new | lake | 3 | `CuratePipeline.step_compact`; `make lake-rebuild` |
| `FetchLog` | new | lake | 3 | `BaseFetcher` (skip/record), `DownloadPipeline` (progress), `LakeCatalog.rebuild` |
| `RunLog` | new | lake | 3 | `LocalRunner`, `BaseFetcher.run`, `main.ipynb` (run history) |
| `LakeQuery` | new | lake | 3 | `PitAligner`, `main.ipynb`, later `statistic`/`back_testing` |
| `SingleCallFetcher` (trade_cal, namechange) | new | data_loading | 4 | `FetcherFactory`; `DownloadPipeline` |
| `EnumFetcher` (stock_basic L/D/P, index_daily) | new | data_loading | 4 | `FetcherFactory`; `DownloadPipeline` |
| `DateSweepFetcher` (daily, adj_factor, daily_basic, moneyflow, stk_limit) | new | data_loading | 4 | `FetcherFactory`; `DownloadPipeline` |
| `PeriodSweepFetcher` (4 vip endpoints) | new | data_loading | 4 | `FetcherFactory`; `DownloadPipeline` |
| `FetcherFactory` | new | data_loading | 4 | `DownloadPipeline` |
| `KeyExecutor` | new | pipeline | 4 | `BaseFetcher.run` via `LocalRunner` |
| `BaseRunner`, `LocalRunner` | new | pipeline | 4 | `DownloadPipeline`, `CuratePipeline`, `make download` |
| `DownloadPipeline` | new | pipeline | 4 | CLI entry point; `main.ipynb` (incremental refresh) |
| `CuratePipeline` | new | pipeline | 5 | CLI entry point (`make lake-rebuild`), `main.ipynb` |
| `BaseChart`, `PriceChart` | new | visualization | 6 | `main.ipynb`; later `statistic`/`back_testing` notebooks via `to_frame()` |
| `TradingCalendar` | new | lake | 5 | `PitAligner` (next-day shift), `DailySweepFetcher` (date list), later `RebalanceSchedule`, `ExecutionModel` |
| `PitAligner` | new | lake | 5 | `CuratePipeline.step_pit`; `main.ipynb`; later `pipeline` features step |

Each row's Used by becomes the class's docstring section at creation time and is corrected as code lands.

Dataset metadata (primary key, known-on column, sweep param, field list, units) is data, not code: one row per dataset in `config/base.yaml`, loaded by `LakeCatalog`. Adding a dataset = one YAML entry + at most one fetcher subclass.

## Risks
- Volume reliability: the old disk corrupted `.venv`/`.git`. Lake root is `/Volumes/Treasury/quant_cn_lake` (D-021), switchable in `.env`; `make lake-backup` rsyncs `raw/` + `meta/fetch_log.parquet`; everything else is rebuildable (D-012).
- Small-file count in `raw/` (~250 files/year/dataset): acceptable for resumability; queries use `curated/` yearly files, never `raw/` directly, except during compaction.
- `*_vip` endpoints need account points; phase 4 live test will reveal missing permissions.
- Rate limits make full history a multi-day job; phase 4 only proves one month + one quarter. Full backfill is a run, not a phase.
- Parquet schema drift across years (Tushare adds columns): `Schema` enforces column set and dtypes on write.
- DuckDB API changes between versions: exact version held by `uv.lock`; upgrade only via `uv lock --upgrade-package duckdb` with a decision entry.
- Contract linter false positives (e.g. dynamic dispatch not visible to grep): allow `# contract: ignore <reason>` with a decision/issue reference, tracked so exceptions stay rare.

## Open questions
- none; defaults recorded in D-015

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-27 | — | Plan drafted; awaiting approval |
| 2026-09-27 | 1 | D-019 applied to skeleton: `src/quant_cn/visualization/` (`__init__.py`, `INDEX.md`) and `tests/visualization/INDEX.md`; parent indexes updated. uv files remain phase-1 work |
| 2026-09-27 | 1 | Folder skeleton built per FOLDER_STRUCTURE v1.0: `src/quant_cn/` 7 packages (`__init__.py` only), `tests/` 7 folders, `config/`, `scripts/`, `research_space/notebooks/`, all `INDEX.md`, `.gitignore`, `.env.example`. Remaining phase-1 deliverables untouched |
| 2026-09-27 | 1, 6 | D-010: Used-by section required; audit script added to phase 1, full audit to phase 6; class table gains planned Used by |
| 2026-09-27 | 1–4 | DATA_LOADING_DESIGN v1.0 approved (D-021 lake outside repo, D-022 RunLog + rich, Prefect deferred): phase deliverables and class table updated; fetchers renamed per sweep pattern |
| 2026-09-27 | — | User clarified "start data loading design": no execution; `Plans/DATA_LOADING_DESIGN.md` drafted; status back to not started |
| 2026-09-27 | 1, 5 | SRC_DESIGN (D-020): `core.frames`, `Clock`, `BaseApiClient`, `BaseFetchLog` in phase 1; `TradingCalendar` in phase 5 |
| 2026-09-27 | 1, 6 | D-019: `visualization` package (L5, plotly); `BaseChart`/`PriceChart` added to phase 6 |
| 2026-09-27 | 1 | D-018: uv manages packages; phase 1 deliverables and done criterion updated |
| 2026-09-27 | 1, 3 | Indexes required at every depth (incl. package and test subfolders); lake zone indexes generated by `LakeCatalog.write_indexes()` |
| 2026-09-27 | — | Plan approved ("approve all"); D-015 records defaults. Agent began phase 1 prematurely; user said "just plan"; scaffold and core drafts moved out of the repo, phase 1 back to todo |
| 2026-09-27 | 1 | D-014: INDEX.md per folder; `--index` check added to the linter; every phase creating a folder creates its index |
| 2026-09-27 | 1 | D-013: registry detail blocks with per-method purpose; `lint_contracts.py` also checks method-table parity |
| 2026-09-27 | 3, 5 | D-012: lake zones raw/curated/meta/external; storage classes move to `lake` package; `Compactor` and `CuratePipeline` added; rebuild criterion added |
| 2026-09-27 | 1, 6 | D-011: full linter toolchain (ruff, mypy, import-linter, contract linter, pre-commit, make) moved into phase 1; audit script becomes `lint_contracts.py`; phase 6 done criterion is `make check` |
