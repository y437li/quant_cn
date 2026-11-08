# Naming Convention (v1.1, 2026-09-27, decisions D-029, D-030, D-031)

Binding for every file, folder and identifier in the repository and the lake. `lint_contracts.py --names`
(plan 01 phase 1 deferred item) enforces the file rules; ruff `N` rules enforce the identifier rules.

## 1. Universal rules
- ASCII letters, digits, `_`, `-`, `.` only. No spaces, no CJK in paths (CJK is fine inside files).
- **Folders are lowercase** `snake_case` (`plans/`, `research_space/`, `back_testing/`). No capitals anywhere in a path
  except the fixed governance file names below and Python's `__init__.py`.
- One thing per name: a file is named for its primary content, never for its author, date of creation or status
  (status lives inside the file and in `ROADMAP.md`).
- Rename = decision. Renaming a class, module, dataset or plan is logged with the `decisions` skill and applied
  to code, tests, registry, indexes and docs in one change.

## 2. Python
| Thing | Rule | Example |
|---|---|---|
| package folder | `snake_case`, noun, matches the layer table | `data_loading/`, `factor/` |
| module | `snake_case` noun = the primary class in `snake_case` | `parquet_writer.py` → `ParquetWriter` |
| family module | plural noun, holds small sibling subclasses of one base, ≤ 300 lines total | `fetchers.py` (four `*Fetcher`), `runner.py` (`BaseRunner`, `LocalRunner`) |
| library module | `<name>_<kind>.py` inside a `library/` folder, one class each | `factor/library/momentum_factor.py` → `MomentumFactor` |
| abstract base | `Base<Noun>` in `base_<noun>.py` | `base_fetcher.py` → `BaseFetcher` |
| exception | `<Noun>Error`, all in `core/exceptions.py` | `PermissionDeniedError` |
| schema constant | `UPPER_SNAKE` in `core/frames.py` | `PRICE_PANEL` |
| class | `PascalCase`; abbreviations capitalised as words | `PitAligner`, `TushareClient`, `LakeQuery` |
| method / function | `snake_case`, verb-first; full rules in §2.1 | `fetch_one`, `write_raw` |
| variable / attribute / parameter | `snake_case` noun; full rules in §2.2 | `n_rows`, `trade_date` |
| private | one leading underscore; no double-underscore name mangling | `_deep_merge` |
| constant | `UPPER_SNAKE` at module level | `PAGE_SIZE` |
| test module | `tests/<layer>/test_<module>.py`, mirrors `src/` | `tests/lake/test_parquet_writer.py` |
| test function | `test_<tc_id_lower>_<short_desc>` | `test_tc_pw_005_schema_refusal` |
| test helpers | `tests/conftest.py` (fixtures), `tests/support.py` (fakes, builders); fakes are `Fake<Noun>` | `FakeTushareClient` |
| scripts | `scripts/<verb>_<noun>.py` | `lint_contracts.py` |
| entry point | `cli.py` only | |

### 2.1 Methods and functions
Every method name starts with a verb from this table, then the object. The verb tells the caller what kind
of effect to expect; the contract docstring says the rest. Names that do not fit a row need a new row here
(a decision), not an exception.

| Verb prefix | Meaning | Returns | Side effects | Example |
|---|---|---|---|---|
| `get_` | look up something already in memory or cheap to derive | value; raises if absent | none | `get_spec(name)` |
| `find_` | look up, may not exist | value or `None` | none | `find_partition(year)` |
| `list_` | enumerate | `list[...]`, possibly empty | none | `list_keys(dataset)` |
| `read_` / `load_` | bring data in from disk / lake / config | DataFrame or object | I/O read | `read_raw(spec, key)`, `load()` |
| `fetch_` | bring data in from a remote API | DataFrame | network | `fetch_one(key)` |
| `query` / `sql` | run SQL against the catalog | DataFrame | read | `query.sql(text)` |
| `write_` / `save_` | persist | `Path` written | I/O write | `write_raw(spec, key, df)` |
| `build_` | construct an object or frame from parts | the built thing | none | `build(spec)` in factories |
| `compute_` | pure calculation on frames | DataFrame / number | none | `compute(panels)` |
| `validate_` / `check_` | verify; raise on failure | the validated input (validate) / `None` (check) | none | `validate(df)`, `check_root()` |
| `is_` / `has_` / `can_` | predicate | `bool`, never raises | none | `is_done(dataset, key)`, `has_rows()` |
| `ensure_` | make a state true if it is not already | `None` or the resource | idempotent write | `ensure_dirs()` |
| `to_` / `as_` | convert this object | new representation | none | `to_frame()`, `to_str(date)` |
| `from_` | classmethod constructor from a representation | instance | none | `from_spec(spec)` |
| `mark_` / `record_` / `log_` | append a fact to a log | `None` | append | `mark_done(...)`, `record_event(...)` |
| `run` / `execute` | do the class's main job end to end | report object | many | `run(start, end)` |
| `refresh_` / `rebuild_` | recompute derived state from its source | `None` / report | write | `refresh_views()`, `rebuild()` |
| `register_` / `add_` / `remove_` | mutate a collection the object owns | `None` | in-memory | `register(dataset)` |
| `normalize_` / `parse_` / `format_` | canonicalise a value | canonical value; raise on garbage | none | `normalize(raw)`, `parse(date)` |
| `open_` / `close` / `connect` | resource lifecycle; prefer context managers | resource / `None` | resource | `connect()` |
| `plot_` / `render_` | produce a figure / HTML | figure / str | none | `render()` |
| `sleep` / `wait_` | block for a duration or until a condition; `Clock` (and fakes) only, so tests never really wait | `None` | time passes | `clock.sleep(seconds)`, `wait_for_idle()` |

Rules:
- No bare nouns as method names (`data()`, `calendar()`); use a property for cheap derived attributes and a
  `get_`/`build_` verb otherwise.
- No `handle_`, `process_`, `do_`, `manage_`, `util`, `helper`, `misc`: they say nothing.
- One verb per method. If two verbs are needed (`load_and_validate`), split the method.
- Boolean-returning methods use `is_/has_/can_` and never raise; anything that can raise is `validate_/check_`.
- A method that returns a DataFrame names the frame in the docstring Output, not in the method name
  (`prices()` not `prices_df()`); the only exception is `to_frame()`.
- Private helpers follow the same verbs with a leading underscore (`_write_atomic`).
- Standalone functions (only `core/utils`) follow the same table.

### 2.2 Variables, attributes and parameters
| Rule | Example |
|---|---|
| Tushare fields keep Tushare names everywhere (`ts_code`, `trade_date`, `ann_date`, `end_date`, `period`) | `def keys(self, start: str, end: str)` uses `start`/`end` for ranges, `trade_date` for one day |
| Ranges are `start`/`end` (inclusive both ends, `YYYYMMDD` strings) | `sessions(start, end)` |
| Counts are `n_<noun>`; flags are adjectives or `is_<state>`; collections are plural nouns | `n_rows`, `dry_run`, `is_open`, `tickers` |
| A DataFrame is named for what it holds, never `df`/`data` outside a local scope of ≤ 10 lines | `prices`, `factor_panel`, `raw` |
| Injected dependencies are named for their role, typed as their base | `client: BaseApiClient`, `store: BaseStore` |
| Paths are `<noun>_path` / `<noun>_dir`; roots are `<noun>_root` | `lake_root`, `catalog_path` |
| Config objects are `config` (whole) or `<section>_config` | `config`, `tushare_config` |
| No single-letter names except loop indices `i`, `j` and mathematical formulas with a comment | |

## 3. Documents
| Thing | Rule | Example |
|---|---|---|
| governance docs (standards, designs, logs) | `UPPER_SNAKE.md`, singular noun; designs end in `_DESIGN` | `CODING_STANDARD.md`, `SRC_DESIGN.md`, `DECISIONS.md` |
| folder index | `INDEX.md`, exactly, in every folder | |
| skill | folder `kebab-case` verb-or-noun, file `SKILL.md` | `.claude/skills/new-class/SKILL.md` |
| execution plan | `NN_<slug>.md`, two-digit sequence, `snake_case` slug ≤ 3 words | `plans/execution/01_data_lake.md` |
| roadmap | `ROADMAP.md` | |
| reference handbook | folder `snake_case`, files `UPPER_SNAKE.md` | `reference/fresh_start/TUSHARE_API.md` |
| repo-root docs | `README.md`, `CLAUDE.md`, `INDEX.md` | |
| identifiers inside docs | decisions `D-NNN`; test cases `TC-<ClassAbbrev>-NNN`; plan phases `NN.P` | `D-028`, `TC-PW-005`, `01.3` |

## 4. Configuration and environment
| Thing | Rule | Example |
|---|---|---|
| YAML files | lowercase `snake_case.yaml`, `.yaml` not `.yml` | `base.yaml`, `datasets.yaml`, `local.yaml` |
| YAML keys | `snake_case`, dataset keys = Tushare endpoint name | `lake.root`, `fina_indicator_vip` |
| env vars | `UPPER_SNAKE`, project ones prefixed `QUANT_CN_`; vendor tokens keep the vendor's name | `QUANT_CN_LAKE_ROOT`, `TUSHARE_TOKEN` |
| dotfiles | as their tools require | `.env`, `.python-version`, `.pre-commit-config.yaml` |

## 5. Research space
| Thing | Rule | Example |
|---|---|---|
| main notebook | `main.ipynb` | |
| themed notebook | `notebooks/YYYYMMDD_<topic>.ipynb`, topic `snake_case` ≤ 4 words | `notebooks/20261003_momentum_ic_decay.ipynb` |
| outputs | `outputs/YYYYMMDD_<topic>/<artifact>.<ext>` (git-ignored) | `outputs/20261003_momentum_ic_decay/ic_series.html` |

## 6. Lake (outside the repo)
| Thing | Rule | Example |
|---|---|---|
| dataset folder | Tushare endpoint name | `raw/daily/`, `curated/daily_basic/` |
| raw file | `<sweep_key>=<value>.parquet`, hive style, value as Tushare returns it | `trade_date=20260828.parquet`, `period=20260630.parquet`, `list_status=L.parquet` |
| single-call raw file | `all.parquet` | `raw/trade_cal/all.parquet` |
| curated partition | `year=YYYY/part-<n>.parquet`, `n` zero-based | `curated/daily/year=2026/part-0.parquet` |
| derived dataset | `curated/derived/<noun>_<qualifier>/` | `prices_adj/`, `fundamentals_pit/` |
| manifest | `meta/manifest/<dataset>.json` | `meta/manifest/daily.json` |
| catalog | `meta/quant_cn.duckdb`; schemas `main` (data), `meta`, `project` | |
| temp file | `<final_name>.tmp`, renamed on success; never left behind | |

## 7. Git
| Thing | Rule | Example |
|---|---|---|
| branch | `<type>/<slug>`; types `feat`, `fix`, `docs`, `plan`, `chore`; slug `kebab-case` | `feat/data-loading`, `docs/readme` |
| commit subject | imperative, ≤ 72 chars, prefixed with the plan/phase when applicable | `Plan 01 phase 3: lake core` |
| tag | `vMAJOR.MINOR.PATCH` | `v0.1.0` |

## 8. Abbreviations allowed in identifiers
`ts_code`, `pit` (point in time), `adj`, `nav`, `ic`, `icir`, `ohlcv`, `mv` (market value), `pe`, `pb`, `roe`,
`yoy`, `cfg` (only in local variables), `df` (only in local variables). Anything else is spelled out.
Tushare column names are kept verbatim in data frames even when they break these rules (`pct_chg`, `vol`).

## 9. Known deviations (accepted, tracked)
- `tests/core/test_base_classes.py` covers several base classes in one module (family test, mirrors §2 family module rule).
- Governance files are the only capitalised names, so they stand out from code in any listing.
