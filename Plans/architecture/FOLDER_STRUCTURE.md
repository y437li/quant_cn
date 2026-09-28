# Folder Structure Plan (v1.3, 2026-09-27; D-007, D-009, D-012, D-014, D-015, D-021, D-028, D-032)

Three areas from the user (config, package, research space) plus the data lake (D-009), a `core`
layer the standard needs, tests mirroring the package, and data kept out of git.

## 1. Repository

Every folder at every depth holds an `INDEX.md` (D-014): packages, sub-packages, test folders, skill
folders, plan folders. Shown explicitly below. Root `INDEX.md` -> folder `INDEX.md` -> `CLASS_REGISTRY.md` -> code.

```
quant_cn/
├── INDEX.md                      # top of the index tree: every top-level folder and file
├── CLAUDE.md                     # agent entry point
├── pyproject.toml                # package metadata + [dependency-groups]; ruff, mypy, import-linter, pytest, coverage config
├── uv.lock                       # exact resolved versions (uv, D-018); committed
├── .python-version               # 3.12, read by uv
├── Makefile                      # setup (uv sync), lint, check, lake-rebuild, download; every target runs `uv run ...`
├── .pre-commit-config.yaml
├── .env                          # git-ignored: TUSHARE_TOKEN, QUANT_CN_LAKE_ROOT (D-021)
├── .env.example                  # same keys, empty values
├── .gitignore                    # data/, *.parquet, *.duckdb, .env, config/local.yaml, research_space/**/outputs/
│                                 # (no .venv in the repo: UV_PROJECT_ENVIRONMENT=~/.venvs/quant_cn, exFAT volume has no symlinks, D-025)
│
├── config/                       # 1. configuration, no code
│   ├── INDEX.md
│   ├── base.yaml                 #    lake zones + root, universe rules, date ranges, download plan
│   ├── datasets.yaml             #    one entry per dataset: endpoint, sweep param, primary key, known_on, partition, fields, units
│   ├── local.yaml                #    git-ignored machine overrides: lake.root, lake.backup_target, download.default_start
│   └── README.md                 #    meaning of every key
│
├── src/
│   ├── INDEX.md
│   └── quant_cn/                 # 2. the package (installed editable by `uv sync`, D-018)
│       ├── INDEX.md              #    lists the eight packages and their layers
│       ├── core/INDEX.md         #    L1  Config, exceptions, BaseFetcher/BaseStore, Schema, DateCodec, TickerNormalizer, logging
│       ├── lake/INDEX.md         #    L2  ParquetWriter, LakeCatalog (DuckDB), FetchLog, Compactor, LakeQuery, PitAligner
│       ├── data_loading/INDEX.md #    L3  TushareClient, one fetcher class per sweep pattern; writes into the lake
│       ├── statistic/INDEX.md    #    L4  generic math on frames: winsorize, standardize, neutralize, IC, return stats, regressions
│       ├── calculation/INDEX.md  #    L4  domain financial computations: VIX (CBOE method), risk-free curve, option chains; later IV, greeks (D-032)
│       ├── factor/INDEX.md       #    L5  BaseFactor + concrete factors, FactorPreprocessor, FactorEvaluator, SignalCombiner (D-028)
│       ├── pipeline/INDEX.md     #    L6  resumable steps: download -> compact -> curate -> features (runs factors)
│       ├── back_testing/INDEX.md #    L7  engine, fills constrained by stk_limit, costs, results
│       ├── portfolio/INDEX.md    #    L7  position sizing, constraints, rebalancing schedules
│       └── visualization/INDEX.md#    L7  charts for prices, factors, backtest results; plotly, themed, notebook + HTML export
│                                 #    (each package folder: INDEX.md + __init__.py + one module per class)
│
├── scripts/                      # dev tooling, not part of the package
│   ├── INDEX.md
│   ├── lint_contracts.py         #    project linter (CODING_STANDARD §4.1)
│   └── lint.py                   #    runs ruff, mypy, lint-imports, lint_contracts in order
│
├── research_space/               # 3. exploration, never imported by the package
│   ├── INDEX.md
│   ├── main.ipynb                #    working notebook; imports only from quant_cn; reads via LakeQuery
│   ├── notebooks/INDEX.md        #    dated one-offs: YYYYMMDD_<topic>.ipynb, each listed with its question
│   └── outputs/                  #    figures/tables (git-ignored, no index)
│
├── tests/                        # mirrors src/quant_cn; conftest.py builds a tiny lake in tmp_path
│   ├── INDEX.md
│   ├── conftest.py
│   ├── test_contracts.py         #    runs the contract + index linter as a test
│   ├── core/INDEX.md  lake/INDEX.md  data_loading/INDEX.md  statistic/INDEX.md  calculation/INDEX.md  factor/INDEX.md
│   └── pipeline/INDEX.md  back_testing/INDEX.md  portfolio/INDEX.md  visualization/INDEX.md
│
│   (no data/ folder in the repo: the lake lives OUTSIDE it, see §2 and D-021)
│
├── plans/                        # governance by document type (D-023)
│   ├── INDEX.md                  #    what each type answers and its lifecycle
│   ├── standards/INDEX.md        #    CODING_STANDARD.md (binding)
│   ├── architecture/INDEX.md     #    FOLDER_STRUCTURE.md, SRC_DESIGN.md, DATA_LOADING_DESIGN.md (versioned designs)
│   ├── execution/INDEX.md        #    ROADMAP.md (status board) + NN_<slug>.md execution plans
│   ├── decisions/INDEX.md        #    DECISIONS.md (append-only log)
│   └── reference/INDEX.md        #    fresh_start/ Tushare handbook + data catalog
│
└── .claude/                      # agent tooling
    ├── INDEX.md
    ├── CLASS_REGISTRY.md
    ├── settings.json             # optional ruff PostToolUse hook (D-011)
    ├── notion.json               # Notion parent page id (created on first sync)
    ├── agents/INDEX.md           # planner / executor agent definitions (model pinning, pending verification)
    └── skills/INDEX.md           # one folder per skill, each with INDEX.md + SKILL.md:
        plan/  decisions/  test-cases/  new-class/  registry/  standard-review/  index/
```


## 2. The lake (`LAKE_ROOT`, outside the repo)

Resolved as env `QUANT_CN_LAKE_ROOT` > `config/local.yaml lake.root` > `config/base.yaml` default `~/quant_cn_lake`.
On this machine: `/Volumes/Treasury/quant_cn_lake/`, a sibling of the repo. `Config` refuses a root inside the
repository unless `lake.allow_inside_repo: true` is set (tests use `tmp_path`). Details: `DATA_LOADING_DESIGN.md` §1.

Four zones. Data only flows downward; each zone can be rebuilt from the one above it.

```
/Volumes/Treasury/quant_cn_lake/          # = LAKE_ROOT
├── raw/                                  # ZONE 1  landing: exactly what Tushare returned, one file per fetch key
│   ├── trade_cal/all.parquet             #   whole-history single calls -> one file, overwritten on refresh
│   ├── stock_basic/list_status=L.parquet │ =D.parquet │ =P.parquet
│   ├── namechange/all.parquet
│   ├── index_daily/ts_code=000300.SH.parquet  ...
│   ├── daily/trade_date=20260828.parquet      # daily sweeps: one file per trading day (~5.5k rows)
│   ├── adj_factor/trade_date=...  daily_basic/  moneyflow/  stk_limit/  cyq_perf/  margin_detail/
│   ├── fina_indicator_vip/period=20260630.parquet   # period sweeps: one file per quarter
│   ├── income_vip/  balancesheet_vip/  cashflow_vip/  forecast/  express/  disclosure_date/
│   ├── stk_holdertrade/ann_date=20260828.parquet    # event sweeps: one file per announce day
│   └── share_float/month=202608.parquet             # month-window sweeps (offset paging is broken)
│
├── curated/                              # ZONE 2  compacted + typed + deduped, hive-partitioned for DuckDB scans
│   ├── daily/year=2026/part-0.parquet    #   daily tables: one file per year (~1.4M rows), schema enforced
│   ├── adj_factor/  daily_basic/  moneyflow/  stk_limit/  ...
│   ├── fundamentals/income/year=2026/part-0.parquet   # report_type=1 kept, all ann_date versions kept
│   ├── reference/stock_basic.parquet     #   L+D+P merged, one row per ts_code
│   ├── reference/trade_cal.parquet  reference/namechange.parquet  reference/index_daily.parquet
│   └── derived/                          #   built from curated, never from raw
│       ├── prices_adj/year=YYYY/         #     close*adj_factor etc., dense on trade_cal optional
│       └── fundamentals_pit/year=YYYY/   #     latest version per (ts_code,end_date) visible at each trade_date (ASOF)
│
├── meta/                                 # ZONE 3  catalog and bookkeeping, fully rebuildable
│   ├── INDEX.md                          #   generated by LakeCatalog: every dataset, zone, partition count, last update (also in raw/ and curated/)
│   ├── quant_cn.duckdb                   #   views over raw/ and curated/, fetch_log, run_log (D-022), dataset_meta; schema `project` (plan 02); delete+rebuild any time
│   ├── fetch_log.parquet                 #   durable copy of fetch_log (endpoint, key, n_rows, fetched_at, file); DuckDB loads it
│   └── manifest/<dataset>.json           #   schema version, row counts per partition, last compaction, min/max key
│
└── external/                             # ZONE 0  files we did not download here (read-only)
    └── legacy_parquet/                   #   old repo exports (klines_daily, daily_basic, ...) if reused, plus a README of provenance
```

### Zone rules

| Zone | Written by | Mutability | Rebuild from | Partition key |
|---|---|---|---|---|
| `raw/` | `ParquetWriter` via fetchers | append-only; a key is fetched once, file existence + `fetch_log` = done | Tushare (costly) | the sweep key (`trade_date`, `period`, `ann_date`, `month`, `list_status`, `ts_code`) |
| `curated/` | `Compactor`, `Curator` steps | replaced per partition, never edited in place | `raw/` | `year=YYYY` of the primary date (`trade_date`, `end_date`, `ann_date`) |
| `curated/derived/` | `PitAligner`, price builders | replaced per partition | `curated/` | `year=YYYY` |
| `meta/` | `LakeCatalog`, `FetchLog` | rebuildable | `raw/` + `curated/` listing | — |
| `external/` | human | read-only | n/a | as delivered |

### File and naming conventions
- Hive style `key=value` directories/filenames so DuckDB `read_parquet(..., hive_partitioning=true)` exposes keys as columns.
- Writes are atomic: write to `<file>.tmp`, `fsync`, rename. A crash never leaves a half file.
- Parquet: zstd compression, row group ~256k rows, dictionary on `ts_code`; dates stay `YYYYMMDD` strings (D-005); Tushare column names unchanged in `raw/`; `curated/` may add derived columns but never renames.
- Every `curated/` partition has a `Schema` (columns, dtypes, invariants) declared in `config/datasets.yaml`; `Compactor` refuses to write a partition that fails it.
- Lake root comes only from `Config.lake.root` (env > local.yaml > base default). Nothing in the package hardcodes a path; the default is outside the repo.
- Lake folders are outside git, so their `INDEX.md` is **generated**, not hand-written: `LakeCatalog.write_indexes()` writes one into `lake/`, `raw/`, `curated/`, `curated/derived/`, `meta/` and `external/` after every download or compaction, listing datasets, partition counts, min/max keys and last update. Same table format as the repo indexes.

### Why zones
- Resumability lives in `raw/`: one file per fetch key means "is it done?" is a file check backed by `fetch_log`, and a crash loses at most one key.
- Query speed lives in `curated/`: yearly files avoid the small-file problem (raw `daily/` alone is ~250 files/year).
- Safety lives in the rebuild chain: only `raw/` is expensive; everything else is derived and can be thrown away. Back up `raw/` (and `meta/fetch_log.parquet`) with `rsync` to another disk; `make lake-rebuild` recreates the rest.
- `external/` keeps the old repo's exports usable without pretending they came through our fetchers.

### Test lake
`tests/conftest.py` builds a miniature lake in `tmp_path` (3 tickers, 10 days, 2 quarters) with the same zone layout, so `LakeCatalog`, `Compactor`, `LakeQuery` and `PitAligner` are tested against real parquet + DuckDB, never mocks.

## 3. Layer rules (mirrored in CODING_STANDARD §2.1)

| Layer | Packages | May import from |
|---|---|---|
| L1 | `core` | stdlib, pandas, pyarrow, duckdb |
| L2 | `lake` | L1 |
| L3 | `data_loading` | L1, L2 |
| L4 | `statistic`, `calculation` | L1–L3 (pure computation on frames; mutually independent) |
| L5 | `factor` | L1–L4 (may use both `statistic` and `calculation`) |
| L6 | `pipeline` | L1–L5 |
| L7 | `back_testing`, `portfolio`, `visualization` | L1–L6 |
| L8 | `cli.py`, `research_space` | anything in the package |

`statistic` and `calculation` never import each other or `factor`. `back_testing`, `portfolio` and `visualization` are
mutually independent: `visualization` plots DataFrames and `core` schemas only, so a backtest result is
plotted via its `to_frame()` output, never by importing `back_testing`. Nothing in `src/` imports `research_space`. Enforced by `import-linter` (D-011).

## 4. Why these choices
- **uv-managed (D-018, D-025)**: `uv sync` builds the venv at `~/.venvs/quant_cn` (outside the exFAT volume) from `uv.lock`; `uv run` executes every tool; `uv add` is the only way a dependency enters the project.
- **`src/` layout**: tests and notebooks import the same installed package.
- **`lake` separate from `data_loading` (D-012)**: storing/querying and fetching change for different reasons; `statistic`/`back_testing` need the lake but must never import Tushare code.
- **`core` added**: base classes must sit below every package.
- **`config/datasets.yaml`**: a dataset is data, not code. Adding one = a YAML entry (+ a fetcher subclass only for a new sweep pattern).
- **Notebooks import, never define**: reusable code found in `main.ipynb` is promoted to a class with a registry row.
- **Index tree (D-014)**: three granularities, one path down: folder indexes (files) -> registry (classes, methods) -> docstrings (contracts). The lake's own map is `meta/manifest/`, not `INDEX.md`, because `data/` is ignored.

## 5. First classes per package (plan 01)

| Package | Classes |
|---|---|
| core | `Config`, `QuantCnError` + subclasses, `BaseFetcher`, `BaseStore`, `Schema`, `DateCodec`, `TickerNormalizer` |
| lake | `ParquetWriter`, `LakeCatalog`, `FetchLog`, `RunLog`, `Compactor`, `LakeQuery`, `PitAligner`, `TradingCalendar` |
| data_loading | `TushareClient`, `FetcherFactory`, `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher` (one per sweep pattern, DATA_LOADING_DESIGN §2.2) |
| pipeline | `BaseRunner`, `LocalRunner`, `KeyExecutor`, `DownloadPipeline`, `CuratePipeline` (`PrefectRunner` deferred, D-022) |
| statistic | `Winsorizer`, `Standardizer`, `Neutralizer`, `ICCalculator`, `ReturnStats` (plan 04) |
| calculation | `BaseCalculation`, `RiskFreeCurve`, `OptionChainBuilder`, `TermSelector`, `ForwardPriceEstimator`, `VarianceStripCalculator`, `TermInterpolator`, `VixCalculator`, `CalculationFactory` (plan 03) |
| factor | `BaseFactor`, six concrete factors, `FactorPreprocessor`, `FactorEvaluator`, `SignalCombiner`, `FactorFactory` (plan 04) |
| back_testing, portfolio | base classes only until plan 05 |
| visualization | `BaseChart` (theme, size, export), `PriceChart` (candles + volume, adjusted), `PanelChart` (many tickers, small multiples); factor and equity-curve charts follow their producers (D-019) |

## 6. Open questions
None. All closed by D-007, D-012, D-015 on 2026-09-27.
