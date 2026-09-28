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
| D-022 | 2026-09-27 | Flow monitoring: built-in RunLog + rich; Prefect as optional adapter | accepted | DATA_LOADING_DESIGN §3, SRC_DESIGN §2.4 |
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
