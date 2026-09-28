# 01 — Data lake and Tushare download

| | |
|---|---|
| Status | doing — phases 1–4 code-complete (commit `a62bef1`, session quant-cn-b7, branch `feat/data-loading`); phases 1–5 done (commits `a62bef1`, `4aa43c0`, `7bd9b36`, `97a2f7e`); phase 6 doing |
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
| 1 | Scaffold + toolchain + core | `pyproject.toml` (src layout, dependencies and dev group added via `uv add`, ruff/mypy/import-linter config), `uv.lock`, `.python-version` (3.12), `Makefile` (`setup`, `lint`, `check`, `doctor`, `lake-backup`, all via `uv run --env-file .env`), `.env.example`, `python-dotenv` + `rich` deps, `Config` lake-root resolution (env > local.yaml > base) with inside-repo guard, `.pre-commit-config.yaml`, `scripts/lint_contracts.py` (incl. `--index`) + `tests/test_contracts.py`, `INDEX.md` for every new folder at every depth (`src/`, `src/quant_cn/`, each of the eight packages incl. `visualization`, `tests/` and each test folder, `config/`, `scripts/`), optional `.claude/settings.json` ruff hook, `core` classes, `config/base.yaml` + `Config` | `uv sync --all-extras` ok from a clean clone; `make check` green including contract linter on the `core` classes; registry rows added | — | done |
| 2 | Tushare client | `TushareClient` (POST, paging, retry, rate-limit sleep via injected `Clock`) + `FakeTushareClient` (canned pages, scripted rate-limit/permission errors) | TC pass against fake incl. paging and rate-limit; one live `trade_cal` call returns rows | 1 | done |
| 3 | Lake core | `lake` package: `ParquetWriter` (atomic, hive-named raw files), `LakeCatalog` (DuckDB views over raw/ and curated/, `dataset_meta` from `config/datasets.yaml`), `FetchLog` (DuckDB table + `meta/fetch_log.parquet`), `RunLog` (`meta.run_log`), `Compactor` (raw -> curated yearly partitions with `Schema` check, manifests), `LakeQuery`; `LakeCatalog.write_indexes()` generating `INDEX.md` in every lake zone folder | test lake in tmp_path: raw write → compact → `LakeQuery.sql()` roundtrip; delete `.duckdb` → `rebuild()` restores views and fetch_log; resume skips logged keys; schema violation refuses partition | 1 | done |
| 4 | Fetchers + pipeline | `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher`, `FetcherFactory`, `KeyExecutor` (serial), `BaseRunner`/`LocalRunner` (rich progress + RunLog), `DownloadPipeline` (`dry_run`, blocked datasets, long-history starts) | dry run lists keys; crash-resume on fake client; blocked dataset does not stop the run; live pull of 2026-08 daily datasets and 2026Q2 fundamentals lands in `/Volumes/Treasury/quant_cn_lake` | 2, 3 | done |
| 5 | Derived + PIT | `curated/derived/prices_adj` (`close*adj_factor`), `fundamentals` (report_type=1, all ann_date versions), `PitAligner` building `derived/fundamentals_pit` via DuckDB ASOF JOIN; `CuratePipeline` | synthetic restatement test proves no row visible before its `ann_date`; suspended days absent (dense option deferred to plan 04/05, see Log); `make lake-rebuild` reproduces derived byte-identical | 3, 4 | done |
| 6 | Research entry | `research_space/main.ipynb` querying lake through `LakeQuery` and plotting adjusted prices with `visualization.PriceChart` (`BaseChart`, `PriceChart` built here); `config/README.md` | notebook runs top to bottom on the phase-4 sample; `make check` green across the whole tree | 5 | done |

## Classes (with planned Used by, D-010)

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `ContractLinter` (+ `DocstringParser`, `RegistryReader`, `UsageScanner`) | new | scripts/lint_contracts.py | 1 | `make lint`, pre-commit, `tests/test_contracts.py` |
| `Config` | new | core | 1 | every class via injection; `DownloadPipeline`, `LakeCatalog`, `main.ipynb`; resolves lake root env > local.yaml > base and refuses roots inside the repo (D-021) |
| `QuantCnError` + `DataSourceError` (+ `PermissionDeniedError`), `SchemaError`, `ConfigError`, `LakeError` | new | core | 1 | raised by `TushareClient`, `Schema`, `Config`, `LakeCatalog` |
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
| `KeyExecutor` | deferred (D-026: serial loop stays inside `BaseFetcher.run` until concurrency is added) | pipeline | — | — |
| `BaseRunner`, `LocalRunner` | new | pipeline | 4 | `DownloadPipeline`, `CuratePipeline`, `make download` |
| `DownloadPipeline` | new | pipeline | 4 | CLI entry point; `main.ipynb` (incremental refresh) |
| `CuratePipeline` | new | pipeline | 5 | CLI entry point (`make lake-rebuild`), `main.ipynb` |
| `BaseChart`, `PriceChart` | new | visualization | 6 | `main.ipynb`; later `statistic`/`back_testing` notebooks via `to_frame()` |
| `TradingCalendar` | new | lake | 4 (moved from 5, D-026) | `PitAligner` (next-day shift), `DailySweepFetcher` (date list), later `RebalanceSchedule`, `ExecutionModel` |
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

## Open items (2026-09-27)
- ~~`TUSHARE_TOKEN` empty~~ set by user 2026-09-27; `make doctor` green. Phase 2 and phase 4 live criteria met the same day (see Log).
- ~~Deferred phase-1 items~~ landed in `7bd9b36` (linter, pre-commit, `core.frames`); the `.claude/settings.json` ruff hook belongs to plan 00.

## Open questions
- none; defaults recorded in D-015

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-27 | — | Plan drafted; awaiting approval |
| 2026-09-27 | 1 | D-019 applied to skeleton: `src/quant_cn/visualization/` (`__init__.py`, `INDEX.md`) and `tests/visualization/INDEX.md`; parent indexes updated. uv files remain phase-1 work |
| 2026-09-27 | 1 | Folder skeleton built per FOLDER_STRUCTURE v1.0: `src/quant_cn/` 7 packages (`__init__.py` only), `tests/` 7 folders, `config/`, `scripts/`, `research_space/notebooks/`, all `INDEX.md`, `.gitignore`, `.env.example`. Remaining phase-1 deliverables untouched |
| 2026-09-27 | 1, 6 | D-010: Used-by section required; audit script added to phase 1, full audit to phase 6; class table gains planned Used by |
| 2026-09-27 | 6 | `visualization.ChartTheme`/`BaseChart`/`PriceChart` (plotly 7.1 via uv; adjusted candles over a volume panel, category x of trading days, DataFrame-only input per D-019); `research_space/main.ipynb` (prices + charts, PIT fundamentals, run history); `make notebook`; `config/README.md` documents every key (7388daf, quant-cn-b7) |
| 2026-09-27 | 6 | Phase 6 done: `make notebook` ran main.ipynb top to bottom on the 2026-08 sample (21 sessions each for 000001.SZ and 600519.SH, two PriceChart figures, PIT table, run_log). `make check`: ruff passed; mypy 59 files; Layers KEPT; lint_contracts 0 findings; coverage 95%; 174 passed. Deviations from D-019 recorded in D-039: no `to_png` (needs kaleido + Chrome), no `PanelChart` yet. **Plan 01 complete** |
| 2026-09-27 | 5 | `DerivedViews` (prices_adj = close×adj_factor in PRICE_PANEL shape; fundamentals_long = period datasets unpivoted, report_type 1, all versions; fundamentals_states), `PitAligner` (effective = first session after known_on; latest period then latest restatement; ASOF read → FUNDAMENTALS_PIT), `LakeQuery.read_prices`, `CuratePipeline` + `cli curate` + `make lake-rebuild`; synthetic restatement tests TC-PA-001..005 pass (97a2f7e, quant-cn-b7) |
| 2026-09-27 | 5 | Live: `make curate` run 806b2a5e9bf3 compacted 10 datasets, 307,430 state rows over 6,196 tickers; `make lake-rebuild` deleted the DuckDB file, restored fetch log from parquet, re-curated: digests unchanged (prices_adj 90af8965…, fundamentals_long ffadd6a8…, fundamentals_states d27b3ddd…). PIT spot check: 000001.SZ H1-2026 (f_ann_date Sat 20260815) first visible 20260817 |
| 2026-09-27 | 5 | Data finding: income/balancesheet/cashflow_vip return original + corrected versions per filing (`update_flag`); field was not requested, so compaction dropped 4,075 keys, 4 with differing values. Fix (D-038): `update_flag` added to fields and primary key; 2026Q2 statements refetched with --force (run 1d39f8033d89); curated keeps 10,602 / 11,187 / 10,553 rows |
| 2026-09-27 | 5 | Phase 5 done. `make check`: ruff passed; mypy 56 files; Layers KEPT; lint_contracts 0 findings; coverage 95%; 168 passed. Criterion narrowed: `dense=True` (reindex on trade_cal) not built; prices_adj is sparse; dense option deferred to plan 04/05 |
| 2026-09-27 | 6 | Phase 6 started (quant-cn-b7): plotly, BaseChart/PriceChart, main.ipynb, config/README.md |
| 2026-09-27 | 1 | Deferred items landed (7bd9b36, quant-cn-b7): `core.docs` package (DocstringParser, MarkdownTableReader, IndexReader, RegistryReader, ConventionReader, CodeScanner, RepoFiles; ContractChecker, IndexChecker, SizeChecker, NameChecker; ContractLinter); `scripts/lint_contracts.py` (--contracts --index --size --names) in `make lint`, pre-commit and `tests/test_contracts.py`; `core/frames.py` (PRICE_PANEL, FUNDAMENTALS_PIT; registry E); `.pre-commit-config.yaml`; settings hook left to plan 00. Used by sections rewritten to actual references; test helpers renamed (Sample.build_*, add_failure). Registry A–E regenerated: 62 classes, 8 abstract, 6 exceptions, 2 schemas |
| 2026-09-27 | 1 | Phase 1 done. `make check`: ruff "All checks passed!"; mypy "Success: no issues found in 53 source files"; "Layers KEPT"; "lint_contracts (contracts, index, size, names): 0 finding(s)"; coverage TOTAL 95%; "155 passed in 3.56s" |
| 2026-09-27 | 5 | Phase 5 started (quant-cn-b7) on the Aug-2026 / 2026Q2 sample |
| 2026-09-27 | 4 | Live pull done (quant-cn-a1). Run 15e5023731fd, Aug 2026 (20260801–20260831), 21 trading days each: daily 116,335 rows; adj_factor 116,723; daily_basic 116,335; moneyflow 116,335; stk_limit 118,088. Run 2b40d3f7feb1, period 20260630: fina_indicator_vip 10,747; income_vip 10,609; balancesheet_vip 11,191; cashflow_vip 10,560. All keys fetched, none empty or failed; ~3.5 min total, no rate-limit sleeps. Phase 4 done |
| 2026-09-27 | 2 | Token set by user; `make doctor` green; live `trade_cal` download run 68e484f15774 ok: 1 key, 13,067 rows into the lake. Phase 2 done |
| 2026-09-27 | 1–4 | D-031: all methods renamed to the NAMING_CONVENTION verb table (commit 4aa43c0, quant-cn-b7); `make check` green (ruff, mypy 37 files, layers kept, 112 passed); registry A–D and code INDEX.md files regenerated |
| 2026-09-27 | 1 | Toolchain (uv, ruff, mypy strict, import-linter, Makefile), core classes, `config/base.yaml` + `datasets.yaml` (13 datasets) built; `make check` green; `lint_contracts`/pre-commit/settings hook/`core.frames` deferred on user instruction |
| 2026-09-27 | 2 | `TushareClient` + `HttpTransport`; TC-TC-001..007 pass against a scripted transport; live `trade_cal` call blocked: `TUSHARE_TOKEN` not set |
| 2026-09-27 | 3 | `ParquetWriter`, `LakeCatalog`, `FetchLog` (+parquet mirror, restore), `RunLog`, `LakeQuery`, `Compactor`; test-lake criteria pass (TC-LC-003 rebuild, TC-FL-002/004 restore, TC-BF-002 resume, TC-PW-005 schema refusal); phase done |
| 2026-09-27 | 4 | Fetchers per sweep pattern, `FetcherFactory`, `TradingCalendar`, `LocalRunner`, `DownloadPipeline`; dry run, crash-resume and blocked-dataset tests pass (TC-DP-001..005); live pull blocked: token |
| 2026-09-27 | 1–4 | Reported `make check` (quant-cn-b7, commit a62bef1): ruff "All checks passed!"; mypy --strict "Success: no issues found in 37 source files"; lint-imports "Layers (CODING_STANDARD §2.1) KEPT"; pytest "112 passed in 2.11s", coverage TOTAL 94% |
| 2026-09-27 | 1–4 | Execution started by session quant-cn-b7 on user instruction ("update the env config, and execute the data_loading plan"), branch `feat/data-loading`; plan 00 not applied. Adjustments D-024–D-026 recorded; `TradingCalendar` moved to phase 4; `KeyExecutor` deferred; core gains `BaseRunLog`, `StepReport`, `PermissionDeniedError`; `sweep.refetch_recent` for period datasets; `Compactor` dedupes on primary key |
| 2026-09-27 | 1–4 | DATA_LOADING_DESIGN v1.0 approved (D-021 lake outside repo, D-022 RunLog + rich, Prefect deferred): phase deliverables and class table updated; fetchers renamed per sweep pattern |
| 2026-09-27 | — | User clarified "start data loading design": no execution; `plans/architecture/DATA_LOADING_DESIGN.md` drafted; status back to not started |
| 2026-09-27 | 1, 5 | SRC_DESIGN (D-020): `core.frames`, `Clock`, `BaseApiClient`, `BaseFetchLog` in phase 1; `TradingCalendar` in phase 5 |
| 2026-09-27 | 1, 6 | D-019: `visualization` package (L5, plotly); `BaseChart`/`PriceChart` added to phase 6 |
| 2026-09-27 | 1 | D-018: uv manages packages; phase 1 deliverables and done criterion updated |
| 2026-09-27 | 1, 3 | Indexes required at every depth (incl. package and test subfolders); lake zone indexes generated by `LakeCatalog.write_indexes()` |
| 2026-09-27 | — | Plan approved ("approve all"); D-015 records defaults. Agent began phase 1 prematurely; user said "just plan"; scaffold and core drafts moved out of the repo, phase 1 back to todo |
| 2026-09-27 | 1 | D-014: INDEX.md per folder; `--index` check added to the linter; every phase creating a folder creates its index |
| 2026-09-27 | 1 | D-013: registry detail blocks with per-method purpose; `lint_contracts.py` also checks method-table parity |
| 2026-09-27 | 3, 5 | D-012: lake zones raw/curated/meta/external; storage classes move to `lake` package; `Compactor` and `CuratePipeline` added; rebuild criterion added |
| 2026-09-27 | 1, 6 | D-011: full linter toolchain (ruff, mypy, import-linter, contract linter, pre-commit, make) moved into phase 1; audit script becomes `lint_contracts.py`; phase 6 done criterion is `make check` |
