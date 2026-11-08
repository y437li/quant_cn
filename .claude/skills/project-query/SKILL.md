---
name: project-query
description: Answer questions about the quant_cn repository with SQL against schema `project` in the lake's DuckDB (plan 02, D-017) instead of opening many markdown files - what exists, where, its purpose, who calls it, which tests cover it, what is not done, which decisions apply, what drifted. Use when asked "where is", "what calls", "is there a class that", "what's left", "which decision", "what's stale", or before new-class/registry lookups on a large tree.
---

# project-query

Schema `project` in `<QUANT_CN_LAKE_ROOT>/meta/quant_cn.duckdb` is a rebuildable mirror of the repo:
markdown and code stay the source of truth; the schema is dropped and rebuilt, never edited.

## Freshness
- `make check` ends with `make project-catalog`, and the pre-commit hook `project-catalog` refreshes it, so after
  either the schema matches the working tree. Rebuild by hand: `make project-catalog` (add `ARGS=--no-lint` to skip
  lint_findings). The command exits 1 while `project.stale` has rows.
- If you edited files since the last check, refresh first or the answer may be old.

## How to query (read-only)
```bash
make query SQL="SELECT * FROM project.todo"                  # rich table, 50 rows (ARGS not needed)
uv run --env-file .env python -m quant_cn.cli query "SELECT ..." --limit 200
```
Both open DuckDB read-only. DuckDB refuses a read-only open while another process writes (a running download,
curate or project-catalog): wait for it to finish and retry. Never open the file read-write for queries.

## Tables
| Table | Row = | Useful columns |
|---|---|---|
| `folders` | folder | `path`, `parent`, `purpose`, `depth`, `has_index` |
| `files` | visible file (git-aware) | `path`, `folder`, `purpose`, `contains`, `kind`, `lines`, `mtime`, `in_index` |
| `classes` | class in src/ | `name`, `module`, `layer`, `base`, `purpose`, `tests`, `added`, `in_registry`, `path`, `line` |
| `methods` | public method | `class`, `name`, `purpose`, `input_output`, `raises`, `in_registry`, `line` |
| `used_by` | Used-by edge | `callee_class`, `caller`, `caller_class`, `caller_method`, `note` |
| `contracts` | class/method docstring | `class`, `method`, `purpose`, `input`, `output`, `raises`, `test_cases` |
| `test_cases` | TC ID | `tc_id`, `class`, `description`, `test_function`, `test_file` |
| `decisions` | decision | `id`, `date`, `title`, `status`, `applies_to`, `context`, `decision` |
| `plans` / `phases` | plan / phase | `nn`, `title`, `status`, `decisions`; `plan`, `n`, `phase`, `done_criterion`, `status` |
| `datasets` | dataset | `name`, `endpoint`, `sweep_kind`, `primary_key`, `known_on`, `partition_curated` |
| `lint_findings` | linter finding | `check`, `path`, `line`, `message`, `run_at` |

Views: `tree` (indented folder tree), `class_graph` (used_by with both modules), `stale` (unindexed files,
folders without INDEX.md, classes/methods missing from the registry, lint findings), `todo` (phases not done).

## Recipes (each verified on the plan 01 build)
**1. Find a class by purpose**
```sql
SELECT name, module, purpose FROM project.classes WHERE purpose ILIKE '%trading day%' ORDER BY name;
```
**2. Who calls a class**
```sql
SELECT caller, note FROM project.class_graph WHERE callee_class = 'LakeQuery' ORDER BY caller;
```
**3. What a class depends on**
```sql
SELECT callee_class, callee_module FROM project.class_graph WHERE caller_class = 'DownloadPipeline' ORDER BY 1;
```
**4. Methods of a class with purposes**
```sql
SELECT name, purpose, input_output FROM project.methods WHERE class = 'PitAligner' ORDER BY line;
```
**5. What is not done**
```sql
SELECT plan, n, phase, status FROM project.todo;
```
**6. Decisions touching an area**
```sql
SELECT id, title, status FROM project.decisions WHERE applies_to ILIKE '%DATA_LOADING_DESIGN%' OR decision ILIKE '%PitAligner%' ORDER BY id;
```
**7. Tree of a folder**
```sql
SELECT entry, purpose FROM project.tree WHERE path = 'src/quant_cn' OR path LIKE 'src/quant_cn/%';
```
**8. Files in a folder**
```sql
SELECT name, purpose, contains, lines FROM project.files WHERE folder = 'src/quant_cn/lake' ORDER BY name;
```
**9. Test cases of a class**
```sql
SELECT tc_id, description, test_function, test_file FROM project.test_cases WHERE class = 'Compactor' ORDER BY tc_id;
```
**10. Test cases without a test**
```sql
SELECT tc_id, class FROM project.test_cases WHERE test_function IS NULL;
```
**11. Drift between docs and code**
```sql
SELECT kind, item, reason FROM project.stale;
```
**12. Datasets and their pit column**
```sql
SELECT name, sweep_kind, known_on, partition_curated FROM project.datasets ORDER BY name;
```
**13. Files closest to the size limit**
```sql
SELECT path, lines FROM project.files WHERE kind = 'py' ORDER BY lines DESC LIMIT 5;
```
**14. Open decisions**
```sql
SELECT id, title, status FROM project.decisions WHERE status ILIKE 'proposed%' ORDER BY id;
```

## Rules
- Quote rows you rely on; do not paraphrase a purpose or decision from memory.
- `stale` non-empty means docs and code disagree: fix the source (index, registry, docstring), never the schema.
- Data questions (prices, fundamentals) go to `raw.*`, `curated.*`, `derived.*` views or `LakeQuery`; `project.*`
  is about the repository only.
