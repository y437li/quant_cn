# 02 — Project catalog: the repo tree, registry and plans queryable in DuckDB

| | |
|---|---|
| Status | proposed, awaiting approval |
| Owner | user (approve) / executor (build) |
| Created | 2026-09-27 |
| Notion | pending |
| Decisions | D-014, D-013, D-017 |
| Depends on plans | 01 phase 3 (LakeCatalog, LakeQuery) |

## Goal
An agent can answer "what exists, where, why, who calls it, what is planned" with SQL against the lake's
DuckDB catalog, rebuilt from the markdown sources on every change. Markdown stays the source of truth.

## Scope
- In: parsers for `INDEX.md`, `CLASS_REGISTRY.md`, `DECISIONS.md`, `Plans/plans/*.md`, `config/datasets.yaml`, and the Python AST (classes, methods, docstring sections); a `project` schema in `meta/quant_cn.duckdb`; rebuild command and hook; SQL recipes for agents.
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
| 1 | Parsers in `core.docs` | `IndexParser`, `RegistryParser`, `DecisionsParser`, `PlanParser`, `DocstringParser`, `AstScanner` returning typed records; shared by `lint_contracts.py` (which stops having its own parsers) | each parser round-trips today's files; linter output unchanged | 01 phase 1 | todo |
| 2 | `ProjectCatalog` in `lake` | builds/refreshes schema `project` in the catalog DuckDB from parsers + disk; `rebuild()`, `refresh(paths)`; views above; `make project-catalog` | `SELECT count(*) FROM project.classes` equals registry rows; `tree` view reproduces the INDEX tree; rebuild is idempotent | 01 phase 3, 1 | todo |
| 3 | Keep it fresh | pre-commit hook and `make check` call `refresh`; executor agent prompt ends with refresh; `stale` view empty after `make check` | edit a file -> `make check` -> `stale` returns 0 rows | 2 | todo |
| 4 | Agent access | `.claude/skills/project-query/SKILL.md`: how to query (`duckdb data/lake/meta/quant_cn.duckdb -readonly`), 12 recipe queries (find class by purpose, who calls X, what is not done, which decisions touch a file, tree of a folder); CLAUDE.md reading order gains "or query `project.*`" | each recipe runs and returns the expected rows on the phase-2 build | 2 | todo |

## Classes

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `IndexParser`, `RegistryParser`, `DecisionsParser`, `PlanParser`, `DocstringParser`, `AstScanner` | new | core.docs | 1 | `ProjectCatalog`, `scripts/lint_contracts.py` (`ContractLinter`) |
| `ProjectCatalog` | new | lake | 2 | `make project-catalog`, pre-commit, `tests/test_contracts.py`, `.claude/skills/project-query` |
| `ContractLinter` | extend (use `core.docs` parsers; write `lint_findings`) | scripts | 1, 3 | `make lint`, pre-commit |

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
| 2026-09-27 | 2 | User approved same-file / separate-schema layout |
| 2026-09-27 | — | Drafted from user request: keep the project tree in the lake so agents read the project through DuckDB |
