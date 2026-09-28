# plans/execution/

Execution plans, `NN_<slug>.md`, from the `plan` skill template. `ROADMAP.md` is the single status board.

## Files
| File | Purpose | Contains |
|---|---|---|
| `00_model_roles.md` | pin Fable to planning/review and Opus to execution via agent, settings, hook, skill routing | 5 phases, exact config files, risks |
| `01_data_lake.md` | build the lake, Tushare client, pattern fetchers, compaction, PIT views, first charts, research entry | 6 phases, class table with planned callers, risks, log |
| `02_project_catalog.md` | load INDEX tree, registry, decisions, plans, datasets and AST into a `project` schema in the lake DuckDB | 4 phases, 12 tables, views, risks |
| `03_vix_calculation.md` | calculation package with CBOE-method VIX from option data: datasets, building blocks, formulas, pipeline step, iVIX validation | 5 phases, class table, risks |
| `ROADMAP.md` | every plan with what it builds, which design it implements, dependencies and status | roadmap table, status vocabulary |
