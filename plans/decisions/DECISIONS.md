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
- Decision: `src/quant_cn/factor/` at L5 owns `BaseFactor`, the factor library (`factor/library/<name>_factor.py`, one class each), `FactorPreprocessor`, `FactorEvaluator`, `SignalCombiner`, `FactorFactory`. `statistic` (L4) keeps generic, factor-agnostic math (`Winsorizer`, `Standardizer`, `Neutralizer`, `ICCalculator`, `QuantileReturns`, `ReturnStats`, `CrossSectionalRegression`) and never imports `factor`. `pipeline` moves to L6 because `FeaturePipeline` runs factors; `back_testing`/`portfolio`/`visualization` become L7, `cli` L8.
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
- Decision: `statistic` gains `ICCalculator`, `HacVariance`, `BlockBootstrap`, `ICSignificance` (Newey-West t on mean IC, block-bootstrap CIs, Pesaran-Timmermann, sub-period/regime consistency, Bai-Perron break, decay), `MultipleTestingAdjuster` (Holm, Benjamini-Hochberg-Yekutieli, Romano-Wolf; Harvey-Liu-Zhu t ≥ 3 hurdle), `DataSnoopingTest` (White Reality Check, Hansen SPA), `DeflatedSharpe` (PSR/DSR, minimum backtest length), `BacktestOverfitting` (CSCV PBO), `SharpeRatioTest` (Ledoit-Wolf), `TrialLog`. Acceptance into `factor/library/` = FACTOR_TESTING_DESIGN §6. Built in plan 04 phase 2 (core set) and later phases (backtest-level tests).
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
