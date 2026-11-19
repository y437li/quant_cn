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
- Status: proposed with plan 12 (2026-11-07); provider, endpoint and default model superseded by D-122 (2026-11-11).
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

### D-120 Watchlist targets live in a git-ignored config file; the app stays read-only
- Status: accepted (2026-11-08, user "ok" to plan 15 phase 7).
- Context: plan 15 keeps the Go API read-only and every number in Python (D-116). A watchlist needs user-owned targets (buy range, thesis) and daily prices.
- Decision: targets in `config/local.watchlist.yaml` (matches the existing `config/local.*.yaml` ignore rule; `config/watchlist.example.yaml` committed); Python `WatchlistBuilder` computes gap, status and valuation at the buy price into `watchlist.json`; Go serves it at `GET /api/watchlist`; React shows it. Targets change by editing the file or asking Claude.
- Alternatives: a write endpoint to edit targets in the page (rejected for now: breaks D-116, needs storage and validation in Go); targets committed in `config/` (rejected: personal positions in git history); keep the claude.ai artifact (rejected by the user).
- Consequences: plan 15 phase 7; `make watchlist`; the page shows data as of the last refresh, not live quotes.
- Links: D-116, plan 15 ph7

### D-121 Opportunity discovery is a PIT pipeline: priced-in expectations, screens validated by replay, source-tagged deep dives
- Status: accepted (2026-11-09, user "都行" to plan 16 v2; v1 text replaced before any approval).
- Context: the 2026-11-09 rounds showed that industry labels do not find ideas. YoY alone misleads (memory modules), and low PE at peak margins is a trap (周期股卖便宜买贵). "Cheap" must be replaced by "priced in": aluminium at PE 6.4 already pays for about 7.6 years of excess profit. Agents used different profit bases, and 4 of 17 checked numbers needed correction.
- Decision:
  - Discovery runs on a PIT company cycle panel (QoQ and YoY, deducted profit, 10-year median and max margin) and on daily market-implied expectations: years priced over three fixed bases, the commodity price implied against the futures curve, and reverse DCF.
  - Screens are rules in `config/discovery_rules.yaml`, ranked by the gap between what is priced and the evidence. They are frozen before a replay from 2019 and shown as `validated` (t ≥ 2) or `descriptive`.
  - Deep dives use versioned briefs; every claim is tagged [自算/研报/新闻/假设], and [自算] claims are rechecked against the lake.
- Alternatives: industry-label pipeline (v1, rejected: describes, does not discover); LLM judgement without tags (rejected: unverifiable); a single "normal earnings" base (rejected: drives opposite answers).
- Consequences: plan 16 v2 classes (`CompanyCyclePanel`, `FuturesCurve`, `ImpliedExpectations`, `IdeaScreener`, `ClaimVerifier`, `DiscoveryReplay`, `DiscoveryStep`); new `config/discovery_rules.yaml`; app page 机会发现.
- Links: BUSINESS_MODEL_DESIGN §4.2, §4b.4–4b.6; D-112, D-118; plan 16

### D-122 LLM extraction runs on Volcengine Ark Coding Plan, model pinned to deepseek-v4-1-flash
- Status: accepted (2026-11-11, user "改一下" after a live test of the new key).
- Context: the user replaced the DeepSeek direct key with a Volcengine Ark Coding Plan key (`ark-…`), which api.deepseek.com does not accept.
- Decision: `llm.url` = `https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions`; default model `deepseek-v4-1-flash` (pinned, not the moving alias `ark-code-latest`, so the prompt-hash cache stays one model); `deepseek-v4-pro` stays available on the same plan. Key still from env `DEEPSEEK_API_KEY`; `DeepSeekClient` unchanged (same OpenAI-compatible payload, `thinking: {type: disabled}` and JSON mode verified on 2026-11-11). Prices set to 0 because the plan is a flat subscription.
- Alternatives: `ark-code-latest` (rejected: model can change under the cache); Ark pay-per-use `/api/v3` (not chosen: user holds a Coding Plan key); keep DeepSeek direct (rejected: user switched keys).
- Consequences: cached replies under `deepseek-flash` are not reused (cache key includes model); logged `cost_cny` reads 0; plan rate limits and terms of use apply to bulk extraction and are the user's to check; the rest of D-098 (extractor/validator split, Opus review) stands. Amendment 2026-11-11: `llm.peak_hours: []`, so the run scripts' off-peak wait no longer blocks daytime runs.
- Links: D-098, plan 12 ph4

### D-123 Peers come from labeled evidence and replace SW L3 in peer comparisons
- Status: accepted (2026-11-11, user approved plan 17).
- Context: peer comparisons (GM rank, pricing power, moat) use Shenwan L3, which mixes chain stages; D-102's `GraphQuery.peers` was never built. Labels now cover product mix (83% of companies with a cosine ≥ 0.5 peer), business mode (94%), broker comparables (17%, 3,813 pairs) and named competitors (476 resolved mentions).
- Decision: score company pairs from these signals with config weights and a chain-stage penalty, keep the reason per pair, cluster within chain stage into named peer groups, and use the groups instead of SW L3; companies with weak evidence fall back to SW L3 and are flagged. Quality is measured on broker pairs named in ≥ 2 reports, held out of the evidence.
- Alternatives: SW L3 only (rejected: mixes upstream and downstream); product cosine only (rejected: mapping errors pair equipment makers with their customers); LLM judges every pair (rejected: unverifiable, O(n²)).
- Consequences: plan 17; `GraphQuery.peers` moves from plan 12 ph6 to plan 17; groups are a snapshot (`as_of`), not PIT, so factor backtests must not join them historically.
- Links: D-099, D-102, D-118, D-122, plan 12 ph6, plan 13, plan 17

### D-124 Company guidance is tracked as quote-checked PIT items matched to first-known actuals
- Status: accepted (2026-11-11, user approved plan 18).
- Context: the lake has earnings previews (`forecast_vip`, 84.1% of 2026 H1 actuals inside the range) but no forward statements; business plans, IR records and incentive targets sit in CNINFO PDFs.
- Decision: one item table (company, source, metric, period, value or range, kind target / expectation / commitment, quote, page, `known_on` = ann_date next session). LLM labeling runs on the Ark API (D-122) and every item is quote-checked. Outcomes use the first actual known after the item, never a restated value. Credibility per company = hit rate and mean bias with n.
- Alternatives: previews only (rejected: not forward-looking); LLM summary of "management tone" (rejected: unverifiable, not matchable to actuals); latest restated actuals (rejected: look-ahead).
- Consequences: plan 18; new CNINFO keyword 股权激励 and doc type `incentive_plan`; periodic-report rules exclude 问询函 / 回复; `SectionDetector` gains the 经营计划 section; the Q&A datasets must be brought current. Amendment 2026-11-11 (user): contracts, bid wins and operating-data announcements are tracked the same way (`ContractItem`, quote-checked, `known_on` = ann_date); backlog = announced, unrecognised value / trailing revenue.
- Links: D-102, D-105, D-122, plan 12, plan 13, plan 16, plan 18

### D-125 Label backfill runs one fiscal year at a time into per-year staging, period taken from the title
- Status: accepted (2026-11-11, user: "我们可以补齐老数据的label" → "we can do it year by year").
- Context: labels cover only the latest period (FY2025 annual, 2026 H1, 2026 Q1/Q3, broker reports of the last 12 months) while FY2023–FY2024 annual reports, 2024–2025 interim reports and 37k older broker reports are downloaded or listed. `applications_full.py` labels every PDF in a folder as the current period, and `business_modes` / `moat_claims` rows carry no period, so appending history to the current files would mix years.
- Decision: `meta/runs/backfill_annual.py <FY> <stage>` selects reports from the manifest by the title's fiscal year (latest version per company), reuses AnnualReportParser, ApplicationExtractor, BusinessModeExtractor and MoatExtractor unchanged, writes `meta/runs/backfill/fy<FY>/{parse.parquet, applications, business_modes, moat_claims}.jsonl` with `period` on every row, on Ark (D-122). Order: FY2024, FY2023 annual; broker stock reports 2023-11 → 2025-10 (download, then ValuationExtractor); 2024–2025 interim reports. Industry reports need a new extractor and a plan change first.
- Alternatives: append to the current files (rejected: mixed years, period bug); one big run over everything (rejected by the user: year by year lets each year be checked before the next).
- Consequences: the current FY2025 files stay the source of the chain view; the per-year files become the history that plan 15 ph2 (`GraphExportStep`) and plan 17 / 18 read; the old `applications_full.py` must not be rerun without a title-year filter.
- Links: D-098, D-118, D-122, plan 12 ph4, plan 13 ph3, plan 17, plan 18

### D-126 National-team positioning is proxied by per-index ETF AUM and split-proof net flows
- Status: accepted (2026-11-11; user: "他们的合算是国家队的持仓", "各个指数的etf proxy", "但基本国家队有那么大的力量", "要track一下", "可以每天track吗？"). The 11 core ETFs are the proxy, the rest are shown as other money; position is measured at the current price of each index's reference ETF so price moves do not read as trading; refreshed daily by launchd.
- Context: 汇金/证金 buy and sell the market mostly through the big broad-index ETFs (510300, 510310, 510330, 159919, 510050, 510500, 512100, 159915, 588000, ...). Their exact holdings are disclosed only twice a year, but ETF shares are daily (`fund_share`). On the lake: 143 such ETFs hold 13,114亿 on 2026-11-06; flows were +9,608亿 in 2024, −17,966亿 in 2026H1 and +5,418亿 since 2026-10-01.
- Decision: one proxy per index (沪深300, 中证A500, 上证50, 中证500, 中证1000, 创业板指, 科创50) plus the total. Members are listed, non-feeder, non-enhanced ETFs that track 100% of the index, mapped by rule and committed in `config/etf_proxies.yaml`. Net flow = AUM_t − AUM_{t−1} × close/pre_close, so share splits and consolidations do not count as flows. 沪深300 is the benchmark for the watchlist stocks.
- Alternatives: a single largest ETF (510300) as the index (rejected by the user: the sum is what the national team holds); Δshares × close (rejected: 159845 2022-08 and 512100 2022-09 consolidations show up as fake flows); index levels from index_daily alone (rejected: no positioning signal).
- Consequences: the proxy measures all holders, not just the national team, until disclosed holder data (plan 11 ph11) is joined in; `make watchlist` also refreshes fund_daily and fund_share; `fund_share` lags `fund_daily` by a few days (2026-11-06 vs 11-11).
- Links: D-120, plan 15 ph7b, plan 11 ph11, plan 06b

### D-128 US market sensitivity: S&P 500 partial beta from Tushare index_global, gated style
- Status: accepted (2026-11-11, user: "这里面要加美股s&p的factor", "spx only"); gate passed the same day (adj R² 0.2711 vs 0.2695, bias stats in band), so the default model is `cne5_v2_spx`.
- Context: A-shares open after the US close, so the overnight S&P 500 move is a common shock that country, industry and Beta may not fully absorb; RISK_FACTOR_LIST §4b planned macro betas behind the v3 gate but no US series was in the lake (FRED blocked on its key, plan 11 ph6).
- Decision: dataset `index_global` (Tushare, SPX from 2015, `known_on_rule: next_session`). Descriptor `us_beta` = the S&P coefficient of a 252-session (half-life 63) weighted regression of the stock's China close-to-close return on the China cap-weighted market and the S&P return of every US close dated in [previous China session, session), compounded; style `us_sensitivity` in `config/risk_model.yaml`, entering the default only if median adjusted R² rises and random-portfolio and benchmark bias stats stay in [0.85, 1.15] against `cne5_v2`.
- Alternatives: FXCM `SPX500` already in fx_daily (rejected: history only from 2022-07, bar dates shifted one day, weekend bars); a raw (not partial) S&P beta (rejected: mostly re-measures China Beta, as the overnight S&P return correlates with the next China market return); Nasdaq / Hang Seng too (user: SPX only).
- Consequences: `PriceDescriptors.compute_partial_beta`, `DescriptorBuilder.compute_overnight_return`; configured as an `external_series` entry (generalised the same day for D-134 / D-130: `ExternalSeriesSpec`, `ThemeBasketSpec`, `RiskInputs.external` / `themes`); `make download` gains index_global; plan 05 phase 7.
- Links: D-061, D-127, RISK_FACTOR_LIST §4b, plans/execution/05_risk_model.md ph7

### D-129 CNINFO periodic-report list starts 2023-01-01 (FY2022 annual and 2023 interim reports)
- Status: accepted (2026-11-11, user "可以" to extending the history; follows D-125 year-by-year backfill).
- Context: `cninfo_announcements` started 2023-11-01, so the lake holds only ~100 FY2022 annual reports and ~60–120 of each 2023 Q1 / H1 / Q3 report, while FY2023–FY2025 are complete. Three-year comparisons of business mix, business mode and moat need a full 2023 year.
- Decision: `cninfo_announcements.start` = 2023-01-01. The keyword dataset (`cninfo_keyword_announcements`: IR records, contracts, inquiry replies …) keeps 2023-11-01 for now. PDFs for doc types annual, semiannual, q1, q3 published in 2023 are downloaded after the FY2023 label backfill finishes, then labelled with the same per-year staging as D-125 (period from the title).
- Alternatives: keep 2023-11 (rejected: no FY2022 / 2023 interim history); extend the keyword dataset too (deferred: larger download, less needed for the year comparison).
- Consequences: about 20k more PDFs and the CNINFO request load that comes with them; interim-report labelling needs a title-period script like `backfill_annual.py` (applications for semiannual, QuarterlyNoteExtractor for Q1/Q3).
- Links: D-111, D-125, plan 12 ph2 / ph4


### D-132 Factor monitor and holdings risk are daily app pages fed by the stored risk frames
- Status: accepted (2026-11-12, user "ok"; plan 15 ph7c / ph7d).
- Context: the user wants each factor's daily return and volatility recorded, and the risk exposure of their real holdings. The risk model already stores daily factor returns and covariance (D-127); `make risk-model` is a full refit (≈ 12–20 min).
- Decision: no new model math. `FactorMonitorBuilder` turns `derived.risk_factor_return` / `risk_factor_cov` into `factor_monitor.json` (returns over windows, forecast vol, realized vol, σ-move). Holdings live in git-ignored `config/local.positions.yaml` (same rule as D-120); `HoldingsRiskBuilder` reuses `RiskModel.load_snapshot` + `RiskDecomposer` against 沪深300 into `holdings_risk.json`, and appends each day's positions and risk decomposition to the lake (`derived/holdings/{positions,risk}`, partition per date, replaced on rerun) so history accumulates outside git; the YAML stays the only input. Both are served read-only by Go and run in `make track-daily` after a full `risk-model` refit.
- Alternatives: an incremental risk-model step (deferred: bigger change, refit fits in the evening window); positions in the claude.ai artifact or committed config (rejected: personal data, D-120); computing factor stats in Go / TS (rejected: D-116).
- Consequences: the daily job runs ≈ 25 min longer and holds the DuckDB write lock during the refit; pages show the last close, not live quotes.
- Links: D-116, D-120, D-126, D-127, plan 05, plan 15 ph7c / ph7d

### D-133 External sensitivities: Arm, gold, US 10y yield and crude oil as gated styles
- Status: proposed (2026-11-12, plan 05 ph8 (d)–(g); user: "把arm也加进去吧", "还有原油,美国的利率，以及黄金的sensitive").
- Context: the user wants exposure to Arm (Nasdaq ARM) in the risk model and the factor monitor (plan 15 ph7c). The model already has an overnight S&P 500 partial beta (D-128) built from the generic `external_series` mechanism.
- Decision: add dataset `us_daily` (Tushare; ARM only), drop the IPO-day row, and add `{descriptor: arm_beta, dataset: us_daily, code: ARM}` to `external_series` with style `arm_sensitivity` = partial beta on the last ARM return before the China session, China market controlled (252 d, half-life 63). Same mechanism for gold (XAUUSD.FXCM, +1 day), the US 10-year yield (`us_tycr` y10, new kind `level` = daily change, next China session) and crude (INE SC main contract from `fut_daily`, same day; FXCM USOil/UKOil end 2023-06-01). Each enters the default model only if it passes the phase-7 gate (adjusted R², bias stats) against the current default.
- Alternatives: a theme basket of A-share Arm-ecosystem names (rejected for now: membership is a judgement call, and the user asked for Arm itself); the SOX index (not requested; can be a second series later).
- Consequences: exposures exist only from ≈ 2024-09 (ARM listed 2023-09-14, 252-day window); before that the style is absent, not zero. One more Tushare dataset to refresh daily.
- Links: D-127, D-128, plan 05 ph8, plan 15 ph7c

### D-134 USD sensitivity style from USDCNH (FXCM bars shifted one day)
- Status: accepted (2026-11-11, user request "美元因子" via session quant-cn-5c; default chosen by the user's "ok" to the recommendation).
- Context: CNY moves separate exporters (USD revenue, e.g. TiO2) from USD-cost / USD-debt names; USDOLLAR in fx_daily starts only 2022-07.
- Decision: `usd_beta` = partial beta of the China-day-t return on the USDCNH.FXCM bid-close change over [previous session, session), China market controlled (252 d, half-life 63); FXCM dates a bar by its open, so `date_shift_days: 1`. Style `usd_sensitivity` in the default. Gate vs `cne5_v2_spx` (2019→2026, alone): median adj R² 0.2727 vs 0.2711; random portfolios 100% in band (median 1.018); CSI 300/500/1000 0.933/1.081/1.044; own bias 1.075.
- Alternatives: USDOLLAR (rejected: history from 2022-07); onshore CNY fixing (not in the lake).
- Consequences: `ExternalSeriesSpec` entry in `config/risk_model.yaml`; plan 05 phase 8; combined `cne5_v3` numbers in D-131.
- Links: D-128, plans/execution/05_risk_model.md ph8

### D-130 AI / data-center sensitivity is a monitor style, not a model factor
- Status: accepted (2026-11-11, user: "AI/数据中心因子可以monitor", "单独展示").
- Context: the 885887.TI 数据中心(AIDC) basket beta is the strongest new style (daily mean |t| 5.4, 6.9 in 2026; adj R² 0.2756 vs 0.2711 alone) but raised under-forecasting (random-portfolio median bias 1.019 → 1.044, CSI 500 1.08 → 1.11), and `ths_member` is a 2026 snapshot without in/out dates, so history before 2025 carries hindsight.
- Decision: `ThemeBasketSpec` (circ_mv-weighted members excluding the stock, from the 2020-03-06 list date) feeds `aidc_beta`; style `ai_dc_sensitivity` is a `monitor_styles` entry: exposures in RISK_EXPOSURE and daily returns from the regression re-run with the style added (`FactorReturnEstimator.compute_monitor`), written to `derived/reports/risk_<name>/monitor_returns.parquet` and shown in its own notebook section; not in FACTOR_COV, SPECIFIC_RISK or any risk forecast. Revisit as a model style after the USE4 NW-lag fix.
- Alternatives: model style now (rejected: worse bias, hindsight); drop it (rejected: the user wants it tracked).
- Consequences: monitor regressions double the regression time of `make risk-model` (~+1 min).
- Links: D-061, D-128, plans/execution/05_risk_model.md ph8

### D-131 Free-cash-flow yield as its own style, not inside Earnings Yield
- Status: accepted (2026-11-11, user request via session quant-cn-5c; default per the recommendation the user accepted).
- Context: OCF and FCF diverge for heavy-capex names (钛白粉, express, coal); FCFP = (TTM n_cashflow_act − TTM c_pay_acq_const_fiolta) / mcap, PIT through `read_fundamentals_pit`.
- Decision: style `cash_flow_yield` (FCFP, orthogonalised to earnings_yield and book_to_price) in the default. Gate alone vs `cne5_v2_spx`: (A) own style adj R² 0.2714 vs 0.2711, bias stats unchanged, median factor |bias − 1| 0.054 vs 0.057 — passes, marginally; (B) FCFP inside earnings_yield (0.44 / 0.23 / 0.33) 0.2707 — fails, rejected.
- Alternatives: variant B (rejected by the gate); leave out (rejected: passes and isolates the capex effect).
- Consequences: `c_pay_acq_const_fiolta_ttm` read with the other TTM fields. Combined default `cne5_v3` (with D-134), live run 650d1711f7fe: median adj R² 0.2732 vs 0.2711, last-year 0.3012 vs 0.2985, random portfolios 100% in band (median 1.018), median factor abs(bias − 1) 0.054, CSI 300/500/1000 0.934/1.082/1.046; own bias cash_flow_yield 0.989, usd_sensitivity 1.079.
- Links: D-061, D-127, plans/execution/05_risk_model.md ph8

### D-135 Scalable digests for the risk tables
- Status: accepted by execution (2026-11-11).
- Context: the exact digest (md5 of every row's text, ordered) failed on `derived.risk_exposure` (115.6 M rows with 13 styles): DuckDB out of memory at 32 GB.
- Decision: `DeriveStep.build_digests(views, scalable=True)` = "h:" + md5(row count | sum | xor of a 64-bit hash of every row's text), order-independent; 3.9 s and 0.5 GB on 115.6 M rows. `RiskModelStep` uses it; every other view keeps the exact digest, so existing manifest values are unchanged.
- Alternatives: per-year exact digests (rejected: still materialises ~15 M rows of text per year); raise the DuckDB memory limit (rejected: shared catalog, 64 GB machine).
- Consequences: risk digests detect any change but are not byte-level proofs of order; rebuild comparisons still work.
- Links: D-094, D-127

### D-127 Risk model build choices (plan 05): reuse industry view, full seeded refit outside curate, monthly growth snapshots
- Status: accepted by execution (2026-11-11, user: "把A股版barra 做好"); open to review. (Re-added 2026-11-11 after the entry was lost in a concurrent rewrite of this file; text unchanged.)
- Context: plan 05 was approved with an `IndustryClassifier`, a per-date incremental `RiskModelStep` inside curate and six frames; building it on the real lake (5,000+ stocks, 2019→) needed concrete choices.
- Decision: (1) no `IndustryClassifier`: `derived.industry_l1.l1_grouping` via `ExposureReader` is the industry definition (D-071, D-093). (2) `make risk-model` refits the whole history (exposures, factor returns and residuals per year; covariance and specific risk over the full history), seeded so reruns are byte-identical; it records digests but is not part of `curate`. (3) Growth descriptors (EGRO, SGRO) come from `StatementVersionReader` snapshots on each month-end session, held until the next one (PIT at the snapshot, at most one month stale); SGRO uses revenue, not revenue per share (a constant share count cancels in slope / mean). (4) A seventh frame `SPECIFIC_RETURN` keeps the residuals. (5) A style is left out of a session when less than `min_coverage` (50%) of the names have a raw value, so a style made only of filled values never enters the regression. (6) Descriptors are clipped iteratively at ±3 sd. (7) Covariances are daily variances with NW for a 21-day horizon; eigenfactor bias profile refitted every 21 sessions; R² is the weighted uncentred Barra R²; returns are total returns (no risk-free subtraction). (8) Default model `cne5_v2` = CNE5's ten styles without analyst descriptors (renormalised weights, RISK_FACTOR_LIST §1).
- Alternatives: incremental per-date fit inside curate (rejected: curate runs daily and the covariance / specific stages need the whole history; a full refit takes ~15 min); a new `IndustryClassifier` (rejected: duplicates `derived.industry_l1`); daily `StatementVersionReader` calls for growth (rejected: ~2,000 queries for a slowly changing descriptor).
- Consequences: `config/risk_model.yaml` holds every tunable; `derived/risk_{exposure,factor_return,specific_return,factor_cov,specific_risk}` + `derived/reports/risk_<name>/validation.parquet`; `portfolio` / `back_testing` read the frames; import-linter layer 5 now lists `quant_cn.factor | quant_cn.risk`. Later defaults: `cne5_v2_spx` (D-128), `cne5_v3` (D-131, D-134).
- Links: D-045, D-061, D-071, D-093, plans/execution/05_risk_model.md, RISK_MODEL_DESIGN

### D-136 Morning e-mail report sent over Gmail SMTP with an app password
- Status: accepted (2026-11-13; test send OK, layout approved; two e-mails per day: 持仓监测 and 机会清单).
- Context: the 因子监控 / 持仓 / 观察账本 pages only exist on this Mac. The user wants the same facts in their inbox each morning, in Chinese, laid out for a desktop mail client. No mail connector is available in this environment.
- Decision: Python `MorningReportBuilder` renders one e-mail-safe HTML (tables + inline styles, no scripts or external images, 960 px desktop layout) from factor_monitor.json, holdings_risk.json and watchlist.json; `MailSender` sends it with `smtplib` over smtp.gmail.com:587 (STARTTLS) using a Gmail app password in `.env` (`GMAIL_APP_PASSWORD`, never committed); sender and recipient addresses in git-ignored `config/local.yaml`. A weekday launchd job sends at a fixed morning time after the evening `track-daily` run; it skips with a log line when the data is older than the last session.
- Alternatives: a claude.ai artifact or Notion page (rejected: the user asked for Gmail; holdings are personal); Gmail API with OAuth (deferred: more setup for one fixed recipient); macOS Mail via AppleScript (rejected: depends on a configured Mail account and the GUI session).
- Consequences: personal holdings leave the Mac by e-mail to the user's own Gmail; the user must create an app password (needs 2-step verification on the Google account); one more launchd job.
- Links: D-116, D-120, D-132, plan 15 ph7e

### D-137 Daily App Store game charts from Apple's public RSS feeds
- Status: accepted (2026-11-11, plan 19 approved: "可以track"; asked: "在湖里 track一下各个国家，各个地区的苹果畅销榜和免费榜游戏").
- Context: there is no free history of game chart ranks (七麦 / 点点 / Sensor Tower are login- or pay-walled); revenue and contract liabilities arrive quarterly, too late to see a game fading.
- Decision: capture Apple's legacy iTunes RSS charts (top grossing and top free, genre 6014 games, top 100) for the markets in `config/app_charts.yaml` once a day into dataset `app_store_charts` via a new `snapshot` sweep kind (one key per capture date, never backfilled, `known_on` = capture date); link apps to listed companies by `artist_id` in `config/app_publishers.yaml`.
- Alternatives: paid rank vendors (rejected for now: cost and terms); scraping 七麦 web pages (rejected: login wall, terms); LLM web search (rejected: the Ark DeepSeek endpoint has no browsing, and answers are not a time series).
- Consequences: history starts on the first capture day; iOS only; one more step in `make track-daily`; a new sweep kind that later "today only" sources can reuse.
- Links: D-063, D-120, plan 19, plan 15 ph7b

### D-138 DeriveStep uses the D-135 hash digest for derived.risk_* (amends D-135)
- Status: accepted by execution (2026-11-12).
- Context: once the risk tables were registered as derived views, `curate`'s DeriveStep built the exact digest of `derived.risk_exposure` (142 M rows) and ran out of memory at 32 GB, so the 11-12 daily update stopped before the features and the risk refit.
- Decision: `DeriveStep.run` uses `build_digests(..., scalable=True)` for views starting `derived.risk_`, exact for all others — the same digest RiskModelStep writes, so the manifest values agree.
- Alternatives: drop risk tables from DeriveStep digests (rejected: curate would stop recording them); raise memory (rejected in D-135).
- Consequences: TC-CP-006; non-risk digests unchanged. (Numbered D-138: D-137 was taken concurrently.)
- Links: D-135, D-094

### D-139 Manual cycle series: committed public file + git-ignored licensed file, PIT by publication date
- Status: accepted (2026-11-12, user approved plan 20).
- Context: the cycle signals behind several holdings and watchlist names are not in Tushare: the Clarksons newbuilding price index (中国船舶) and TiO2 / ilmenite prices (龙佰). Wind EDB likely has them, but it is licensed and terminal-bound.
- Decision:
  - Public observations go in a committed `config/manual_series.yaml`, each row with a source URL.
  - Licensed exports go in git-ignored `config/local.manual_series.yaml` and are flagged `licensed`.
  - Both files are loaded into curated `alt/manual_series` with `known_on` = publication date.
  - Series that akshare covers use the existing akshare source instead.
- Alternatives:
  - WindPy integration: rejected, because it needs a logged-in terminal and adds new paid data (plan 16 scope).
  - Ad-hoc scripts in meta/runs: rejected, because the data is not PIT and is invisible to the app.
- Consequences: values are only as good as their sources. The rows are context for cycle position, not trading signals.
- Links: D-120, D-121, D-005, plan 20

### D-140 statsmodels as a project dependency
- Status: accepted by execution (2026-11-12, user: "装呗").
- Context: the time-series tests used in research sessions were run ad hoc in a throwaway `uv run --with` environment: Engle-Granger and Johansen cointegration (中证1000 vs 银行) and ADF.
- Decision: add `statsmodels>=0.15.0` to `pyproject.toml` / `uv.lock`. It is used in research notebooks and scripts; any library class that uses it goes through `new-class` as usual.
- Alternatives: hand-rolled tests in numpy (rejected: error-prone critical values); keep using throwaway environments (rejected: not reproducible).
- Consequences: one more dependency in the shared venv; peers sharing `$HOME/.venvs/quant_cn` see it after `uv sync`.
- Links: D-005

### D-141 lightgbm and scikit-learn as project dependencies
- Status: accepted (2026-11-18, plan 21 ph1 started on user "先做计划21"; lightgbm 4.7.0, scikit-learn 1.9.1 added with `uv add`). Peers sync with `uv sync --all-extras` (a plain `uv sync` drops the akshare / baostock / prefect extras).
- Context: the shareholder-count nowcast was prototyped with LightGBM and scikit-learn in throwaway `uv run --with` environments. Productionising it in plan 21 needs both in the shared venv.
- Decision: add `lightgbm` and `scikit-learn` to `pyproject.toml` / `uv.lock` when plan 21 phase 1 starts. Library classes that use them go through `new-class`.
- Alternatives: keep the prototype outside the package (rejected: no daily run, no tests); HistGradientBoosting only (rejected: LightGBM v5 was better and faster).
- Consequences: peers run `uv sync`; lightgbm ships native wheels for macOS.
- Links: D-140, plan 21

### D-142 散户温度计 RetailGauge (shareholder-count nowcast): v5 LightGBM on within-quarter ranks, point-in-time walk-forward
- Status: accepted (2026-11-18, plan 21 build started; user "以V5为准" on 2026-11-12), plan 21.
- Context: several versions were compared (research_space/prototypes/holder_nowcast): linear IC 0.47, LightGBM v3 0.639, v4 0.646, v5 0.686. Adding national-team ETF flows (v6) and an industry-neutral target gave no gain.
- Decision:
  - Target: within-quarter percentile of ln(holders_q / holders_{q-1}).
  - Features: 83, all as of the prediction date.
  - Protocol: expanding walk-forward; labels and lags only once announced; medians from training only; calibration table maps deciles to the expected change and IQR.
  - Order size is not treated as retail identity. Small orders enter only as a model feature.
- Alternatives:
  - Use raw small-order flow as "散户资金": rejected, correlation with holder change −0.07.
  - Sequence models: deferred.
- Consequences: outputs are directions and ranges, not exact counts. Accuracy is reported every quarter.
- Links: D-141, D-139, plan 21

### D-143 社融 dataset `sf_month` and a daily macro monitor in the app and morning report
- Status: proposed (2026-11-13), plan 15 ph7h.
- Context: the user wants PPI, 社融 and CPI tracked. `cn_cpi`, `cn_ppi`, `cn_m`, `cn_pmi` exist (plan 11 ph5, D-080, lags D-086) but are refreshed only by hand; 社融 is not in the lake.
- Decision: add Tushare `sf_month` as a monthly dataset with `period_end_lag` and release_lag_days 20 (same conservative rule as `cn_m`); refresh the five macro datasets in `track-daily`; `MacroMonitorBuilder` writes `macro_monitor.json` for a `#macro` page and a 宏观 block in the 持仓监测 e-mail.
- Alternatives: akshare / PBOC scraping for 社融 (rejected: Tushare covers it with the existing token); a separate plan (rejected: it is one dataset plus one builder on the plan 15 app pattern).
- Consequences: no consensus data, so no surprise-vs-expectation column; the lag rule may hide a print for a few days until a release calendar is added.
- Links: D-080, D-086, D-136, plan 15

### D-143 status update
- Status: accepted (2026-11-13, user: "可以，批了"). Entry above unchanged; DECISIONS.md is append-only.

### D-148 Dividend yield as a risk-model style (cne5_v3_dy)
- Status: accepted (2026-11-12, user: "加入股息率"; added by session quant-cn-5c while the risk-model owner quant-cn-b5 was offline).
- Context: the A-share 红利 style was strong 2022–2026 and the user's book holds high-yield names (巨人 4.8%, 徐工 3.7%), but cne5_v3 had no dividend style, so that exposure was absorbed by value, earnings yield and industries.
- Decision: style `dividend_yield` = DTOP = trailing 12-month yield (`daily_basic.dv_ttm` / 100; 0 for a stock with a market cap and no dividend, NaN without one), not orthogonalised (CNE5); default model renamed `cne5_v3_dy`. Gate vs cne5_v3 (run 7eab5093c5aa): median adj R² 0.2741 vs 0.2733 (last year 0.3013 vs 0.3013), random portfolios 100% in band (median bias 1.031 vs 1.031), CSI 300/500/1000 bias 0.933/1.082/1.047 (unchanged), own bias 1.031. Passes.
- Alternatives: DPIBS (forecast DPS / price) as well (deferred: needs the consensus step of plan 13 ph6); monitor-only like AIDC (rejected: it passes the gate).
- Consequences: `RiskInputLoader` reads dv_ttm; `DescriptorBuilder` adds `dtop` (TC-DB-006). Factor return by year (sum): 2019 +0.3%, 2020 −2.2%, 2021 −0.6%, 2022 +2.3%, 2023 +4.2%, 2024 +1.0%, 2025 −2.2%, 2026 YTD +2.3%.
- Links: D-127, D-131, plans/execution/05_risk_model.md ph8, RISK_FACTOR_LIST §2

### D-144 Research log: ad-hoc analyses recorded in git, outputs in the lake, queryable in `project`
- Status: accepted (2026-11-13, user: "可以"), plan 02 ph5–6.
- Context: the `project` schema covers plans, phases and decisions, but phase status is free text (31 spellings) and ad-hoc analyses (screens, event studies, curves) live only in the session scratchpad and are lost when it ends.
- Decision: phase status follows `<state> <date> (<commit>) — <note>` with state in todo / doing / blocked / done, parsed into columns. Each ad-hoc analysis is a row in `research_space/RESEARCH_LOG.md`, its scripts in `research_space/runs/<date>_<slug>/` (git), its outputs in the lake `meta/runs/research/<date>_<slug>/`; the catalog loads the log into a `project` table.
- Alternatives: write the log only into DuckDB (rejected: the catalog is rebuildable from the repo and is never edited by hand, D-017); keep outputs in git (rejected: size, and personal holdings must stay git-ignored, D-120).
- Consequences: agents must record each analysis; committed scripts read personal data only at runtime.
- Links: D-017, D-042, D-120, plan 02

### D-145 Daily futures monitor in the app and morning report, built on `FuturesCurve`
- Status: accepted (2026-11-13, user: "ok"), plan 15 ph7i.
- Context: the user wants futures tracked systematically. The lake holds all four exchanges' `fut_daily` / `fut_holding`; plan 16 ph2 built `FuturesCurve`; plan 10 ph3 (`TermStructure`) is unapproved and broader (factors, descriptors). Curve and spread checks so far were one-off scripts (research_space/runs/20261113_metal_curves).
- Decision: a `FuturesMonitorBuilder` reusing `FuturesCurve` writes `futures_monitor.json` daily (price, curve shape, OI change, value-chain spreads from `config/futures_monitor.yaml`, percentile flags) for a `#futures` page and a 期货 block in the 持仓监测 e-mail; `fut_daily` / `fut_holding` join `track-daily`.
- Alternatives: build plan 10 ph3 first (rejected: unapproved, larger scope); keep one-off scripts (rejected: no daily alerts).
- Consequences: spread coefficients live in config and must be checked; overseas prices wait for plan 20; plan 10 ph3 keeps only what its factors need.
- Links: D-121, D-136, D-144, plan 10, plan 16

### D-147 Dividend yield replaces EP in the factor-campaign score
- Status: accepted (2026-11-12, user: "就股息吧"; the risk style is D-148, renumbered twice after ID collisions with D-144 research log and D-146 structured conditions).
- Context: campaign factor_campaign_01 tested DP (`DividendYieldFactor`, dv_ttm / 100, 0 for non-payers), industry- and size-neutralised: 20d IC 0.041 (t 2.58), ICIR 0.54, LS Sharpe 0.72, Romano-Wolf p 0.049; EP 0.038 (t 1.95), 0.42, 0.21, p 0.144. Rank correlation DP–EP 0.59; DP residual on EP keeps a monthly 20d IC of 0.034 (t 5.8). Positive in 2019–21, 2022–24 and 2025–.
- Decision: score weights use dividend_yield instead of ep_ttm (equal weights otherwise); ep_ttm stays in the campaign as a single factor.
- Alternatives: DP as a seventh factor next to EP (not chosen by the user; both carry information, to retest later); keep EP (rejected: weaker on every metric).
- Consequences: `config/factors.yaml` weights changed; `derived.features` score rebuilt; the trial log records the new trial.
- Links: D-093, D-148, FACTOR_LIBRARY §1, plans/execution/04_*.md ph5

### D-146 Structured conditions: kinds, unknown-is-not-met, k of n, and the app composition root
- Status: accepted (2026-11-13), plan 15 ph7f (approved by the user 2026-11-13).
- Context: buy ranges and position notes carried their real conditions as prose; the user asked for them to be listed and checked. `cli.py` (599 lines) and `ServiceBuilder` (289-line class) were at their size limits.
- Decision: a `Condition` is `<metric> <op> <value>` of a kind whose metrics are listed in `core.condition.METRICS` (kind `chip` added for winner rate, institutions, northbound, margin, unlocks, insiders). A missing value is `unknown` and never counts as met. Watchlist entries may require k of n conditions (`conditions_needed`). Northbound change compares the last two disclosures because `hk_hold` is quarterly since 2024. Readers stay in `lake`, evaluation in `portfolio`; a new `AppServiceBuilder` wires the app's builders.
- Alternatives: free-text conditions parsed by an LLM (rejected: not reproducible); counting unknown as met (rejected: hides missing data such as `winner_rate` before plan 21).
- Consequences: `winner_rate` and `bank_etf_z` conditions show unknown until plan 21 ph1 and plan 15 ph7g; new metrics need a METRICS entry and a reader column.
- Links: D-120, D-132, D-136, D-142, plan 15, plan 21

### D-149 CNINFO title rules: inquiry replies first, H-share filings dropped, re-type downloaded files
- Status: accepted (2026-11-12, plan 18 ph2 approved by the user: "可以").
- Context: rules are first-match; "关于2024年年度报告的信息披露监管问询函的回复公告" contains 年度报告 and was typed annual (1,240 files incl. 1,190 from the keyword source), and "港股公告：2024年度报告" / "H股公告-…季度报告" were typed periodic. The FY2022–2024 label backfill picked such replies as the company's annual report (found 2026-11-12, plan 12 log).
- Decision: `inquiry_reply` is the first cninfo rule (问询函 | 问询的回复 | 审核问询); periodic noise adds 港股公告 | H股 (not 港股: port companies 广州港股份 / 天津港股份); new types `incentive_plan`, `operating_data` and keywords 股权激励 / 激励计划 / 经营数据 / 新签合同 (激励计划 added 2026-11-13: draft titles read "…限制性股票激励计划（草案）"). `DocumentRetyper` (new; manifest parts through the new `DocumentManifestWriter`, shared with `DocumentDownloader`) re-applies the rules to downloaded files: changed type = file moved + new manifest row; no rule = `excluded`. Run 2026-11-12: cninfo moved 52, excluded 61 of 85,654; cninfo_kw moved 1,298 of 21,455; 0 inquiry replies left under annual / semiannual / q1 / q3.
- Alternatives: filter replies in every reader (rejected: each reader would repeat the rule); delete and re-download (rejected: needless traffic).
- Consequences: readers that take the latest manifest row per doc_id see the new types; FY2025 labels made from `documents/cninfo/annual/` by folder glob (applications_full.py) include replies and must be re-checked.
- Links: D-101, D-124, plans/execution/18_*.md ph2

### D-150 Guidance and contract extraction rules (plan 18 ph3 pilot)
- Status: accepted (2026-11-13, plan 18 ph3; user: "开始第三阶段吧").
- Context: the pilot needed rules for which LLM items count as guidance or orders. Round-1 hand checks failed on IR records (63%) and 重大合同 / 中标 (61%): undated or present-tense amounts, wrong bid stage, consortium totals, unit prices.
- Decision:
  - Guidance items must carry a value, a quote found on a sent page, a kind (target / expectation / commitment) and a period no earlier than the announcement year minus one. Undated items are dropped.
  - Pages per source: annual reports from the outlook heading (SZSE 未来发展的展望, SSE 未来发展的讨论与分析, BSE 未来展望) to the end of the MD&A chapter; incentive drafts from the 业绩考核 pages plus the next page; IR records all pages.
  - Contracts: status is the furthest stage reported, and a bare "中标公示" is 预中标. The amount is the company's own share; otherwise the consortium total, tagged 联合体总额. A range is amount..amount_high. A unit price, a total investment, a concession or BOT deal, or a purchase by the company is not an order. Related-party deals are flagged.
  - Amounts are scaled by the unit word.
  - Operating-data notices go to the contract extractor only when the title names orders (新签 / 合同 / 订单 / 中标 / 承接); the rest are production and sales data.
  - Numeric text ("30%") is parsed by `LenientItem` instead of failing the reply.
  - Periodic-report noise adds 持续督导 | 管理办法.
- Alternatives:
  - Keep qualitative statements: rejected, because they cannot be scored against actuals.
  - Treat "中标公示" as a win: rejected, because a candidate posting can still change.
- Consequences: yields are low for annual plans (7/50 companies give numeric targets) and IR records (6/50). Incentive drafts and order notices carry most items.
- Links: D-122, D-124, D-149, plan 18

### D-143 status update (2)
- Status: accepted; implementation note (2026-11-13, plan 15 ph7h). Tushare `cn_pmi` now returns lower-case columns (`month`, `pmi010000`…) without the metadata columns (`ID`, `CREATE_BY`…); the request with the old upper-case field list fails. The `cn_pmi` spec now uses the lower-case fields; primary key and known-on `month`. No code read the old upper-case columns. Entry above unchanged.

### D-151 Daily refresh of every market dataset, scheduled after the China close in local time
- Status: accepted (2026-11-13, user: "我们的数据应该每天都更新"), plan 15 ph7b / ph7e.
- Context: the Mac runs on US Eastern time. The data job ran at 18:30 local (07:30 Beijing next day) and refreshed only the watchlist, ETF and macro datasets, so moneyflow, margin, northbound, futures and options lagged by 2–7 sessions; the 08:00 e-mail (21:00 Beijing) went out before that day's China data was fetched.
- Decision: `make market-data` downloads the last 14 days of every daily market dataset (trade-date sweeps with `--start`; overwrite / date-window datasets without it, D-049) and compacts them; `track-daily` runs it first, then the app documents (watchlist, ETF, macro, futures, risk model, holdings). The launchd data job moves to weekdays 06:00 local (18:00/19:00 Beijing, after the stock and futures day close); the e-mail stays at 08:00.
- Alternatives: `download` of all datasets (rejected: documents and slow vendors would delay the e-mail); schedule in Beijing time (rejected: launchd uses the Mac's zone).
- Consequences: the e-mail carries the same-day China close; a catalog lock held by another session at 06:00 fails the job, visible in ~/Library/Logs/quant_cn-daily-track.log.
- Links: D-049, D-126, D-136, plan 15

### D-152 Daily volatility monitor: CBOE CSV for US VIX, A-share VIX computed on the fly
- Context: the user wants VIX monitored daily (2026-11-13: "vix也需要监测"). Tushare has no VIX; plan 03's `VixCalculator` exists but its daily `derived/vix/` step (ph4) is not built, and `opt_daily` started 20260801 (too short for a 1-year percentile).
- Decision: US VIX comes from CBOE's public daily CSV through a new source `cboe` (`CboeClient`, dataset `cboe_vix`, overwrite, refreshed by `make market-data`). The A-share VIX (50 / 300 / 500 ETF, 中证1000, 科创50; trading clock, D-052) is computed by `VolatilityMonitorBuilder` from the lake on each run over a 250-session window; `opt_daily` starts 20250101. Alerts in `config/volatility_monitor.yaml`: US VIX ≥ 25 or +30% in a day; 300ETF and 科创50 VIX ≥ 1-year 90th percentile (after 120 sessions). Shown in the 持仓监测 e-mail (波动率 block) and the app page 波动率监测.
- Alternatives: wait for plan 03 ph4 partitions (rejected: delays the monitor; the on-the-fly run takes seconds); akshare QVIX feeds (rejected: third-party mirror of the same CBOE-method index, and we already compute it); a fixed-level alert for A-share VIX (rejected: levels differ by underlying, 50ETF ~15 vs 科创50 ~45).
- Consequences: one more external source (no key, public URL); a CBOE outage leaves the US line stale (the fetch fails visibly in the download table). When plan 03 ph4 lands, the builder can read `derived/vix/` instead of computing.
- Links: plan 03 ph6, D-052, D-151, plan 15 ph7 (monitor stack)

### D-153 Phone alerts by iMessage from this Mac, plain-language, recipients git-ignored
- Context: the user wants alerts sent to phones ("可以做个发信息的功能吗？" → 手机信息, first for their mother on an iPhone, "要写大白话一点").
- Decision: send iMessage through this Mac's Messages app with `osascript` (handle and text passed as argv, never in the script). Recipients, triggers and the line cap live in git-ignored `config/local.notify.yaml`; template `config/notify.example.yaml`. Text is plain Chinese without jargon or English abbreviations, one message per run, each alert once.
- Alternatives: China SMS platforms (rejected: need a company signature and template approval); Twilio SMS to +86 (rejected: registration, cost, unreliable delivery); WeChat bots (rejected: user chose phone messages); e-mail (already the morning report).
- Consequences: works only while this Mac is on and signed in to Messages, and the launchd job needs the macOS Automation permission. Phone numbers never enter git. `AlertMessageBuilder` (ph2) owns the plain-language wording.
- Links: plan 22, D-136 (mail), D-152 (volatility monitor), plan 15 ph7


### D-154 Buyback data and shareholder yield
- Status: proposed (2026-11-13, user: "起草回购数据的计划吧"), plan 23.
- Context: returns already include cash dividends (adj_factor reinvests them at the ex-date) and buybacks act through the price, but no buyback data is in the lake, so the dividend-yield style (D-148) and the watchlist yield miss companies that return cash by buying back shares; buybacks grew after the 2024 回购增持再贷款 and 市值管理 policies.
- Decision: add Tushare `repurchase` as a point-in-time event dataset (known on ann_date), group announcements into programmes, and publish a shareholder yield = (cash dividends + executed buybacks over 12 months) ÷ total market cap for display and conditions. Whether it joins or replaces the risk model's dividend style waits for the phase 4 research.
- Alternatives: scrape buyback amounts from CNINFO announcements (rejected: Tushare has structured progress rows); use planned amounts (rejected: plans are often not executed; only 实施 / 完成 amounts count).
- Consequences: stage semantics of `amount` (planned vs cumulative executed) must be handled; buyback purpose (cancellation vs employee plans) is unknown, so the yield is gross.
- Links: D-148, D-151, D-086, plan 23, plan 05, plan 15 ph7f

### D-154 status update
- Status: accepted (2026-11-13, user: "全部同意，按顺序开工"). Entry above unchanged.

### D-154 status update (2)
- Status: accepted; outcome of plan 23 phase 4 (2026-11-13). Executed buyback yield adds nothing over the dividend yield (month-end IC 0.011 vs 0.072 at 60 days), so the risk model's dividend style (D-148) stays as it is and shareholder yield is display-only. Buyback plans of at least 2% of total market cap do predict returns (60-day excess +2.0%, t 3.6; +4.6% since 2024), so phase 5 exposes `buyback_plan_pct` (largest live plan as % of market cap) as a condition metric and phase 6 reports new large plans. Entry above unchanged.

### D-155 RetailGauge top decile is an avoid flag (散户过热回避标记)
- Status: accepted (2026-11-13, user: "把第10组回避标记加进 plan 21"), plan 21.
- Context: plan 21 excluded price signals ("不在乎预测股价"). Research run `20261113_retail_gauge_returns` found that the v5 prediction, known at the quarter-end close, is the strongest holder-based return signal we have. Its 60-day excess rank IC is −0.085, or −0.058 net of size / reversal / turnover / momentum and the last announced change. Over 18 quarters the top decile trails the equal-weight market by 3.75% a quarter (t 3.9, 16/18). The long side (deciles 1–4) adds only +1.1% a quarter, and shorting decile 10 is not feasible.
- Decision:
  - A stock whose gauge pct is at or above `retail_gauge.avoid_pct` (default 0.9, in config) carries `avoid = true` in `derived/retail_gauge`.
  - The flag excludes the stock from the opportunity list. It is shown on the holdings and watchlist pages.
  - The morning report names any holding that enters the flag.
  - It is a flag only: no automatic trades, no sizing rule.
- Alternatives:
  - Long/short decile portfolio: rejected; the short leg carries three quarters of the effect and cannot be borrowed.
  - Index-hedged long of deciles 1–4: rejected; t 1.7, worst quarter −17.7%, futures basis not included.
  - Keep plan 21 free of price use: overridden by the user.
- Consequences:
  - `RetailGaugeEvaluator` also reports, each quarter, the flagged names' 60-session excess return against the equal-weight market. This keeps the flag's value checked out of sample.
  - The flag goes to review if flagged names beat the equal-weight market in four consecutive quarters.
- Links: plan 21 ph3–5, D-142, research_space/RESEARCH_LOG.md (20261113_retail_gauge_returns, 20261113_holder_count_returns)

### D-156 Mean-reversion flag only on cost-anchored futures spreads
- Status: accepted (2026-11-14, user: "把PTA加工费和MTO利润加到监测里"), plan 15 ph7i.
- Context: research run `20261114_mean_reversion` found that single futures do not keep a stable trend or reversion trait (variance-ratio class formed 2020–22 has rank corr −0.14..+0.08 with 2023–26). Only spreads anchored by a production cost revert out of sample: PTA 加工费 (half-life 12 sessions, ADF p 0.00, z-reversion Sharpe 1.34 since 2023) and PP − 3×甲醇 (94 sessions, p 0.04, Sharpe 1.06).
- Decision:
  - A spread in `config/futures_monitor.yaml` may carry `reversion: true` and `half_life_d`. Only PTA 加工费 and the new 甲醇制烯烃利润 (PP − 3×MA) do.
  - Every spread gets a one-year z (`z_1y`, at least 120 values). A reversion spread with |z| ≥ `reversion_z` (default 2.0) raises a flag of kind "reversion". The phone alert says plainly that it is far from normal and how long it usually takes to return.
  - It is a flag only: no automatic trades or sizing.
- Alternatives:
  - Classify each family as trend or reversion by variance ratio: rejected, the trait is not stable out of sample.
  - Flag ratios (金银比, 铜金比, 金油比, 铝−氧化铝): rejected, z-reversion lost money on them.
  - 5-year percentile only: kept as is for every spread, but it is slow for a 12-session half-life.
- Consequences:
  - Steel margins (Sharpe 1.1 since 2023 but not stationary) stay without the flag; review after a year of the flag on the two spreads.
  - Half-lives are measured values from one sample; re-run `research_space/runs/20261114_mean_reversion/` yearly.
- Links: plan 15 ph7i, plan 22, D-145, D-153, research_space/RESEARCH_LOG.md (20261114_tsmom, 20261114_mean_reversion)

### D-156 status update
- 2026-11-14, user: "钢厂利润也加进去吧". 螺纹利润 and 热卷利润 also carry `reversion: true` (half-lives 152 / 149 sessions). This overrides the "steel margins stay without the flag" consequence. Their z-reversion Sharpe was 1.1 since 2023 but only 0.31 over the full sample, and the ADF test did not reject a unit root (p 0.16 / 0.24). Read their flags as weaker than the PTA and MTO ones; review after a year.

### D-157 Index trend position: short-trend blend with volatility sizing; fear as context only
- Status: proposed (2026-11-14), plan 24.
- Context: research runs 20261114_tsmom_robust and 20261114_vix_vs_trend. The 12-month signal alone exits a median 8 months after a top. Short windows are better on A-share indices but window- and period-sensitive. "Buy when the VIX is high" lowers the result when it is added to the position.
- Decision:
  - The suggested position per broad index = share of {10, 21, 42, 252}-session signals that are up × min(1, 20% / 60-day realised volatility).
  - Fear (A-share VIX percentile, realised volatility where no options exist) is shown next to it, with the historical fear × trend row, and does not change the position.
  - It is a research signal shown in the monitor: no orders.
- Alternatives:
  - Single 21-day window: rejected; similar Sharpe but the neighbours (15, 30 days) are much worse and the best window changed between halves.
  - 12-month only: rejected; slow exits (median −35% by the exit).
  - Moving averages (MA200, 50/200): rejected; no better than 12 months.
  - Add a fear-buy leg: rejected; Sharpe 0.47 → 0.32, drawdown −31% → −46%.
- Consequences: the parameters live in `config/volatility_monitor.yaml` (`trend`); a 3-month live check before any wider use.
- Links: plan 24, D-152, D-153, research_space/RESEARCH_LOG.md (20261114_tsmom_robust, 20261114_vix_vs_trend)

### D-152 status update
- 2026-11-14, user chose "回补期权，算真实VIX": `opt_daily` start moves from 20250101 to 20150209 (first 50ETF option listing) so the A-share VIX can be computed over its full history for plan 24 research. Disk and API cost: about 2,400 extra trading days.

### D-158 QDII premium alert: fund_nav joins the etf-proxy refresh
- Status: proposed (2026-11-14), plan 26.
- Context:
  - User: "加一个QDII溢价提醒".
  - On 2026-11-05/06 the QDII 纳指 ETFs traded at +20..25% over NAV and the 标普 ETFs at +12..13%.
  - `fund_nav` is in the lake but not in any daily refresh.
- Decision:
  - Add `fund_nav` (market E) to `ETF_PROXY_DATASETS`, refreshed over the last 14 days.
  - Premium = close / unit_nav − 1 on the latest date where both exist (QDII NAV lags one to two sessions).
  - 可买 below 3%, 很高 at or above 10%; flag only on a crossing.
  - Shown in the ETF panel and the morning e-mail. No phone line (plan 22 sends only to 妈妈, A股 focus).
- Alternatives:
  - Intraday IOPV premium: rejected; needs real-time quotes.
  - Phone alert: not by default; only if the user asks.
- Consequences: one more dataset in the daily job; `EtfPremiumMonitor` and `EtfPremiumSettings` to build.
- Links: plan 26, plan 15 ph7b, D-126, research_space/RESEARCH_LOG.md (20261114_etf_universe)

### D-159 Backfill ETF, fund NAV, futures and SGE history for long ETF-book backtests
- Status: accepted (2026-11-14), user: "回溯到最早补齐数据".
- Context:
  - The ETF risk-budget book (research `20261114_etf_universe`) can only be tested from 2020: fund_daily, fund_nav, fut_daily, fut_mapping and sge_daily all start in 2019.
  - The core ETFs list in 2011-2013, so earlier history would cover the 2013 and 2016-17 bond bears, the 2015 crash and 2018.
- Decision: move the dataset starts back and backfill once, after the opt_daily backfill (D-152 update) has finished (one lake writer).
  - fund_daily and fund_nav: 20050222 (first listed ETF, 510050).
  - fut_daily, fut_mapping and sge_daily: 20100104 (same start as index_daily and cn_bond_yield). The commodity group before the commodity ETFs (2019-12) uses a main-contract proxy.
- Alternatives: proxies only (indices and the bond curve). Rejected: no tracking error, fees or QDII premium, and no gold or commodity series before 2019.
- Consequences:
  - Older years add raw and curated partitions.
  - Daily refreshes are unchanged (they use their own windows).
  - Research reruns from 2013.
- Links: research_space/RESEARCH_LOG.md (20261114_etf_universe), D-074, D-077, D-152

### D-160 ETF CTA book: long-only risk budget with A股 trend timing
- Status: accepted (2026-11-14, user: "每周看，2点不动，开工吧"), plan 27.
- Context:
  - The user cannot trade futures and wants a long-only ETF version of a CTA ("只做多的 ETF 版 CTA", "我们自己做").
  - Research `20261114_etf_universe` compared fixed mixes, risk parity / budgets, vol timing, trend switches and VIX helpers.
- Decision:
  - Groups 股票 (A股 + 港股, 2 : 1), 债券, 黄金, 商品 (有色 + 能化 + 原油), each at a 1 / 60-day-vol risk weight. Budget 1:1:1:1, monthly.
  - A股 ETFs scaled weekly by the plan-24 position (D-157).
  - Bond trend switch, no 30-year and a 65% bond cap stay options until the 2013– backtest (D-159 data).
  - Freed weight goes to the money-market ETF 511880.
  - Update 2026-11-14 (user: "可以，就按60/40定"), after the 2014– backtest and the user's duration concern:
    - 60% 风险资产: 股票 / 黄金 / 商品 at 1:1:1 risk weights (1 / 60-day vol), monthly.
    - 40% bonds: 5-year 511010 and 30-year 511090 at equal capital, scaled weekly by the bond trend switch (21/63/252). Replaces the 1:1:1:1 bond budget and the 65% cap.
    - 原油 = 易方达 161129, with the premium guard: buy or add below 3%, no adds at 10% or more.
    - Evidence `bond_mix.py` 2014-01..2026-11: +7.6%/y, Sharpe 0.84, max dd −7.5%, no losing year, full-weight duration 4.7.
- Alternatives:
  - 40/60 fixed: rejected; Sharpe 0.27 and almost all risk in equities.
  - Covariance ERC: rejected; Sharpe 1.09 with 75% bonds.
  - Portfolio vol targeting or VIX helpers: rejected; lower Sharpe.
  - Trend switches on gold and commodity ETFs: rejected; worse.
  - Buying CTA funds or DBMF: declined by the user.
- Consequences:
  - New `EtfCtaSettings` and `EtfCtaBook`.
  - Plan 24's trend rule is reused on ETF prices.
  - QDII / LOF lines use the plan 26 premium guard.
- Links: plan 27, plan 24, plan 26, D-157, D-159, research_space/RESEARCH_LOG.md (20261114_etf_universe)

### D-161 Temporal chain graph: company leaves, industry nodes, labels in parquet
- Status: proposed (2026-11-14), plan 28.
- Context:
  - The user wants a multi-year graph: "leaf是公司，应该在公司里可以看到自己业务的变化。node是行业，行业带有公司。然后行业间可以通过supplier 和buyer，finance invest的关系连接上".
  - The user also wants every downloaded document type labelled, with labels stored as local parquet: "把其他的文件也打标，打标的应该都在parquet存在本地".
  - Labels now exist for FY2022–FY2025 and H1 2023–2026, but sit in jsonl files under `meta/runs/`.
  - FY2022 product lines are almost empty because `fina_mainbz` starts at 2023-06.
  - Event documents (contracts, inquiry replies, IR Q&A, prospectuses, deals) are downloaded but not labelled.
- Decision:
  - Every graph table carries `period`, or an event date for events.
  - Companies are leaves with a history page.
  - Industry nodes hold member companies with revenue weights per period.
  - Node-to-node edges are of two kinds:
    - supplier / buyer;
    - finance / invest: equity stakes, outside investment, M&A, subsidiaries.
  - Node-to-node edges are aggregated from company evidence per period. Prior edges (D-097) are kept apart.
  - All labels live in `derived/labels/<label_set>/period=<YYYYMMDD>/` parquet through one `LabelStore`; jsonl stays only as the LLM response cache.
  - This takes over plan 12 phases 5–6 (EntityResolver, GraphStore, GraphQuery), which are built with periods from the start.
- Alternatives: keep one-period graph tables and diff jsonl files per year; rejected because it gives no node-level history and no single query surface.
- Consequences: new `LabelStore`, document-type extractors, `NodeEdgeAggregator`; plan 12 ph5–6 point to plan 28.
- Links: plan 28, plan 12, D-097, D-102, D-104, D-125, D-129

### D-161 update 1
- User, 2026-11-14: "公司leaf，应该包括我们打标的各种信息".
- The company leaf is the per-period CompanyCard (D-104).
- It carries every label set: applications, top-5 customers and suppliers, business mode and pricing power, moat, quarterly notes, guidance and contracts (plan 18), broker valuation and views (plan 13), sector KPIs, and the new document-type sets.
- Plan 18's `ContractExtractor` is reused; plan 28 reads its output.

### D-161 update 2
- User, 2026-11-14: "然后应该是哪找时间线排好的", i.e. everything arranged on a timeline.
- Each label row carries two dates:
  - `period`: what the fact describes;
  - `known_on`: when the fact became public, i.e. the announcement date or Q&A reply date.
- Contracts and deals also carry an `event_date`.
- Timelines and `as_of` queries order and filter by `known_on`, so a company "as known on a date" never sees a report filed later (handbook point-in-time rule).
- Company and industry pages lead with a 时间线 view.

### D-161 update 3
- User, 2026-11-14:
  - "我想让opus自己来根据初始行业和打标，来调整";
  - "未来往前走会有linearage".
- Opus curates the industry nodes for each period. It starts from the starting taxonomy (D-097, D-107) and reads the labels. It proposes new, split, merge, rename and retire changes, each with reasons citing label rows.
- Accepted changes create a new taxonomy version and `graph.node_lineage` rows (from_node, to_node, kind, effective_period, share of members moved, reason, evidence).
- Labels keep the taxonomy version they were made with. They are remapped through lineage, not relabelled.
- Lineage replaces a fixed node set; D-097 still holds: prior product edges stay priors, and company edges need evidence.

### D-161 status update
- Accepted. User, 2026-11-14: "可以".
- Open questions settled with the recommendations:
  - industry nodes start from taxonomy segments;
  - finance / invest starts with equity stakes, outside investments, M&A and subsidiaries.
- Phase 0 implementation notes:
  - Label partitions are `year=<YYYY>` of the period, not `period=`.
  - There is one row per (company, document), with the record as JSON.

### D-162 Optuna as a research-only tuning tool, walk-forward only
- Status: accepted (2026-11-14, user: "1" = 可以，装 Optuna), plan 27.
- Context:
  - One-at-a-time parameter sweeps of the plan 27 book all land within ±0.07 Sharpe of base (SE ≈ 0.28). The user asked how Optuna / Bayesian optimisation fits in.
- Decision:
  - Add `optuna` to the `dev` dependency group. Import it only under `research_space/`, never in `src/`.
  - Tuning is walk-forward only: fit on data up to year Y−1, score year Y, roll yearly. Robust objective (mean yearly Sharpe − 0.5 × std, max-drawdown cap). Report the out-of-sample record against fixed base parameters, deflated by the number of trials.
  - Production parameters stay in `config/etf_cta.yaml`. A change needs a clear out-of-sample gain and the user's approval.
- Alternatives:
  - Grid search only: rejected; the grid grows too fast with several parameters at once.
  - Tune on the full history: rejected; the best in-sample point is mostly noise.
- Consequences:
  - Research script `research_space/runs/20261114_etf_tuning/`.
  - The `statistic` deflated-Sharpe tools (D-060) may be reused for the trial count.
- Links: plan 27, D-160, D-060, research_space/RESEARCH_LOG.md (20261114_etf_tuning)

### D-161 update 4
- Plan 28 phase 1, 2026-11-14:
  - `fina_mainbz_p` / `fina_mainbz_i` start moves from 20230101 to 20220101 (FY2022 labels had revenue lines for 491 companies). 2022 downloaded: 6,597 companies at 20221231, 5,444 at 20220630.
  - Quarterly reports are chosen by the title's year and quarter (latest real version per company and period), not by the publish-year folder. The folder rule labelled 75 corrected 2025 reports as 2026 Q1/Q3; they are re-read under their own period.

### D-163 ETF CTA views: bounded multipliers in a local file, two tracks
- Status: accepted (2026-11-14, user: "可以，按1、2、3类做，开工吧"), plan 27 ph5.
- Context:
  - The user wants to tilt the book by their own views ("我可以根据我的view来调整他们的weight吗"). They chose the multiplier method and kept A股 timing ("ok").
- Decision:
  - Views live in the git-ignored `config/local.etf_cta_views.yaml`. Each view has a group (股票 / 黄金 / 商品 / 债券), a multiplier in 0.5–2, a reason, a start date and an expiry no more than 92 days after the start. Optional settings: the 港股 share and an A股 floor (0–1 of the full A股 weight).
  - A multiplier scales the group's final weight, after A股 timing and the bond switch. Extra weight comes from cash. If the total passes 100%, all non-cash lines scale down to fit.
  - Expired views are ignored and flagged.
  - Two paper tracks, 系统 and 含观点, are always shown side by side.
- Alternatives:
  - Black-Litterman: rejected; it needs return views and a covariance prior, and the user's views are about weights.
  - Views overriding A股 timing: rejected by the user's choice. The optional floor is the only override.
  - Tilt within the 60% risk sleeve only: open; it keeps the risk level fixed, but scaling every group would then do nothing.
- Consequences:
  - New `core.EtfCtaViews` and `portfolio.EtfCtaViewTilt`; `EtfCtaBook` writes both tracks.
  - Plan 27 ph3 displays both tracks.
- Links: plan 27, D-160, D-162
- Update 2026-11-14 (accepted scope): three view kinds.
  - Scale: a group, a named subset (A股 / 港股 / 5年 / 30年, `subsets` in etf_cta.yaml) or one ETF, × 0.5–2. Inside a group the group total is kept. The combined multiplier per ETF is clipped to 0.5–2.
  - Relative: move up to 5 points of capital from one set to another, capped by the source. Nothing moves into a set at zero weight, so A股 timing is respected.
  - Price condition: optional `when` (an ETF close below or above a level). The view waits until the condition is met on a decision date, then stays on until expiry.
  - The A股 floor stays optional. The 港股 share setting is dropped; use a subset scale instead.

### D-161 update 5
- Plan 28 phase 1, 2026-11-15:
  - Each label source file is authoritative for its own rows. A re-import removes the rows it wrote earlier for documents the file no longer holds (`LabelStore.write(replace_source=…)`).
  - `LabelSource.exclude_file` lists keys of a file that are not imported. The 2026 quarterly file uses it for 104 rows that name another period and 9 H-share copies.
  - A corrected report and its original stay as two rows, each with its own `known_on`. Readers take the latest known version per company and period as of their date.
  - The report title filter matches only Hong Kong filings (港股公告, a leading 港股, 港股：), not company names containing 港股份.

### D-164 CGO top decile is an avoid flag (浮盈过高别买标记)
- Status: proposed (2026-11-15, user: "可以，当一个别买信号"), plan 29 ph4–5.
- Context: plan 29 ph1 (runs `20261115_cgo_reproduce`, `20261115_cgo_ic`): CGO (turnover-decay mean cost, free-float turnover, a = 1.5) has raw 20d rank IC −0.044 (t −2.6) but none net of reversal; the effect is one-sided, the top decile trails by 0.95% over 20 days and the others are flat. Shorting it nets about 0 after borrow cost and lending is scarce. Dropping the high-CGO 20% from the score top 20% lifts its excess from +2.8% to +3.9% a year (t 1.6 -> 2.1).
- Decision:
  - `cgo_pct` (market percentile of CGO on the day, all listed stocks) is a 筹码结构 metric; at or above `chips.cgo_avoid_pct` (default 0.9, base.yaml) a held stock carries the flag 浮盈过高, shown on the holdings page and in the morning report.
  - It is usable in watchlist and position conditions (`cgo_pct < 0.9`).
  - A flag only: not in the score, no automatic trade, no sizing rule. Plan 29 ph2–3 (factor class, score) are not built.
- Alternatives:
  - Score factor: rejected; no IC net of reversal_1m.
  - Short the top decile: rejected; +1.0%/yr net (t 0.2), years from −37% to +36%, borrow unavailable since 2024.
- Consequences: new `ChipSettings`, `CgoReader`; `ChipStructureReader`, `Condition`, `PositionReviewer`, the app's chip columns extended. History of 500 sessions per stock is enough (rank corr 1.000 with the 2010 start).

### D-161 update 6
- Plan 28 phase 2 scope, 2026-11-15 (user: "可以"):
  - Incentive plans are labelled in phase 2. Their performance targets come from `GuidanceExtractor` (plan 18): plan 28 reads plan 18 phase 4's output into the LabelStore and does not extract them again. Contracts are handled the same way.
  - Industry reports (55,428, about industries, not companies) move to phase 3b. There they are labelled against the curated industry nodes (cycle, price trend).
  - The new extractors (inquiry replies, IR records, prospectuses, deals, operating data, broker named customers) share one base, `BaseQuotedExtractor`: prompt file, reply model, page-tagged text, quote check, kept and dropped counts. Each subclass defines only its item model and its item check. The existing extractors (applications, guidance, contracts, quarterly notes …) are not moved onto it in this plan.

### D-165 launchd jobs start /bin/zsh, which holds Full Disk Access
- Status: accepted (2026-11-16; user: "处理").
- Context: the first scheduled runs on 2026-11-16 (06:00 track-daily, 08:00 morning-report) both failed with `make: getcwd: Operation not permitted`. macOS privacy (TCC) blocks a launchd agent from the external volume /Volumes/Treasury unless the program launchd starts has been granted access, and `/usr/bin/make` is an xcode-select shim that is awkward to grant.
- Decision: both plist templates run `/bin/zsh -c 'cd <repo> && exec /usr/bin/make <target>'` with no `WorkingDirectory`; the user grants Full Disk Access to `/bin/zsh` once in System Settings → Privacy & Security. Reinstall with `make track-install` and `make report-install`.
- Alternatives: grant access to `/usr/bin/make` (rejected: shim, the real binary path changes with Xcode updates); move the repo to the internal disk (rejected: the lake and repo live on the Treasury volume by design).
- Consequences: every zsh started by the user also has Full Disk Access; a missed run still needs a manual `make track-daily`.
- Links: D-126, D-136

### D-166 Partial sells lower the position cost (摊薄成本); a paid-back cost may be negative
- Status: accepted (2026-11-16; user: "我卖出了赢了的股票，还持有，那么还应该算在浮动盈亏里", "牧原的成本应该降低", "改程序，云意也算进去").
- Context: `Position.cost` was the buy average and had to be >= 0, so the gain from selling part of a winner (牧原 3,400 shares, +15,358; 云意电气 2,000 shares, +12,234) left the floating P&L although the rest is still held.
- Decision: `cost` in `config/local.positions.yaml` is the diluted cost = (buys − sell proceeds) / shares still held, the broker's 盈亏成本 view. Only a fully closed position counts as realised. The cost may be zero or negative once the position has paid back; `HoldingsRiskBuilder` then reports pnl = shares × (close − cost) and pnl_pct = null, and the app and the 持仓监测 e-mail show "已回本".
- Alternatives: keep the buy average and add a per-position realised P&L field (rejected: two numbers for one position, and the broker screens already show the diluted cost); floor the cost at 0 (rejected: understates P&L, 云意 by about 4,900).
- Consequences: `Position` drops its `ge=0` check; 盈亏% is not shown for a paid-back position. The research-log secret check still hides costs, including negative ones.
- Links: D-132, plan 15 ph7d

### D-161 update 7
- Plan 28 phase 4, 2026-11-16 (user: "可以"):
  - `company_edge` stays one row per observation (period, known_on, share or amount, stage, quote). A new table `edge_span` joins the observations of one company pair and edge kind into a relationship: first_seen and last_seen (known_on), the stage path with the date of each step, ended or denied with the date, share or amount per period, status active / ended / denied / silent.
  - Silent (not seen for N periods) is not a lost customer: only an end or denial in the text, a top-5 drop or a contract end counts as hard evidence of change (plan 28 risk "text drift").
  - `edge_span` is rebuilt for an as_of date from the rows known by that date, so it has no look-ahead. The app's customers new / dropped / kept reads it.


### D-161 update 8
- Plan 28 phase 2 counterparty checks, 2026-11-16 (user: "ok"):
  - New `CounterpartyName` holds the two name rules every customer / supplier / partner row passes. `is_named`: a numbered (客户一, 供应商A, 客商9), hidden (某) or class name (头部车企, 国内无人机厂商) is not a name; a bare letter name (GE, LG) is. `is_in_text`: the name, its alias, the name without its legal suffix or its first 4 characters must occur in the quote.
  - `BaseQuotedExtractor` gains the hook `is_item_anchored(item, page_text)` (default True). Inquiry replies and prospectuses require the name or alias in the quote. IR Q&A, IR records and broker reports require the name in the quote, or a quote that points back (该公司, 上述, 您所说, 双方) with the name elsewhere on the page (the investor's question); unnamed rows are dropped there. Inquiry rows keep anonymous rows with `is_named` false, because phase 3 may name them from another document.
  - Inquiry and prospectus rows gain `share_base`: what the share is a percent of (营业收入, 境外收入, 采购总额 …), so a 97% of overseas revenue is not read as 97% of revenue.
  - The old inquiry anonymity regex took a bare letter name (GE, IBM, LG) as a number; replaced.

### D-165 update 1
- 2026-11-16 (user chose "做一个小 App"): Full Disk Access on `/bin/zsh` did not take effect (probe from launchd still got `Operation not permitted` reading the Makefile). The jobs now start `~/Applications/QuantCN Runner.app/Contents/MacOS/quantcn-runner <repo> <target>`, a small C program (`scripts/launchd/quantcn_runner.c`, ad-hoc signed, bundle id `local.quantcn.runner`) that runs make as a child via posix_spawn, so make keeps the app as its responsible process. The user grants Full Disk Access to that app instead of zsh, so ordinary shells do not gain it. `make runner-install` builds it; `track-install` and `report-install` depend on it. Rebuilding changes the ad-hoc signature, which may require granting access again.

### D-165 update 2
- 2026-11-16 (user: "remove the quantcn runner"): the runner app of update 1 is removed (`~/Applications/QuantCN Runner.app`, `scripts/launchd/quantcn_runner.c`, `runner_info.plist`, `make runner-install`). The plist templates are back to the D-165 form (`/bin/zsh -c 'cd <repo> && exec make <target>'`). The jobs still need Full Disk Access on the program they start; until it is granted, a missed run needs a manual `make track-daily` / `make morning-report`.

### D-161 update 9
- Plan 28 phase 3 name resolution, 2026-11-16 (user: "可以", go for phase 3):
  - `EntityResolver` resolves by rule, in order: alias map, A-share full name (stock_company), A-share short names current and former (namechange, ST marks removed), the same without a bracketed region, then an A-share short name of at least 4 characters as the name's prefix (marked a group member). Three-character prefixes are not used (史丹利百得 → 史丹利, 新大洲本田 → 新大洲A were wrong). Ambiguous hits do not resolve. Group tails (及其关联方, 子公司4, 分公司) are cut and mark a group member: an edge to a subsidiary of 中国移动 counts as an edge to 中国移动, flagged.
  - On the full-run names (45k distinct, 117k mentions) the rules resolve 16% of mentions to A-share companies; 84% are unlisted, listed abroad or nicknames (华为, 特斯拉, 小米, LGES).
  - `EntityAliasExtractor` (DeepSeek, 50 names per call, each with a context line) proposes a canonical short name, kind (company / government / university / institute / hospital / person / generic / unknown), group membership and a security code hint for the names with ≥ 2 mentions that the rules leave unresolved or resolve only by prefix. Its code is never trusted: the canonical name is resolved again by the rules, and an A-share id is kept only when they agree. The alias map is a lake file, rebuilt from the cached replies.
  - Ids: "a:<ts_code>" for A-share companies, "x:<canonical key>" otherwise; kind generic / unknown names do not become graph nodes.

### D-161 update 10
- Plan 28 phases 3–4 after the 300-edge review, 2026-11-16 (user: "ok"):
  - The review found 89.7% correct, below the 90% done criterion. The largest error groups were anonymous placeholders stored as entities, and listed companies or their subsidiaries left as x: ids.
  - `CounterpartyName.is_named` now also refuses:
    - numbered or ranked names anywhere in the name (应付账款-供应商7, 内销客户8, 客户（一）, 2019年第1大客户, 第四名供应商, 法人一);
    - placeholders (无, 不适用, a bare 客户 / 供应商, codes of 5 or more digits, 香港公司 and other place + 公司 forms).
    - Short numeric brands (360, 1688, 7-11) remain names.
  - The entity pass now reads its names from `company_edge`, i.e. from every label set: applications, top-5 tables and deals as well as the plan 28 sets. Names the rules leave unresolved or resolve only by prefix go to `EntityAliasExtractor`, as before.
  - `EntityResolver` gains `member_names`: an alias the model marked as a subsidiary or branch resolves as a group member.
  - Stages and roles that the prompts get wrong are noted for the next extraction run and are not patched in the data. Examples: a minority stake (参股) tagged holds, a certifier tagged partner, a joint lab tagged volume, 拟 / 同意设立 tagged completed.

### D-161 update 11
- Plan 28 step 4a, 2026-11-16 (user: "做好计划，继续"):
  - A group member (a subsidiary, brand or branch the entity pass marks is_member) resolves to an A-share id only through its parent's short name. `EntityAliasExtractor` returns the parent's short name in a new `parent` field, and `EntityResolver` must resolve that name by rule (full or short name). The code the model proposes is not used on its own: on 40 rows it was right only about 80% of the time.
  - Subsidiaries a company names in its own report now resolve to that company and are dropped as self edges. Company-to-company edges keep only other companies; the company's own subsidiary list belongs in the leaf (`company_period`), not in `edge_span`.

### D-167 RetailGauge daily reading: raw value, 3-in-a-row confirmation
- Status: accepted (2026-11-17, user: "可以" to plans 21 and 30); plan 21 ph3 and ph5.
- Context: the user asked whether filtering the gauge improves it ("是否滤波一下散户温度计，可以让预测更好一点？", "有fine tune ema的weight吗？").
  - Readings were rebuilt every 3 trading days for 2023Q1–2026Q3 (298 dates; research run 20261117_gauge_daily).
  - Smoothing the value lowers holder IC: raw 0.503; mean of 2 / 3: 0.498 / 0.489; EMA α 0.5 / 0.33: 0.497 / 0.484; median of 3: 0.485.
  - An EMA α grid tuned on 2023–24 and checked on 2025–26 peaks at α 0.8–0.9, +0.001 IC over raw.
  - Requiring N readings in a row on the same side improves precision: for N = 2 / 3 / 5, ≤0.3 holders-fell 80 / 81 / 83% (raw 79%), and hot-group 60d excess −4.0 / −4.3 / −4.7% (raw −3.7%). Flag counts fall 19 / 31 / 49%.
- Decision:
  - Use the raw daily reading.
  - Streaks are counted at checkpoints t, t−3, t−6 … sessions.
  - `retail_leaving` (the watchlist ≤ 0.3 condition) needs 3 checkpoints in a row ≤ 0.3.
  - `avoid_strong` needs 3 in a row ≥ 0.9. A single reading ≥ 0.9 stays the D-155 warning.
  - `persist_n` = 3 and `persist_step` = 3 go in config.
- Alternatives:
  - EMA or moving mean: rejected; lower IC.
  - 5 in a row: rejected; most precise, but half the flags are gone and the signal fires 15 sessions late.
  - Raw threshold only: kept as the D-155 warning.
- Consequences:
  - Watchlist names that read ≤ 0.3 once no longer pass that condition until confirmed.
  - The ≤0.3 group still has no reliable return edge (+0.6..+0.8%, t ≤ 1.5), so it is a holder-trend check, not a buy signal.
- Links: plan 21, D-155, research_space/RESEARCH_LOG.md (20261116_gauge_filter, 20261117_gauge_daily, 20261117_gauge_ema_grid)

### D-161 update 12
- Plan 28 step 3b-3, 2026-11-16: the curation dry run found that many anomalies in the node data come from the matcher, not from the taxonomy. Out of the company's Shenwan context, about half of the "contains" matches were cross-sector (e.g. 零部件业务 of 上汽 → semiconductor silicon parts, ICT基础设施 → CT scanners).
- `ProductMatcher` changes:
  - A label found inside a longer line counts outside the company's context only when it has at least 3 characters and at least half the line's length.
  - A Latin label (CT, PVC, BDO) counts only as a whole word.
  - Inside the context, matching is unchanged.
- Effect on FY2025: mapped revenue falls from 72% to 68%, which is the removed false matches; cross-sector "contains" falls from 55% to 44%. The remaining cross-sector errors are over-broad aliases in the taxonomy (零部件, 信息服务, 消费电子, 精密零部件). They are handled as alias removals in the curation change list, not in code.
- The curation change lists (3 sectors, 33 changes) are proposals. A taxonomy version is written only after the user spot-checks them.

### D-161 update 13
- Plan 28 step 3b-4, 2026-11-17 (user: "可以" to the 33-change list, with the recommendation to keep SEG_AUTO_ROBOT_PARTS):
  - The taxonomy is versioned. The YAML files of config/industry_chain are v0. Each accepted version is one file under config/industry_chain/_changes/ (`TaxonomyChangeSet`), applied in name order by `ProductTaxonomy(folder, change_sets)`.
  - A change either upserts a node or retires it. An upsert creates a node or changes its name, segment or parent; aliases are merged, and an alias is removed only when the change lists it under drop_aliases. A retire moves the node's children and products to its successor, and the old id resolves to the successor.
  - The base files are never edited, so a version can be read, diffed or reverted on its own.
  - `NodeLineageBuilder` derives `node_lineage` by comparing the taxonomy before and after each change. Kinds: new, split, rename, move, alias, merge / retire. It raises an error for a missing successor or a retire loop.
  - Labels keep the node ids they were made with. `ProductTaxonomy.get_surviving_id` resolves a retired id through lineage, so no separate NodeRemapper class is needed (deviation from the plan's class list). `node_member` records the taxonomy version used.
  - v1-20261117 holds 59 changes from the auto, electronics and power-equipment dry run. Left out:
    - retiring SEG_AUTO_ROBOT_PARTS;
    - the over-generic aliases 开关 and 电气设备产品.
  - The over-broad aliases 精密零部件, 导电浆料 and 智能终端SoC are dropped.

### D-161 update 14
- Plan 28 step 3b, batch 1, 2026-11-17 (user: "ok继续"):
  - v2-20261117 holds 162 changes from the curation of 8 sectors: 基础化工, 机械设备, 计算机, 医药生物, 有色金属, 通信, 国防军工, 家用电器. The proposals came to 85: 45 alias, 19 new, 17 rename, 4 split. 耳机 becomes an alias of PROD_ELEC_TWS instead of a new home-appliance node.
  - Most renames turn a generic parent segment (工程机械, 医疗器械, 软件开发, 中药 …) into an umbrella "…产业" and give its wording to a child segment, so a parent no longer collects members directly.
- Matcher and builder fixes the curators found:
  - Outside the company's context, a revenue line contained in a longer label no longer matches (运营商 vs 电信运营商, 原油运输 vs 原油运输船).
  - More broad words: 中间体, 功能性, 新材料, 精细化学品, 包装材料, 互联网, 工艺设备, 运营商, 机器人, 光通信, 授权许可.
  - A Latin label may be followed by digits (WPS365).
  - `NodeMemberBuilder` keeps the sub-lines of a wrapper parent line (持续经营业务, 主营业务 …) and drops the parent.
- Effect on FY2025: cross-sector matches among non-fallback rows fall from 44% to 37.5%; mapped revenue moves from 69% to 67.5% as false matches are removed.

### D-161 update 15
- Date: 2026-11-17. Batch 2 of the node curation (石油石化, 公用事业, 建筑装饰, 建筑材料, 食品饮料, 钢铁, 煤炭, 农林牧渔) accepted by the user → `config/industry_chain/_changes/v3-20261117.yaml` (105 changes: 76 proposals plus 9 context-alias upserts).
- New taxonomy field `context_aliases`: 2-character wordings (板材, 卷板, 中板, 棒材, 涂料, 末煤, 混煤, 煤油, 钻井, 售热, 蒸汽, 生猪). They match only an exact whole revenue line of a company whose Shenwan context holds the node (`how = context_exact`); the 3-character floor for ordinary aliases stays.
- `NodeMemberBuilder`: an exact match on a material node with no segment takes the company's sector segment (`ProductMatcher.find_sector_segment`). Lines are stripped of a "主营-" prefix. 工程承包 is a broad word.
- Coal: SEG_COAL_WASHING is re-parented under the coking-coal mining segment, and the coking by-products under coking. The coking-coal Shenwan L3 then has one root segment, so the sector fallback works again.
- Effect on FY2025:
  - mapped revenue including the sector fallback goes from 86.1% to 87.9%;
  - context_exact lines total 6,458 亿, all of them in the company's own sector (中国石化 煤油, 牧原 生猪, 华菱 / 首钢 板材).

### D-161 update 16
- Date: 2026-11-17. Batch 3 accepted by the user → `config/industry_chain/_changes/v4-20261117.yaml` (113 changes from 79 proposals). Sectors: 轻工制造, 纺织服饰, 交通运输, 商贸零售, 社会服务, 传媒, 环保, 美容护理.
- The bare 服装 context alias was left off garment OEM, so brand apparel lines are not booked as OEM.
- Generic parent segments were renamed to umbrella names: 造纸, 印刷, 物流, 贸易, 教育, 广告营销, 出版, 化妆品, 医疗美容. The environmental sector now has one root segment, which restores its sector fallback.
- Effect on FY2025:
  - mapped revenue including the fallback goes from 87.9% to 88.1%;
  - context_exact lines total 7,544 亿.
- Left open:
  - Shenwan L3 code 350209 still maps to two root segments. A change set cannot remove a sw_l3 entry yet.
  - 杭钢's steel lines sit in the recycling segment.

### D-161 update 17
- Date: 2026-11-17. Batch 4 accepted by the user → `config/industry_chain/_changes/v5-20261117.yaml` (30 changes). Sectors: 房地产, 银行, 非银金融, 综合.
- Non-bank finance gets one root segment (非银金融业) with 证券 / 保险 / 多元金融 under it. Generic 2-character finance names (租赁, 证券, 保险, 期货, 信托, 资产管理, 房地产) become context aliases only.
- `ProductMatcher` change: a label that suffix stripping cuts below 3 characters (代理业务 → 代理, 同业业务 → 同业) now matches a line exactly only inside the company's context. Labels written with 2 characters (电煤, 生猪) are unchanged. Covered by TC-PM-010.
- With this, the Opus node curation of all 31 Shenwan sectors is done: v1–v5, 471 changes.
- Effect on FY2025:
  - mapped revenue including the fallback is 88.0%;
  - 中国外运 (570 亿) and 智飞生物 (77 亿) leave the banking segment;
  - the leasing segment goes from 131 companies to 5.

### D-168 Plan 31 sector monitor: public sources, game links, briefs through operating_data
- Status: accepted (2026-11-17, user: "可以，一线加二三线平均就行，继续"). Plan 31 ph1–3.
- Context:
  - data.stats.gov.cn answers 403 to this host (WAF UrlACL). The 国家统计局 release pages and the 国家新闻出版署 lists are reachable as plain HTML.
  - Rules alone link 2% of 版号 approvals to listed companies, because the holders are subsidiaries with other names.
  - Developers' 销售简报 were not in the announcement datasets.
- Decision:
  - **70-city prices:** dataset `house_price_70` holds city-level indices from the release pages (`NbsHousePriceClient`). Tier averages are simple means over the 4 tier-1 cities and the 二线 / 三线 lists in config; they are not NBS's weighted tier figures. The user chose 一线 plus 二 / 三线 averages, with no city picker.
  - **版号:** dataset `game_license` (`NppaGameClient`), domestic and imported lists, known_on = the list's publication date.
  - **Game ↔ company:** holder names resolve by rule, else through a DeepSeek alias proposal (`game_alias`, lake script) that is checked by rule (`EntityResolver.find_by_alias`). Publishing houses are kept without a company. Unresolved holders go to a review list and are never guessed.
  - **Sales briefs:** the cninfo keyword sweep gains 简报, and the `operating_data` title rule gains 销售…简报. The existing `OperatingDataExtractor` (plan 18) reads the briefs, so the planned `SalesBriefExtractor` is dropped.
- Consequences:
  - The tier averages can differ from NBS's published tier numbers by a few hundredths. October 2026 tier-1 second-hand MoM is +0.20% both ways.
  - Brief coverage follows what each developer files: 万科 stopped in 2025-01, and 滨江 / 金地 file none.

### D-169 Plan 32: market-wide buyback and 增持 monitor labelled from plan announcements on Ark
- Status: accepted (2026-11-17, user: "监控所有回购，可以用方舟计划lable", then "分清楚吧，都标记好"). Plan 32.
- Context: plan 23 shows only the book's buyback events and new plans ≥ 2% of market cap. Tushare `repurchase` has no purpose or funding source, and 增持 plans (often funded by 增持专项贷款 since 2024-10) have no structured plan data. D-154 left buyback purpose open.
- Decision: CNINFO plan announcements (searchkeys 回购, 增持; doc_types `buyback_plan`, `holder_increase_plan`) are labelled by `BuybackTermsExtractor` on the Ark Coding Plan (D-122) into LabelStore set `buyback_terms`. Fields: kind 回购 / 增持, purpose or holder type, funding, loan, amount range, price cap, period, each with a checked quote. Buybacks and 增持 always stay apart by `kind`. History starts 2024-01; no phone alert.
- Alternatives: title-only rules (rejected: purpose and funding sit in the body); Tushare `stk_holdertrade` alone for 增持 (rejected: it has execution, not plans).
- Consequences: two new doc_types in the shared CNINFO config; about 5.8k buyback and several thousand 增持 LLM calls for the backfill, gated by a 100-document pilot.

### D-111 update 1
- Date: 2026-11-17. Found in plan 31 ph3: `CninfoClient` dropped the last page of every query.
- Cause: CNINFO's `totalpages` is one short when the total is not a multiple of the page size (84 rows → 2 pages, 1,224 → 40, 57 → 1). The client read pages 1..totalpages, so up to 29 announcements per query were missing from `cninfo_announcements` and `cninfo_keyword_announcements` since D-111. Examples: 招商蛇口's June, July and October 2026 sales briefs.
- Fix: the page count is max(totalpages, ceil(totalAnnouncement / 30)), still capped at MAX_ROWS. Covered by TC-CNC-005.
- Both datasets are being re-fetched with `--force` (append; rows are only added).
- After the re-fetch, `download-docs` and the label runs pick up the recovered documents on their next pass.

### D-137 update 1
- Date: 2026-11-17. Plan 19 ph2, at the user's request ("游戏行业应该给我排行榜的信息啊").
- The publisher link is a hand-curated map, `config/app_publishers.yaml`: App Store seller account (artist_id) → company and listed code (A / HK, null when the company is not listed). Accounts were found in the charts. When an account's name doesn't name its company, the YAML comment gives the evidence: the store page copyright, the 版号 holder (game_company), or the title's known owner.
- Changed from the plan: there is no `derived.app_chart_company` view. `portfolio.AppRankReader` joins the map in Python over `curated.app_store_charts`. A view would need the YAML loaded into DuckDB on every refresh for about 40 rows. The 7- and 30-day mean ranks wait until there is enough history: 5 captures as of 2026-11-17.
- The results go in the #sector-monitor 游戏 sector (plan 31, D-168):
  - an `app_rank` chart: each company's best China grossing rank, axis inverted;
  - a table column;
  - a leaderboard: the companies' games with China grossing and free ranks, best overseas grossing rank and number of overseas markets, plus the China top 20 with each game's company.
- Alternatives:
  - Rejected: link through 版号 titles. Store names rarely match licence titles; 3 of the 6 companies matched.
  - Rejected: an LLM mapping. Mostly English seller names; small list; wrong links are costly.
- Consequences: an unmapped account shows no company. The Log lists unmapped China top-50 publishers for review. 完美世界 and 恺英网络 have no game in any market's top 100, so they have no account yet.
- Same day, after the user asked whether every game company was covered ("所有的游戏公司都有吗？"):
  - The leaderboard now lists the games of every A-share company in the map, not only the six sector companies. The company table and charts keep the six.
  - Seven 申万游戏Ⅱ accounts were added: 恺英, 游族, 冰川, 汤姆猫, 电魂, 星辉, 宝通.
  - 15 of the 26 listed members have no game in any market's top 100. The YAML header names them.

### D-168 update 1
- Date: 2026-11-17 (plan 31 ph3 check). 新城控股 titles its monthly briefs 经营简报, so the operating_data title rule gains `经营简报`. Across both CNINFO datasets this adds 130 documents, all operating data: 新城 37, 申通 36, 顺丰 36, 华夏幸福 12, 东华科技 8, 滨江 1. Check: 招商蛇口's monthly 签约 for 2026-01..10 sums to 1,587.7亿, against 1,588亿 in its 10月 brief.

### D-170 Plan 33: definitions of the sector-monitor signals
- Status: accepted (2026-11-17, user: "可以" to the six proposed indicators). Plan 33.
- Context: the 行业监控 tab (plan 31) shows levels, so turning points are hard to read. The user asked which indicators to add.
- Decision:
  - **sales_yoy:** year-on-year change of the 3-month rolling sum of monthly contracted sales, computed from the brief levels, not from the yoy figures the briefs print. The table shows the year-to-date yoy.
  - **house_price_breadth:** the number of the 70 cities with month-on-month index < 100, for 新房 and 二手.
  - **New games:** apps released within `new_game_days` (90) that are, at the latest capture, on the home grossing or free top 100, or on any overseas grossing top 100. Every publisher is included; the company is shown when the account is mapped.
  - **valuation:**
    - Measure: PB for 房地产, PE TTM for 游戏, set per sector in config.
    - Source: companies from `daily_basic`, the index from `sw_daily`.
    - Percentile: over the last 1,250 sessions (about 5 years), with at least 250 observations.
    - Loss-makers: a PE ≤ 0 or missing PE gives no value.
  - **Revision:** FY1 is the as-of year from May on, otherwise the year before. For each window, take the median `report_rc` net profit forecast for FY1 over the reports of the trailing 90 days. The revision is the % change of that median against the window ending 90 days earlier, computed only when both windows target the same FY.
  - **Surveys:** distinct `stk_surv` survey dates per company per month. The table shows the last 90 days.
- Alternatives:
  - Rejected: the briefs' printed yoy figures. Not every brief prints them, and the bases differ.
  - Rejected: a consensus from mean EPS. Share counts change, and medians are robust to stale outliers.
- Consequences: new metric keys and settings in config/sector_monitors.yaml; a new MarketSignalReader; no new datasets.
- Update (same day): the revision median takes **one value per broker**, its latest report in the window. Repeated notes from one broker skewed the median: 申万宏源's 8亿 FY2026 note for 招商蛇口 appeared 8 times in 90 days, which made the revision −34%. With one value per broker it is −11.7% (12.71亿 → 11.22亿).
- Update (same day): no revision is computed when either median is ≤ 0. A % change of a forecast loss is meaningless: 万科 forecasts losses, and near-zero profits gave −700% spikes on the 房地产 chart. The range is now −80% to +45%.

### D-171 Plan 34: rates and RMB monitor sources and definitions
- Status: accepted (2026-11-18, user: "show in app" after the plan 34 draft; defaults taken for alert levels, currencies and no phone alert). Plan 34.
- Context: the user asked for a 国债利率 monitor and then for RMB against the dollar and other currencies. `cn_bond_yield` and `fx_daily` were downloaded daily but shown nowhere; the PBOC fixing and US yields were not in the lake.
- Decision:
  - **New datasets (AkShare, D-065):** `cny_fixing` from `currency_boc_safe` (SAFE central parity, all 25 currencies, since 1994, known_on as_is: published 09:15 the same day) and `us_treasury_yield` from `bond_zh_us_rate` (US 2Y / 5Y / 10Y / 30Y since 2015, next_session). Both refresh in `make market-data` (MARKET_RANGE_DATASETS).
  - **Onshore USDCNY close is left out:** no stable daily source was found; the spot−fixing gap uses offshore USDCNH (FXCM mid) instead.
  - **Lines (config/rates_fx_monitor.yaml):** 中债国债 1Y–30Y; term spreads 10Y−1Y, 30Y−10Y; credit spreads AAA bank 10Y and AAA notes 3Y over govt; 1Y govt − SHIBOR 3M; 股债性价比 = CSI 300 earnings yield − 10Y; USDCNH, USD fixing, USDCNH ÷ fixing − 1, EURUSD, USDJPY, EUR/CNH, CNH/JPY, HKD and GBP fixing, FXCM USDOLLAR, US 10Y, 中美利差 10Y.
  - **CSI 300 earnings yield:** Σ total_mv / pe_ttm ÷ Σ total_mv over the members of the latest `index_weight` date on or before each day; loss-makers (no pe_ttm) count in market value only, so the yield is slightly understated.
  - **Statistics:** changes over 5 / 21 / 63 / 250 observations (bp for yields and spreads, % for FX); percentile over the last 5 years with ≥ 250 observations; 1-year range excludes today.
  - **Alerts:** 10Y extreme (new 1-year low / high) or weekly move ≥ 10bp; 30Y weekly move ≥ 10bp; credit spreads widening ≥ 10bp in a week; 股债性价比 ≥ 90th percentile; USDCNH extreme or weekly move ≥ 1%; |USDCNH ÷ fixing − 1| ≥ 1%; 中美利差 extreme. App and e-mail only, no phone alert.
- Alternatives:
  - Rejected: FXCM 10USNOTE for the US 10Y. It is a price, not a yield.
  - Rejected: index_dailybasic for the CSI 300 PE. It is not in the lake.
- Consequences: two new datasets, config/rates_fx_monitor.yaml, `make rates-fx-monitor` in track-daily, `#rates` tab, 利率汇率 block in the 持仓监测 e-mail.

### D-172 Plan 35: sector earnings-season top signal definitions
- Status: accepted (2026-11-18, user: "可以" to plan 35). Plan 35. Implementation note: a preview dated before its quarter end counts as the first disclosure; deciles, share and the signal date use the events with a SUE and a pre window (the research basis).
- Context: research runs 20261118_priced_in / _tech / sector_peak_signal showed A-share earnings news is mostly priced before disclosure (52% of the top–bottom spread pre60, post20 ≈ 0), and that a rallied sector whose best-surprise companies no longer rise on the news underperforms (fwd60 −6.1% vs +0.3%, t −2.9, n 25).
- Decision:
  - **Event:** one per (ts_code, end_date), dated at the first of forecast_vip / express_vip / income_vip (report_type 1) ann_date; first trading day on or after it is day 0.
  - **Surprise:** SUE = (single-quarter parent net profit − same quarter a year earlier) ÷ std of the prior 8 such changes (≥ 4); deciles within end_date.
  - **Excess:** log return minus the equal-weight mean of all A shares (BJ excluded; |daily log return| ≥ 0.25 dropped); windows pre60 [-60,-1], react [0,+1], post20 [+2,+21].
  - **Sector:** SW L2, membership point in time at end_date; best-surprise = global deciles 8–9, ≥ 5 events; firing = pre60 ≥ 15% and react ≤ 1% once ≥ 80% of the sector's events are out; rally = 120-session sector-index excess vs the mean L2 index ≥ 20%.
  - **Output:** app and e-mail only, no phone alert.
- Alternatives:
  - Rejected: consensus surprise from report_rc. Coverage is too thin outside large caps.
  - Rejected: shareholder-count crowding as a trigger. Rally sectors with holders ≥ +10% went on to fwd60 +1.8%. It is shown as context only.
- Consequences: `derived/earnings_events`, config/sector_earnings_signal.yaml, `make earnings-events` and `make sector-earnings-signal`, a 财报季信号 table in `#sector-monitor`.

### D-173 Plan 36: linear-pricing gap factor definition
- Status: accepted (2026-11-18, user: "可以"; score inclusion "可以，加进综合打分", kept after the campaign with "放进去吧，当个指标看一看"). Plan 36. Campaign result: pricing_gap fails FACTOR_TESTING_DESIGN §6 criteria 1–2 (20-day NW t 1.55, sub-periods 0.61 / 1.80 / 0.98); the score with it is unchanged within noise (IC 0.0679 → 0.0691, LS Sharpe 1.20 → 1.19). Kept at weight 1 as an indicator to watch, against the agent's revert recommendation; revisit at the next campaign.
- Context: research run 20261118_linear_pricing_gap. The gap between the market cap and a consensus-based value with fading growth predicts 20-day returns: IC −0.053, net FM t −3.7. On equal weight with industry + size neutralisation, the long-short earns 10.4% a year net, Sharpe 0.86. The edge is in small and mid caps; for large caps only avoiding the dear end works.
- Decision:
  - **Consensus:** report_rc, report_date in (t − 90 days, t], latest note per broker and fiscal year, median np. FY1 = the as-of year from May, else the year before. FY1 and FY2 must be > 0; a missing FY3 = FY2 × FY2/FY1.
  - **Value:** FY1–FY3 discounted at 9% from each fiscal year end (FY1 end floored at 0.1 years). Then growth starts at FY2→FY3 (clipped to [−0.3, 1.0]) and fades ×0.7 a year for 7 years. Exit at PE 15.
  - **Factor:** `pricing_gap` = log(total_mv ÷ value), sign −. Campaign standard: winsorise, standardise, Shenwan L1 + log mcap neutral (D-093), equal-weight deciles.
  - **Use:** in the composite score at weight 1 (amended 2026-11-18, user: "可以，加进综合打分"). Run 20261118_pricing_gap_complement: score + pricing_gap 20-day IC 0.051 → 0.054, decile LS Sharpe 0.75 → 0.98 (large caps 0.50 → 0.71). The veto was dropped: inside the score's top quintile it adds 0.12%/yr.
  - **Fixed in advance:** the parameters were set before the first test, with one sensitivity run (fade 0.5, PE 20: net t −3.57). They are not tuned on returns.
- Alternatives:
  - Rejected: buy signals on the cheap side for large caps (−0.12% a month).
  - Rejected: cap weighting as the evaluation basis (Sharpe 0.42). The user chose equal weight.
  - Rejected: a revision filter on the cheap leg. It added nothing (14.6% vs 14.9%).
- Consequences: a consensus panel in FactorInputs (also enables forward EP later); a new factor line; a `pricing_gap_pct` condition metric.

### D-174 Plan 25: intraday reversal replaces reversal_1m in the score
- Status: accepted (2026-11-18; the plan 25 default approved 2026-11-14, user: "ok"; run on "先做计划25"). Plan 25 named this decision D-156, a number already used for the futures-spread flag.
- Context: the plan 04 campaign (run 5f65090ede53) tested reversal_intraday_1m (minus intraday returns on the 10 highest-turnover of the last 21 sessions).
  - reversal_intraday_1m passes FACTOR_TESTING_DESIGN §6 criteria 1–3: 20-day IC 0.0664, NW t 8.17, sub-period t 4.72 / 5.97 / 3.39, ICIR 0.95 (CI 0.79–1.14), quintile LS Sharpe 1.71.
  - reversal_1m: IC 0.0515, t 4.91, ICIR 0.57, LS Sharpe 1.04.
  - The two factors have rank correlation 0.67. In a joint Fama-MacBeth, reversal_1m adds t 0.31.
  - Raw month-end IC 0.0761 reproduces the research (0.076). The TrialLog holds 79 trials, including the 7 research variants.
- Decision: in config/factors.yaml campaign.weights, reversal_intraday_1m replaces reversal_1m at weight 1. reversal_1m stays in the campaign as a single factor, as ep_ttm did under D-147.
- Alternatives:
  - Rejected: keeping both, which doubles the reversal weight (correlation 0.67).
  - Rejected: keeping reversal_1m, which is weaker on every horizon from 5 to 60 days.
- Consequences: derived/features rebuilt and the campaign rerun with the new score. The score's factors are not shown by name in the app, so no app change is needed. Result:
  - 20 days: score IC 0.0691 → 0.0718, ICIR 0.770 → 0.788; LS Sharpe 1.19 → 1.18 (unchanged).
  - 60 days: IC 0.0847 → 0.0921, ICIR 0.98 → 1.07, LS Sharpe 0.94 → 1.04.

### D-180 Plan 37: analyst descriptors adopted in the risk model (cne5_v4)
- Status: accepted (2026-11-18, user: "新版"). Plan 37 phase 2 gate.
- Context: cne5_v3_dy (D-148) had trailing-only Earnings Yield (CETOP, ETOP) and Growth (EGRO, SGRO). Plan 37 added the CNE5 analyst descriptors from the plan 36 consensus panel. Gate run f39696bd936d against cne5_v3_dy on the same dates (report research_space/runs/20261118_risk_v4_gate):
  - adj R² 0.2745 → 0.2744 (last year 0.3039 → 0.3038);
  - 100 random portfolios: in band 100% both, median bias 1.026 → 1.026;
  - CSI 300 / 500 / 1000 bias 0.927 / 1.087 / 1.051 → 0.926 / 1.086 / 1.050;
  - factor bias: Earnings Yield 1.032 → 1.062, Growth 1.007 → 1.000;
  - |t| > 2 on 43% (Earnings Yield) and 44% (Growth) of days.
- Decision: config/risk_model.yaml becomes cne5_v4 with consensus_days 90; Earnings Yield = EPFWD 0.68, CETOP 0.21, ETOP 0.11; Growth = EGRLF 0.18, EGRSF 0.11, EGRO 0.24, SGRO 0.47 (CNE5 weights; a stock without consensus renormalises over the descriptors it has). EPFWD blends FY1 / FY2 by months left in FY1; EGRSF = FY2/FY1 − 1; EGRLF = (FY3/FY1)^(1/2) − 1.
- Alternatives:
  - Rejected: keeping cne5_v3_dy. The gate is neutral; v4 completes the CNE5 design and the exposures follow market expectations.
- Consequences: the risk model depends on report_rc; a stale consensus mislabels Earnings Yield exposure until brokers revise. Exposures move at month ends. The Earnings Yield factor bias (1.06) is within the band and is watched at the next refit. Style names are unchanged, so the app and morning report need no change.


### D-181 Plan 38: update task ledger as append-only parquet parts, not RunLog
- Status: accepted (2026-11-18, user: "ok"). Plan 38.
- Context: the user asked for a parquet record of every update task and one command that runs all updates in order. `make track-daily` stops at the first failure and records nothing per step. RunLog (D-022) writes `meta.run_log` in DuckDB, which needs the single catalog writer lock that download, compact, curate and risk-model take themselves.
- Decision: `update-all` runs the make targets listed in config/update_all.yaml as subprocesses. After each step it writes one zstd parquet part to `meta/task_log/` (tmp + rename, as for the document manifest, D-101). It refreshes a view `meta.task_log` once at the end. A failed step does not stop the run; steps whose `needs` failed are skipped. `track-daily` delegates to `update-all`.
- Alternatives:
  - Rejected: RunLog rows, because the orchestrator would hold or fight for the catalog lock between every step.
  - Rejected: a Prefect flow over all steps. Prefect is optional (extra `flows`) and adds a server dependency for a sequential list.
  - Rejected: `make -k`, which continues past failures but records nothing and cannot skip dependents.
- Consequences: the Makefile stays the single source of each step's commands; the YAML holds only order, dependencies and timeouts. The ledger survives a crash mid-run, with the rows written so far.


### D-182 Plan 21 ph6: RetailGauge stays out of the risk model and joins the score
- Status: accepted (2026-11-19, user: "Add at weight 1 (Recommended)"). Plan 21 phase 6.
- Context: phase 6 tested the 散户温度计 (derived.retail_gauge, daily from 2022-05) two ways (research run 20261118_gauge_risk_style).
  - Risk style `retail_crowding`: pct orthogonalised to size and standardised like the other styles, added to the model's own constrained WLS on the stored cne5_v4 exposures (FactorReturnEstimator.compute_monitor; the base R² matched the fitted model on all 19 check dates), 2022-06 → 2026-11, 1,083 sessions. |t| > 2 on 50% of days (styles 23–78%); factor vol 1.8%/yr (styles 0.9–7.3%); mean return −5.8%/yr, t −6.7, negative every year; R² gain +0.001; cap-weighted correlation with every style ≤ 0.2 in absolute value. The score's style-residual IC20 is 0.0189 without the style and 0.0192 with it (large caps 0.0092 → 0.0102).
  - Score input: factor `retail_gauge` (RetailGaugeFactor, −pct, industry + size neutral) in the campaign, run 09f20ffab055. 20-day IC 0.041, NW t 3.79, BHY p 0.0015 (criterion 1 passes); sub-periods 2022–24 t 4.06, 2025– t 1.91, 2019–21 empty (criterion 2 fails on the missing period only); ICIR CI 0.53–0.87 (criterion 3 passes). Month ends 2022-06 → 2026-10: score IC20 0.0673 → 0.0751 with the gauge at weight 1 (t 5.14 → 5.65), IC60 0.0865 → 0.0966, decile long-short Sharpe 1.16 → 1.29; large caps IC20 0.0671 → 0.0720, Sharpe 0.84 → 0.83.
- Decision:
  - Risk model: no `retail_crowding` style. It explains almost no return variance; its steady negative return is alpha, which a risk-neutral optimisation against a model containing it would remove.
  - Score: `retail_gauge` joins the campaign weights at 1.0 (config/factors.yaml).
- Alternatives:
  - Monitor style (D-130) for exposure reporting only: not needed; the daily gauge and its avoid flags already show crowding per stock.
  - Score weight 0.5: not tested; the equal-weight convention of the other seven inputs is kept.
- Result after adoption (campaign run e19de0698424, 2019–2026 daily): score 20d IC 0.0718 → 0.0755, NW t 3.97 → 4.12; 60d IC 0.0963; LS Sharpe 1.22.
- Consequences: the score depends on the daily retail-gauge run (step after the market-data downloads) and starts 2022-05; earlier months keep 7 inputs (SignalCombiner averages what is present, min_factors 3).

### D-161 update 18
- Date: 2026-11-19. Plan 28 ph4d: `node_edge` design.
- Grain: one row per year (period YYYY1231), supplier **segment** → buyer segment, kind `sales` (customer / supplier rows) or `invests` (holds / invests_in). Segments, not products: every mapped node_member line has a segment, products often do not, and the app's industry pages are segment pages.
- Evidence: only company_edge rows where both ends are A-share companies (other counterparties have no node_member). One observation per (year, src, dst, kind) however many documents state it, so weight = Σ over company pairs of w_src × w_dst (each side's segment weights from node_member: annual of the year, else interim, else latest earlier, else earliest later). The year is the edge period's year, or the known_on year when the period lies after known_on (forecast contract periods).
- Prior: taxonomy edges `upstream_of`, `component_of`, `used_in` (subject supplies object) and `uses_material` (object supplies subject), mapped to the segments of both ends; ends without a segment (most materials) and same-segment pairs dropped. Prior-only pairs get a weight-0 `prior` row in every year with members; pairs with both are `both`.
- Point in time: `--as-of` drops edges and node_member rows known after the date. Without it the table is "as known now" (a 2023 edge may use FY2024 members when FY2023 has none).
- Alternatives: product-level node edges (rejected: sparse, products missing for sector-fallback members); counting every observation in the weight (rejected: one customer named in five documents would count five times).
