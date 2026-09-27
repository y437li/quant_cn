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
| D-007 | 2026-09-27 | Folder structure: config / src pkg / research_space | accepted | Plans/FOLDER_STRUCTURE.md |
| D-008 | 2026-09-27 | Plans local-first, Notion mirrors phases | accepted | .claude/skills/plan |
| D-009 | 2026-09-27 | Local data lake: parquet files + DuckDB catalog | accepted | Plans/plans/01_data_lake.md, FOLDER_STRUCTURE.md |
| D-010 | 2026-09-27 | Docstrings carry a Used by dependency map | accepted | CODING_STANDARD §3, §5; CLASS_REGISTRY |
| D-011 | 2026-09-27 | Linter toolchain: ruff, mypy, import-linter, contract linter | accepted | CODING_STANDARD §4.1, plan 01 phase 1 |
| D-012 | 2026-09-27 | Lake zones raw/curated/meta/external; `lake` package | accepted | FOLDER_STRUCTURE §2–3, plan 01 |
| D-013 | 2026-09-27 | Registry tracks per-method purpose in detail blocks | accepted | CLASS_REGISTRY §B, CODING_STANDARD §5 |
| D-014 | 2026-09-27 | INDEX.md in every folder, forming a tree from root | accepted | CODING_STANDARD §5.1, all folders |
| D-015 | 2026-09-27 | Plan 01 defaults: lake root, backfill depth, views first, names, notebook | accepted | Plans/plans/01_data_lake.md, config/base.yaml |
| D-016 | 2026-09-27 | Model roles: Fable plans + reviews, Opus executes | proposed | .claude/agents, CLAUDE.md, skills |
| D-017 | 2026-09-27 | Project catalog: repo tree + registry + plans queryable in lake DuckDB | proposed | Plans/plans/02_project_catalog.md |
| D-018 | 2026-09-27 | Packages managed by uv (pyproject + uv.lock, uv run) | accepted | CODING_STANDARD §4.1, FOLDER_STRUCTURE, plan 01 phase 1 |
| D-019 | 2026-09-27 | `visualization` package at L5, plotly, DataFrame-only inputs | accepted (library: proposed) | FOLDER_STRUCTURE §1, §3; plan 01 phase 6 |

### D-001 Plan first, standard is binding
- Context: new repo; user wants no code before an approved plan and a standard agents must follow.
- Decision: every non-trivial task starts with a plan in `Plans/plans/`; `CODING_STANDARD.md` is mandatory.
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
- Decision: see `Plans/FOLDER_STRUCTURE.md`; adds a `core` package for base classes and maps packages to layers.
- Alternatives: flat package without `core` (rejected: base classes would live in `data_loading` and create upward imports).
- Consequences: CODING_STANDARD §2.1 updated to these package names once accepted.
- Links: Plans/FOLDER_STRUCTURE.md

### D-008 Plans local-first, Notion mirrors phases
- Context: user wants phases tracked in Notion.
- Decision: markdown plan in `Plans/plans/` is the source of truth; the `plan` skill mirrors phases to a Notion database and stores the page URL in the plan header.
- Alternatives: Notion as source of truth (rejected: agents need the plan offline and in version control).
- Consequences: Notion auth must be completed once; until then plans carry `notion: pending`.
- Links: .claude/skills/plan/SKILL.md

### D-009 Local data lake: parquet files + DuckDB catalog
- Context: user asked for a local data lake on parquet with DuckDB managing the data; downloads come from the Tushare API.
- Decision: parquet is the storage of record (`data/lake/raw/<dataset>/year=YYYY/*.parquet`, immutable, hive-partitioned). One DuckDB file (`data/lake/meta/quant_cn.duckdb`) holds the catalog: views over every dataset, the `fetch_log`, dataset metadata (primary key, known-on column, units), and curated views (adjusted prices, deduped fundamentals). All reads go through DuckDB SQL; PIT alignment uses DuckDB `ASOF JOIN`.
- Alternatives: store tables inside the `.duckdb` file (rejected: single-file corruption risk seen before, less portable, harder to back up incrementally); parquet + pandas only (rejected: full scans, joins in memory, no SQL); SQLite landing zone (rejected: D-004 reasoning, slow scans).
- Consequences: classes `ParquetWriter`, `LakeCatalog`, `FetchLog`, `LakeQuery`, `PitAligner` in `data_loading`; the `.duckdb` file is rebuildable from parquet at any time (`LakeCatalog.rebuild()`); pin the `duckdb` version in `pyproject.toml`.
- Links: Plans/plans/01_data_lake.md, FOLDER_STRUCTURE.md, DATA_CATALOG §4

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
- Links: CODING_STANDARD §4.1, Plans/plans/01_data_lake.md

### D-012 Lake zones raw/curated/meta/external; `lake` package
- Context: user asked the folder structure to account for the lake; D-009 only fixed "parquet + DuckDB".
- Decision: four zones under `LAKE_ROOT`: `raw/` one file per fetch key (append-only, resumability), `curated/` yearly hive partitions with enforced schemas plus `derived/` (adjusted prices, PIT fundamentals), `meta/` DuckDB catalog + durable `fetch_log.parquet` + manifests, `external/` for legacy files. Storage/query classes move to their own `lake` package (L2) below `data_loading` (L3).
- Alternatives: single zone partitioned by year written directly by fetchers (rejected: resumability then needs row-level dedupe and rewrites of yearly files); lake classes inside `data_loading` (rejected: `statistic`/`back_testing` would import Tushare code to read data).
- Consequences: a `Compactor` step raw -> curated; `make lake-rebuild`; backups target `raw/` + `meta/fetch_log.parquet` only; layer table gains a row.
- Links: FOLDER_STRUCTURE.md §2–3, CODING_STANDARD §2.1, §2.7, Plans/plans/01_data_lake.md

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
- Links: Plans/plans/01_data_lake.md, FOLDER_STRUCTURE.md

### D-016 Model roles: Fable plans + reviews, Opus executes
- Context: user wants a strict split: Fable 5.1 for planning and code review, Opus for execution (writing code, tests, running phases).
- Decision (proposed; mechanism verified, see Plans/plans/00_model_roles.md): the main session runs Fable and owns the `plan`, `decisions`, `standard-review` and `code-review` work. Execution (`new-class`, `test-cases` scaffolding, plan `execute` mode, `index`/`registry` updates that accompany code) is delegated to a project subagent pinned to Opus. Fable never edits `src/`, `tests/`, `scripts/` or `config/` directly; Opus never edits `Plans/` or `DECISIONS.md` except the plan Log table. Fable reviews executor output with `standard-review` / `code-review` only when the user asks; review is not an automatic gate per phase (user, 2026-09-27).
- Alternatives: manual `/model` switching (rejected: not enforceable, easy to forget); one model for everything (rejected by user).
- Consequences: `.claude/agents/executor.md` (`model: opus`), `.claude/settings.json` (`model`, `availableModels`, PreToolUse hook), `.claude/hooks/guard_code_paths.sh` (deny code-path edits without `.claude/run/executor.lock`), `new-class`/`test-cases` skills run with `context: fork`, `agent: executor`. Hooks cannot see the active model (documented input has no model field), so enforcement is by path + run marker.
- Links: CODING_STANDARD §7, .claude/skills/plan/SKILL.md, .claude/skills/standard-review/SKILL.md

### D-017 Project catalog: repo tree + registry + plans queryable in lake DuckDB
- Context: user wants the tree structure maintained in the local data lake so an agent can read the project through DuckDB rather than opening many markdown files.
- Decision (proposed): a `project` schema in `meta/quant_cn.duckdb` with tables for folders, files, classes, methods, used_by, contracts, test_cases, decisions, plans, phases, datasets and lint findings, rebuilt from the markdown/YAML/AST sources by `ProjectCatalog` on every `make check`. Markdown remains the source of truth and is never written from SQL. Parsers live in `core.docs` and are shared with the contract linter.
- Alternatives: separate `project.duckdb` (rejected by user 2026-09-27: same file, schema `project`); agents grep markdown only (rejected: no joins, e.g. "which phases touch classes that call LakeQuery").
- Consequences: fourth view in the documentation stack: index -> registry -> docstring -> SQL; a `project-query` skill with recipe queries; `stale` view exposes drift.
- Links: Plans/plans/02_project_catalog.md, CODING_STANDARD §5.1, D-013, D-014

### D-018 Packages managed by uv
- Context: user instruction: "the package are managed by the uv".
- Decision: uv owns the environment. `pyproject.toml` + committed `uv.lock` + `.python-version` (3.12); `uv sync --all-extras` builds `.venv`; every tool runs via `uv run`; dependencies enter only through `uv add` / `uv add --dev`; upgrades via `uv lock --upgrade-package` with a decision entry for pinned-sensitive packages (duckdb).
- Alternatives: pip + requirements.txt (rejected: no lock, slower); poetry (rejected: user chose uv, already installed).
- Consequences: Makefile, pre-commit entries and CI use `uv run`; exact versions live in the lock, not in `==` pins.
- Links: CODING_STANDARD §4.1, FOLDER_STRUCTURE §1, Plans/plans/01_data_lake.md phase 1

### D-019 `visualization` package at L5, plotly, DataFrame-only inputs
- Context: user asked to add a visualization package in `src/`.
- Decision: `src/quant_cn/visualization/` at layer 5, mutually independent of `back_testing` and `portfolio` (import-linter contract). Charts accept DataFrames / `core` schemas only; producers expose `to_frame()`. All charts subclass `BaseChart` (theme tokens, size, `show()`, `to_html()`, `to_png()`). Library proposed: **plotly** (interactive in notebooks, HTML export, no display server); the `dataviz` skill's palette/form rules apply.
- Alternatives: matplotlib (rejected as primary: static only in notebooks; may be added later behind the same `BaseChart` for print export); a plotting layer inside `statistic`/`back_testing` (rejected: mixes presentation with computation, breaks independence).
- Consequences: eighth package and test folder; `plotly` added via `uv add`; first charts (`BaseChart`, `PriceChart`) built in plan 01 phase 6 for `main.ipynb`.
- Links: FOLDER_STRUCTURE §1, §3, §5; CODING_STANDARD §2.1, §4.1; Plans/plans/01_data_lake.md
