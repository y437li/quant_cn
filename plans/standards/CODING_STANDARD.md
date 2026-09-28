# quant_cn Coding Standard (DRAFT v0.1, 2026-09-27)

This document is binding for every human and agent writing code in this repository.
An agent must read it before writing or changing any code. The root `CLAUDE.md`
points here. Deviations require an explicit note in the plan and user approval.

Stack: Python 3.12, managed by **uv** (`pyproject.toml` + `uv.lock`, D-018); `pandas`, `pyarrow` (parquet),
`duckdb` (catalog + SQL), `pydantic`, `pytest`, `ruff`, `mypy`, `import-linter`; type hints everywhere.
Data vendor: Tushare Pro. Domain rules and data traps live in `plans/reference/fresh_start/` (`README.md`, `DATA_CATALOG.md`, `TUSHARE_API.md`); this standard defers to them on data semantics.

---

## 1. Core principles

1. **Object-oriented.** All behaviour lives in classes. A module exposes classes, not loose functions. Module-level code is limited to imports, constants and an optional `if __name__ == "__main__":` block.
2. **One class, one responsibility.** If a class name needs "And" or "Manager" to describe it, split it.
3. **Extend, do not duplicate.** Before writing a class or method, search the class registry (Section 5) and the codebase. If something close exists, extend it, subclass it, or refactor it. Never write a second version.
4. **Contracts are explicit.** Every class and public method declares its Purpose, Input contract, Output contract, Used by, and Test cases in its docstring (Section 3). If the contract cannot be written down, the design is not ready.
5. **Tests are part of the deliverable.** No class is "done" without a test file that covers the documented test cases (Section 6).
6. **Easy to maintain, easy to expand.** Extension points are abstract base classes. New behaviour is a new subclass or a new composed object, not an `if/else` branch inside an existing class.

---

## 2. Architecture rules

### 2.1 Layering
Code is organised in layers. A layer may import only from itself or layers below it.
Package names follow `plans/architecture/FOLDER_STRUCTURE.md` §3 (D-007, D-012).

| Layer | Packages (`src/quant_cn/...`) | Holds |
|---|---|---|
| 8 | `cli.py`, `research_space/` | Composition root; notebooks (import only, never define) |
| 7 | `back_testing`, `portfolio`, `visualization` | Engine, fills, costs; sizing, constraints, rebalancing; charts (mutually independent) |
| 6 | `pipeline` | Resumable download / curate / universe / feature steps |
| 5 | `factor` | `BaseFactor`, factor library, preprocessing, evaluation, signal combination |
| 4 | `statistic`, `calculation` | Generic math on frames; domain financial computations (VIX, curves, option chains). Mutually independent |
| 3 | `data_loading` | Tushare client and fetchers; writes into the lake |
| 2 | `lake` | Parquet writer, DuckDB catalog, fetch log, run log, compactor, query API, PIT aligner, calendar |
| 1 | `core` | Base classes, exceptions, config, logging, schemas, date/ticker codecs |

### 2.2 Extension points
Every family of interchangeable things has an abstract base class in `core` or the owning layer, for example `BaseDataSource`, `BaseFactor`, `BaseStrategy`, `BaseBacktester`. Concrete classes subclass the base and override only the abstract methods. Adding a new data vendor or factor must never require editing an existing concrete class.

### 2.3 Composition and injection
Dependencies (data sources, config, clock, logger) are passed into `__init__`, never created inside a method or imported as globals. This keeps classes testable with fakes.

### 2.4 Configuration
No hardcoded paths, tickers, dates, tokens or thresholds inside classes. They come from a typed config object in `core/config.py`. Secrets come from environment variables only.

### 2.5 Errors and logging
- A single exception hierarchy rooted at `QuantCnError` in `core/exceptions.py`. Raise specific subclasses (`DataSourceError`, `SchemaError`, `ConfigError`, ...).
- Use `logging.getLogger(__name__)`. `print` is forbidden outside `app` entry points.

### 2.6 Size limits (D-030)
| Unit | Hard limit (linter fails) | Target | Applies to |
|---|---|---|---|
| file | **600 lines** | ≤ 400 | every `.py` under `src/`, `tests/`, `scripts/`; notebooks measured as code cells |
| class | 300 lines | ≤ 200 | all classes |
| method / function | 50 lines | ≤ 30 | all callables; `__init__` included |
| `INDEX.md`, `SKILL.md`, plan file | 300 lines | | docs stay scannable |

- Lines are counted as physical lines including docstrings and blank lines (`wc -l`), so a long contract
  docstring is a reason to split behaviour, not to shorten the contract.
- Over a hard limit: split by responsibility (a family module → one module per class; a class → composition;
  a method → named steps). Never silence the check.
- Enforced by `scripts/lint_contracts.py --size` (fails `make check`); the `standard-review` skill reports
  sizes (check 8).
- No circular imports. If one appears, the layering is wrong; fix the design, not the import order.

### 2.7 Point-in-time (PIT) and data rules
These come from `plans/reference/fresh_start/DATA_CATALOG.md` and are enforced in code, not left to memory.
- Every dataset class declares its **primary key** and its **known-on column** (e.g. `trade_date`,
  `f_ann_date`, `ann_date`) as class attributes. A dataset without a known-on column cannot be used
  by any alignment or feature class.
- All alignment of fundamentals/events to a trading date goes through one class (`PitAligner`)
  that filters on `known_on <= t` and shifts to the next trading day when the announcement may be
  after the close. No other class may implement this join.
- Restatements and forecast revisions are kept as versions; "latest version with `ann_date <= t`"
  is the only allowed selection rule.
- Fundamentals are always joined on `(ts_code, end_date)`, never on `ts_code` alone, and filtered
  to `report_type == 1` unless a class explicitly documents otherwise.
- The universe includes delisted (`D`) and paused (`P`) stocks. Any class that drops them says so
  in its contract.
- Prices from `daily` are unadjusted. Adjusted prices are produced by one class using `adj_factor`.
- Units follow Tushare conventions (DATA_CATALOG §2). A class that converts units documents the
  conversion in its Output contract.
- Downloads are resumable: every fetch class records `(endpoint, key)` completion through a
  shared `FetchLog` class (a DuckDB table in the lake catalog).
- Storage is a local lake (D-009, layout in `FOLDER_STRUCTURE.md` §2): `raw/` is append-only and
  the only expensive copy; `curated/`, `derived/` and `meta/` are rebuildable from it. Reads go
  through `LakeQuery` (SQL over DuckDB views); no class outside `lake` touches parquet paths.

---

## 3. Mandatory class contract (docstring format)

Every class and every public method carries this docstring. Fields are fixed; keep the headings exactly so tooling and agents can parse them.

```python
class PriceLoader(BaseDataSource):
    """
    Purpose:
        Load daily OHLCV bars for A-share tickers from a local Parquet store.

    Contract:
        Input:
            tickers: list[str]      -- Tushare codes, e.g. "600519.SH"; non-empty
            start:   datetime.date  -- inclusive
            end:     datetime.date  -- inclusive, >= start
        Output:
            pandas.DataFrame
                index:   MultiIndex (date: datetime64[ns], ticker: str), sorted
                columns: open, high, low, close, volume (float64), amount (float64)
                guarantees: no duplicate index rows; no NaN in close
        Raises:
            SchemaError      -- if the store is missing a required column
            DataSourceError  -- if any ticker has no rows in range

    Used by:
        pipeline.DownloadPipeline.run_daily      -- source of bars for the daily step
        data_loading.PitAligner.align            -- price index for alignment
        research_space/main.ipynb                -- ad-hoc loading

    Test cases:
        TC-PL-001  happy path, 2 tickers, 5 trading days
        TC-PL-002  end < start raises ValueError
        TC-PL-003  unknown ticker raises DataSourceError
        TC-PL-004  store missing 'close' raises SchemaError
        TC-PL-005  output index sorted and unique
    """
```

Rules for the contract section:
- **Every input** names its type, allowed range or format, and whether it may be empty/None.
- **Every DataFrame** names its index, columns, dtypes and invariants (sorted, unique, no NaN where it matters). Reuse a shared schema class from `core/schemas.py` when the shape is common; reference it by name instead of repeating columns.
- **Every output** states what is guaranteed, not just its type.
- **Raises** lists the project exceptions that a caller is expected to handle.
- **Used by** lists every class or method in the codebase that calls this one, as `package.Class.method`,
  plus notebooks by path. `(none yet)` is allowed for a class just created. This is the dependency
  map read before any change: if you change a contract, you visit every entry in Used by.
- **Test cases** lists IDs that exist in the test file. The list and the test file must match.

Keeping **Used by** true:
- When you add a call to class B from class A, you edit B's docstring in the same change and add A.
- When you remove the call, you remove the entry.
- The registry's `Used by` column mirrors the docstring. `grep -rn "ClassName" src/` must agree with
  both; `scripts/lint_contracts.py` (§4.1) fails on mismatches, and the `test-cases` audit mode reports them.
- Public methods list their own callers only when they differ from the class-level list.

Test case IDs follow `TC-<ClassAbbrev>-<3 digits>`. The abbreviation is the class's capital letters (PriceLoader -> PL). Resolve collisions by adding a letter.

---

## 4. Naming and style

File, folder, document, config, lake and git names: `plans/standards/NAMING_CONVENTION.md` (binding). Identifier rules below are the summary.

- Classes `PascalCase`; methods, functions, variables `snake_case`; constants `UPPER_SNAKE`; private members `_leading_underscore`.
- Modules are nouns: `price_loader.py` holds `PriceLoader`. One primary class per module; helpers that only serve that class may live beside it.
- Type hints on every signature. `from __future__ import annotations` at the top of every module.
- **Dates in stored tables and at the API boundary are `YYYYMMDD` strings**, exactly as Tushare returns them (DATA_CATALOG §4: joins never hit type mismatches). Column names keep Tushare names (`trade_date`, `ann_date`, `end_date`). Conversion to `datetime` for research/plotting happens only through one class, `DateCodec`, and never mutates stored data.
- Tickers are Tushare `ts_code` (`600519.SH`, `000001.SZ`, `830799.BJ`) everywhere. Any conversion from other vendors' formats lives in one class, `TickerNormalizer`.
- Secrets (`TUSHARE_TOKEN`, model API keys) are read from environment variables only. `.env` is git-ignored. A hardcoded token in any file fails review.

### 4.1 Linting toolchain (all must pass before a change is done)

| Tool | Checks | Config |
|---|---|---|
| `ruff format` | formatting, line length 100 | `pyproject.toml [tool.ruff]` |
| `ruff check` | rules `E,F,W,I,N,UP,B,SIM,PL,RUF,D1` (D1 = docstring *present* on every public class/method; our own format replaces pydocstyle style rules D2-D4, which are disabled) | `pyproject.toml` |
| `mypy --strict` | types on every signature; no `Any` leaks from pandas boundaries without a typed `Schema` | `pyproject.toml [tool.mypy]` |
| `import-linter` (`lint-imports`) | layer contract from `FOLDER_STRUCTURE.md`: `core` < `lake` < `data_loading` < `statistic`/`calculation` < `factor` < `pipeline` < `back_testing`/`portfolio`/`visualization` < `cli`; `statistic`/`calculation` independent; `back_testing`/`portfolio`/`visualization` independent; no `research_space` imports inside `src/` | `pyproject.toml [tool.importlinter]` |
| `scripts/lint_contracts.py` (project linter) | every public class/method has `Purpose`, `Contract` (Input, Output, Raises), `Used by`, `Test cases`; each TC ID has a test function and vice versa; `Used by` matches `grep` over `src/` and `research_space/`; every class has a registry row + detail block whose method table matches the code; no duplicate class names across packages; no module-level functions outside `core/utils`; `--index`: every folder has `INDEX.md`, entries match disk, `Contains` matches classes; `--size`: file ≤ 600, class ≤ 300, method ≤ 50 lines (§2.6); `--names`: method verb prefixes and file names per NAMING_CONVENTION | none; also runs as `tests/test_contracts.py` so `pytest` fails on violations |
| `pytest --cov` | coverage targets in §6 | `pyproject.toml [tool.pytest]`, `[tool.coverage]` |

How they run:
- **Environment**: `uv sync --all-extras` creates `.venv` from `uv.lock`; every tool runs as `uv run <tool>`. Nobody calls `pip`; dependencies are added with `uv add` / `uv add --dev` so the lock file changes in the same commit.
- **One command**: `make lint` (`uv run python -m scripts.lint`) runs all of the above in order; `make check` = lint + tests. Agents paste its output in the report.
- **pre-commit**: `.pre-commit-config.yaml` runs ruff format, ruff check, mypy, lint-imports and `lint_contracts.py` on staged files, so a bad commit cannot land.
- **Claude Code hook** (optional, proposed in plan 01 phase 1): a `PostToolUse` hook on Edit/Write in `.claude/settings.json` runs `ruff format` and `ruff check --fix` on the touched file, so agents see style problems immediately instead of at commit time.
- **CI** (when a remote exists): the same `make check`.

Rules:
- No `# noqa`, `# type: ignore` or `# contract: ignore` without a reason on the same line, and the reason names a decision ID or an issue.
- Linter configuration changes are decisions (log them); an agent may not relax a rule to make its own change pass.
- Dependency changes go through `uv add`/`uv remove` only; `uv.lock` is committed; exact versions come from the lock, not from `==` pins in `pyproject.toml` (except where a decision says so, e.g. `duckdb`).

---

## 5. Class registry (duplication control)

File: `.claude/CLASS_REGISTRY.md`. It is the single source of truth for what already exists.

**Before writing a class or public function**, the agent must:
1. Read the registry and search it for the concept (name, synonyms, purpose keywords).
2. `grep` the codebase for the same concept.
3. If a match or near-match exists: extend, subclass or refactor it. State this in the plan.
4. Only if nothing exists: create the new class.

**After creating or materially changing a class**, the agent must add or update the registry row in the same change set, including the `Used by` column of every class it now calls. A change is not complete until the registry is current.

Registry format (`.claude/CLASS_REGISTRY.md`, maintained with the `registry` skill):
- **Section A, index**: one row per class: Class, Module, Layer, Base, Purpose (one line), Public
  methods (count), Used by, Tests, Added.
- **Section B, class details**: one block per class with the class Purpose, Base, injected
  dependencies, Used by, Tests, and a **method table**: `Method | Purpose | Input -> Output | Raises
  | Used by | TC IDs`. Every public method has a row with its own purpose; private helpers over 20
  lines are listed too. This is where a reader learns what each function does without opening code.
- **Sections C–F**: abstract base classes (with the purpose of each abstract method), exceptions,
  schemas (produced by / consumed by), and allowed standalone functions with purpose and justification.

The method table's Purpose must match the method docstring's Purpose in meaning; `lint_contracts.py`
checks that every public method in code has a row and vice versa.

### 5.1 Folder indexes (file-level map)

Every folder in the repository, at every depth, contains an `INDEX.md`: packages and sub-packages, each
test folder, each skill folder, `config/`, `scripts/`, `research_space/notebooks/`, `plans/execution/` and so on
(format and the short ignore list: `.claude/skills/index/SKILL.md`). Lake folders under `data/` are git-ignored,
so their indexes are generated by `LakeCatalog.write_indexes()` instead of hand-written.
It lists the folder's purpose, its subfolders (linking to their own `INDEX.md`) and its files with a
one-line purpose and what each contains (classes for `.py`, fixtures for `conftest.py`, sections for
`.md`, dataset keys for YAML). The root `INDEX.md` is the top of the tree.

- Adding, renaming, moving or deleting a file or folder updates the parent `INDEX.md` in the same change set.
- A new folder is created together with its `INDEX.md`.
- `Contains` must agree with the class registry and the code; `lint_contracts.py --index` fails on a
  folder without an index, an entry missing from disk, or a file on disk missing from its index.
- Four views, one truth: `INDEX.md` tree = files; `CLASS_REGISTRY.md` = classes and methods; docstrings =
  contracts; the lake's `project` schema (plan 02) = all of the above as SQL tables, rebuilt from them,
  never edited directly. A reader goes root index -> folder index -> registry block -> code, or queries DuckDB.

---

## 6. Testing standard

- Every class has a test module at `tests/<layer>/test_<module>.py`. Mirror the package layout.
- Every test case ID in the class docstring maps to exactly one test function named `test_<tc_id_lower>_<short_description>`, e.g. `test_tc_pl_002_end_before_start_raises`.
- Each class covers at minimum: one happy path, one boundary/edge case, one failure path, and one output-contract check (shape, dtypes, invariants).
- Unit tests never touch the network, real credentials, or files outside `tmp_path`. External services are replaced by fakes implementing the same base class.
- Use `pytest.mark.parametrize` for input variations; use fixtures in `tests/conftest.py` for shared sample data (small, deterministic, built in code, not loaded from large files).
- Use `pandas.testing.assert_frame_equal` for DataFrame outputs. Never compare floats with `==`.
- Coverage target: 90% lines on `core`, `lake` and `data_loading`, 80% elsewhere. Report with `pytest --cov`.
- Use the `test-cases` skill (`.claude/skills/test-cases/SKILL.md`) to derive test cases from a contract and scaffold the test file.

---

## 7. Agent workflow (mandatory order)

1. Read `CLAUDE.md`, this standard, and `.claude/CLASS_REGISTRY.md`.
2. Use the `plan` skill to write or update the plan in `plans/execution/` (classes created, extended, reused), keeping `plans/execution/ROADMAP.md` current. Record choices with the `decisions` skill. Wait for approval on anything non-trivial.
3. Write the class docstring contract first (Purpose, Contract, Used by, Test cases). Add the new class to the Used by of everything it calls. The `new-class` skill drives steps 3–7.
4. Run the `test-cases` skill to produce the test file from the contract. Tests should fail at this point.
5. Implement the class until the tests pass.
6. Run `make check` (ruff, mypy, import-linter, contract linter, pytest). Paste real output in the report; do not claim success without it.
7. Update `.claude/CLASS_REGISTRY.md` (`registry` skill).
8. Run the `standard-review` skill on the changed files; it runs the Section 8 checklist.
9. Report: what was created/reused, test results, anything left out.

---

## 8. Definition of done checklist

- [ ] Class has the full docstring contract (Section 3), including Used by
- [ ] Every class this change calls has this caller added to its Used by (docstring + registry)
- [ ] No duplicate of an existing class or function (registry and grep checked)
- [ ] Depends only on lower layers; no circular imports
- [ ] Dependencies injected; no hardcoded config or secrets
- [ ] Test file exists; every TC ID has a test; tests pass locally
- [ ] `make lint` clean: ruff, mypy, import-linter, contract linter (§4.1)
- [ ] Registry row and detail block added or updated
- [ ] Parent folder `INDEX.md` updated (new folder: its own `INDEX.md` created)
- [ ] Plan in `plans/` updated to reflect what was actually built

---

## 9. Decisions taken from `plans/reference/fresh_start/` (override if wrong)

- Vendor: Tushare Pro via raw HTTP POST (no SDK dependency), token from `TUSHARE_TOKEN`.
- Storage: local data lake, parquet per dataset partitioned by `year=YYYY`, DuckDB catalog on top (D-009).
- Dates: `YYYYMMDD` strings in stored data; ticker: Tushare `ts_code`.
- Universe includes L, D and P; fundamentals aligned on `f_ann_date`/`ann_date`, never `end_date`.

## 10. Open questions for the user

1. Schemas/config: `pydantic` (validation at runtime) or stdlib `dataclasses` (fewer deps)? Recommendation: `pydantic` for config, a light `Schema` class over pandas for DataFrame contracts.
2. Confirm package name `quant_cn` and the five-layer layout in Section 2.1.
3. Should the registry also track data schemas as first-class entries (recommended yes; template already has the table)?
4. Concurrency for downloads: keep the old 8-thread + single-writer pattern, or start single-threaded and add later?
