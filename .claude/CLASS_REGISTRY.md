# Class Registry

Single source of truth for every class, base class, exception, schema and allowed standalone
function in `quant_cn`. Rules: `Plans/CODING_STANDARD.md` §5. Maintained with the `registry` skill.

**Before writing anything new:** search this file and `grep` the codebase. Extend or subclass a match
instead of writing a duplicate.
**After creating or changing a class:** update its index row *and* its detail block in the same
change set, and add the new caller to the `Used by` of every class or method it calls.

Layers: 1 core, 2 lake, 3 data_loading, 4 pipeline/statistic, 5 back_testing/portfolio, 6 research_space.

---

## A. Index (one row per class; details in section B)

| Class | Module | Layer | Base | Purpose (one line) | Public methods (count) | Used by | Tests | Added |
|---|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | | |

## B. Class details (one block per class; methods carry their own purpose)

Template. Copy verbatim; keep headings so `lint_contracts.py` can parse them.

### `PascalName` — `quant_cn.package.module` (L?)
- **Purpose:** one or two lines, identical in meaning to the docstring.
- **Base:** `BaseX` | none. **Depends on (injected):** `Config`, `BaseY`.
- **Used by:** `package.Class.method`, `research_space/main.ipynb`.
- **Tests:** `tests/<layer>/test_<module>.py` (TC-XX-001..NNN).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__(config, dep)` | wire dependencies | `Config`, `BaseY` -> instance | `ConfigError` | callers of the class | — |
| `method_a(x)` | what it does, one line | `list[str]` -> `DataFrame[SchemaZ]` | `DataSourceError` | `pipeline.DownloadPipeline.step_daily` | TC-XX-001, 003 |

Rules: every public method gets a row; private helpers (`_name`) are listed only if longer than 20
lines, so a reader knows they exist. `Input -> Output` uses type names or a registered `Schema` name,
never column lists (those live in section E).

_(no blocks yet)_

## C. Abstract base classes / extension points

| Class | Module | Layer | Purpose | Abstract methods (purpose each) | Known subclasses | Added |
|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | |

## D. Exceptions

| Class | Module | Parent | Purpose / raised when | Raised by | Added |
|---|---|---|---|---|---|
| _(none yet)_ | | | | | |

## E. Schemas (DataFrame / typed records)

| Schema | Module | Purpose | Index | Columns (dtype) | Invariants | Produced by | Consumed by | Added |
|---|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | | |

## F. Allowed standalone functions (`core/utils` only, with justification)

| Function | Module | Purpose | Input -> Output | Why not a class method | Used by | Tests | Added |
|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | |
