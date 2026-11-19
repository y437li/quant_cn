# 02 — Project catalog: the repo tree, registry and plans queryable in DuckDB

| | |
|---|---|
| Status | phases 1–4 done 2026-09-27 (855585f; deviation: whole-schema rebuild only, D-042); phases 5–6 approved 2026-11-13 |
| Owner | user (approve) / executor (build) |
| Created | 2026-09-27 |
| Notion | pending |
| Decisions | D-014, D-013, D-017, D-144 |
| Depends on plans | 01 phase 3 (LakeCatalog, LakeQuery) |

## Goal
An agent can answer "what exists, where, why, who calls it, what is planned" with SQL against the lake's
DuckDB catalog, rebuilt from the markdown sources on every change. Markdown stays the source of truth.

## Scope
- In: parsers for `INDEX.md`, `CLASS_REGISTRY.md`, `DECISIONS.md`, `plans/execution/*.md`, `config/datasets.yaml`, and the Python AST (classes, methods, docstring sections); a `project` schema in `meta/quant_cn.duckdb`; rebuild command and hook; SQL recipes for agents.
- Out: editing markdown from SQL (one-way only); indexing notebooks' cell contents.

## Tables (schema `project`, all rebuildable)

| Table | Row = | Key columns | Source |
|---|---|---|---|
| `folders` | one folder | `path`, `parent`, `purpose`, `depth` | every `INDEX.md` header + parent's folder row |
| `files` | one file | `path`, `folder`, `purpose`, `contains`, `kind`, `lines`, `mtime` | `INDEX.md` file rows + disk stat |
| `classes` | one class | `name`, `module`, `layer`, `base`, `purpose`, `tests`, `added` | registry §A/§B + AST |
| `methods` | one public method | `class`, `name`, `purpose`, `input_output`, `raises`, `tc_ids` | registry §B method tables + AST |
| `used_by` | one edge | `callee_class`, `caller` (`package.Class.method` or notebook path) | docstring `Used by:` + registry |
| `contracts` | one docstring | `class`, `method`, `purpose`, `input`, `output`, `raises`, `test_cases` | AST docstrings |
| `test_cases` | one TC ID | `tc_id`, `class`, `description`, `test_function`, `test_file` | docstrings + `tests/` AST |
| `decisions` | one decision | `id`, `date`, `title`, `status`, `applies_to`, `context`, `decision` | `DECISIONS.md` |
| `plans` | one plan | `nn`, `title`, `status`, `decisions`, `depends_on` | plan header tables |
| `phases` | one phase | `plan`, `n`, `phase`, `deliverable`, `done_criterion`, `depends_on`, `status` | plan Phases tables |
| `datasets` | one dataset | `name`, `endpoint`, `sweep_kind`, `primary_key`, `known_on`, `zone`, `partition_raw`, `partition_curated` | `config/datasets.yaml` |
| `lint_findings` | one linter finding | `check`, `path`, `line`, `message`, `run_at` | last `lint_contracts.py` run |

Views: `tree` (recursive CTE over `folders` -> indented path list), `class_graph` (`used_by` joined both
ways), `stale` (files on disk missing from `files`, classes in AST missing from `classes`), `todo`
(phases not done, ordered by plan and dependency).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Parsers in `core.docs` | `IndexParser`, `RegistryParser`, `DecisionsParser`, `PlanParser`, `DocstringParser`, `AstScanner` returning typed records; shared by `lint_contracts.py` (which stops having its own parsers) | each parser round-trips today's files; linter output unchanged | 01 phase 1 | done (via 01 ph1, D-033) |
| 2 | `ProjectCatalog` in `lake` | builds/refreshes schema `project` in the catalog DuckDB from parsers + disk; `rebuild()`, `refresh(paths)`; views above; `make project-catalog` | `SELECT count(*) FROM project.classes` equals registry rows; `tree` view reproduces the INDEX tree; rebuild is idempotent | 01 phase 3, 1 | done |
| 3 | Keep it fresh | pre-commit hook and `make check` call `refresh`; executor agent prompt ends with refresh; `stale` view empty after `make check` | edit a file -> `make check` -> `stale` returns 0 rows | 2 | done |
| 4 | Agent access | `.claude/skills/project-query/SKILL.md`: how to query (`duckdb data/lake/meta/quant_cn.duckdb -readonly`), 12 recipe queries (find class by purpose, who calls X, what is not done, which decisions touch a file, tree of a folder); CLAUDE.md reading order gains "or query `project.*`" | each recipe runs and returns the expected rows on the phase-2 build | 2 | done |
| 5 | Structured phase status | `PlanReader` splits each phase status into `state` (todo / doing / blocked / done only), `state_date`, `commit`, `note`; the raw text stays in `status`. `project.phases` gains these columns and `todo` filters on `state`. A status that does not start with a valid state becomes a `lint_findings` row. The `plan` skill and `plan_template.md` fix the format `<state> <YYYY-MM-DD> (<commit>) — <note>`; existing plans are rewritten to it | TCs: each of today's 31 status spellings parses to the expected (state, date, commit, note); an invalid status yields one lint finding. Real catalog: every one of the 110+ phases has a valid `state`; `select state, count(*)` returns ≤ 4 groups; `make check` passes | 2 | done 2026-11-13 (uncommitted) — 112 phases parse to 4 states; legacy statuses parsed, not rewritten |
| 6 | Research log (分析记录) | Every ad-hoc analysis gets one row in `research_space/RESEARCH_LOG.md`: date, slug, question (user's words), script folder, output folder, one-line conclusion, follow-up (plan / decision ID or none). Scripts move from the session scratchpad to `research_space/runs/<YYYYMMDD>_<slug>/` (git, with INDEX.md; personal data only read at runtime from `config/local.*`); outputs go to the lake `meta/runs/research/<YYYYMMDD>_<slug>/` (outside git). A reader in `core.docs` loads the log into a new `project` table (name via `naming`; proposed `research_runs`); a `research-log` skill tells agents to record each analysis before ending the answer. Backfill the 2026-11-12/13 analyses (opportunity list, washout event study, metal futures curves, theme screens, retail-gauge nowcast) | TCs: log rows parse; missing script folder → lint finding; no holdings amounts in committed files (check against `config/local.positions.yaml` share counts). Real catalog: backfilled rows queryable with their output paths; `make check` passes | 5 | done 2026-11-13 (uncommitted) — 6 runs logged, research lint 0; make check blocked only by another session's dividend-yield factor |

## Classes

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `IndexParser`, `RegistryParser`, `DecisionsParser`, `PlanParser`, `DocstringParser`, `AstScanner` | new | core.docs | 1 | `ProjectCatalog`, `scripts/lint_contracts.py` (`ContractLinter`) |
| `ProjectCatalog` | new | lake | 2 | `make project-catalog`, pre-commit, `tests/test_contracts.py`, `.claude/skills/project-query` |
| `ContractLinter` | extend (use `core.docs` parsers; write `lint_findings`) | scripts | 1, 3 | `make lint`, pre-commit |
| `PlanReader`, `DocTableBuilder`, `ProjectCatalog` | extend (status fields, research table) | core.docs, lake | 5–6 | `make project-catalog`, `project-query` skill |
| `ResearchLogReader` | new (name via `naming`) | core.docs | 6 | `DocTableBuilder` |

## Risks
- Two sources drift (markdown vs DuckDB): mitigated by rebuild-on-check and the `stale` view; DuckDB is never edited by hand.
- Parsers coupled to markdown table formats: formats are fixed by the skills (`index`, `registry`, `decisions`, `plan`); a format change is a decision and a parser change together.
- Read-only access for agents: always open with `-readonly` so a query can never lock the writer during a download.

## Open questions
None. Closed 2026-09-27:
- Same DuckDB file (`meta/quant_cn.duckdb`), separate schema `project` (user approved).
- `contracts`/`methods` load both AST and registry; disagreements surface in the `stale` view and the linter decides.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-13 | 6 | Done (uncommitted). `core.docs.ResearchLogReader` / `ResearchRun` (TC-RLR-001..002), `ResearchLogChecker` (lint group `research`: slug, date, scripts path, privacy against the git-ignored book; TC-RSC-001..002), `DocTableBuilder` → `project.research_runs` (TC-DTB-004); `research-log` skill; naming §5 rows for runs and lake outputs; project-query recipes. Backfill: 6 runs in `research_space/RESEARCH_LOG.md`, 5 run folders re-run from the repo into `meta/runs/research/` (book what-if not re-run: lake lock held by another session). Catalog: research_runs 6 (all scripts_exist), phases 112, stale 0, lint_findings 0; release-lags ok. Checks: ruff format ok, mypy 191 files, layers KEPT, lint_contracts 0, 665 passed, go ok, vitest 21. Not green overall: one E501 in another session's new `factor/library/dividend_yield_factor.py` and `tests/core/test_config.py::test_tc_c_012_factors` (expects 6 factors; that session added a 7th to `config/factors.yaml`) — left to that session |
| 2026-11-13 | 5 | Done (uncommitted). New `core.docs.PhaseStatusParser` / `PhaseStatus` (TC-PSP-001..003) and `PlanStatusChecker` (lint group `plans`, TC-PSC-001); `PlanReader` takes the parser (TC-PR-003); `project.phases` gains state, state_date, commit, note (TC-DTB-003); `todo` filters on state; plan skill + template carry the format. Real catalog: 112 phases → todo 57, done 50, doing 4, blocked 1; lint `plans` 0. `make check` exit 0: ruff ok, mypy 188 files, layers KEPT, lint_contracts 0, 660 passed / 96% coverage, go ok, vitest 21, project.stale 0. Deviation: existing plans are not rewritten to the new format — the parser reads every legacy spelling and other sessions edit those plans concurrently |
| 2026-11-13 | 5, 6 | Added and approved (user: "我们lake里有专门记录我们的每个task的schema吗？" → "可以"). Catalog rebuilt the same day: plans 18, phases 110, stale 0; 31 distinct free-text phase statuses; ad-hoc analyses had no record outside the session scratchpad. D-144 |
| 2026-09-27 | 2 | `ProjectCatalog` (lake) builds schema `project`: 12 tables + views tree/class_graph/stale/todo in one transaction; `CodeTableBuilder`/`DocTableBuilder`, `DecisionsReader`/`PlanReader` in `core.docs`; `cli project-catalog` + read-only `query`; `LakeCatalog` read_only mode (855585f, quant-cn-b7). Evidence: project.classes 84 rows = registry A + D; tree view 44 rows = 44 folders; rebuild idempotent (TC-PJC-002) |
| 2026-09-27 | 3 | `make check` ends with `project-catalog`; pre-commit hook `project-catalog`; exits 1 while `project.stale` has rows (TC-PJC-003); live stale = 0 |
| 2026-09-27 | 4 | `.claude/skills/project-query/SKILL.md`: 14 recipes verified against the live catalog ("who calls LakeQuery" → 7; "todo" → 13 open phases). `make check`: ruff passed; mypy 64 files; Layers KEPT; lint_contracts 0; coverage 95%; 190 passed. Catalog counts: classes 84, methods 134, used_by 252, contracts 218, test_cases 161, folders 44, files 197, decisions 40, plans 4, phases 20, datasets 13. **Plan 02 done**; deviation: `rebuild()` whole-schema only (~1 s), no `refresh(paths)` |
| 2026-09-27 | 2–4 | Started by quant-cn-b7 after plan 01 completed |
| 2026-09-27 | 1 | Phase 1 (parsers in `core.docs`) delivered by plan 01 phase 1 via D-033 (7bd9b36); phase 2 can start after 01 phase 5 |
| 2026-09-27 | — | Plan approved by user ("approve") |
| 2026-09-27 | 2 | User approved same-file / separate-schema layout |
| 2026-09-27 | — | Drafted from user request: keep the project tree in the lake so agents read the project through DuckDB |
