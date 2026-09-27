# quant_cn

A-share quantitative research on a local data lake: Tushare Pro data stored as parquet, queried
through DuckDB with point-in-time-safe views, feeding statistics, backtesting and portfolio research.

> **Status:** planning and scaffolding. The standard, decisions and plans are written; the package
> skeleton exists with no classes yet. Next up: plan 01 phase 1 (toolchain + `core`).

## Layout

```
config/           YAML configuration loaded by core.Config (no code)
src/quant_cn/     the package, eight layered sub-packages
scripts/          dev tooling: contract linter, lint runner
research_space/   notebooks that import quant_cn; never imported by it
tests/            pytest suite mirroring src/quant_cn
data/lake/        local lake, git-ignored: raw/ curated/ meta/ external/
Plans/            coding standard, decisions, plans, data handbook
.claude/          class registry and agent skills
```

Every folder has an `INDEX.md`; start at [`INDEX.md`](INDEX.md) and walk down.

### Package layers

A layer imports only from itself or layers below it.

| Layer | Packages | Holds |
|---|---|---|
| L1 | `core` | base classes, exceptions, config, schemas, date/ticker codecs |
| L2 | `lake` | parquet writer, DuckDB catalog, fetch log, compactor, query API, PIT aligner |
| L3 | `data_loading` | Tushare client and fetchers; writes into the lake |
| L4 | `pipeline`, `statistic` | resumable download/curate/feature steps; factor and descriptive statistics |
| L5 | `back_testing`, `portfolio`, `visualization` | engine and costs; sizing and rebalancing; charts (mutually independent) |
| L6 | `research_space/`, CLI | notebooks and orchestration |

### The lake

| Zone | Contents | Rebuild from |
|---|---|---|
| `raw/` | exactly what Tushare returned, one parquet file per fetch key; append-only | Tushare |
| `curated/` | typed, deduped, yearly hive partitions; `derived/` adjusted prices and PIT fundamentals | `raw/` |
| `meta/` | `quant_cn.duckdb` catalog and views, fetch log, manifests | `raw/` + `curated/` |
| `external/` | files not downloaded here (read-only) | n/a |

Only `raw/` (and `meta/fetch_log.parquet`) is expensive; back those up, everything else is rebuildable.
Full design: [`Plans/FOLDER_STRUCTURE.md`](Plans/FOLDER_STRUCTURE.md).

## Setup

Packages are managed by [uv](https://docs.astral.sh/uv/) (D-018). Once plan 01 phase 1 lands:

```bash
cp .env.example .env        # set TUSHARE_TOKEN; optionally QUANT_CN_LAKE_ROOT
make setup                  # uv sync --all-extras
make check                  # lint (ruff, mypy, import-linter, contract linter) + tests
```

Secrets live only in environment variables or the git-ignored `.env`.

## Data rules

From the handbook in [`Plans/fresh_start/`](Plans/fresh_start/README.md):

1. Sweep by date, not by stock.
2. Include delisted and paused stocks (`list_status` L, D and P).
3. Align fundamentals on `f_ann_date` / `ann_date`, never `end_date`.
4. `daily` prices are unadjusted; adjust with `adj_factor`.
5. Downloads are resumable via the fetch log.

Dates stay `YYYYMMDD` strings and tickers stay Tushare `ts_code` in stored data.

## Working in this repo

Plan first, contract first. Read [`CLAUDE.md`](CLAUDE.md) and
[`Plans/CODING_STANDARD.md`](Plans/CODING_STANDARD.md) before changing code.

| Document | Purpose |
|---|---|
| [`Plans/CODING_STANDARD.md`](Plans/CODING_STANDARD.md) | binding standard: OOP, docstring contracts, layering, tests, workflow |
| [`Plans/DECISIONS.md`](Plans/DECISIONS.md) | append-only decision log |
| [`Plans/plans/`](Plans/plans/INDEX.md) | execution plans with phases and status |
| [`.claude/CLASS_REGISTRY.md`](.claude/CLASS_REGISTRY.md) | every class, base, exception and schema; search before writing |
