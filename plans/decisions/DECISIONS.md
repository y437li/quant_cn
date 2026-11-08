# Decisions Log

Append-only. Format and rules: `.claude/skills/decisions/SKILL.md`.

| ID | Date | Title | Status | Where it applies |
|---|---|---|---|---|
| D-001 | 2026-09-27 | Plan first, standard is binding | accepted | CLAUDE.md, CODING_STANDARD.md |
| D-002 | 2026-09-27 | Object-oriented only, class registry | accepted | CODING_STANDARD §1, §5 |
| D-003 | 2026-09-27 | Tushare Pro via raw HTTP, token in env | accepted | data_loading, TUSHARE_API.md |
| D-004 | 2026-09-27 | Parquet storage partitioned by year | superseded by D-009 | data_loading, DATA_CATALOG §4 |
| D-005 | 2026-09-27 | Dates as YYYYMMDD strings, ts_code tickers | accepted | CODING_STANDARD §4 |
| D-006 | 2026-09-27 | PIT alignment on ann dates, one aligner class | accepted | CODING_STANDARD §2.7 |
| D-007 | 2026-09-27 | Folder structure: config / src pkg / research_space | accepted | plans/architecture/FOLDER_STRUCTURE.md |
| D-008 | 2026-09-27 | Plans local-first, Notion mirrors phases | accepted | .claude/skills/plan |
| D-009 | 2026-09-27 | Local data lake: parquet files + DuckDB catalog | accepted | plans/execution/01_data_lake.md, FOLDER_STRUCTURE.md |
| D-010 | 2026-09-27 | Docstrings carry a Used by dependency map | accepted | CODING_STANDARD §3, §5; CLASS_REGISTRY |
| D-011 | 2026-09-27 | Linter toolchain: ruff, mypy, import-linter, contract linter | accepted | CODING_STANDARD §4.1, plan 01 phase 1 |
| D-012 | 2026-09-27 | Lake zones raw/curated/meta/external; `lake` package | accepted | FOLDER_STRUCTURE §2–3, plan 01 |
| D-013 | 2026-09-27 | Registry tracks per-method purpose in detail blocks | accepted | CLASS_REGISTRY §B, CODING_STANDARD §5 |
| D-014 | 2026-09-27 | INDEX.md in every folder, forming a tree from root | accepted | CODING_STANDARD §5.1, all folders |
| D-015 | 2026-09-27 | Plan 01 defaults: lake root, backfill depth, views first, names, notebook | accepted | plans/execution/01_data_lake.md, config/base.yaml |
| D-016 | 2026-09-27 | Model roles: Fable plans + reviews, Opus executes | accepted (plan 00 approved, not applied) | .claude/agents, CLAUDE.md, skills |
| D-017 | 2026-09-27 | Project catalog: repo tree + registry + plans queryable in lake DuckDB | accepted | plans/execution/02_project_catalog.md |
| D-018 | 2026-09-27 | Packages managed by uv (pyproject + uv.lock, uv run) | accepted | CODING_STANDARD §4.1, FOLDER_STRUCTURE, plan 01 phase 1 |
| D-019 | 2026-09-27 | `visualization` package at L5, plotly, DataFrame-only inputs | accepted (library: proposed) | FOLDER_STRUCTURE §1, §3; plan 01 phase 6 |
| D-020 | 2026-09-27 | src architecture: frames between packages, time discipline, config-over-code | accepted | plans/architecture/SRC_DESIGN.md |
| D-021 | 2026-09-27 | Lake outside the repo; root via env > local.yaml > base default | accepted | DATA_LOADING_DESIGN §1, config/base.yaml |
| D-022 | 2026-09-27 | Flow monitoring: built-in RunLog + rich; Prefect as optional adapter | accepted; adapter timing amended by D-064 | DATA_LOADING_DESIGN §3, SRC_DESIGN §2.4 |
| D-023 | 2026-09-27 | plans/ organised by document type; ROADMAP.md is the status board | accepted | plans/INDEX.md, plan skill |
| D-024 | 2026-09-27 | Config = pydantic v2 + PyYAML; DataFrame contracts = core.Schema | accepted by execution | core.config, core.schema |
| D-025 | 2026-09-27 | uv venv outside the repo (UV_PROJECT_ENVIRONMENT=~/.venvs/quant_cn) | accepted by execution | Makefile, FOLDER_STRUCTURE |
| D-026 | 2026-09-27 | Data-loading execution adjustments: cli.py L6, KeyExecutor deferred, TradingCalendar ph4, refetch_recent, dedupe | accepted by execution | DATA_LOADING_DESIGN v1.1, SRC_DESIGN §2.9, plan 01 |
| D-027 | 2026-09-27 | ruff ignores: PLR0913/PLR0917 (injected constructors), D105/D107 (covered by class contract) | accepted by execution | pyproject.toml [tool.ruff.lint] |
| D-028 | 2026-09-27 | `factor` package (L5) split from `statistic`; 8-layer table | accepted | FOLDER_STRUCTURE v1.2, SRC_DESIGN v0.2, CODING_STANDARD §2.1 |
| D-029 | 2026-09-27 | Naming convention for files, folders, docs, config, lake, git; `Plans/` → `plans/` | proposed (rename applied) | plans/standards/NAMING_CONVENTION.md |
| D-030 | 2026-09-27 | Hard size limits: file 600 / class 300 / method 50 lines; verb-first method names | accepted | CODING_STANDARD §2.6, NAMING_CONVENTION §2.1–2.2 |
| D-031 | 2026-09-27 | Code-wide method rename to the verb table (commit 4aa43c0); `sleep`/`wait_` row added | accepted by execution | src/, tests/, CLASS_REGISTRY, NAMING_CONVENTION §2.1 |
| D-032 | 2026-09-27 | `calculation` package (L4, beside `statistic`); first calculator: CBOE-method VIX | accepted | CALCULATION_DESIGN, SRC_DESIGN §2.4b, plan 03 |
| D-033 | 2026-09-27 | `core.docs` holds governance parsers/checkers; `lint_contracts.py` is a thin CLI | accepted by execution | src/quant_cn/core/docs, scripts/lint_contracts.py, plan 02 |
| D-034 | 2026-09-27 | Used by enforced as code references among src classes; non-class callers free-form | accepted by execution | CODING_STANDARD §3, core.docs.ContractChecker |
| D-035 | 2026-09-27 | mypy scope `files = [src/quant_cn, scripts]` | accepted by execution | pyproject.toml [tool.mypy] |
| D-036 | 2026-09-27 | PIT state rule: latest period, then latest restatement, among versions effective by day t | accepted by execution | lake.PitAligner, CODING_STANDARD §2.7 |
| D-037 | 2026-09-27 | Rebuild check = md5 over ordered rows per derived view, stored in meta/manifest/derived_digests.json | accepted by execution | lake.CuratePipeline, make lake-rebuild |
| D-038 | 2026-09-27 | `update_flag` joins the primary key of the three statement datasets | accepted by execution | config/datasets.yaml, DATA_CATALOG |
| D-039 | 2026-09-27 | Chart palette = dataviz reference via ChartTheme; red-up/green-down hollow-up candles; PNG export and PanelChart deferred | accepted by execution | visualization, D-019 |
| D-040 | 2026-09-27 | Notebooks committed without outputs; `make notebook` executes and discards | accepted by execution | Makefile, research_space |
| D-041 | 2026-09-27 | Lake read API surface on LakeQuery + PanelCache; built in plan 04 phase 1 | accepted | SRC_DESIGN §2.2b, plan 04 |
| D-042 | 2026-09-27 | `project` schema rebuilt whole in one transaction; no incremental refresh | accepted by execution | lake.ProjectCatalog |
| D-043 | 2026-09-27 | `make check` includes `project-catalog` (needs lake root); `make lint test` stays lake-free | accepted by execution | Makefile |
| D-044 | 2026-09-27 | Queries open DuckDB read-only; retry after a writer finishes | accepted by execution | cli query, project-query skill |
| D-045 | 2026-09-27 | `risk` package (L5, beside `factor`): Barra/CNE5-style risk model on Shenwan L1 industries | accepted | RISK_MODEL_DESIGN, SRC_DESIGN §2.5b, plan 05 |
| D-046 | 2026-09-27 | VIX prototype notebook defines its own functions (exception to "notebooks import, never define"); promoted in plan 03 ph2–4 | accepted by execution | research_space/notebooks/20260927_vix_calculation.ipynb |
| D-047 | 2026-09-27 | Sweep kind `exchange` (EnumFetcher); `opt_daily` swept by trade_date across all exchanges | accepted by execution | config/datasets.yaml, data_loading |
| D-048 | 2026-09-27 | Adjusted ETF option contracts identified by name suffix "A", not by `per_unit` | accepted by execution | CALCULATION_DESIGN §2, §5b |
| D-049 | 2026-09-27 | `download` refuses `--start` later than configured start for overwrite + range datasets | accepted by execution | cli download, DownloadPipeline |
| D-050 | 2026-09-27 | `DatasetSpec.extend_days`; `trade_cal` fetched +400 days ahead | accepted by execution | config/datasets.yaml, TradingCalendar |
| D-051 | 2026-09-27 | VIX notebook committed WITH outputs (user request); exception to D-040 for this notebook | accepted by execution | research_space/notebooks/20260927_vix_calculation.ipynb |
| D-052 | 2026-09-27 | `ExpiryClock`: calendar (white paper) and trading-session modes, both stored | accepted by execution | calculation.ExpiryClock, VIX_PANEL.quality_flag |
| D-053 | 2026-09-28 | `derived.prices_adj` drops codes absent from `stock_basic` (retired aliases); backtests read prices only through it | accepted by execution | lake.DerivedViews, LakeQuery.read_prices, DATA_CATALOG §3b |
| D-054 | 2026-09-28 | BJ stocks lack stk_limit/daily_basic before BJ listing; universes exclude BJ or start at list_date | accepted by execution | UniverseStep (plan 04), DATA_CATALOG §3b |
| D-055 | 2026-09-28 | Factor library catalogue as the input to plan 04; first six selected | accepted (plan 04 approved) | FACTOR_LIBRARY.md |
| D-056 | 2026-09-28 | ETF pairs trading as a research track; short legs = borrowable ETFs or index futures | accepted | ETF_PAIRS_DESIGN.md, ROADMAP 06b |
| D-057 | 2026-09-28 | GEX dealer-sign default: dealers long calls, short puts; sign is a parameter, OI changes shown | accepted | calculation.GammaExposureCalculator, plan 09 |
| D-058 | 2026-09-28 | Margin vintages FIFO at entry close; liquidation = entry·1.3/(1+1.0), parameters flagged | accepted | calculation.MarginLadderEstimator, plan 09 |
| D-059 | 2026-09-28 | `fut_holding` treated as gross top-20 broker aggregate, not client intent | accepted | calculation.FuturesPositioning, plan 09 |
| D-067 | 2026-09-28 | `RUNNER=prefect` defaults `PREFECT_API_URL` to the local server in the Makefile; `.env` may override | accepted | Makefile, .env.example |
| D-066 | 2026-09-28 | FIFO margin vintages accepted as-is; seeded pre-window balance retires within weeks, ladder driven by 2024+ entries | accepted | calculation.MarginLadderEstimator, plan 09 |
| D-065 | 2026-09-28 | Data sources: AkShare gap-filler, official exchange lists, BaoStock verification, NBS/PBOC release dates; candidates documented | accepted | plans/reference/DATA_SOURCES.md, plan 11 ph10 |
| D-064 | 2026-09-28 | Prefect 3 chosen as the flow tool now; `PrefectRunner` built, `--runner local\|prefect`, optional extra `flows` | accepted (user choice via executor) | pipeline.PrefectRunner, Makefile, .env.example |
| D-063 | 2026-09-28 | Multi-source data loading (`DatasetSpec.source`, FRED client, date-window fetcher, known-on rules); plan 11 consolidates all dataset additions | accepted (user assignment) | DATA_LOADING_DESIGN §3c, plan 11 |
| D-062 | 2026-09-28 | Commodity, macro and sector data: Tushare futures/SGE/yields/FX/macro + FRED second source; continuous futures; gated macro-beta risk descriptors | proposed | MACRO_COMMODITY_DESIGN, plan 10 |
| D-061 | 2026-09-28 | Risk factor sets: v1 six / v2 CNE5 ten with published weights / v3 CNE6 additions; analyst descriptors renormalised when absent | proposed | RISK_FACTOR_LIST, RISK_MODEL_DESIGN §3, plan 05 |
| D-060 | 2026-09-28 | Factor significance: NW t, block bootstrap, HLZ t ≥ 3, BHY FDR, Romano-Wolf, SPA, DSR, CSCV PBO in `statistic`; acceptance bar redefined | accepted (plan 04 approved) | FACTOR_TESTING_DESIGN, FACTOR_LIBRARY §7, plan 04 |

### D-001 Plan first, standard is binding
- Context: new repo; user wants no code before an approved plan and a standard agents must follow.
- Decision: every non-trivial task starts with a plan in `plans/execution/`; `CODING_STANDARD.md` is mandatory.
- Alternatives: ad-hoc coding (rejected: old repo drifted into duplicates and data bugs).
- Consequences: slower first step, cheaper maintenance; `plan` and `decisions` skills exist to keep it light.
- Links: CLAUDE.md

### D-002 Object-oriented only, class registry
- Context: old repo had duplicated functions across scripts.
- Decision: behaviour lives in classes with a Purpose/Contract/Test-cases docstring; every class is registered in `.claude/CLASS_REGISTRY.md`; search before write.
- Alternatives: functional modules (rejected: harder to register and extend consistently).
- Consequences: extension via subclassing base classes; standalone functions need justification.
- Links: CODING_STANDARD §1, §3, §5

### D-003 Tushare Pro via raw HTTP, token in env
- Context: old repo hard-coded tokens and used the SDK inconsistently.
- Decision: one `TushareClient` class over the JSON POST API; token from `TUSHARE_TOKEN` only.
- Alternatives: `tushare` SDK (rejected: extra dependency, same endpoint underneath).
- Consequences: we own paging, retry and rate-limit handling; `.env` is git-ignored.
- Links: TUSHARE_API.md §2, §4

### D-004 Parquet storage partitioned by year
- Context: old repo kept SQLite plus parquet copies.
- Decision: parquet only; daily tables under `data/<dataset>/year=YYYY/`, small tables as single files.
- Alternatives: SQLite (rejected: double storage, slow scans); DuckDB (deferred, can read parquet later).
- Consequences: one `ParquetStore` class; resumability via a `FetchLog`.
- Links: DATA_CATALOG §4

### D-005 Dates as YYYYMMDD strings, ts_code tickers
- Context: type mismatches on joins in the old repo.
- Decision: stored/API dates stay `YYYYMMDD` strings; tickers are Tushare `ts_code`; conversions only via `DateCodec` / `TickerNormalizer`.
- Alternatives: datetime64 everywhere (rejected: constant boundary conversions, join bugs).
- Consequences: research code converts explicitly when plotting or resampling.
- Links: CODING_STANDARD §4

### D-006 PIT alignment on announcement dates, one aligner class
- Context: look-ahead from aligning fundamentals on `end_date`.
- Decision: a single `PitAligner` joins on `f_ann_date`/`ann_date <= t`, next trading day when needed; datasets declare a known-on column.
- Alternatives: per-feature joins (rejected: the bug reappears in every new feature).
- Consequences: dataset classes must expose `known_on`; restatements kept as versions.
- Links: CODING_STANDARD §2.7, DATA_CATALOG §3

### D-007 Folder structure: config / src package / research_space
- Context: user proposed config, a package with pipeline/portfolio/statistic/data_loading/back_testing, and a research space with a main notebook.
- Decision: see `plans/architecture/FOLDER_STRUCTURE.md`; adds a `core` package for base classes and maps packages to layers.
- Alternatives: flat package without `core` (rejected: base classes would live in `data_loading` and create upward imports).
- Consequences: CODING_STANDARD §2.1 updated to these package names once accepted.
- Links: plans/architecture/FOLDER_STRUCTURE.md

### D-008 Plans local-first, Notion mirrors phases
- Context: user wants phases tracked in Notion.
- Decision: markdown plan in `plans/execution/` is the source of truth; the `plan` skill mirrors phases to a Notion database and stores the page URL in the plan header.
- Alternatives: Notion as source of truth (rejected: agents need the plan offline and in version control).
- Consequences: Notion auth must be completed once; until then plans carry `notion: pending`.
- Links: .claude/skills/plan/SKILL.md

### D-009 Local data lake: parquet files + DuckDB catalog
- Context: user asked for a local data lake on parquet with DuckDB managing the data; downloads come from the Tushare API.
- Decision: parquet is the storage of record (`data/lake/raw/<dataset>/year=YYYY/*.parquet`, immutable, hive-partitioned). One DuckDB file (`data/lake/meta/quant_cn.duckdb`) holds the catalog: views over every dataset, the `fetch_log`, dataset metadata (primary key, known-on column, units), and curated views (adjusted prices, deduped fundamentals). All reads go through DuckDB SQL; PIT alignment uses DuckDB `ASOF JOIN`.
- Alternatives: store tables inside the `.duckdb` file (rejected: single-file corruption risk seen before, less portable, harder to back up incrementally); parquet + pandas only (rejected: full scans, joins in memory, no SQL); SQLite landing zone (rejected: D-004 reasoning, slow scans).
- Consequences: classes `ParquetWriter`, `LakeCatalog`, `FetchLog`, `LakeQuery`, `PitAligner` in `data_loading`; the `.duckdb` file is rebuildable from parquet at any time (`LakeCatalog.rebuild()`); pin the `duckdb` version in `pyproject.toml`.
- Links: plans/execution/01_data_lake.md, FOLDER_STRUCTURE.md, DATA_CATALOG §4

### D-010 Docstrings carry a Used by dependency map
- Context: user wants each class/function to state which pipeline classes or functions call it, so impact of a change is visible without searching.
- Decision: mandatory `Used by:` section in every class/public-method docstring listing callers as `package.Class.method` (notebooks by path); mirrored in a `Used by` registry column; updated in the same change that adds or removes a call; verified by the `test-cases` audit against `grep`.
- Alternatives: rely on IDE "find usages" (rejected: agents and reviewers read files, not IDEs); generated call graph only (deferred: can later replace manual upkeep, the audit already compares against grep).
- Consequences: one extra docstring edit per new call; contract changes come with an explicit list of callers to revisit.
- Links: CODING_STANDARD §3, §5, §8; .claude/skills/test-cases/SKILL.md

### D-011 Linter toolchain: ruff, mypy, import-linter, contract linter
- Context: user asked how linting fits the standard; ruff alone cannot enforce the docstring contract, Used by map, registry sync or layer rules.
- Decision: `ruff` (format + lint, D1 docstring presence only), `mypy --strict`, `import-linter` for the layer contract, and a project `scripts/lint_contracts.py` that enforces the docstring sections, TC-ID/test parity, Used by vs grep, registry rows and no-duplicate-class rule. All run via `make lint`, pre-commit, and as a pytest test so CI/agents cannot skip it. Optional Claude Code PostToolUse hook runs ruff on edited files.
- Alternatives: ruff only (rejected: does not know our contract); pylint (rejected: slower, overlaps ruff); flake8 plugins (rejected: ruff covers them).
- Consequences: phase 1 of plan 01 builds the toolchain before any domain code; relaxing a rule requires a decision entry.
- Links: CODING_STANDARD §4.1, plans/execution/01_data_lake.md

### D-012 Lake zones raw/curated/meta/external; `lake` package
- Context: user asked the folder structure to account for the lake; D-009 only fixed "parquet + DuckDB".
- Decision: four zones under `LAKE_ROOT`: `raw/` one file per fetch key (append-only, resumability), `curated/` yearly hive partitions with enforced schemas plus `derived/` (adjusted prices, PIT fundamentals), `meta/` DuckDB catalog + durable `fetch_log.parquet` + manifests, `external/` for legacy files. Storage/query classes move to their own `lake` package (L2) below `data_loading` (L3).
- Alternatives: single zone partitioned by year written directly by fetchers (rejected: resumability then needs row-level dedupe and rewrites of yearly files); lake classes inside `data_loading` (rejected: `statistic`/`back_testing` would import Tushare code to read data).
- Consequences: a `Compactor` step raw -> curated; `make lake-rebuild`; backups target `raw/` + `meta/fetch_log.parquet` only; layer table gains a row.
- Links: FOLDER_STRUCTURE.md §2–3, CODING_STANDARD §2.1, §2.7, plans/execution/01_data_lake.md

### D-013 Registry tracks per-method purpose in detail blocks
- Context: user asked whether the tracking doc lists the purpose of classes *and* their functions; it only listed method names.
- Decision: the registry gets an index (section A) plus one detail block per class (section B) with a method table: Purpose, Input -> Output, Raises, Used by, TC IDs per public method. Abstract base classes list the purpose of each abstract method. `lint_contracts.py` checks code methods against the table.
- Alternatives: generate the method list from docstrings at build time (deferred: can replace manual upkeep later since the linter already compares both); purpose only in code (rejected: user wants a readable map without opening files).
- Consequences: one more block per class to maintain; the `registry` and `new-class` skills updated; the contract linter gains a method-parity check.
- Links: .claude/CLASS_REGISTRY.md, CODING_STANDARD §5, plan 01 phase 1

### D-014 INDEX.md in every folder, forming a tree from root
- Context: user wants each folder to carry an index of its files, and the root an index of everything, so the repo reads as a tree.
- Decision: every non-ignored folder has an `INDEX.md` (purpose, subfolders linking to their index, files with one-line purpose and `Contains`). Root `INDEX.md` is the top. Updated in the same change as any file add/rename/move/delete; `lint_contracts.py --index` enforces parity with disk and with the registry's class names. Maintained with the `index` skill.
- Alternatives: generated tree in one README (rejected: goes stale, no per-file purpose); rely on registry alone (rejected: registry is class-level, not file-level).
- Consequences: one more file per folder; three coherent views (index -> registry -> docstring); `data/` excluded, its map is `meta/manifest/`.
- Links: .claude/skills/index/SKILL.md, CODING_STANDARD §5.1, FOLDER_STRUCTURE §1

### D-015 Plan 01 defaults: lake root, backfill depth, views first, names, notebook
- Context: user approved plan 01 and the folder structure with "approve all"; the open questions take the recommended defaults so work can start. Each is a config value or a one-line change to revisit.
- Decision: (a) lake root defaults to `<repo>/data/lake`, overridable by `QUANT_CN_LAKE_ROOT` / `config/local.yaml`; (b) first backfill 2019-01-01 onward for all plan-01 datasets, plus 2010-01-01 onward for `daily`, `adj_factor`, `index_daily` only; (c) `curated/derived/` starts as DuckDB views, materialised to parquet only when a query is measurably slow; (d) package names stay `back_testing`, `data_loading` as the user wrote them; (e) one `research_space/main.ipynb` acting as index, themed notebooks under `notebooks/`; (f) feature construction is a `pipeline` step calling `statistic` classes; (g) downloads single-threaded first.
- Alternatives: separate disk for the lake now (deferred: config switch, no code change); 2010+ for everything (rejected: `daily_basic`/`moneyflow` etc. not available before 2019 anyway); materialise derived from day one (deferred).
- Consequences: `config/base.yaml` carries (a), (b); FOLDER_STRUCTURE §6 questions closed.
- Links: plans/execution/01_data_lake.md, FOLDER_STRUCTURE.md

### D-016 Model roles: Fable plans + reviews, Opus executes
- Context: user wants a strict split: Fable 5.1 for planning and code review, Opus for execution (writing code, tests, running phases).
- Decision (mechanism verified, see plans/execution/00_model_roles.md): the main session runs Fable and owns the `plan`, `decisions`, `standard-review` and `code-review` work. Execution (`new-class`, `test-cases` scaffolding, plan `execute` mode, `index`/`registry` updates that accompany code) is delegated to a project subagent pinned to Opus. Fable never edits `src/`, `tests/`, `scripts/` or `config/` directly; Opus never edits `plans/` or `DECISIONS.md` except the plan Log table. Fable reviews executor output with `standard-review` / `code-review` only when the user asks; review is not an automatic gate per phase (user, 2026-09-27).
- Alternatives: manual `/model` switching (rejected: not enforceable, easy to forget); one model for everything (rejected by user).
- Consequences: `.claude/agents/executor.md` (`model: opus`), `.claude/settings.json` (`model`, `availableModels`, PreToolUse hook), `.claude/hooks/guard_code_paths.sh` (deny code-path edits without `.claude/run/executor.lock`), `new-class`/`test-cases` skills run with `context: fork`, `agent: executor`. Hooks cannot see the active model (documented input has no model field), so enforcement is by path + run marker.
- Links: CODING_STANDARD §7, .claude/skills/plan/SKILL.md, .claude/skills/standard-review/SKILL.md

### D-017 Project catalog: repo tree + registry + plans queryable in lake DuckDB
- Context: user wants the tree structure maintained in the local data lake so an agent can read the project through DuckDB rather than opening many markdown files.
- Decision: a `project` schema in `meta/quant_cn.duckdb` with tables for folders, files, classes, methods, used_by, contracts, test_cases, decisions, plans, phases, datasets and lint findings, rebuilt from the markdown/YAML/AST sources by `ProjectCatalog` on every `make check`. Markdown remains the source of truth and is never written from SQL. Parsers live in `core.docs` and are shared with the contract linter.
- Alternatives: separate `project.duckdb` (rejected by user 2026-09-27: same file, schema `project`); agents grep markdown only (rejected: no joins, e.g. "which phases touch classes that call LakeQuery").
- Consequences: fourth view in the documentation stack: index -> registry -> docstring -> SQL; a `project-query` skill with recipe queries; `stale` view exposes drift.
- Links: plans/execution/02_project_catalog.md, CODING_STANDARD §5.1, D-013, D-014

### D-018 Packages managed by uv
- Context: user instruction: "the package are managed by the uv".
- Decision: uv owns the environment. `pyproject.toml` + committed `uv.lock` + `.python-version` (3.12); `uv sync --all-extras` builds `.venv`; every tool runs via `uv run`; dependencies enter only through `uv add` / `uv add --dev`; upgrades via `uv lock --upgrade-package` with a decision entry for pinned-sensitive packages (duckdb).
- Alternatives: pip + requirements.txt (rejected: no lock, slower); poetry (rejected: user chose uv, already installed).
- Consequences: Makefile, pre-commit entries and CI use `uv run`; exact versions live in the lock, not in `==` pins.
- Links: CODING_STANDARD §4.1, FOLDER_STRUCTURE §1, plans/execution/01_data_lake.md phase 1

### D-019 `visualization` package at L5, plotly, DataFrame-only inputs
- Context: user asked to add a visualization package in `src/`.
- Decision: `src/quant_cn/visualization/` at layer 5, mutually independent of `back_testing` and `portfolio` (import-linter contract). Charts accept DataFrames / `core` schemas only; producers expose `to_frame()`. All charts subclass `BaseChart` (theme tokens, size, `show()`, `to_html()`, `to_png()`). Library proposed: **plotly** (interactive in notebooks, HTML export, no display server); the `dataviz` skill's palette/form rules apply.
- Alternatives: matplotlib (rejected as primary: static only in notebooks; may be added later behind the same `BaseChart` for print export); a plotting layer inside `statistic`/`back_testing` (rejected: mixes presentation with computation, breaks independence).
- Consequences: eighth package and test folder; `plotly` added via `uv add`; first charts (`BaseChart`, `PriceChart`) built in plan 01 phase 6 for `main.ipynb`.
- Links: FOLDER_STRUCTURE §1, §3, §5; CODING_STANDARD §2.1, §4.1; plans/execution/01_data_lake.md

### D-020 src architecture: frames between packages, time discipline, config-over-code
- Context: user asked for the design of `src`.
- Decision: `plans/architecture/SRC_DESIGN.md` (v1.0; daily-bar backtests, `stock_basic.industry` first, `SignalCombiner` in `factor`). Packages exchange only DataFrames with registered `Schema`s (`core.frames`, long format); one place owns the T-close → T+1-open lag (`ExecutionModel`); universe is a computed panel; factors/constructors/costs are selected by name in YAML via factories; `statistic`/`portfolio`/`back_testing`/`visualization` do no I/O; tests use fakes and a synthetic market. Roadmap plans 03–06.
- Alternatives: rich objects passed between packages (rejected: couples layers, breaks independence contracts, not DuckDB-friendly); a single `strategy` package for portfolio+backtest (rejected: user separated them, independence keeps constructors reusable outside backtests).
- Consequences: `core.frames` and `core.testing.SyntheticMarket` added to plan 01/03 scope; import-linter independence contracts already cover the L5 trio.
- Links: plans/architecture/SRC_DESIGN.md, FOLDER_STRUCTURE §3, CODING_STANDARD §2

### D-021 Lake outside the repo; root via env > local.yaml > base default
- Context: user wants the local machine's config to point the code at a data location so data is never pushed to GitHub.
- Decision: lake root resolved as `QUANT_CN_LAKE_ROOT` env > `config/local.yaml` > `config/base.yaml` default `~/quant_cn_lake`; `.env` and `local.yaml` git-ignored; `Config` refuses a root inside the repo unless explicitly allowed; `.gitignore` covers `data/`, `*.parquet`, `*.duckdb`; `make doctor` verifies; `make lake-backup` rsyncs `raw/` + fetch log.
- Alternatives: `data/` inside the repo relying on `.gitignore` alone (rejected: one bad ignore edit leaks gigabytes); symlink `data/` → external disk (rejected: symlinks in git and on the corrupting volume are fragile).
- Consequences: FOLDER_STRUCTURE drops `data/` from the repo tree; `python-dotenv` added; `Config` gains the guard; this machine's lake: `/Volumes/Treasury/quant_cn_lake`.
- Links: plans/architecture/DATA_LOADING_DESIGN.md §1

### D-022 Flow monitoring: built-in RunLog + rich; Prefect as optional adapter
- Context: user asked for a third-party tool to monitor flows, not Airflow or Dagster.
- Decision: `RunLog` (DuckDB `meta.run_log`) + `rich` progress is the baseline and source of truth; Prefect 3 (local server, open source) is offered through a `PrefectRunner` implementing the same `BaseRunner` interface as `LocalRunner`; steps and fetchers never import Prefect.
- Alternatives: Hamilton (rejected: functional DAG style conflicts with the OOP standard); Kestra/Windmill (rejected: server platforms heavier than a single-machine job); Grafana/Loki (deferred to unattended server runs); Logfire (rejected: data leaves the machine).
- Consequences: `BaseRunner`/`LocalRunner`/`RunLog`/`KeyExecutor` in plan 01 phase 4; `PrefectRunner` deferred to a later plan (user, 2026-09-27).
- Links: plans/architecture/DATA_LOADING_DESIGN.md §3

### D-023 plans/ organised by document type; ROADMAP.md is the status board
- Context: user: "we need to organize the plan as well"; plans/ had standards, designs, plans, the decision log and the handbook at one level.
- Decision: five subfolders by document type with distinct lifecycles: `standards/` (binding rules), `architecture/` (versioned designs), `plans/` (numbered execution plans + `ROADMAP.md`), `decisions/` (append-only log), `reference/` (external facts). `ROADMAP.md` is the only place plan status is summarised; the `plan` skill keeps it current. Designs name the plans that implement them; plans name the design they implement.
- Alternatives: flat folder with prefixes (rejected: no lifecycle distinction); one decision file per ADR now (deferred: single file is readable at 23 entries; split when it passes ~50).
- Consequences: all path references updated (repo, skills, memory); `plans/INDEX.md` explains the types; CLAUDE.md reading order includes the roadmap and the design.
- Links: plans/INDEX.md, plans/execution/ROADMAP.md, .claude/skills/plan/SKILL.md

### D-024 Config = pydantic v2 + PyYAML; DataFrame contracts = core.Schema
- Context: CODING_STANDARD §10 Q1 left schemas/config open; execution (session quant-cn-b7) needed an answer.
- Decision: typed config models in pydantic v2 loaded from YAML via PyYAML; a light `core.Schema` class (columns, dtypes, primary key, invariants) validates DataFrames. Accepted by execution; user can reverse.
- Alternatives: stdlib dataclasses (rejected: no validation, more boilerplate); pandera for DataFrames (deferred: extra dependency, `Schema` covers current needs and can wrap pandera later).
- Consequences: `pydantic`, `pyyaml` in dependencies; `pydantic.mypy` plugin enabled.
- Links: CODING_STANDARD §10, plans/execution/01_data_lake.md phase 1

### D-025 uv venv outside the repo
- Context: `/Volumes/Treasury` is exFAT (no symlinks) and corrupted a `.venv` in the old project.
- Decision: `UV_PROJECT_ENVIRONMENT=~/.venvs/quant_cn` set in the Makefile so `uv sync`/`uv run` use a venv on the system disk; nothing under the repo. Accepted by execution; user can reverse.
- Alternatives: `.venv` in repo (rejected: exFAT + prior corruption); conda (rejected: D-018 chose uv).
- Consequences: `.gitignore` no longer needs `.venv/`; `make setup` documents the location; CI uses the default.
- Links: D-018, FOLDER_STRUCTURE §1

### D-026 Data-loading execution adjustments
- Context: building plan 01 phases 1–4 surfaced five design details; recorded here so the design and the code agree.
- Decision: (1) `src/quant_cn/cli.py` is the L6 composition root and top import-linter layer (`doctor`, `download`, `compact`, `rebuild`, `backup`); (2) `KeyExecutor` deferred, serial key loop inside `BaseFetcher.run` because `core` cannot import `pipeline`; (3) `TradingCalendar` built in phase 4 (needed by `DateSweepFetcher`); (4) `core` gains `BaseRunLog`, `StepReport`, `PermissionDeniedError(DataSourceError)` so the pipeline marks permission failures `blocked`; (5) period datasets re-fetch the most recent `sweep.refetch_recent` quarters; `Compactor` drops duplicate primary keys (keeps last) and logs the count in the manifest. Accepted by execution; user can reverse.
- Alternatives: entry points in `pipeline` (rejected: pipeline would import L5); force-refetch all periods each run (rejected: cost); fail the whole run on duplicates (rejected: Tushare emits occasional duplicates).
- Consequences: DATA_LOADING_DESIGN v1.1, SRC_DESIGN §2.9, FOLDER_STRUCTURE tree/layer table, plan 01 class table updated.
- Links: plans/architecture/DATA_LOADING_DESIGN.md, plans/architecture/SRC_DESIGN.md, plans/execution/01_data_lake.md

### D-027 ruff ignores: PLR0913/PLR0917, D105/D107
- Context: CODING_STANDARD §4.1 makes linter configuration a decision; execution (quant-cn-b7) needed four ignores.
- Decision: ignore `PLR0913`/`PLR0917` (too many arguments) because constructors receive injected dependencies by design (§2.3); ignore `D105`/`D107` (docstrings on magic methods and `__init__`) because the class-level contract documents construction. Every other selected rule stays on. Accepted by execution; user can reverse.
- Alternatives: per-line `# noqa` on each constructor (rejected: noise, and §4.1 requires a reason per noqa); grouping dependencies into a context object (rejected: hides what a class needs).
- Consequences: none beyond `pyproject.toml`; the contract linter, when built, enforces the `__init__` contract through the class docstring instead.
- Links: CODING_STANDARD §2.3, §4.1

### D-028 `factor` package split from `statistic`
- Context: user asked for a factor folder in the plan; factors had been designed inside `statistic`.
- Decision: `src/quant_cn/factor/` at L5 owns `BaseFactor`, the factor library (`factor/library/<name>_factor.py`, one class each), `FactorPreprocessor`, `FactorEvaluator`, `SignalCombiner`, `FactorFactory`. `statistic` (L4) keeps generic, factor-agnostic math (`Winsorizer`, `Standardizer`, `Neutralizer`, `IcCalculator`, `QuantileReturns`, `ReturnStats`, `CrossSectionalRegression`) and never imports `factor`. `pipeline` moves to L6 because `FeaturePipeline` runs factors; `back_testing`/`portfolio`/`visualization` become L7, `cli` L8.
- Alternatives: factors stay in `statistic` (rejected by user); `factor` beside `statistic` at the same layer with an independence contract (rejected: factors need the math, so a real direction exists).
- Consequences: `pyproject.toml` import-linter layers must be updated to the 8-layer list when plan 03 starts (executor task); new `tests/factor/` and `factor/library/` folders with indexes; ROADMAP plan 03 renamed "factors".
- Links: plans/architecture/SRC_DESIGN.md §2.4–2.6, plans/architecture/FOLDER_STRUCTURE.md §3, plans/standards/CODING_STANDARD.md §2.1

### D-029 Naming convention; `Plans/` renamed `plans/`
- Context: user asked for a file naming convention and for `Plans/` to become `plans/`.
- Decision (proposed; the rename is applied): `plans/standards/NAMING_CONVENTION.md`. Folders lowercase `snake_case`; modules named for their primary class; family and library modules defined; governance docs `UPPER_SNAKE.md`; `INDEX.md` everywhere; plans `NN_slug.md`; YAML `snake_case.yaml`; env vars `QUANT_CN_*`; notebooks `YYYYMMDD_topic.ipynb`; lake files hive `key=value.parquet`, curated `year=YYYY/part-n.parquet`; branches `type/slug`. Renames are decisions.
- Alternatives: kebab-case for docs (rejected: Python-side consistency); dated file names for designs (rejected: version lives in the header, status in ROADMAP).
- Consequences: `Plans/` → `plans/` applied 2026-09-27 with all references rewritten; the execution-plans subfolder is now `plans/execution/` (see open question); `lint_contracts.py --names` to enforce file rules.
- Links: plans/standards/NAMING_CONVENTION.md, CODING_STANDARD §4

### D-030 Hard size limits and verb-first method names
- Context: user: "naming convention for function as well" and "set up a restriction for the lines of code, not exceed 600 lines".
- Decision: hard limits enforced by `lint_contracts.py --size`: file ≤ 600 lines (target 400), class ≤ 300, method ≤ 50; counted as physical lines. Method names are verb-first from the prefix table in NAMING_CONVENTION §2.1 (get/find/list/read/fetch/write/build/compute/validate/is/ensure/to/from/mark/run/refresh/register/normalize/plot…), one verb per method, predicates never raise; variable rules in §2.2 (Tushare names verbatim, `start`/`end`, `n_<noun>`, no `df`/`data` beyond a short local scope).
- Alternatives: soft guidance only (rejected: user asked for a restriction); 400-line hard cap (rejected: contract docstrings are long by design, 600 leaves room; 400 stays the target).
- Consequences: `--size` and `--names` added to the deferred linter item in plan 01; `standard-review` checks 8 and 11 updated; existing modules (largest today well under 600) unaffected.
- Links: plans/standards/CODING_STANDARD.md §2.6, plans/standards/NAMING_CONVENTION.md §2.1–2.2

### D-031 Code-wide method rename to the verb table
- Context: NAMING_CONVENTION §2.1 (D-030) introduced verb-first method names after plan 01 phases 1–4 were built; §1 makes a rename a decision.
- Decision: session quant-cn-b7 renamed every non-conforming method in `src/` and `tests/` in commit `4aa43c0` on `feat/data-loading` (`make check` green: ruff, mypy strict 37 files, layers kept, 112 tests). Main renames: `keys→list_keys`, `params→build_params`, `to_fetch→list_due_keys`, RunLog `start_run/event/finish_run→open_run/record_event/close_run`, FetchLog `done_keys/flush/pending/restore→read_done_keys/save/list_pending/rebuild_from_mirror`, `prepare→list_units`, Clock `now/today_str/monotonic→get_now/get_today/get_monotonic`, `Config.dataset/start_for→get_dataset/get_start`, `raw_filename/frame_schema→get_raw_filename/build_schema`, `quarter_ends/weekdays→list_quarter_ends/list_weekdays`, Schema `coerce/empty/dtype→normalize/build_empty/get_dtype`, `HttpTransport.post→fetch_json`, `Compactor.compact→rebuild`, `raw_files→list_raw_files`, `raw_path/curated_path→get_raw_path/get_curated_path`, `db_path→catalog_path`, TradingCalendar `reload/sessions/next/prev→refresh/list_sessions/get_next/get_prev`, `PipelineReport.blocked→list_blocked`, `QuantCnCli.main→run`, `root→lake_root`, `TushareClient(config)→tushare_config`. One name had no verb: `Clock.sleep`; a `sleep`/`wait_` row (Clock and fakes only) is added to §2.1 rather than renaming it.
- Alternatives: grandfather old names (rejected: the table would be advisory from day one); rename `sleep` to `wait_seconds` (rejected: `sleep` is the universal term and already restricted to `Clock`).
- Consequences: registry sections A–D regenerated from code; DATA_LOADING_DESIGN v1.2 uses the new names; `standard-review` check 11 and the `naming` skill enforce the table from here on.
- Links: plans/standards/NAMING_CONVENTION.md §2.1, plans/execution/01_data_lake.md Log

### D-032 `calculation` package; first calculator: CBOE-method VIX
- Context: user asked for a calculation package whose first function computes a VIX from option data by the CBOE method.
- Decision: `src/quant_cn/calculation/` at L4 beside `statistic`, mutually independent: `statistic` = generic math, `calculation` = domain financial computations that know options, forwards and rate curves. Six building-block classes plus `VixCalculator` and `CalculationFactory`; datasets `opt_basic`, `opt_daily`, `shibor` added; `pipeline.CalculationStep` writes `curated/derived/vix/`. Deviations forced by Tushare data (closes instead of bid/ask midpoints, zero-price/volume cut-off, SHIBOR rates, adjusted contracts excluded) are configurable and stamped per row in `quality_flag`. Validation against the exchange's historical iVIX (2015-02 to 2018-02). Plans renumbered: VIX = 03, factors 04, portfolio+backtest 05, events 06, research ops 07 (none of the shifted plans were drafted).
- Alternatives: VIX as a `factor` (rejected: it is a market series, not a cross-sectional score; factors may consume it); inside `statistic` (rejected: statistic must stay domain-agnostic); user-defined functions instead of classes (rejected: CODING_STANDARD §1).
- Consequences: 8-layer table now has two L4 packages with an independence contract; `core.frames.VIX_PANEL`; `DateWindowFetcher` arrives earlier than planned and serves plan 06.
- Links: plans/architecture/CALCULATION_DESIGN.md, plans/execution/03_vix_calculation.md, SRC_DESIGN §2.4b

### D-033 `core.docs` holds the governance parsers and checkers
- Context: the contract linter needs parsers for docstrings, INDEX/registry tables, the naming convention and the code; plan 02's `ProjectCatalog` needs the same parsers.
- Decision: `src/quant_cn/core/docs/` (L1) holds `DocstringParser`, `MarkdownTableReader`, `IndexReader`, `RegistryReader`, `ConventionReader`, `CodeScanner`, `RepoFiles` and the checkers `ContractChecker`, `IndexChecker`, `SizeChecker`, `NameChecker`, run by `ContractLinter`; `scripts/lint_contracts.py` is a thin CLI. Accepted by execution (7bd9b36).
- Alternatives: parsers in `scripts/` (rejected: `src` cannot import scripts, so plan 02 could not reuse them).
- Consequences: plan 02 phase 1 ("parsers in core.docs") is effectively delivered; `ProjectCatalog` consumes these classes and the lint findings table.
- Links: plans/execution/02_project_catalog.md, CODING_STANDARD §4.1

### D-034 Used by enforced as code references
- Context: CODING_STANDARD §3 requires a `Used by` list; the linter needs a checkable definition.
- Decision: for `src` classes, `Used by` must list exactly the src classes whose code references the class (names, annotations, bases, calls; docstrings excluded); listed src classes that do not reference it are flagged stale. Non-class callers (Makefile targets, notebooks, scripts) may be listed freely. Accepted by execution.
- Alternatives: manual lists with grep hints only (rejected: drifts immediately).
- Consequences: Used by sections in `src` were rewritten to actual references in 7bd9b36; `ContractChecker` is the arbiter.
- Links: CODING_STANDARD §3, D-010

### D-035 mypy scope includes scripts
- Context: linter CLI lives in `scripts/`; `packages = ["quant_cn"]` left it unchecked.
- Decision: `[tool.mypy] files = ["src/quant_cn", "scripts"]`, strict for both. Accepted by execution.
- Alternatives: leave scripts unchecked (rejected: the linter is code like any other).
- Consequences: 53 files under mypy strict; `scripts/` must satisfy the same standard.
- Links: pyproject.toml, CODING_STANDARD §4.1

### D-036 PIT state rule
- Context: multiple versions of fundamentals (periods, restatements) can be effective on the same day; the aligner needs one deterministic choice.
- Decision: among versions effective by day t (effective = first trading session after `known_on`), the visible value is argmax(`end_date`, `effective_date`): the latest period, then its latest restatement. A later restatement of an older period never replaces a newer period. Ties on effective day order by `known_on`, `ann_date`, `update_flag`, all descending (corrected version wins). Accepted by execution (97a2f7e); tests TC-PA-001..005.
- Alternatives: latest announcement wins regardless of period (rejected: an old-period restatement would overwrite the newest quarter); first version only (rejected: ignores corrections).
- Consequences: `PitAligner` is the only implementation (§2.7); `fundamentals_states` view materialises the rule.
- Links: CODING_STANDARD §2.7, D-006, plans/architecture/DATA_LOADING_DESIGN.md

### D-037 Byte-identical rebuild check
- Context: plan 01 phase 5 requires `make lake-rebuild` to reproduce derived data byte-identically.
- Decision: md5 over each derived view's rows, ordered by row text; digests stored in `meta/manifest/derived_digests.json`; `curate` prints unchanged / CHANGED / new per view. Accepted by execution.
- Alternatives: file-level checksums (rejected: parquet encoding is not deterministic across writers); row-count only (rejected: too weak).
- Consequences: any schema or rule change shows as CHANGED and must be explained in the plan log.
- Links: plans/execution/01_data_lake.md phase 5

### D-038 `update_flag` in the statement primary keys
- Context: `income_vip`, `balancesheet_vip`, `cashflow_vip` return an original and a corrected row per filing; without `update_flag` the compactor treated them as duplicates and kept an arbitrary one (4 of 4,075 dropped keys differed).
- Decision: `update_flag` added to fields, text fields and primary key of the three statements; 2026Q2 refetched with `--force`; every backfill requests it from day one. Accepted by execution.
- Alternatives: keep only `update_flag = 1` at fetch time (rejected: loses the originally published number, which is what was knowable before the correction).
- Consequences: curated statement rows increase slightly; `PitAligner` prefers the corrected version when both share an effective day (D-036).
- Links: config/datasets.yaml, plans/reference/fresh_start/DATA_CATALOG.md §3 (restatements)

### D-039 Chart palette and candle convention; PNG export deferred
- Context: D-019 asked for `BaseChart` with `to_png()` and a `PanelChart`; building phase 6 showed PNG export needs kaleido plus a Chrome install.
- Decision: `ChartTheme` carries the dataviz reference palette as tokens; candles are red up / green down (A-share convention) with hollow up candles as the secondary encoding (light-mode CVD ΔE 7.2, validator passes both modes). `BaseChart` exposes `render`, `to_html`, `write_html`; `to_png` and `PanelChart` are deferred until a report needs them. Accepted by execution (7388daf); amends D-019.
- Alternatives: install kaleido + Chrome now (rejected: heavy dependency for no current consumer); Western green-up convention (rejected: A-share readers expect red up).
- Consequences: `ReportBuilder` (plan 05) decides on PNG; visualization tests cover HTML output only.
- Links: D-019, plans/architecture/SRC_DESIGN.md §2.9

### D-040 Notebooks committed without outputs
- Context: plotly figures serialise as large JSON in notebook outputs.
- Decision: `make notebook` executes `research_space/main.ipynb` with nbconvert as the done-criterion check and discards outputs; notebooks are committed clean. Accepted by execution.
- Alternatives: nbstripout pre-commit hook (deferred: same effect; add if outputs ever get committed by mistake); committing outputs (rejected: repo bloat).
- Consequences: reviewers run `make notebook` to see figures; `research_space/outputs/` stays git-ignored for exported HTML.
- Links: Makefile, .gitignore

### D-041 Lake read API surface
- Context: user asked whether a loading engine for the local lake exists; `LakeQuery` had `sql`, `has_view`, `read_prices` only.
- Decision: complete `LakeQuery` as the single read API: `read_panel`, `read_prices(dense=)`, `read_fundamentals_pit`, `read_reference`, `read_universe`, `register_frame`, `list_views`, with an injectable `PanelCache`; every output schema-validated. Built as plan 04 phase 1 because factors and the universe step are the first consumers; `dense=True` closes the phase-5 deferral.
- Alternatives: separate `DataLoader` facade above the lake (rejected: two read paths); notebooks writing SQL (rejected as the only path: repetitive and unvalidated).
- Consequences: SRC_DESIGN §2.2b; ROADMAP plan 04 phase 1; `PanelCache` registered in lake.
- Links: plans/architecture/SRC_DESIGN.md §2.2b, plans/execution/ROADMAP.md

### D-042 `project` schema rebuilt whole
- Context: plan 02 phase 2 named `rebuild()` and `refresh(paths)`; a full rebuild takes about one second on this tree.
- Decision: `ProjectCatalog.rebuild()` drops schema `project` (CASCADE) and recreates all 12 tables and 4 views in one transaction; no incremental mode. Accepted by execution (855585f).
- Alternatives: per-path incremental refresh (rejected for now: complexity for no measurable gain at this size; revisit if rebuild exceeds ~10 s).
- Consequences: plan 02 phase 2 deliverable narrowed; the `stale` view still detects drift between runs.
- Links: plans/execution/02_project_catalog.md

### D-043 `make check` includes `project-catalog`
- Context: keeping the catalog fresh on every check requires the lake DuckDB file, hence a lake root.
- Decision: `make check` = lint + test + project-catalog and therefore needs `.env`/lake root; `make lint test` remains lake-free for clones without data. Accepted by execution.
- Alternatives: catalog in a repo-local DuckDB (rejected: D-017 chose the lake file so one query joins data and project); skip catalog in check (rejected: staleness would go unnoticed).
- Consequences: CI without a lake runs `make lint test`; `make doctor` explains a missing root.
- Links: Makefile, D-017

### D-044 Read-only query access
- Context: DuckDB allows one writer; agents and notebooks query while pipelines may be writing.
- Decision: `quant_cn query` / `make query` open the catalog read-only; DuckDB refuses a read-only open while a writer holds the file, so callers retry after downloads/curate finish. Accepted by execution.
- Alternatives: a query server process (rejected: overkill for a single machine).
- Consequences: project-query skill documents the retry; pipelines close connections promptly.
- Links: .claude/skills/project-query/SKILL.md

### D-045 `risk` package: Barra-style multi-factor risk model
- Context: user asked for a Barra-style risk management model.
- Decision: `src/quant_cn/risk/` at L5 beside `factor`, mutually independent (frames only). CNE5-style specification adapted to A-shares: country + 31 Shenwan L1 industry factors + CNE5 style factors (six in v1, ten in a second pass), constrained WLS with √cap weights, EWMA + Newey-West covariance with eigenfactor and volatility-regime adjustments, EWMA specific risk with structural fallback and Bayesian shrinkage, bias-statistic validation. Datasets `index_classify`, `index_member_all`, `index_weight` added. Six frames in `core.frames`. Plans renumbered: risk 05, portfolio+backtest 06, events 07, research ops 08.
- Alternatives: statistical (PCA) risk model (rejected for v1: less interpretable, no industry/style attribution; can be added as another `BaseRiskModel`); risk inside `portfolio` (rejected: risk is consumed by both portfolio and backtesting, and must not import either); vendor model (none available).
- Consequences: `portfolio` optimiser (plan 06) consumes `FACTOR_COV`/`SPECIFIC_RISK`; `factor.Neutralizer` may consume `RISK_EXPOSURE`; import-linter gains `factor`/`risk` independence.
- Links: plans/architecture/RISK_MODEL_DESIGN.md, plans/execution/05_risk_model.md, SRC_DESIGN §2.5b

### D-046 VIX prototype in a research notebook
- Context: user asked quant-cn-b7 for the VIX calculation in a notebook before the package existed, then for all underlyings and the latest CSI 300 values.
- Decision: `research_space/notebooks/20260927_vix_calculation.ipynb` defines its own calculation functions, an explicit exception to SRC_DESIGN §4 ("notebooks import, never define"). Plan 03 phases 2–4 promote them into `calculation` classes with tests and the notebook is then rewritten to import. Accepted by execution (4add2d4).
- Alternatives: build the package first (rejected by the user's sequencing); leave the prototype as the product (rejected: violates the standard permanently).
- Consequences: plan 03 phase 1 partly delivered; package phases must reproduce the notebook's numbers (468 underlying-days, latest IO 17.28 / 159919 17.05 / 510300 16.96) as a regression check.
- Links: plans/execution/03_vix_calculation.md, CALCULATION_DESIGN §5b

### D-047 Sweep kind `exchange`; `opt_daily` across all exchanges
- Context: `opt_basic` is fetched per exchange; `opt_daily` per trade_date returns all exchanges (~24k rows/day incl. commodities) and a composite (date, exchange) sweep key is not supported.
- Decision: new `sweep.kind: exchange` handled by `EnumFetcher` (SSE, SZSE, CFFEX); `opt_daily` swept by `trade_date` without exchange filter; the chain builder filters by underlying. Accepted by execution.
- Alternatives: composite sweep keys (deferred: more fetcher complexity, ~5× more calls); per-exchange daily sweeps (rejected: same data, more calls).
- Consequences: `opt_daily` raw is ~1M rows per 39 days; curated partitioning by year unchanged; commodity options are available for free.
- Links: config/datasets.yaml, DATA_LOADING_DESIGN §2.2

### D-048 Adjusted contracts by name suffix
- Context: dividend-adjusted ETF option contracts must be excluded from the strip (CALCULATION_DESIGN §2); `per_unit != 10000` misclassifies CFFEX index options (multiplier 100).
- Decision: an adjusted contract is one whose `opt_basic.name` ends in "A". Accepted by execution.
- Alternatives: `per_unit` rule (rejected: wrong for CFFEX); exercise-price grid detection (deferred: heuristic).
- Consequences: `OptionChainBuilder` implements the rule with an `include_adjusted` flag.
- Links: CALCULATION_DESIGN §2, §5b

### D-049 `download` refuses a narrower `--start` on overwrite datasets
- Context: `index_daily --start 20260101` overwrote the full raw history because reference datasets refresh by overwrite.
- Decision: for overwrite + range datasets, `download` refuses a `--start` later than the configured start unless `--force`. Accepted by execution (dda0409).
- Alternatives: append semantics for reference datasets (rejected: they are whole-history snapshots by design).
- Consequences: partial refreshes of reference data are impossible by accident.
- Links: plans/execution/03_vix_calculation.md Log (incident)

### D-050 `trade_cal` fetched 400 days ahead
- Context: expiry maths (days to expiry, next trading session after an announcement) needs sessions beyond today.
- Decision: `DatasetSpec.extend_days` (per dataset); `trade_cal` uses +400 days so `TradingCalendar` knows future sessions. Accepted by execution.
- Alternatives: derive future sessions from weekday rules (rejected: Chinese holidays are irregular).
- Consequences: calendar refreshes must run at least yearly; `make doctor` could warn when the horizon is < 90 days (follow-up).
- Links: config/datasets.yaml, lake.TradingCalendar

### D-051 VIX notebook committed with outputs
- Context: user asked that the notebook "should have the results as well".
- Decision: `20260927_vix_calculation.ipynb` is committed with executed outputs, overriding D-040 for this notebook only; all other notebooks stay output-free. Accepted by execution.
- Alternatives: export results to `outputs/` HTML (rejected by the user's request); strip and re-run on demand (that remains the default elsewhere).
- Consequences: repo grows by the plotly JSON of this notebook; re-executions must be committed deliberately.
- Links: D-040

### D-052 `ExpiryClock` with calendar and trading-session modes
- Context: the CSI 300 VIX fell on 20260917 when the near term rolled onto an expiry spanning the Mid-Autumn and National Day holidays; the white-paper calendar clock counts those days as time, the market does not.
- Decision: `ExpiryClock` implements `calendar` (white paper, what iVIX published) and `trading` (21 sessions / 244-session year); `VixCalculator` computes and stores both, `quality_flag` records the clock; the headline default is chosen in plan 03 phase 5 against iVIX. Accepted by execution.
- Alternatives: calendar only (rejected: holiday artifacts mislead users); trading only (rejected: breaks comparability with published indices).
- Consequences: `VIX_PANEL` carries both series; notebooks show both.
- Links: CALCULATION_DESIGN §5b, plans/execution/03_vix_calculation.md

### D-053 Retired code aliases dropped from adjusted prices
- Context: Tushare double-lists code-changed stocks (000043→001914, 000022→001872, 300114→302132), so the same company appeared twice on 7,637 bars.
- Decision: `derived.prices_adj` (and therefore `LakeQuery.read_prices`) keeps only codes present in `stock_basic`; `curated.daily` is left complete. Backtests and factors read prices only through `prices_adj`/`read_prices`, never `curated.daily`. An old→new alias map joins plan 04 phase 1 so the retired code's history and limits can be attached to the surviving code. Accepted by execution (7970a13, TC-DV-004).
- Alternatives: dedupe on (date, close) fingerprints (rejected: fragile); drop the old code from raw (rejected: raw is immutable).
- Consequences: three companies lose pre-change history in `prices_adj` until the alias map exists; documented in DATA_CATALOG §3b.
- Links: plans/reference/fresh_start/DATA_CATALOG.md §3b, plan 04

### D-054 Beijing-exchange history before BJ listing
- Context: 58k `.BJ` bars from the NEEQ era have no `stk_limit` or `daily_basic`.
- Decision: backtest universes exclude `.BJ`, or start each BJ stock at its BJ `list_date`; the `UniverseStep` (plan 04) implements the choice as config (`universe.exchanges`, `universe.bj_from_list_date`). Accepted by execution.
- Alternatives: back-fill limits by rule (rejected: BJ limit rules differ and changed over time).
- Consequences: default universe excludes BJ (consistent with RISK_MODEL_DESIGN §7 recommendation).
- Links: DATA_CATALOG §3b, plans/execution/05_risk_model.md

### D-055 Factor library catalogue
- Context: user wants a construction list of fundamental, momentum, quality and value factors before plan 04 is drafted.
- Decision: `plans/architecture/FACTOR_LIBRARY.md` catalogues ~55 candidate factors in six families with construction, Tushare data mapping, PIT notes and an evaluation protocol; the acceptance bar for `factor/library/` is |ICIR| ≥ 0.3 at 20 sessions with stable sign across sub-periods. First six for plan 04: EP or BP, ROE TTM, net profit TTM yoy, 12-1 momentum, 1-month reversal, turnover. Two statement fields added to `datasets.yaml` before the next refetch. Analyst revision family (§3b) depends on `report_rc` (broker earnings forecasts; permission tier to verify) and lands with plan 07; it also supplies the forward earnings yield the CNE5 model lacks.
- Alternatives: build factors ad hoc as ideas come (rejected: no shared evaluation bar, duplicates).
- Consequences: plan 04 phases 4–5 take their scope from §8; the catalogue is a living document updated with each accepted or rejected factor.
- Links: plans/architecture/FACTOR_LIBRARY.md, plan 04 (to draft)

### D-056 ETF pairs trading as a research track
- Context: user wants to find long/short pair trades among ETFs.
- Decision: research-first per `ETF_PAIRS_DESIGN.md`; short legs restricted to margin-eligible ETFs, T+0 ETF duplicates and CFFEX index futures; pair families and a cointegration/OU/z-score method defined; new datasets (`fund_basic`, `fund_daily` by trade_date, `fund_nav`, `fund_share`, margin targets, `fut_basic`, `fut_daily`); promotion to `portfolio.PairsConstructor` and a short-leg/futures `CostModel` only if out-of-sample Sharpe ≥ 1.0 after costs on ≥ 3 pairs in 2 families. Roadmap row 06b.
- Alternatives: single-stock pairs (rejected: shorting single A-shares is impractical); build strategy classes first (rejected: plan-first, and the bar may not be met).
- Consequences: `fund_daily` sweep changes from an ETF enum to `trade_date`; futures datasets arrive earlier than otherwise planned.
- Links: plans/architecture/ETF_PAIRS_DESIGN.md, plans/execution/ROADMAP.md

### D-057 GEX dealer-sign default
- Context: dealer gamma exposure needs a sign convention for who holds which side; A-share option chains have no dealer-position data.
- Decision: default dealers long calls and short puts (customers buy puts, sell calls); the sign is a constructor parameter; signed and unsigned GEX are both stored and open-interest changes are shown next to levels so the assumption can be judged. Confirmed by the user in this session on 2026-09-28.
- Alternatives: infer sign per strike from OI vs price changes (deferred to after the event study); unsigned only (rejected: no flip level).
- Consequences: gamma-flip level depends on the default; validation phase tests it.
- Links: POSITIONING_FLOWS_DESIGN §1, plan 09

### D-058 Margin vintages FIFO; liquidation parameters
- Context: `margin_detail` gives balances and flows per stock, not per account; liquidation prices need an entry price and a maintenance rule.
- Decision: daily net new financing opens a vintage at that day's close; repayments retire vintages first-in-first-out; liquidation price = entry × maintenance 1.3 / (1 + initial margin 1.0); both parameters in config and flagged as assumptions, with a sensitivity table in the notebook. Confirmed by the user in this session on 2026-09-28.
- Alternatives: LIFO or pro-rata retirement (rejected: FIFO matches typical forced-close ordering by age); per-broker parameter mixture (deferred to sensitivity).
- Consequences: aggregate ladder is the deliverable; per-stock liquidation prices are indicative only.
- Links: POSITIONING_FLOWS_DESIGN §3, plan 09

### D-059 `fut_holding` as gross broker aggregate
- Context: CFFEX publishes top-20 member firms' long/short volume and OI; these mix client and proprietary books.
- Decision: treat as a gross aggregate: net = Σ long OI − Σ short OI over listed brokers, with a top-5 concentration column; never described as "client positioning". Confirmed by the user in this session on 2026-09-28.
- Alternatives: attribute intent by broker type (rejected: no data).
- Consequences: regime classification uses total OI and price; the broker net is a secondary indicator.
- Links: POSITIONING_FLOWS_DESIGN §2, plan 09

### D-060 Factor significance testing in `statistic`
- Context: user: "statistic need the IC/IR ... newest significant test"; the evaluation protocol reported IC/ICIR without inference, and a 55-factor catalogue invites false discoveries.
- Decision: `statistic` gains `IcCalculator`, `HacVariance`, `BlockBootstrap`, `IcSignificance` (Newey-West t on mean IC, block-bootstrap CIs, Pesaran-Timmermann, sub-period/regime consistency, Bai-Perron break, decay), `MultipleTestingAdjuster` (Holm, Benjamini-Hochberg-Yekutieli, Romano-Wolf; Harvey-Liu-Zhu t ≥ 3 hurdle), `DataSnoopingTest` (White Reality Check, Hansen SPA), `DeflatedSharpe` (PSR/DSR, minimum backtest length), `BacktestOverfitting` (CSCV PBO), `SharpeRatioTest` (Ledoit-Wolf), `TrialLog`. Acceptance into `factor/library/` = FACTOR_TESTING_DESIGN §6. Built in plan 04 phase 2 (core set) and later phases (backtest-level tests).
- Alternatives: ICIR threshold only (rejected: ignores autocorrelation and the search); vendor library (none covers HLZ/DSR/CSCV together; formulas are short and testable).
- Consequences: every factor report carries t, p, CI and adjusted p; a `TrialLog` per campaign is mandatory so DSR can be computed honestly; tests-for-the-tests (§7) are part of the definition of done.
- Links: plans/architecture/FACTOR_TESTING_DESIGN.md, FACTOR_LIBRARY §7, SRC_DESIGN §2.4

### D-061 Risk factor sets from the public Barra models
- Context: user asked for the list of Barra risk factors, preferring the China model, else the public US one.
- Decision (proposed): `RISK_FACTOR_LIST.md` compiles CNE5 (10 factors, 21 descriptors, published weights), CNE6 (9 groups, ~20 factors, ~46 descriptors, weights not public) and USE4 (12 factors) with the Tushare mapping. Plan 05 builds v1 (Size, Beta, Momentum, Residual Volatility, Book-to-Price, Liquidity), then v2 = CNE5's ten with published weights, then v3 = CNE6 additions in a follow-up plan. Analyst-based descriptors (EPFWD, EGRLF, EGRSF, sentiment) depend on `report_rc`; when absent the remaining descriptor weights are renormalised and the factor flagged `no_analyst`. CNE6 descriptor weights start equal and are estimated by the validator.
- Alternatives: invent a custom factor set (rejected: comparability with published models and with broker replications is worth more); Fama-French style factors as the risk model (rejected: too few factors for attribution; kept as sanity checks).
- Consequences: RISK_MODEL_DESIGN §3 replaced by a pointer with corrected CNE5 weights; six balance-sheet/income fields added to `datasets.yaml` before the next refetch; plan 05 phase 6 = v2.
- Links: plans/architecture/RISK_FACTOR_LIST.md, RISK_MODEL_DESIGN §3, plans/execution/05_risk_model.md

### D-062 Commodity, macro and sector data
- Context: user asked to add oil, gold and other commodity prices, and sectors.
- Decision (proposed): plan 10 adds domestic commodity futures (INE, SHFE, DCE, CZCE) with `fut_mapping` for main contracts, SGE gold, China yields and FX, monthly macro with a release-date PIT rule, and Shenwan/CSI sector indices; international benchmarks (Brent, WTI, LBMA gold, DGS10, DXY) come from FRED through a second `BaseApiClient` (`DatasetSpec.source`), AkShare only for series FRED lacks. `calculation` gains `ContinuousFutures` (ratio back-adjusted, roll log), `TermStructure`, `MacroSeries`, `SectorIndexPanel`. Uses: gated macro-beta risk descriptors (RISK_FACTOR_LIST §4b), commodity-spillover and sector-momentum factors, regime variables, commodity ETF/futures pairs. Start with a small product set (oil, gold, copper, iron ore, 10y, USDCNY) and extend on demand.
- Alternatives: Tushare only (rejected: no international benchmarks); AkShare only (rejected: scraping fragility, keep as fallback); embed commodity exposure only via industries (rejected: misses within-industry differences and the regime uses).
- Consequences: `data_loading` becomes multi-source; four new frames; monthly-macro PIT approximated by a documented lag rule; FRED key in `.env`.
- Links: plans/architecture/MACRO_COMMODITY_DESIGN.md, plans/execution/10_macro_commodity_sectors.md, FACTOR_LIBRARY §5b, RISK_FACTOR_LIST §4b

### D-063 Multi-source data loading and the consolidated lake expansion
- Context: the research asks (factors, risk model, ETF pairs, positioning, commodities/macro/sectors, analysts) each added datasets to their own plans; the user asked for the data-loading lake to be designed for all of them and assigned to the executor.
- Decision: DATA_LOADING_DESIGN §3c: `DatasetSpec.source` selects the client (`tushare`, `fred`, optional `akshare`); `FredClient` for international benchmarks; `DateWindowFetcher`; `values_from_dataset`; `known_on_rule` (`next_session`) and `release_lag_days` for series without announce dates. Plan 11 consolidates every dataset addition into nine ordered phases with a one-call permission check per new endpoint, reconciliations, PIT tests, byte-identical rebuilds and DATA_CATALOG rows; the data phases of plans 05 and 10 become verification-only. Accepted by user instruction.
- Alternatives: keep dataset additions inside each research plan (rejected: repeated lake-busy windows and no single view of coverage); single-source Tushare (rejected: no international benchmarks).
- Consequences: lake grows ~3–4 GB raw; `.env` gains `FRED_API_KEY`; two long download phases (futures, analysts) to run overnight; `fund_daily` raw key changes.
- Links: plans/architecture/DATA_LOADING_DESIGN.md §3c, plans/execution/11_lake_expansion.md

### D-064 Prefect 3 as the flow tool, built now
- Context: D-022 chose RunLog + rich as the baseline and Prefect as an optional adapter, deferred. The user picked Prefect 3 when asked by quant-cn-b7 (AskUserQuestion) during plan 09.
- Decision: `pipeline.PrefectRunner` implements `BaseRunner`; flow "quant_cn <kind>" named by the RunLog run id, each step a task with a progress artifact over its keys, permission-blocked steps non-fatal; `RunLog` stays the source of truth. `--runner local|prefect` on `download` and `curate`; `make prefect-server` (UI 127.0.0.1:4200), `make download RUNNER=prefect`; Prefect is the optional extra `flows` (`uv sync --all-extras`); `PREFECT_API_URL` in `.env.example`; tests TC-PFR-001..003 run real flows in Prefect's harness. Steps and fetchers still never import Prefect. Amends the deferral in D-022.
- Alternatives: keep deferring (rejected by the user's choice); Prefect as a hard dependency (rejected: `make lint test` stays lake- and Prefect-free).
- Consequences: roadmap plan 08's `PrefectRunner` item is delivered early; DATA_LOADING_DESIGN §3 monitoring table updated.
- Links: D-022, plans/architecture/DATA_LOADING_DESIGN.md §3, plans/execution/09_positioning_flows.md

### D-065 Additional data sources
- Context: user asked whether other data sources exist and said "add them".
- Decision: `plans/reference/DATA_SOURCES.md` records every source with role and caveats. Plan 11 gains phase 10: `AkShareClient` as gap-filler (LME if needed, official macro release calendars, exchange member position files), SSE/SZSE margin-target lists loaded with provenance (closes the ETF pairs short-leg eligibility question), `BaoStockClient` as a verification-only source feeding a nightly price cross-check view, NBS/PBOC release dates replacing lag rules. Paid options (Wind/iFinD/Choice, Go-Goal, JoinQuant/RiceQuant, CSMAR/CNRDS, Hibor) documented as candidates; the analyst-data choice waits for the `report_rc` tier check.
- Alternatives: integrate a paid terminal now (rejected: cost before need); rely on Tushare alone (rejected: release dates, lending lists and cross-checks are cheap and valuable).
- Consequences: verification sources never overwrite primaries (`raw/<source>_<dataset>/` + quality view); licence terms recorded before integration.
- Links: plans/reference/DATA_SOURCES.md, plans/execution/11_lake_expansion.md phase 10, ETF_PAIRS_DESIGN §7

### D-066 FIFO margin vintages accepted as-is
- Context: with FIFO retirement (D-058), the balance existing before the `margin_detail` window (2024-01) is retired within weeks, so by 2026-09 every open vintage has an entry price from 2024-01 onward; results do not depend on an unknown pre-window cost basis.
- Decision: keep FIFO and the (1.3, 1.0) parameters as the default; the notebook keeps the parameter sensitivity table; extending `margin_detail` to 2019 is optional and only for a longer event-study window. Accepted (user can reverse).
- Alternatives: pro-rata retirement (rejected: keeps a stale seeded basis alive indefinitely).
- Consequences: none for code; documented in plan 09 log.
- Links: D-058, plans/execution/09_positioning_flows.md

### D-067 Prefect API URL default
- Context: without `PREFECT_API_URL` the CLI starts a throwaway Prefect server and the run does not appear in the UI.
- Decision: when `RUNNER=prefect`, the Makefile exports `PREFECT_API_URL=http://127.0.0.1:4200/api` unless `.env` sets it; `.env.example` keeps the line commented as an override; `make doctor` warns if `RUNNER=prefect` and the server is unreachable. Accepted.
- Alternatives: require users to copy the line into `.env` (rejected: one more manual step to forget).
- Consequences: `make download RUNNER=prefect` always lands in the local UI when `make prefect-server` is running.
- Links: D-064, Makefile

### D-068 Sector and index-composition datasets (plan 11 phase 2)
- Context: tier checks on 2026-09-28 (one call each): `index_classify`, `index_member_all`, `index_weight`, `sw_daily` all accessible. `index_member_all` returns current members only by default; historical members (with `out_date`) need `is_new=N`. `index_weight` pages correctly over a 2010–2026 range (CSI 300: 60,000 rows, 300 per month-end, 200 months).
- Decision: new enum sweep kinds `index_code` and `is_new` (kind name = API parameter, as `exchange`/`list_status`). `index_classify` one call `src=SW2021`; `index_member_all` swept by `is_new` Y/N, key `(ts_code, l3_code, in_date)`, known-on `in_date`; `index_weight` per index (300/500/1000/50) over the whole range from 2010 with `refresh: overwrite` (EnumFetcher skips done keys, so append would never pick up new months); `sw_daily` swept by `trade_date` from 2019. `sw_daily` is fetched directly, so the member-computed fallback is not built; the 10 bp/day reconciliation is still run. Accepted.
- PIT caveat: Shenwan 2021 was published in 2021-07; earlier `in_date`s are vendor reconstructions. Industry history before 2021-07 is usable for grouping and neutralisation but is not what investors saw then; factor tests before 2021-07 must say so.
- Alternatives: `index_weight` by monthly date window (needs a second key dimension per index; rejected for now); `index_member_all` swept by `l1_code` (31 × 2 calls instead of 2).
- Consequences: each download refetches ~150k `index_weight` rows (~4 paged calls per index); `sw_daily` adds ~440 rows per session.
- Links: D-047, D-049, D-063, plan 11 phase 2

### D-069 `index_weight` by index × yearly window (supersedes the index_weight part of D-068)
- Status: accepted by execution (2026-09-28).
- Context: the first live run failed on CSI 1000: Tushare refuses `offset > 100000` ("offset不能大于100000"), and 000852.SH has ~150k weight rows since 2014. One range call per index only works below 100k rows (CSI 300: 60k).
- Decision: `sweep.value_param` (date_window only) adds a second key dimension: `DateWindowFetcher` fetches each window once per value, keys `<window>_<value>` (e.g. `2025_000852.SH`), window-major. `index_weight` uses yearly windows × `weight_indices` (≤ 12k rows per call), `refresh: append` with `refetch_recent: 4` (current year of each index). The `index_code` enum kind from D-068 is dropped (unused); `is_new` stays. Raw files of the failed run (`index_code=000300.SH`, `=000905.SH`) moved out of the lake before the rerun; `make lake-rebuild` drops their fetch-log rows.
- Alternatives: monthly windows (4× the calls, no benefit); keep overwrite (68 calls every run).
- Consequences: 68 keys for the backfill, 4 per later run. The same mechanism serves `fund_nav` per ETF (phase 3).
- Links: D-063, D-068, plan 11 phase 2

### D-070 `shibor` by yearly window (row cap without paging)
- Status: accepted by execution (2026-09-28).
- Context: `shibor` was one range call from 2015 (`kind: none`, `range_params`). The endpoint returns at most 2,000 rows and does not page, so the lake held 2018-08-21 → 2026-09-28 only (exactly 2,000 rows), silently missing 2015–2018. Found in the phase 2 coverage check.
- Decision: `shibor` swept by `date_window` (year), `refresh: append`, `refetch_recent: 1`. The old `raw/shibor/all.parquet` moved out of the lake; refetched 12 windows, 2,907 rows from 2015-01-04. Rule for new datasets: any single range call whose row count is a round number (2,000 / 5,000 / 6,000 …) is treated as truncated until proven otherwise; the coverage notebook (phase 9) checks first date against `start` for every dataset.
- Alternatives: none needed; date_window already exists (D-063).
- Consequences: VIX rates before 2018-08 now available; `derived` digests unaffected (shibor is not in derived views).
- Links: D-063, D-069, plan 03, plan 11 phase 9

### D-071 Industry grouping before the SW2021 start
- Context: Shenwan 2021 membership begins 2021-07 for many stocks; 70 of 3,612 SH/SZ stocks had no L1 on 2019-06-28 (phase 2 criterion 1). Point-in-time classification is correct as delivered; neutralisation and grouping still need an industry for every stock on every date.
- Decision: `IndustryClassifier` exposes two columns: `l1_pit` (membership as of the date, NULL when unknown) and `l1_grouping` = `l1_pit` when known, else the stock's **first known** L1 back-filled, with `industry_backfilled = true`. Factor neutralisation and the risk model's industry dummies use `l1_grouping`; anything claiming PIT purity reports the backfilled share. Criterion (1) is met as delivered.
- Alternatives: leave pre-2021-07 stocks unclassified (rejected: drops them from neutralised factors and the risk model); map `stock_basic.industry` to L1 for the gap (deferred: adds a second scheme; use if the backfilled share matters).
- Consequences: one extra column and flag; RISK_MODEL_DESIGN §1 estimation universe uses `l1_grouping`.
- Links: plan 11 ph2, plans/execution/04_factors.md ph5, plans/execution/05_risk_model.md ph1, DATA_CATALOG §3b

### D-072 Index-replication criterion restated
- Context: member-computed Shenwan L1 returns vs published `sw_daily`: median 2.5 bp, 89.7% within 10 bp, 98.1% within 25 bp on free-float weights; the residual is Shenwan's tiered weighting, which we do not reproduce.
- Decision: the criterion becomes median ≤ 5 bp, ≥ 85% of industry-days within 10 bp, ≥ 95% within 25 bp, on free-float (`close × free_share`, previous day) weights. Met. The member-computed series is the documented fallback only when `sw_daily` is unavailable; `sw_daily` is the primary.
- Alternatives: implement Shenwan tiered weights (deferred: rules are published but add complexity for a fallback path).
- Consequences: plan 10 `SectorIndexPanel` reads `sw_daily` first.
- Links: plan 11 ph2, plans/execution/10_macro_commodity_sectors.md

### D-073 Fetch-log orphan cleanup
- Context: three orphan fetch-log rows (shibor "all", index_weight "000300.SH"/"000905.SH") survive `rebuild` because it restores from the parquet mirror and nothing removes rows whose raw file is gone.
- Decision: `FetchLog.remove_orphans()` drops rows whose raw file does not exist; `rebuild` calls it after restoring; the count is logged and appears in the manifest. Accepted.
- Alternatives: leave orphans (rejected: fetch log must equal the raw files, plan 01 verification rule).
- Consequences: rebuild output shows "orphans removed: n".
- Links: lake.FetchLog, D-037

### D-074 ETF and fund datasets (plan 11 phase 3)
- Status: accepted by execution (2026-09-28).
- Context: one-call checks on 2026-09-24 (2026-09-25 is the Mid-Autumn holiday, which is why date calls on it came back empty): `fund_basic(market=E)` 2,961 funds in one call (L 2,238 / D 677); `fund_daily(trade_date)` 2,163 rows (567 on 2019-01-02); `fund_nav(nav_date, market=E)` 2,116 rows (25,189 without `market`, mostly off-exchange `.OF`); `fund_share(trade_date)` 1,774 rows; `margin_secs(trade_date)` 4,479 rows (SZSE 2,106 / SSE 2,002 / BSE 371) — endpoint exists, one call covers all exchanges. On a holiday `margin_secs` still returns the SSE list only.
- Decision: `fund_basic` one call `market=E`, overwrite; `fund_daily` swept by `trade_date` from 2019, partitioned (replaces the `option_etfs` enum, which is removed); `fund_nav` swept by new date kind `nav_date` (trading sessions, `market=E`), key `(ts_code, nav_date)`, `known_on_rule: next_session` (NAV of T is published that evening); `fund_share` by `trade_date`, `next_session` (share count after the close); `margin_secs` by `trade_date`, `as_is` (list effective before the open). The plan-03 per-ETF `fund_daily` raw files (`ts_code=*.parquet`) are checked to be a subset of the new data, then moved to `external/tushare_fund_daily_option_etfs/` with `PROVENANCE.md`; the old curated `reference/fund_daily` folder is removed (rebuildable).
- Alternatives: `fund_nav` per ETF over a range (per-code `date_window`, D-069): ~2,000 codes × 8 years of calls; rejected, the by-date call covers every exchange fund.
- Consequences: ~7,500 calls (~4 h) for the 2019+ backfill; `fund_daily` grows from 16 k to ~3 M rows. `report_rc` on 2026-09-24: 177 rows, 66 stocks, 21 brokers (the earlier 66-row check was on the holiday) — row volume still to be judged in phase 7.
- Links: D-063, D-069, plan 11 phase 3, ETF_PAIRS_DESIGN

### D-075 ETF universe by name
- Context: plan 11 phase 3 criterion (1) counts ETFs per date; `fund_share.fund_type` is NULL for almost all rows before 2026, so it cannot define the set.
- Decision: an ETF on date t is a `fund_basic` row (market E) whose `name` contains "ETF" and which has a `fund_daily` bar on t. Year-end counts 269 (2019) → 1,705 (2026-09) accepted as plausible. Size = `fd_share × 1e4 × unit_nav` (`net_asset` is sparse). Accepted.
- Alternatives: `fund_type` label (rejected: unusable); index-tracking flag from `fund_basic.benchmark` (deferred: useful to classify ETFs by underlying for pairs, add in the pairs research).
- Consequences: ETF_PAIRS_DESIGN §3 universe rule uses this definition; premium/discount uses `unit_nav`.
- Links: plan 11 ph3, plans/architecture/ETF_PAIRS_DESIGN.md

### D-076 Paging past per-endpoint caps below `limit`
- Status: accepted by execution (2026-09-29).
- Context: `TushareClient` requested `limit=6000` pages and stopped at the first page shorter than 6,000. Several endpoints cap one call lower: `fut_holding` returns at most 4,000 rows (a no-exchange call on 2026-09-24 returned exactly 4,000, DCE + SHFE only), `fund_share` at most 2,000. A scan of `meta.fetch_log` (a cap C means no single page ever exceeds C) found one affected dataset: `fund_share`, 21 quarter-end dates at exactly 2,000 rows whose true size is 8,400–26,000 rows (off-exchange funds report at quarter-ends). All other round counts are below a page size the same endpoint has already exceeded, so they are genuine.
- Decision: keep paging while a page is non-empty and either full or a multiple of 1,000 (`CAP_STEP`; Tushare caps are 2,000 / 4,000 / 6,000 …); advance `offset` by the rows received. Costs one extra call only for keys whose size is a round number. The 21 `fund_share` dates were refetched with `--force` (2019-09-30: 8,422 rows; 2026-06-30: 26,003). With the fix a no-exchange `fut_holding` call returns all exchanges (10,259 rows on 2026-09-24 = the sum of the per-exchange calls).
- Alternatives: per-dataset `page_size` (needs every cap known in advance; rejected); always fetch until an empty page (doubles calls).
- Consequences: truncation at an unknown cap is detected for any endpoint whose cap is a multiple of 1,000. The coverage notebook (phase 9) repeats the round-count scan.
- Links: D-069, D-070, plan 11 phases 3–4

### D-077 Futures and gold datasets (plan 11 phase 4)
- Status: accepted by execution (2026-09-29).
- Context: one-call checks on 2026-09-24: `fut_basic` per exchange (CFFEX 728, SHFE 3,632, DCE 3,335, CZCE 2,954, INE 489, GFEX 149 contracts); `fut_daily(trade_date)` without `exchange` returns all six (1,075 rows); `fut_holding` see D-076 — INE has no top-20 rows under its own code, and bc/lu/nr appear under SHFE while `sc` and `ec` have none; `fut_mapping(trade_date)` 202 continuous codes; `sge_basic` 13 contracts; `sge_daily(trade_date)` 41 rows (incl. forward quotes).
- Decision: `fut_daily`, `fut_holding` drop the CFFEX filter and start 2019 (`fut_holding` gains `exchange`, key `trade_date, exchange, symbol, broker`); the plan-09 CFFEX-only raw files for 2025–2026 are moved out and refetched (checked as a subset before deletion). `fut_basic` swept by exchange (6 values, overwrite); `fut_mapping`, `sge_daily` by `trade_date` from 2019; `sge_basic` one call. All `as_is` on `trade_date`.
- Risk found: an empty key is marked done permanently (TC-BF-005), so a run before a day's data is published loses that day. This backfill ends at 2026-09-28 explicitly. Proposal for a decision: empty keys within the last N sessions (N = 3) are not marked done (or are always refetched like `refetch_recent`).
- Consequences: ~7,500 calls (~4–5 h); `fut_daily` ~1.7 M rows, `fut_holding` ~15 M rows.
- Links: D-076, plan 09, plan 11 phase 4

### D-078 Empty keys near the present are not marked done
- Context: an empty result marks a key done permanently (plan 01 rule "empty is not an error"); a download run before the vendor has published a day's data therefore loses that day for good. Raised by quant-cn-b7 inside D-077.
- Decision: `BaseFetcher.run` marks an empty key done only if its date is more than 3 trading sessions before today (`TradingCalendar`); more recent empty keys are logged in `run_log` with status `empty_recent` and retried on the next run. Non-date keys (enum, single-call) keep the old behaviour. Accepted.
- Alternatives: never mark empty keys done (rejected: holidays and no-event days would be refetched forever); a per-dataset publication-lag table (deferred: 3 sessions covers Tushare's observed lags; revisit if a dataset needs more).
- Consequences: `make download` on the same day is safe to rerun; `FetchLog.list_pending` includes recent empties; one test on a fake clock.
- Links: DATA_LOADING_DESIGN §2.3, D-077, plan 11 ph4

### D-079 Futures cleaning views in the lake
- Context: `fut_holding` mixes member-category totals and product-level symbols with broker/contract rows (exchange- and period-specific labels), and commodity-exchange oi/vol are two-sided before 2020-01-02; a stray "ZCE" label exists. Three consumers need clean data: `FuturesPositioning` (plan 09), `ContinuousFutures`/`TermStructure` (plan 10), pairs research.
- Decision: cleaning lives in the lake as derived views, not in calculators: `derived.fut_holding_brokers` drops category rows (label list per exchange and period in `config/futures_categories.yaml`), keeps only contract symbols (`^[A-Z]{1,2}\d{3,4}$` per exchange convention), normalises exchange labels (ZCE → CZCE); `derived.fut_daily_one_sided` halves oi and vol for SHFE/DCE/CZCE/INE before 2020-01-02 and flags rows `two_sided_adjusted`. Raw and curated stay untouched. `FuturesPositioning` switches to the views. Accepted.
- Alternatives: clean inside each calculator (rejected: three copies of the same rules); modify curated (rejected: curated mirrors the vendor, D-012).
- Consequences: two views + a config file; digests for new views recorded; DATA_CATALOG §3b lists the traps.
- Links: plan 11 ph4, plans/execution/09_positioning_flows.md, plans/execution/10_macro_commodity_sectors.md

### D-080 Domestic macro and FX datasets (plan 11 phase 5)
- Status: accepted by execution (2026-09-29).
- Context: one-call checks on 2026-09-29: `yc_cb` (ChinaBond curves) is **not permitted** on this account ("没有接口(yc_cb)访问权限"); `cn_cpi`, `cn_ppi`, `cn_m`, `cn_pmi` return 140 months 2015-01 → 2026-08 in one call (`start_m`); `cn_pmi` ignores `fields` and always adds `ID`, `CREATE_BY`, `CREATE_TIME`, `UPDATE_BY`, `UPDATE_TIME` (a numeric schema rejected `UPDATE_TIME`); `shibor_lpr` 1,234 rows since 2015; `fx_daily(trade_date)` returns 272 FXCM instruments including stock CFDs.
- Decision: the four monthly series are one call each (overwrite) with `known_on_rule: period_end_lag` and conservative lags until phase 10 brings the official NBS/PBOC calendars: CPI 12, PPI 12, M0–M2 15, PMI 1 day (released the last day of the month at 09:30). `cn_pmi` keeps its metadata columns as text. `shibor_lpr` by yearly `date_window`. `fx_daily` by yearly window × 14 codes (`value_param: ts_code`, `enum_values.fx_codes`: USDCNH, USDOLLAR, EURUSD, USDJPY, XAUUSD, XAGUSD, UKOIL, USOIL, COPPER, 10USNOTE, SPX500, NAS100, HKG33, CHN50), `next_session`. The yield curve criterion of phase 5 cannot be met from Tushare: China government yields come from phase 10 (ChinaBond via AkShare) and US 10y from FRED (phase 6).
- Findings: the FXCM CFDs (oil, copper, US notes, dollar index, equity indices) start only in 2022-07 in Tushare; currency pairs and metals go back to 2015. FXCM bars are dated by the Beijing date of the New York close: Friday's bar carries Saturday's date and a short Sunday bar opens the week, so a `next_session` effective date is never early (at most one day late).
- Consequences: macro effective dates check out (CPI 2026-08 → 2026-09-14; M 2026-01 → 2026-02-24 after the Spring Festival); ~185 calls in total.
- Links: D-063, D-065, D-069, plan 11 phases 5, 6, 10

### D-081 Analyst and event datasets and the loader changes they need (plan 11 phase 7)
- Status: accepted by execution (2026-09-29); design approved by quant-cn-a1 before the backfill.
- Context: probes on 2026-09-12 … 09-24. `report_rc`: a normal week has 189–493 rows/day (23–35 brokers, 61–174 stocks); a one-month range stops at exactly 5,000; weekends are not empty (69–155 rows). `share_float`: a one-month `float_date` window already returns the 6,000 cap and the endpoint is documented to ignore `offset`. Event endpoints (`report_rc`, `stk_surv`, `stk_holdertrade`, `share_float`) publish on Saturdays/Sundays. `disclosure_date` takes `end_date`, `stk_holdernumber` `enddate`, `broker_recommend` `month` (YYYYMM). `stk_surv` has no disclosure date. `broker_recommend` has no publication date.
- Decision (seven loader changes + the datasets):
  1. `SweepSpec.days: sessions | weekdays | all` (event datasets `all`; `DateCodec.list_days`).
  2. `SweepSpec.param_name` renames the key parameter; for `date_window` the window key itself is sent (`broker_recommend`).
  3. `TushareClient` raises `DataSourceError("offset ignored")` when a page repeats the previous one (never loops).
  4. `known_on_rule: period_start_lag` (month start + lag) for `broker_recommend` (lag 0; a rule, not an observed date).
  5. `DatasetSpec.lag_sessions` for `next_session`: `stk_surv` = surv_date + 2 sessions (visits disclosed 1–2 days later; conservative, DATA_CATALOG §3).
  6. `DatasetSpec.key_defaults`: NULL text key columns filled before validation (`report_rc.quarter` "" for 3,486 rating-only reports; `stk_surv.rece_org` "" for 1 row).
  7. `derived.fundamentals_long` limited to datasets curated under `fundamentals/` (event data is period-swept too and would otherwise enter the PIT states; digests unchanged).
  Datasets: `report_rc` by `report_date` (days all, next_session, from 2019); `stk_surv` (days all); `broker_recommend` (monthly window); `hk_hold` (days all, next_session); `forecast_vip`, `express_vip` by period with every version; `stk_holdertrade` by `ann_date` (days all) **without a primary key** (vendor repeats rows: 65,459 rows in 20,023 key groups, 24,517 distinct; ~4.5 k groups are real second trades; exact duplicate rows dropped); `share_float` by `ann_date` from 2016 (days all); `disclosure_date` and `stk_holdernumber` by period.
- Results: report_rc 1.72 M rows (90–107 brokers, 2.5–3.5 k stocks a year; max 5,589 rows on one day); share_float 6.66 M (IPO lock-up notices list every offline placement investor, up to 44,069 rows on one day; 124 duplicate keys); hk_hold 5.76 M; stk_surv 905 k (from 2021-08-05); broker_recommend 18 k (from 2020-03); PIT test OK for all ten; a 90-day consensus snapshot works (600519.SH, 2026-09-24: 45 brokers, median 2026 EPS 67.34). `report_rc.tp` is total profit (10k CNY), not a target price (targets: `max_price`/`min_price`).
- Links: D-038, D-063, D-076, D-082, plan 11 phase 7

### D-082 Paging step 100 (amends D-076)
- Status: accepted by execution (2026-09-29).
- Context: after the phase 7 backfill the round-count scan found three per-call caps that are not multiples of 1,000, so D-076's step missed them: `stk_surv` 400 (760 days at exactly 400), `stk_holdernumber` 5,500 (11 periods), `hk_hold` 4,200 (the 6 quarter-ends since 2024-12, when full holdings are still disclosed). `offset` works on all three (disjoint second pages).
- Decision: `CAP_STEP = 100`: keep paging while a page is full or a multiple of 100 (one extra call for keys whose size is a round hundred). Refetched with `--force`: `stk_holdernumber` all 30 periods (149,032 → 152,592 rows), `hk_hold` 6 dates (4,200 → 4,417 … 5,254), `stk_surv` 2021-08 → 2026-09 (433,119 → 905,248 rows; max 7,626 visits on one day). Rescan: no dataset left whose maximum is a multiple of 100 reached on several keys, except `index_weight` 12,000 (natural: 1,000 constituents × 12 months, already paged past 6,000).
- Consequences: the phase 9 coverage notebook repeats the scan with step 100; a cap that is not a multiple of 100 would still be missed and is caught only by that scan.
- Links: D-070, D-076, D-081

### D-084 SSE lending eligibility proxy
- Context: SZSE publishes an official per-date margin/short-sell eligibility list (AkShare wraps it); SSE has no API list and its per-security page is truncated at 2,000 rows. Tushare `margin_secs` SSE history is frozen before 2024-04 (plan 11 ph3 trap).
- Decision: extend Tushare `margin_detail` back to 2019 (~1,200 calls) and define the SSE proxy per date: `margin_eligible` = has a `margin_detail` row; `short_eligible` = `rqye > 0` (short balance outstanding) — the stricter proxy the ETF-pairs short leg needs. Documented as "had margin/short activity", i.e. a subset of the true list. From 2024-04 the proxy is compared with `margin_secs` SSE monthly and the agreement rate stored in the quality schema. SZSE uses the official list (`szse_margin_targets`). Hand-downloaded SSE lists may be added to `external/` later with provenance for spot checks. Accepted.
- Alternatives: manual SSE downloads per date (rejected: no API, unbounded manual work); Tushare `margin_secs` alone (rejected: frozen before 2024-04).
- Consequences: `margin_targets` derived view unions SZSE official + SSE proxy with a `source` column; ETF_PAIRS_DESIGN §1 short-leg rule references it.
- Links: plan 11 ph10, D-065, ETF_PAIRS_DESIGN

### D-085 BaoStock verification scope
- Context: a full price cross-check is ~5,500 stocks × 2 calls; verification must be cheap to run nightly.
- Decision: one full-history backfill into `raw/baostock_daily` and `raw/baostock_adj_factor`; thereafter nightly only the last 5 sessions per stock (one call per stock with a 5-session range), plus a monthly random sample of 200 stocks over full history to catch silent historical revisions. `quality.price_crosscheck` reports mismatch rate on close and adj_factor (tolerance 1e-6 relative) and lists mismatches; never overwrites Tushare data. Accepted.
- Alternatives: full nightly (rejected: 11k calls/night); no historical resample (rejected: revisions would go unnoticed).
- Consequences: `make verify-prices` target; quality rows in the catalog.
- Links: DATA_SOURCES §2, plan 11 ph10

### D-086 Release-lag validation against observed release dates
- Context: Jin10 release-date series (via AkShare) exist for CPI/PPI/PMI/M2 but stop at 2025-09 and have placeholder early dates, so they cannot replace the lag rules.
- Decision: store the four series as `macro_release_dates`; derive the observed lag per month (release − month end) and validate our `release_lag_days` (CPI/PPI 12, M 15, PMI 1) against them: if any observed release is later than the rule, raise the rule to the observed maximum for that series and log it. Lag rules remain the mechanism; validation runs in the coverage notebook and `make check` warns on violations. Accepted.
- Alternatives: use observed dates where available and rules elsewhere (rejected: two regimes in one series; the conservative rule everywhere is simpler and safe).
- Consequences: `EffectiveDateResolver` unchanged; a small validator class in `lake`.
- Links: plan 11 ph5, ph10, D-080

### D-083 Forced refetches keep the previous raw file (proposed by quant-cn-a1; not yet implemented)
- Status: accepted, implementation pending (after plan 11 phase 10).
- Decision: `--force` keeps the previous raw file as `<key>.prev.parquet` until the next `make lake-rebuild` confirms the new one, then deletes it, so a forced refetch is auditable (the phase 8 statement refetch could not be compared field by field).
- Links: D-038, plan 11 phase 8

### D-087 Third-source loader: AkShare and BaoStock clients, rename, key_field (plan 11 phase 10)
- Status: accepted by execution (2026-09-29).
- Decision: `AkshareClient` (akshare function per query, lazy import from the optional extra `sources`, retries, ISO dates → YYYYMMDD) and `BaostockClient` (lazy login, `600000.SH` ↔ `sh.600000`, lake field names mapped to BaoStock's, numbers parsed, Beijing codes skipped) as `BaseApiClient`s selected by `DatasetSpec.source`. `DatasetSpec.rename` (vendor column → field, applied in `BaseFetcher.fetch_one` before the raw write) and `SweepSpec.key_field` (the sweep key written into a column the response lacks, e.g. the SZSE list's date). `ServiceBuilder` now passes `query` to `FetcherFactory`, so `values_from_dataset` works outside tests. `DatasetSpec.release_dates` + `ReleaseLagChecker` + `make release-lags` in `make check` (D-086); lags raised to the observed maxima since 2010: CPI/PPI 12 → 20, M 15 → 20, PMI 1 → 7 days (23/179 CPI and 11/242 M2 releases had come later than the old rules, i.e. look-ahead). `QualityViews` (schema `quality`): `margin_targets_agreement` (D-084), `price_mismatches` / `price_crosscheck` / `adj_crosscheck` (D-085); `make verify-prices` refetches the last ~10 calendar days from BaoStock and reports the mismatch rate.
- Results: `cn_bond_yield` 3 ChinaBond curves 2010-01-04 → 2026-09-28 (4,184 days each); `lme_copper` 2,537 days from 2016-09; `macro_release_*` 477/363/250/395 rows (Jin10, ends 2025-09); `szse_margin_targets` 2.63 M rows 2019 → 2026 (438 names on 2019-01-02, 2,106 on 2026-09-24); `margin_detail` extended to 2019 (2.80 M new rows); `derived.margin_targets` SSE proxy agrees with `margin_secs` at 29 of 30 month-ends since 2024-04 exactly (one margin_secs-only name in 2025-10). SSE proxy year-end counts 919 (2019) → 2,002 (2026), where Tushare `margin_secs` reported a frozen 1,956.
- Links: D-065, D-080, D-084, D-085, D-086, plan 11 phase 10

### D-088 BaoStock cross-check results and the adjustment tolerance (D-085 follow-up)
- Status: accepted by execution (2026-09-30).
- Context: BaoStock backfill 2019-01-01 → 2026-09-28 for 5,556 SH/SZ stocks (2.53 M bars; about 5 s per stock; three BaoStock server outages of several minutes, bridged by resuming; login is now retried with a longer pause and a logout of the broken session; `T600018.SH`-style non-6-digit codes are skipped) and 26,565 dividend-date factors.
- Results: `quality.price_crosscheck`: 8,650,365 Tushare unadjusted closes compared, **0 mismatches** at 1e-6 relative (every year 2019–2026); 1,693 Tushare SH/SZ rows have no BaoStock row (retired alias codes, D-053). `quality.adj_crosscheck`: median step difference 2.3e-5; 6,630 events above 1e-4 (Tushare stores `adj_factor` with 4 decimals, so a step on a factor near 1 carries up to 1e-4 rounding); 31 events above 1e-3 (0.12%), 21 above 1%. The largest (302132.SZ 2025-02-18, 5.98 vs 1.00) is BaoStock restarting its factor at the code change 300114 → 302132 while Tushare stays continuous; the others are BaoStock factor moves on days where Tushare shows none (a cluster on 2020-11-25, a decrease for 000001.SZ on 2020-12-31).
- Decision: closes keep the 1e-6 tolerance; adjustment steps use 1e-3 (4-decimal storage). The 31 events above 1e-3 are listed, not corrected (verification never overwrites); plan 04 treats them as a watch list when it builds the alias map.
- Links: D-053, D-065, D-085, plan 11 phase 10

### D-089 LakeReader facade and TickerAliasMap (plan 04 phase 1)
- Status: accepted (design approved by quant-cn-a1, 2026-09-30).
- Context: SRC_DESIGN §2.2b put the full read surface on `LakeQuery`, but `PitAligner` reads through `LakeQuery` (import cycle) and the class would exceed 300 lines. Tushare keeps a retired code's rows and back-fills the same history under the new code (D-053), yet `stk_limit`, `moneyflow` and `margin_detail` exist only under the old code before the change.
- Decision: `lake.LakeReader(catalog, query, datasets, aligner, alias_map, calendar, cache)` is the read API above raw SQL (`read_panel`, `read_prices(dense=)`, `read_fundamentals_pit`, `read_reference`, `register_frame`, `list_views`); `LakeQuery` stays unchanged underneath; `PanelCache` (LRU, byte cap, copy-on-write copies) is on in notebooks, off in pipelines (`ServiceBuilder.build_reader`). `TickerAliasMap` builds `derived.ticker_alias` from the data (a code missing from `stock_basic` whose closes equal a listed code's on ≥ 20 shared dates, ≥ 99% equal; statistics kept; an old code matching more than one listed code is recorded, not accepted) plus `config/ticker_aliases.yaml` (floor; config wins on conflict); `LakeReader` applies it to every per-stock panel and to PIT fundamentals, new code winning on a duplicate key. `read_prices` keeps both `close` and `close_adj` (no `adjusted` flag); `prices_adj` is unchanged because every old-code bar is duplicated under the new code.
- Results on the lake: the three known pairs are detected (1,893 / 2,323 / 3,421 shared days, equality 1.0) and no other candidate; reading the new codes adds exactly the old-code-only rows: `stk_limit` 001914 +232, `moneyflow` 001914 +221 / 302132 +1,472, `margin_detail` 001914 +232 / 302132 +560 (the 1,693 no-BaoStock rows of D-088 are these old-code bars); 302132's `adj_factor` is continuous across the change (5.976), so the largest BaoStock adj outlier of D-088 is a BaoStock restart, not a Tushare break.
- Links: D-041, D-053, D-088, SRC_DESIGN §2.2b, plan 04 phase 1

### D-090 Prewhitened Newey-West for IC significance
- Context: the §10 Bartlett rule failed the §7 known-answer test in plan 04 phase 2: 95% interval coverage 93.8% / 89.8% / 88.4% on AR(1) φ = 0.3 / 0.6 and on MA(19) overlapping 20-session sums (the real IC_t structure at h = 20), so ~12% of null factors would pass |t| > 1.96 at h = 20. NW 1994 automatic bandwidth without prewhitening: 93.2% / 91.4%.
- Decision: `HacVariance` defaults to AR(1) prewhitening (Andrews & Monahan 1992): ρ̂ by OLS on the centred series capped at 0.97, Bartlett HAC on the residuals with the same lag rule, recoloured by 1/(1 − ρ̂)². Coverage 94.8% / 95.1% / 99.0%: within ±2 pp on AR(1), conservative on MA(19), the safe direction for acceptance. The plain estimator stays available (`prewhiten=False`) for comparison. Tests TC-HAC-003 (AR(1) ±2 pp) and TC-HAC-005 (MA(19) ≥ 93%). `scipy ≥ 1.14` becomes a core dependency (Student-t, normal, KS). Accepted; §10 amended.
- Alternatives: NW 1994 automatic bandwidth (rejected: still under-covers at φ = 0.6); block bootstrap only (rejected: keep an analytic t alongside the bootstrap CI).
- Consequences: all IC t-statistics in FACTOR_REPORT are prewhitened; the acceptance hurdle HLZ t ≥ 3 applies to this t.
- Links: plans/architecture/FACTOR_TESTING_DESIGN.md §10, plans/execution/04_factors.md ph2

### D-091 Materialised universe and reader split (plan 04 phase 3)
- Status: accepted by execution (2026-09-30).
- Decision: `UniverseStep` (pipeline, one unit per year from `universe.start`) builds `UNIVERSE_PANEL` in one DuckDB query per year and writes `derived/universe/year=YYYY/part-0.parquet` (`ParquetWriter.write_derived`); it runs inside `curate` between compaction and derived views, and `derived.universe` (a view over those files) is digested like every derived view, so `make lake-rebuild` proves it byte-identical. Rules (`config/base.yaml` `universe`): rows for every stock listed on the session (`list_date <= t < delist_date`; retired alias codes are absent from `stock_basic`); exclusion reasons kept comma-joined: `exchange` (suffix not in `exchanges`, BJ excluded, D-054), `st` (name in effect at t — latest `namechange.start_date <= t` — contains ST or starts with PT), `delisting` (name contains 退), `new_listing` (< `min_sessions` = 120 sessions since the first session on/after `list_date`), `suspended` (no `daily` bar). `LakeReader.read_universe(start, end, members_only)`. `register_frame` and `list_views` moved from `LakeReader` to `LakeQuery` (catalog utilities; keeps `LakeReader` under 300 lines; amends D-089).
- Results: 14.78 M rows 2010-01-04 → 2026-09-30; listed rows equal `stock_basic`'s listed count at every year-end (2,041 in 2010 → 5,572 in 2026-09); members 1,663 (2010) → 3,475 (2019) → 4,973 (2026-09-30). On 2026-09-30: 300 BJ, 194 ST, 90 new listings (45 also BJ), 11 suspended, 1 delisting arrangement. PIT: 000004.SZ leaves on its ST start 2022-05-06 and returns 2023-06-28, the day after the ST name ends. Curate time grows to ~3 min; all 13 digests reproduce on rebuild.
- Links: D-041, D-053, D-054, D-089, FACTOR_TESTING_DESIGN §11, plan 04 phase 3

### D-092 PIT TTM in the lake and the first six factors (plan 04 phase 4)
- Status: accepted by execution (2026-09-30).
- Context: FACTOR_TESTING_DESIGN §11 requires TTM "from the four latest PIT-visible quarters" and factors to read fundamentals only through `FUNDAMENTALS_PIT`, which carries the latest visible period per field. Statements report year-to-date flows.
- Decision: `derived.fundamentals_ttm` (DerivedViews): for every income / cash-flow field and every announcement (known_on), the latest visible period P and `TTM = YTD(P) + FY(year − 1) − YTD(P − 1 year)` (= YTD at a year end) from the latest version of each period known by then (ASOF on known_on), as `<field>_ttm`; `<field>_ttm_yoy = (TTM(P) − TTM(P−1y)) / |TTM(P−1y)|` for `n_income_attr_p` and `revenue`. `derived.fundamentals_long` = `fundamentals_base` (statements) ∪ `fundamentals_ttm`, so PitAligner makes TTM fields effective the next session like any field; a restated prior year produces a new TTM row from its effective session. `factor` package (L5; import-linter layers corrected to CODING_STANDARD §2.1: pipeline L6 > factor L5 > statistic/calculation L4): `BaseFactor` (declares inputs, fields, basic_columns, lookback; subclasses self-register), `FactorInputs`, `FactorFactory` (config/factors.yaml; imports every `factor/library` module), and `EarningsYieldFactor` (EP TTM = n_income_attr_p_ttm / (total_mv × 1e4)), `RoeFactor` (TTM profit / latest PIT equity), `ProfitGrowthFactor` (n_income_attr_p_ttm_yoy), `MomentumFactor` (12-1, close_adj carried forward over suspensions), `ReversalFactor` (−1-month return), `TurnoverFactor` (−60-session mean turnover_rate_f, ≥ 40 observations). Statement datasets now start 2016-01-01 and `daily_basic` 2018-09-01 so every factor has history from 2019.
- Results: every factor ≥ 93.6% of universe members at month ends in every year 2019–2026 (EP 99.4–100%, ROE 99.2–99.9%, growth 95.2–98.5%, momentum 93.6–99.1%, reversal and turnover 100%). PIT tests per factor: statement values are invisible on their announcement day and visible the next session; a restatement changes the value only from its effective session; price factors are unchanged when later prices change.
- Links: D-036, D-038, D-089, D-091, FACTOR_TESTING_DESIGN §11, plan 04 phase 4

### D-093 Neutralisation on Shenwan L1 from the start
- Context: plan 04 phase 5 planned `stock_basic.industry` for industry neutralisation until plan 05 delivered Shenwan; `derived.industry_l1` (D-071) already exists, point-in-time with a flagged backfill before 2021-07.
- Decision: `FactorPreprocessor` neutralises on `derived.industry_l1.l1_grouping` (31 Shenwan L1 groups) plus log market cap; every FACTOR_REPORT states the share of backfilled industry labels in the period. `stock_basic.industry` is not used. Accepted.
- Alternatives: coarse `stock_basic.industry` (rejected: a second scheme with no PIT history, would be replaced anyway).
- Consequences: plan 05's `IndustryClassifier` reuses the same view; factor and risk model share one industry definition.
- Links: D-071, plans/execution/04_factors.md ph5, RISK_MODEL_DESIGN §1

### D-094 Features in curate, evaluation on demand (plan 04 phase 5)
- Status: accepted by execution (2026-09-30).
- Decision: `FeatureStep` runs last in `curate` (after the derived views): per year from `campaign.start` the six factors (FactorFactory, PIT inputs), universe members only, `FactorPreprocessor` (winsorise MAD k = 5 → standardise → neutralise on Shenwan L1 `l1_grouping` + log market cap, D-093 → restandardise, each step logged incl. the back-filled industry share) and `SignalCombiner` (weighted mean of processed z-scores over ≥ 3 available factors, restandardised, factor "score"), written to `derived/features/year=YYYY`; `derived.features` view and its digest are refreshed (DeriveStep.refresh_digests), so lake-rebuild proves them byte-identical. Evaluation is not part of curate: `make evaluate` (`EvaluationStep`) evaluates factor by factor (forward returns from the open of t+1, one horizon at a time to bound memory), applies Holm / BHY / Romano-Wolf / HLZ once over all 7 × 5 factor-horizon tests, writes `derived/reports/<campaign>/{ic_series,ic_test,quantiles}.parquet` and resumes / saves `meta/trials/<campaign>.parquet` (identical variants are not recorded twice). Campaign settings in `config/factors.yaml` `campaign` (`CampaignConfig`). `ServiceBuilder` moved to `quant_cn/service_builder.py` (cli.py > 600 lines; import-linter: `cli` > `service_builder` > …); research commands (`release-lags`, `evaluate`) live in `ResearchCommands`.
- Results (factor_campaign_01, 2019-01 → 2026-09, run bb69f4fc6406): features 56.5 M rows (~2.5 min in curate), digest reproduced on rebuild. At h = 20: turnover_60d IC 0.079, NW t 4.85, BHY p < 0.001, sub-period t 3.26 / 3.48 / 1.65, ICIR CI [0.64, 0.99]; reversal_1m IC 0.052, t 4.90, sub-periods 3.19 / 3.07 / 2.12, ICIR CI [0.42, 0.72] — both meet §6 criteria 1–3. score IC 0.061, t 3.59, BHY p 0.003 but 2022–24 sub-period t 1.47 (< 1.5). ep_ttm t 1.86, roe_ttm 0.96, profit_growth_ttm 0.77, momentum_12_1 −0.24 (no 12-1 momentum in A-shares) do not pass. Mean IC rises with horizon for every factor, so the exponential decay half-life is reported as infinite; rank autocorrelation 0.93 (reversal) to 0.999 (fundamentals). 35 trials recorded.
- Links: D-090, D-091, D-092, D-093, FACTOR_TESTING_DESIGN §6, plan 04 phase 5

### D-095 Decay reporting for rising IC profiles
- Context: in campaign 01 mean IC rises with horizon for every factor (slow signals in a reversal-dominated market), so an exponential half-life is infinite and uninformative.
- Decision: `compute_decay` reports `peak_horizon` = argmax of mean IC over {1, 5, 10, 20, 60}; fits the exponential half-life only on horizons at or beyond the peak; when the profile is non-decreasing through 60 sessions it reports `half_life = NA (rising)` and the accumulation ratio `ic_60 / ic_20`. Acceptance (§6) stays at h = 20; a rising profile is a note, not a failure. Accepted.
- Alternatives: force a fit (rejected: meaningless numbers); drop decay (rejected: the horizon profile is useful for holding-period choice in plan 06).
- Consequences: FACTOR_REPORT gains `peak_horizon` and `accumulation_ratio`; FactorChart plots IC by horizon.
- Links: FACTOR_TESTING_DESIGN §2, plans/execution/04_factors.md ph5

### D-096 CNINFO is the document source for the industry-chain graph
- Status: accepted with plan 12's approval (2026-11-07).
- Context: probed 2026-11-07. This Tushare token is denied `research_report` and `anns_d`, but can read `irm_qa_sz`. CNINFO `hisAnnouncement/query` works without a key and covers the whole market by category and date. PDFs download from `static.cninfo.com.cn`.
- Decision: CNINFO supplies metadata and PDFs for 2023-11-01 onwards: annual, semiannual, Q1/Q3, prospectuses, and announcements filtered by title. Tushare supplies the `irm_qa_sh` / `irm_qa_sz` Q&A. Metadata is kept for every category. PDFs are kept only for the selected types.
- Alternatives: buy Tushare `research_report` (deferred: open question in plan 12); scrape broker sites (rejected).
- Links: plan 12 ph2

### D-097 Opus taxonomy is a prior; company edges need document evidence
- Status: proposed with plan 12 (2026-11-07).
- Decision: Opus writes the whole-market product taxonomy and the product-to-product chain edges in `config/industry_chain/*.yaml`, tagged `source: prior`. No company→product, supplier, customer or competitor edge exists without an evidence row: document, page, quote that passes a string check, and confidence. Queries label prior edges.
- Amendment (2026-11-07, user: foreign companies must appear in the chain): `config/industry_chain/_global_companies.yaml` adds the key non-A-share players per segment (NVIDIA, Broadcom, TSMC, Samsung, SK hynix, ASML, Google, Microsoft, Amazon, Meta, Apple, Tesla, BMW, VW, Bosch, Infineon, ST, Pfizer, MSD, ...). Each carries Chinese and English names, country and listing, and role edges (`produces`, `operates`) to taxonomy products. These role edges are priors and are labelled as such. Edges between an A-share company and a foreign company (`sells_to` / `buys_from`) still need document evidence. A-share companies also link to region nodes (境内, 境外, 北美, 欧洲, …) with revenue share from the 分地区 table.
- Alternatives: let the LLM assert company edges from general knowledge (rejected: unverifiable).
- Links: plan 12 ph1, ph5

### D-098 DeepSeek extracts and validates; Opus reviews samples and merges taxonomy proposals
- Status: proposed with plan 12 (2026-11-07).
- Decision: `DeepSeekClient` (`DEEPSEEK_API_KEY` from `.env` only) runs both the extractor and the validator, with separate prompts. Default model `deepseek-flash` (user, 2026-11-07); the phase-4 pilot runs flash and `deepseek-v4-pro` on the same 50 companies, and pro is used only where flash misses the 85% precision bar (customer/supplier edges, the 0.70–0.90 band). The old key was revoked by the user on 2026-11-07. Every response is cached by prompt hash so rebuilds are free and deterministic. Opus reviews the pilot and validation samples and merges node proposals into the taxonomy.
- Links: plan 12 ph4, ph5

### D-099 Package `industry_graph` at layer 4; LLM base in `core`, vendor clients in `data_loading`
- Status: accepted with plan 12's approval (2026-11-07); package created for phase 3.
- Decision: the graph lives inside quant_cn, not a separate repo as the source note suggested, to reuse the lake, `stock_basic`, Shenwan classification and the loader. `industry_graph` sits at layer 4, independent of `statistic` and `calculation`. `BaseLlmClient` sits in `core`. `CninfoClient`, `DocumentDownloader` and `DeepSeekClient` sit in `data_loading`. `ExtractionStep` sits in `pipeline`. Graph tables go in DuckDB schema `graph`.
- Links: CODING_STANDARD §2.1, plan 12

### D-100 Eastmoney research reports as the broker-report source
- Status: accepted by user instruction (2026-11-07: "研报没有是吧" → take the free source).
- Context: Tushare `research_report` is denied (D-096). The Eastmoney list API `reportapi.eastmoney.com/report/list` returns stock (`qType=0`) and industry (`qType=1`) reports, about 1.1–1.9k per month each and back past 2023-11. The PDFs at `pdf.dfcfw.com/pdf/H3_<infoCode>_1.pdf` download without login.
- Decision: datasets `em_industry_reports` and `em_stock_reports` (source `eastmoney`, one key per month, `refetch_recent: 1`), with PDFs fetched by `DocumentDownloader`. Industry reports come first because they carry the chain structure (plan 12 ph4).
- Alternatives: AkShare `stock_research_report_em` (per stock, so 5k calls a pass; rejected for sweeps); buy the Tushare permission (still open).
- Links: D-096, plan 12 ph2

### D-101 Document storage layout
- Status: accepted (2026-11-07, user: "数据存储需要organize好").
- Decision: one place per kind of data, each rebuildable from the zone above it:
  - Metadata lists (what each site returned): `raw/<dataset>/<key>.parquet` → `curated/documents/<dataset>/year=YYYY/` (`cninfo_announcements`, `em_industry_reports`, `em_stock_reports`, `irm_qa_sh`, `irm_qa_sz`).
  - Original files: new zone `documents/`. Write-once: a file is never edited, only added. Path `documents/<source>/<doc_type>/<YYYY>/<MM>/<name>.pdf`, where source is `cninfo` or `eastmoney`. The doc type comes from `config/documents.yaml`, and year/month from the publication date. Names: `<sec_code>_<ann_id>.pdf` (CNINFO), `<stock_code>_<info_code>.pdf` (stock reports), `<em_industry_code>_<info_code>.pdf` (industry reports).
  - Download manifest: `meta/document_manifest/part-<run>.parquet`, append-only, one row per attempt (doc_id, source, doc_type, code, title, publish_date, url, local_path relative to the lake root, bytes, sha256, status, message, downloaded_at). DuckDB view `meta.documents` keeps the latest row per doc_id.
  - Later phases: page text in `derived/doc_pages/`, graph tables in `derived/graph/` plus DuckDB schema `graph`.
  - `documents/` is expensive to rebuild (vendor downloads), so it joins `raw/` in `make lake-backup`.
- Links: FOLDER_STRUCTURE §2, D-096, D-100, plan 12

### D-102 Read only the chain sections; weighted customer, supplier and product edges form one network
- Status: accepted (user, 2026-11-07: "只需要读跟行业相应的章节…顾客以及供应商、占的百分比，最后应该能连成一张网").
- Decision:
  - **Sections only.** `SectionDetector` cuts each report down to the industry-chain sections, and only those go to DeepSeek. The sections are: 主营业务/主要产品及用途、所处行业情况、主营业务构成 (by product, industry, region)、主要销售客户 (top-5 with sales and % of revenue)、主要供应商 (top-5 with purchases and % of purchases)、主要原材料及采购、产能及在建产能、核心技术. Prospectuses also contribute 业务与技术 and 主要客户/供应商 (they usually name them). IR records and Q&A are used whole, since they are short. Everything else (governance, financial statements, notes) is skipped.
  - **Standard formats, rules before LLM.** Annual reports follow the CSRC content-and-format standard (2021 revision) and prospectuses their own standard. `SectionDetector` therefore locates sections by heading text (管理层讨论与分析, 所处行业情况, 主要业务, 营业收入构成, 主要销售客户和主要供应商情况, 业务与技术, 同行业可比公司), not by section number, which differs across SSE, SZSE and BSE. The 营业收入构成 and 前五名客户/供应商 tables are parsed deterministically. Semiannual reports usually omit top-5 customers, and quarterly reports carry little chain information. Banks, insurers and brokers use a different layout and are skipped for customer and supplier edges.
  - **Structured first.** Revenue share by product and by industry comes from Tushare `fina_mainbz_vip` (datasets `fina_mainbz_p`, `fina_mainbz_i`; probed 2026-11-07, whole market per period) without the LLM. The LLM maps each `bz_item` to taxonomy products and extracts what only text has: customers, suppliers, raw materials, capacity.
  - **Weighted edges.** Every company edge carries `period`, `share_pct`, `amount` (CNY, when given), `basis` (`revenue` | `purchases` | `capacity`) and evidence. Edge types: `produces` (company → product, share of revenue), `sells_to` (company → customer company, share of sales), `buys_from` (company → supplier company, share of purchases), `buys_material` (company → material/product).
  - **Anonymous counterparties** ("客户一", "第一名") become placeholder nodes per (company, period, rank) carrying their share. `EntityResolver` names them only when another document (prospectus, inquiry reply, IR record, or the counterparty's own report) states the link. A sells_to edge from A matched by a buys_from edge from B is one relation with two evidence rows.
  - **One network.** Company–company edges plus company–product edges plus the product chain (D-097) form a single graph, so a query can walk customer → supplier → supplier's products → upstream materials, with shares as weights.
  - **Products and services.** Taxonomy product nodes carry `kind: product | service`, so service lines such as IDC operation, cloud, CRO/CDMO, testing, logistics, EPC and financial services are first-class nodes. Revenue vectors, chains and peers span both (user, 2026-11-07: "按照产品、服务来").
  - **Foreign and unlisted counterparties.** Reports name overseas customers in prose rather than in the top-5 table. Examples from the 6-report prototype: 沪硅产业 lists TSMC, UMC, ST and Vishay; 宁德时代 has VW, BMW, Stellantis, Volvo and DMG nominations; 天岳先进 won a Bosch supplier award. The entity master therefore holds non-A-share companies, with country and listing (e.g. TSMC 2330.TW). Named links without a share are kept as `sells_to` with `share_pct` null, `basis: named` and a qualifier (nomination / volume supply / partner). Mere mentions (industry statistics about Google, staff who once worked at Pfizer) must not become edges; the extractor is prompted to tell a counterparty from a mention, and the pilot measures this. Overseas revenue share comes from the 分地区 table.
  - **Dependence runs both ways.** Demand dependence: A-share → foreign customer (`sells_to`) plus overseas and North America revenue share. Supply dependence: A-share ← foreign supplier (`buys_from`); e.g. 中际旭创 says key raw materials are partly imported and its supplier A holds 35.76% of purchases. Supply-side evidence comes from the risk section (可能面对的风险 / 重大风险提示: import dependence, export controls), from prospectuses and inquiry replies (import share, named foreign suppliers), and from a prior node attribute `import_dependence: high | medium | low` on taxonomy products (e.g. lithography, EDA, high-end optical chips: high). Document evidence overrides the prior. Queries propagate a shock both ways: a demand shock goes down `sells_to`; a supply cut goes from the product down `upstream_of` / `buys_from`.
  - **Inferred matches are separate.** An anonymous "客户A 24%" may be matched to a named company (e.g. via region share plus IR or broker text) only as an `inferred` candidate with its reasoning, never as a fact.
  - **Amount matching (prototype 2026-11-07).** An `inferred` sells_to edge from A's customer row to B's supplier row requires all three of:
    - amounts within 0.5% with no VAT scaling, since both tables are normally ex-VAT; VAT multipliers produced false pairs such as 中际旭创 客户E ↔ 牧原 供应商四;
    - a chain path from A's products to B's products;
    - uniqueness across the whole market.
    The prototype found 温氏 客户#1 22.29亿 ↔ 双汇 供应商#2 22.31亿 (0.1%, live hogs → slaughter).
  - **Anonymous-counterparty profile (prototype 2026-11-07, user: "客户都是下游的哪个部分呢…可以推断一下").** Each unnamed top-5 row gets an inferred profile, labelled as inference:
    - **Business line:** the lines whose revenue is at least the customer amount.
    - **Downstream stage:** the direct chain successors of that line's products, ranked by end market last, then relation type (input/component before used_in before upstream_of), then name overlap.
    - **Region:** "确定境外" when the customer share exceeds total domestic revenue share. Arithmetic, e.g. 中际旭创: domestic 9.42% < 客户A 24.06%. "确定境内" in the mirror case. Otherwise "大概率" at ≥80% or ≤20% overseas.
    - **Name hints:** company-named Tonghuashun concept boards (特斯拉概念, 中芯国际概念, …), weak signals only.
    - Rules alone mis-rank where one product feeds several applications (宁德时代 → 环卫装备 ahead of passenger EVs). Phase 4 adds demand weights per downstream application and a DeepSeek read of the company's own 主要应用领域 text.
  - **Broker reports name customers.** E.g. 东吴国际 on 天岳先进: "英飞凌订单翻倍、芯联集成份额80%-90%" names counterparties the annual report keeps anonymous. Broker-report mentions are a source for naming anonymous rows, recorded as `inferred` with the report as evidence.
  - **US reference.** ASC 280 makes US filers disclose ≥10% customers, usually by name. Compustat Customer Segment, FactSet Revere and Bloomberg SPLC build supply chains from that plus text mining, with source and confidence per link, which is the model followed here. US 10-K full-text search, e.g. for a Chinese supplier's name, is a later source for naming anonymous A-share counterparties; it is out of plan 12 scope.
  - **Peers.** `GraphQuery.peers` combines four signals and reports the reason for each pair. The main signal is cosine similarity of revenue-weighted product vectors, built from `fina_mainbz_p` mapped to taxonomy products. The second is explicit `competitor_of` edges extracted from 同行业可比公司 (prospectuses) and 主要竞争对手 / 行业地位 (annual reports), which are added to the section list. The third is shared customers or suppliers. The last is the same Shenwan L3 code (baseline only). Peers are found at chain-stage level: an optical-chip maker and an optical-module maker are upstream and downstream, not peers.
- Links: D-097, plan 12 ph3–ph6

### D-103 Free structured labels before paid LLM labelling
- Status: accepted (user, 2026-11-07: "还有什么我可以打标的，不需要再重新花钱打标" → "概念板块和公司简介都加上").
- Decision: before any DeepSeek call, the graph is seeded from structured sources the token already has, all probed 2026-11-07:
  - `fina_mainbz_p` / `fina_mainbz_i`: revenue by product and by industry.
  - `stock_company`: main business and business-scope text.
  - Shenwan membership, already in the lake.
  - Tonghuashun indices and members: `ths_index`, plus `ths_member` for concept, industry and theme types.
  - Eastmoney boards and members: `dc_index`, `dc_member`, a daily snapshot from 2026-11-06.

  Company → product labels come from deterministic matching of `bz_item`, `main_business` and `business_scope` against taxonomy names and aliases. Concept boards are a weak signal, used for recall (which paragraphs to send to the LLM) and as theme tags, never as relation evidence. DeepSeek sees only unmatched items and keyword-selected paragraphs.
- Consequences: datasets 66 → 71; LLM volume drops by roughly an order of magnitude versus whole-section extraction.
- Links: D-097, D-098, D-102, plan 12 ph4

### D-104 One CompanyCard schema per company, every field with evidence
- Status: accepted (user, 2026-11-07: "每个公司应该有自己独立的数据schema").
- Decision: every company has a record of the same schema, keyed by (ts_code, period), with a history of versions. The record holds: identity, profile, revenue_mix (→ product/service nodes, mapping method), capacity, customers and suppliers (rank, name or anonymous, amount, share, resolved / inferred / unknown counterparty), materials (share of cost, import dependence), peers (score and reasons), chain_position (upstream, downstream, revenue-weighted end-market exposure), dependence (overseas and North America share, key imports, export-control risk), valuation (plan 13) and evidence[]. Every field points to its evidence row (document, page, quote, source type, confidence, extraction method).
  - Storage: tables in schema `graph`, plus a generated `derived/graph/company_card/<ts_code>.json` per company that the view's dossier reads.
  - It is one uniform schema, not a database per company, so cross-company queries stay SQL.
- Vertical integration (user, 2026-11-07: "没有他自己的屠宰业务吗？"): revenue_mix keeps the elimination rows of the main-business breakdown (e.g. 牧原 "减：养殖与屠宰、肉食之间销售抵消" −458 亿, about equal to its 452 亿 slaughter revenue). The record stores the internal supply as an edge between the company's own products (live hogs → slaughter, amount), together with external revenue and an integration ratio (internal sales / downstream segment revenue). Segment shares are stated as a share of consolidated revenue and may sum to more than 100%.
- Freshness by field (user, 2026-11-07: "只有2025 annual report吗？现在应该有季报了"): every field takes its latest available source.
  - Top-5 customers and suppliers, competition and risks: the latest annual report (FY2025, filed Mar–Apr 2026; next in Apr 2027).
  - Business description, revenue mix by product and region, capacity: the latest semiannual or annual report (2026 H1) and `fina_mainbz` (through 2026-06-30).
  - Latest revenue and profit and the SSE 主要经营数据: Q3 2026.
  - Operating KPIs: monthly briefs.
  - The record keeps each field's period, so a reader sees how fresh it is. CNINFO is swept and downloaded in this order: Mar–Apr 2026 (FY2025 annual, 2026 Q1), Aug 2026 (H1), Oct 2026 (Q3), then the rest.
- Links: D-097, D-102, D-103, plan 12 ph6, plan 13

### D-105 Broker-report valuation extraction is plan 13
- Status: accepted as scope (user, 2026-11-07: "后续还需要加research paper是怎么做定价估值的"); plan 13 to draft after plan 12 phase 4.
- Decision: extract from Eastmoney stock reports (D-100), together with `report_rc`: valuation method (PE, PB, PS, EV/EBITDA, DCF, SOTP, PEG), multiple and target year, target price, WACC and terminal growth, comparable-company set (a further peer signal for D-102), segment-level volume, price and margin assumptions linked to taxonomy products, and dispersion across brokers. Results land in CompanyCard.valuation. Same rules as plan 12: section-first, rules before LLM, evidence on every field.
- Links: D-100, D-102, D-104, plan 12

### D-108 LLM operation: reasoning off, priced per call, every run on a cost ledger
- Status: accepted by execution (2026-11-07; user: "每次跑deepseek看一下cost是多少").
- Context: with reasoning on, `deepseek-flash` spent ~13k reasoning tokens on one report and truncated the JSON at max_tokens 6k (empty content, finish_reason "length"). The API accepts `thinking: {"type": "disabled"}`.
- Decision:
  - Extraction runs with reasoning off (`llm.thinking: false`) and `max_tokens` 8000; a truncated reply raises a clear error.
  - Prices live in `config/base.yaml` `llm.prices` (peak CNY per 1M tokens: flash 0.04 / 2 / 8 for cache-hit input / miss input / output; v4-pro 0.30 / 9 / 27; source api-docs.deepseek.com, 2026-11-07). Off-peak is half (Beijing time, outside 9–12 and 14–18 on weekdays).
  - `DeepSeekClient` computes the cost of every call. Each run appends a line (time, label, model, calls, tokens, cost) to `lake/meta/llm_usage.jsonl` and prints the run's cost.
- Results: phase-4a pilot, 10 annual reports, ¥0.157; plan-13 pilot, 28 broker reports, ¥0.200. Full-market estimate, one annual report per company: ≈ ¥86 off-peak.
- Links: D-098, plan 12 ph4, plan 13

### D-109 Broker valuation: implied multiple vs target multiple
- Status: accepted by execution (2026-11-07), plan 13 pilot.
- Context: in 28 reports on 10 companies, A-share brokers mostly state "当前股价对应 PE x 倍" (the multiple implied by today's price) and give no target price. Only HK and foreign brokers (招银国际, 交银国际, 东吴国际) gave target prices, with DCF or EV/EBITDA. Loss-makers are valued on PS (沪硅产业), hog farmers mostly on PE of the next year (10–14x), with cost-per-kg and volume assumptions.
- Decision: CompanyCard.valuation records `multiple_kind: implied_at_price | target` for every multiple, with its base year and the price date. Only `target` multiples and explicit target prices count as a broker's valuation view; implied multiples are kept as context. Industry induction reports both separately.
- Amendment (user, 2026-11-08: "光伏都在亏损，怎么还是p/e估值？"): when the nearest forecast year is a loss, a broker's PE is quoted on a later recovery year (e.g. 2027E/2028E). That is a recovery bet, not a normal multiple. Industry and product statistics therefore:
  - report implied PE per base year;
  - give the share of reports with a near-term loss and the share with no multiple at all;
  - add PB.
  The synthesis prompt must name the base year and call it a recovery bet. The 140 loss-heavy groups are re-synthesized with forecasts in the digests.
- Links: D-105, plan 13

### D-106 Sector-specific KPIs by Shenwan industry
- Status: accepted (user, 2026-11-07: "要加，按申万行业定义专属指标").
- Decision: `config/sector_kpis.yaml` defines, per Shenwan L1 sector and optional L2/L3 groups, the KPIs a company of that industry discloses. Each KPI has an id, name, unit, frequency, definition, sources and extraction keywords; format in the header of `config/sector_kpis.yaml`. Examples: hog farming (sales volume, full cost, average price, sows), banks (NIM, NPL ratio, provision coverage, CET1), batteries (GWh shipped, capacity, utilisation), baijiu (volume, price per tonne, distributors). CompanyCard gets a `sector_kpis` block of rows (ts_code, kpi_id, period, value, unit, evidence). Rules come first where the disclosure is formatted: monthly sales briefs (e.g. 生猪销售简报), regulatory-indicator tables, production and sales tables. The LLM handles the rest. Amendment (user, 2026-11-07: "但这些应该是研究报里读出来的"): the KPI set is read from broker industry reports; Opus's list is only a candidate seed (`origin: prior`).
  - Free step: per Shenwan industry, count metric phrases followed by numbers in industry-report text.
  - Small paid step: DeepSeek flash reads ~15 deep-dive industry reports per sector and extracts the tracked KPIs (name, unit, frequency, data source such as company announcements, an industry association or NBS, and the latest value).
  - Company side (user, 2026-11-07: "应该是broker report和报告一起决定吧"): the same counts over company filings, i.e. the annual-report 产销量 / 主要经营数据 sections and monthly operating briefs, give the share of peer companies disclosing each KPI.
  - Final set by both sides: tracked and disclosed → `core` (value from filings; broker figures as check and forecast); tracked only → `broker` (value from broker estimates or an external source such as an association or NBS, labelled estimated); disclosed only → `disclosed` (secondary field); neither → dropped.
  - Each KPI records `report_citations` and `disclosure_share`, with an example of each. Broker-versus-filing values for the same KPI feed plan 13's assumption checks.
- Links: D-103, D-104, plan 12 ph4, ph6

### D-107 Taxonomy merge: one owner per concept, decided by where the makers sit in Shenwan
- Status: accepted by execution (2026-11-07), as part of plan 12 phase 1.
- Context: the 31 sector files written in parallel had 445 name/alias clashes and lacked cross-sector links.
- Decision: a concept defined in two files is kept once, in the file of the Shenwan L1 sector where its main listed makers are classified, checked against `index_member_all`. The deleted id is recorded in `config/industry_chain/_merged_ids.yaml` (old → surviving), and every stored id is translated through it.
  - Electronic chemicals and semiconductor equipment → electronics. Exceptions: electronic resin, spherical silica and PI film stay in chemicals.
  - Battery chemicals and PV / lithium-battery equipment → power equipment.
  - Superalloys → nonferrous.
  - Satellites and BeiDou → defense.
  - Humanoid-robot parts → machinery.

  Ambiguous aliases were made specific (e.g. TPU芯片 / TPU弹性体). The format gains `upstream_of` → material, `substitute_for` product ↔ material and the relation `operates` (service → asset). 245 bridge edges were added; sector-crossing edges went from 269 to 607. A high-speed copper sub-chain (user request) has 5 sub-segments: conductor and insulation → Twinax → DAC/ACC/AEC with Retimer/Redriver chips → switch, AI server and rack. The merge script, decisions and log are under `quant_cn_lake/meta/runs/merge/` and re-run from the pre-merge backup.
- Result: 610 segments, 3,297 products and services, 78 materials, 36 technologies, 47 end markets, 7,697 edges; checker OK with 0 errors.
- Links: D-097, plan 12 ph1

### D-110 Download concurrency per source in config; one download per site at a time
- Status: accepted (user, 2026-11-07: "好，做成配置参数").
- Context: raising the Eastmoney industry-report download to 8 workers at 0.12 s spacing (~8–11 req/s, alongside the stock-report download) got HTTP 567 (Eastmoney's throttle) on ~250 requests in 4 minutes, and throughput fell. Fetching is network-bound, so threads per process suffice; the limit is the site, not CPU.
- Decision: `config/documents.yaml` sets `workers` and `min_interval_s` per source; the defaults of 4 and 0.25 s (~4 req/s) are the verified safe rate. `DocumentDownloader.run` builds its RequestPacer from the source; the CLI `--workers` only overrides. Only one download per site runs at a time, because the pacer limits a single process. Failed downloads stay in the manifest as `failed` and are retried on the next run.
- Follow-up (same day): the 567s continued after the fast run stopped. pdf.dfcfw.com blocked our IP for single requests, while the list API still answered. Per-worker retries kept hitting the block. Sources now also set `throttle_codes` (default 429, 567) and `cooldown_s` (default 900 s). On a throttle reply `RequestPacer.record_throttle` pauses every worker. Eastmoney is set to 3 workers at 0.3 s. A resume script probes every 10 minutes and restarts the Eastmoney downloads once the block lifts.
- Links: D-101, plan 12 ph2

### D-111 CNINFO: a query reaches ~3,000 rows; sweep by category and keyword, split above the cap
- Status: accepted by execution (2026-11-07).
- Context: CNINFO answers every page after ~101 with the same rows, so one query yields at most ~3,000 rows. The FY2025 annual-report listing for April returned 3,000 of 8,913 rows; the gap showed as only 3,200 annual reports for ~5,400 companies. On peak days a single day is far above the cap. 2026-04-29 had 26,066 announcements: 9,088 in SZSE main board alone and 12,834 in 日常经营 alone. Whole-day sweeps of every announcement therefore silently lose data on the days that matter.
- Decision:
  - `CninfoClient` checks `totalAnnouncement`. Above `MAX_ROWS` (3,000) it splits the date range in halves down to one day, then one day by board (`szmb`, `szcy`, `shmb`, `shkcp`, `bj`, a partition of the market). Whatever is still beyond the cap is logged, never silently dropped.
  - `cninfo_announcements` is swept by month × category: periodic reports (年报, 半年报, 一季报, 三季报), 首发 and 增发. Each stays under the cap per day.
  - The new `cninfo_keyword_announcements` is swept by month × title keyword: 投资者关系活动记录表, 重大合同, 中标, 问询函, 重组报告书, 对外投资, 可行性研究报告. It has its own document source `cninfo_kw` (same title rules, same `documents/cninfo/` folder).
  - The whole-day raw files fetched before this change are kept and deduplicated by the primary key.
- Consequences: far fewer requests than whole-day sweeps; complete periodic reports; announcement types outside these lists are not collected (a deliberate scope, D-102).
- Links: D-096, D-101, D-102, plan 12 ph2

### D-112 Business model as archetypes with revenue-driver trees
- Status: accepted (user, 2026-11-07: "可以，开始做商业模式的第一步"); design plans/architecture/BUSINESS_MODEL_DESIGN.md v0.3.
- Decision: CompanyCard gets a `business_model` block built per revenue segment.
  - Each segment gets one of 12 archetypes, from commodity producer and processing spread through regulated utility to financial balance sheet. The archetype fixes the revenue-driver formula, who sets the price and the profit hinge.
  - Drivers are sector KPI ids (D-106), so filed actuals, IR figures and broker assumptions (plan 13) land on the same node.
  - Further blocks: cost structure, pricing and pass-through, customers and channels, supply, capital intensity, cyclicality (price exposures), growth (capacity under construction) and integration.
  - Rules come first: 营业成本构成, 分销售模式, 分地区, top-5 and fina_indicator. The LLM handles pricing and pass-through, as fields added to the existing business-section call.
  - The SW L3 → archetype defaults are an Opus prior in `config/business_models.yaml`, spot-checked by the user.
  - Config `config/business_models.yaml` (2026-11-07) holds 12 archetypes and 68 variants, with signals readable from filings, and maps 346 SW L3 codes (145 with a secondary archetype, 110 with a note on debatable defaults). 1,349 driver roles link to 716 of the 728 sector KPI ids, and a role may list several KPI ids. Common roles usable under any archetype are listed in the file header: revenue, margin, overseas_share, rd_ratio, customer_concentration, receivables, capex, and others.
  - Operating-mode variants (user: "每个行业其实他们的商业模式也有不太一样"): each archetype lists variants with filing signals, such as integrated vs 公司+农户, ODM vs own brand, or direct vs distributor. Each company's segment gets archetype + variant from its own 经营模式 text and rule signals. The SW L3 map is only a default, and peers and the cycle clock compare on archetype + variant.
  - v0.3 adds (user: "补上吧") binding point-in-time history for every label; accounting-quality flags; governance and capital allocation; competitive structure (CR5/HHI per product); driver sensitivities linked to lake price series; and a validation bar per label type.
  - v0.2 adds four judgements (user: "扩张期，运营期，收缩期…clock…是否会继续长期存在…护城河"): company lifecycle, from capex/depreciation, 在建工程 and capacity text; cycle clock, from demand, margin and capex at industry and product level, with broker narratives as a check; durability, from demand trend, substitution, regulation, cost position and balance sheet; moat, where 核心竞争力 claims are tested against ROIC persistence, relative margins, price premium and share.
- Links: D-097, D-102, D-103, D-104, D-106, plan 12 ph6, plan 13

### D-113 Industry valuation cards and reverse-engineered parameters
- Status: accepted (user, 2026-11-07: "research中要看行业倾向用什么估值方式，给什么multiple，参数我们是否能反推").
- Decision: plan 13 phases 4–5.
  - **Industry valuation cards.** Method mix comes from report extraction. Multiples per base year, PEG, upside and broker dispersion come from `report_rc`, whose target price is `max_price` / `min_price`; `tp` is total profit in 10k CNY, per DATA_CATALOG. Each card lists the KPIs the assumptions bet on, linked to sector_kpis ids.
  - **Implied parameters.** For mature archetypes, a single-stage PB-ROE / Gordon model gives the implied required return. For growth archetypes, the required return comes from CAPM (lake yields and prices), and a two-stage model gives the implied high-growth duration and terminal growth.
  - **Market vs broker.** Both are computed at the target price and at the market price, which shows how far broker optimism runs and where it sits (growth or required return).
- Evidence: the prototype single-stage implied r was 4% for 计算机 and 12% for 银行, so one model does not fit both.
- Links: D-105, D-106, D-109, D-112, plan 13

### D-114 Consensus and forward multiples are a core lake dataset
- Status: accepted (user, 2026-11-07: "还有forward pe吗？这个应该是整个架构的一部分", "research report应该可以读这些").
- Decision: a `ConsensusStep` (pipeline, per year like UniverseStep) materialises `derived/consensus/year=YYYY`, one row per stock and session, using the FACTOR_LIBRARY §3b rules.
  - Each broker's latest forecast within a trailing 90-day window counts once. Reports become usable the session after `report_date`.
  - Each row holds FY1–FY3 EPS, net profit and revenue (median, mean, n_brokers, dispersion), NTM EPS (time-weighted FY1/FY2), the median target price (`max_price`/`min_price`; never `tp`) and the mean rating.
  - The view `derived.forward_valuation` adds forward EP (primary, safe for losses), forward PE (display), forward PEG, implied upside and forward PB from forecast ROE. It also carries coverage and dispersion flags.
  - Sources: `report_rc` first; PDF-extracted forecasts (plan 13) fill brokers missing from report_rc and cross-check it.
  - Consumers: industry valuation cards, implied parameters, CompanyCard, and plan 07's revision factors.
- Prototype (2026-09-30): 2,242 stocks covered (1,231 with ≥ 3 brokers). Forward PE 中际旭创 16.5, 宁德时代 11.8, 恒瑞医药 30.8. Industry medians range from 军工 46 to 银行 6. 天岳先进's dispersion of 1.16 shows why the flag is needed.
- Links: FACTOR_LIBRARY §3b, D-105, D-109, D-113, plan 13 ph6, plan 07


### D-115 Revenue lines map to taxonomy nodes by rules with Shenwan context
- Status: accepted (user, 2026-11-08: "做产品分类，提高产品映射率").
- Decision: `ProductTaxonomy` loads config/industry_chain (names and aliases always strings, merged ids, `sw_l3_map`). `ProductMatcher` maps each 主营构成 line, without the LLM, as follows.
  - Generic lines (其他, 投资收益, 抵销, ...) map to nothing and leave the denominator. Sub-lines of a reported parent line ("利息净收入：利息支出：...") are dropped.
  - Names are normalized: parentheses and suffixes (收入/业务/产品/类) are removed, and the leaf of "A：B" is tried before the top level.
  - Each label is scored: exact 1.0; contains 0.6–0.9 (a line inside a label only with 3+ characters and half the label); bigram overlap only inside the company's Shenwan context. In-context labels get +0.2, and the threshold is 0.55.
  - A compound line is split when two or more parts match.
  - Last resort: a company whose Shenwan codes map to one root segment gets that segment, marked `how: sector` (low confidence).
- Result (FY2025, 5,639 companies): non-generic lines mapped rose from 27% to 78.5% (54% without the sector fallback). Companies with ≥ 50% of revenue mapped rose from 1,805 to 4,477.
- Known limits: rules still mis-map some compound lines. An LLM pass over the unmatched and sector-only lines is the next step, after a cost estimate.
- Links: D-097, D-102, D-107, plan 12 ph1/ph4

### D-116 Web app: React front end, read-only Go API, logic stays in Python
- Status: accepted (user, 2026-11-08: "前后端我们定了吗？可以用go来做后端，前端用react", then "现在本地demo"). Local only for now.
- Decision:
  - The front end is React + TypeScript (Vite, Cytoscape.js).
  - The back end is a read-only Go API (go-duckdb over `derived/graph/*.parquet`) with one OpenAPI contract.
  - All extraction, matching, statistics and business rules stay in Python: `GraphExportStep` writes the tables and Go only serves them.
  - One local binary embeds the built front end.
- Alternatives:
  - Python FastAPI back end (rejected by the user's preference for Go; it would also mix serving into the analysis package).
  - Business logic in Go (rejected: duplicates tested Python classes, CLAUDE.md "never duplicate").
  - Keep the single-file artifact (rejected: 56 MB of JSON, no server-side search, hard to maintain).
- Consequences: a standards addendum for Go and TS before any code; caches kept off the exFAT volume; `make check` gains `app-check`.
- Links: plan 15, D-099, D-104, D-115

### D-117 Income statement keeps the expense lines
- Status: accepted (user, 2026-11-08: "细节表里也显示一下净利润吧，还有其他相关的expense").
- Decision: `income_vip` also stores `total_revenue, sell_exp, admin_exp, fin_exp, biz_tax_surchg, assets_impair_loss, credit_impa_loss, n_income, minority_gain, non_oper_income, non_oper_exp`. The dataset is re-downloaded from 2016 with `--force`, so every period carries the new columns. Primary key and `known_on` are unchanged.
- Consequence: the company financial table (chain view and app) shows FY2023–FY2025 revenue, gross profit, the four expense lines with ratios, impairments, operating profit and net profit attributable. The ratios are computed in Python.
- Links: D-092, D-104, plan 15

### D-118 Pricing power and the posterior archetype check are measured, not assumed
- Status: accepted (user, 2026-11-08: "我们有判断他们是price taker还是price maker吗？定价权", "商业模式有后验结果了吗？", then "ok" to the design and to the DeepSeek 经营模式 reading at about ¥35–45).
- Decision:
  - Pricing power per company (and per segment) comes from six measured signals: GM level, GM stability, cost pass-through against a futures input-cost index, output-price exposure, market share, and margin through the cycle. One text signal adds quarterly notes plus a DeepSeek reading of the annual 经营模式 text.
  - The rule is 3 of 6 signals with no contrary signal. Output: maker / middle / taker / insufficient, with reasons and evidence (BUSINESS_MODEL_DESIGN §4.5).
  - Each archetype gets expected signatures; every company is checked against them, and mismatches go to a review queue (§4b.7).
  - New config `config/material_prices.yaml` maps material nodes to futures contracts for the input-cost index.
- Alternatives:
  - The archetype default pricing mode alone (rejected: it is a prior, the question is the posterior).
  - LLM judgement alone (rejected: not testable).
- Cost: rules ¥0. The DeepSeek 经营模式 reading (variant, 定价方式, 成本传导, price actions) of FY2025 annual reports is about ¥35–45 off-peak and runs only after a cost confirmation.
- Links: D-104, D-106, D-112, BUSINESS_MODEL_DESIGN §4.5, §4b.7, plan 12 ph6

### D-119 Tushare `research_report` replaces the Eastmoney list for new days; coverage comes from `report_rc`
- Status: proposed (2026-11-08; user opened the `research_report` permission, awaiting the call).
- Context: D-096/D-100 chose the Eastmoney list API because `research_report` was denied. Probe on 2026-08-25: `research_report` 208 rows (165 stock, 43 industry), PDFs at `pdf.dfcfw.com` (same source); Eastmoney list 164 stock reports. Neither carries 华泰/中金/招商 PDFs. `report_rc` that day: 584 distinct stock reports (code, org, title) from ~90 brokers; only 76 (code, org) pairs overlap with `research_report`.
- Decision: from approval on, fetch report lists and PDF links from `research_report` (official API, `ts_code` and `ind_name` included); keep existing `em_*` files and documents unchanged. Analyst coverage and consensus are measured from `report_rc` (forecast rows of every report, PDF or not), never from PDF lists.
- Alternatives: keep the Eastmoney scraper (rejected if approved: duplicate source, scraping fragility and site terms); fetch both (rejected: duplicate rows of the same reports).
- Consequences: a `research_report` dataset (trade_date sweep) in plan 11 ph11; `em_stock_reports` / `em_industry_reports` stop at the switch date (`end:` in config); `DocumentDownloader` reads URLs from the new dataset; plan 13 notes that PDF text covers about a quarter of reports.
- Links: D-096, D-100, plan 11 ph11, plan 12 ph2, plan 13
