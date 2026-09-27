# Plans/plans/

Execution plans, `NN_<slug>.md`, from the `plan` skill template. Status lives in each file's header.

## Files
| File | Purpose | Contains |
|---|---|---|
| `00_model_roles.md` | pin Fable to planning/review and Opus to execution via agent, settings, hook, skill routing | 5 phases, exact config files, risks |
| `01_data_lake.md` | build the lake, Tushare client, fetchers, compaction, PIT views, research entry | 6 phases, class table, risks, log |
| `02_project_catalog.md` | load INDEX tree, registry, decisions, plans, datasets and AST into a `project` schema in the lake DuckDB for SQL access by agents | 4 phases, 12 tables, views, risks |
