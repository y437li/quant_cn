---
name: new-class
description: Design and build a class the quant_cn way — search before write, pick layer and base, write the Purpose / Contract / Used by / Test cases docstring first, then tests, then code, as required by plans/standards/CODING_STANDARD.md §1-§7. Use whenever a class, base class, exception, schema or public method is about to be created or its contract changed, or the user says "add a class", "implement X", "build the fetcher", "start phase N" of a plan.
---

# new-class

Contract first, code last. Every step below is mandatory; skipping one means the class is not done.

## Inputs
- The concept to build (name or purpose), and the plan phase it belongs to (`plans/execution/NN_*.md`).
- No approved plan phase covering it -> stop and use the `plan` skill first.

## Procedure

1. **Search before write** (§5).
   - `registry` skill, lookup mode: name, synonyms, purpose keywords.
   - `grep -rniE "<name>|<synonym>" src/ tests/ research_space/`.
   - Near-match found -> extend / subclass / refactor it. Say which in the plan's Classes table (`extend` / `reuse`). Only if nothing matches -> `new`.
   - Existing extension points to subclass first: `BaseApiClient`, `BaseStore`, `BaseFetchLog`, `BaseRunLog`,
     `BaseFetcher`, `BaseStep` (core), `BaseRunner` (pipeline).
   - A new **dataset** is not a class: add an entry to `config/datasets.yaml` (endpoint, sweep, primary_key,
     known_on, fields, text_fields, curated). Write a fetcher subclass only for a new sweep kind, and register
     it in `FetcherFactory.build`.

2. **Place it** (§2.1, FOLDER_STRUCTURE layer table).
   - Choose the lowest layer that can hold it. It may import only its own layer or lower.
   - Module = noun, one primary class: `src/quant_cn/<package>/<snake_name>.py` holds `<PascalName>`.
     Pick every name (class, module, methods, parameters) with the `naming` skill before writing.
   - Family of interchangeable things -> abstract base in `core` (or owning layer) first; the concrete class overrides only abstract methods.
   - Loose function -> only in `core/utils`, with a registry justification. Otherwise it is a method.

3. **Write the skeleton with the full docstring before any logic** (§3).
   ```python
   from __future__ import annotations

   import logging

   from quant_cn.core.<base_module> import <Base>

   logger = logging.getLogger(__name__)


   class <PascalName>(<Base>):
       """
       Purpose:
           <one or two lines>

       Contract:
           Input:
               <name>: <type>  -- <format / range>; <empty/None allowed?>
           Output:
               <type, or a Schema by name (core.schema.Schema / DatasetSpec.build_schema())>
                   guarantees: <sorted / unique / no NaN in ... / units>
           Raises:
               <ProjectError>  -- <when>

       Used by:
           (none yet)

       Test cases:
           (filled by the test-cases skill)
       """

       def __init__(self, config: Config, <deps>: <BaseDep>) -> None:
           ...
   ```
   Rules while writing it:
   - Dependencies (config, client, store, clock, logger) come in through `__init__`, typed as their base class. Nothing created inside methods, no globals.
   - No literal paths, tickers, dates, thresholds or tokens; read them from the injected `Config`. Secrets from env only.
   - Dates are `YYYYMMDD` strings, tickers are `ts_code`; conversions only via `DateCodec` / `TickerNormalizer`.
   - Datasets declare `primary_key` and `known_on` in `config/datasets.yaml` (§2.7, read via `DatasetSpec`). Any fundamentals/event alignment goes through `PitAligner`, never a local join.
   - Raise only subclasses of `QuantCnError`; add a new subclass in `core/exceptions.py` (and the registry) if none fits.
   - Time and sleeping only through the injected `Clock` (tests use `FakeClock`); never `datetime.now()`/`time.sleep`.
   - Objects are wired only in the composition root `cli.QuantCnCli`; add the new class's construction there.
   - Pydantic models (`Config`, `DatasetSpec`, ...): never name a method after a `BaseModel` attribute
     (`schema`, `json`, `dict`, `copy`, `model_*`); mypy flags it as an incompatible override.
   - DataFrame text columns are pandas `string` dtype (pandas 3); cast through `Schema.normalize`, not `astype(object)`.
   - Public methods get their own contract block when their inputs/outputs differ from the class-level one.

4. **Wire the dependency map** (§3 Used by, D-010).
   - For every class this one calls, add this class (`package.Class.method`) to that class's docstring `Used by:` and to its registry row. Same change set.
   - Fill this class's own `Used by:` from the plan's planned callers once they exist; `(none yet)` until then.

5. **Tests from the contract.** Run the `test-cases` skill on the skeleton. Tests must fail for "not implemented" reasons, not import errors.

6. **Implement** until tests pass. Respect size limits (file ~400, class ~300, method ~50 lines); split instead of growing.
   New behaviour for an existing family = new subclass, not an `if/else` in an existing class.

7. **Verify with real output.** Tools run through uv; the venv lives off the exFAT volume
   (`UV_PROJECT_ENVIRONMENT=$HOME/.venvs/quant_cn`, exported by the Makefile).
   ```bash
   UV_PROJECT_ENVIRONMENT=$HOME/.venvs/quant_cn uv run pytest tests/<layer>/test_<module>.py -q   # while iterating
   make check        # ruff format --check, ruff check, mypy --strict, lint-imports, pytest --cov
   ```
   Paste the actual summary lines. Failure -> fix, do not report done. Never add a `# noqa` / `# type: ignore`
   or relax `pyproject.toml` rules to pass (§4.1; existing ignores are D-027).

8. **Close out.**
   - `registry` skill, update mode: row for this class (and base / exception / schema rows if added).
   - A design choice made on the way (new base class, new schema, deviation from standard) -> `decisions` skill.
   - `plan` skill, update mode: phase evidence.
   - Run the `standard-review` skill on the changed files before reporting done.

## Changing an existing contract
1. Read its `Used by:`. Every listed caller is in scope of the change.
2. Update the docstring contract, then the `test-cases` skill (append TC IDs, never renumber), then code, then each caller.
3. A contract change that breaks a caller without updating it is not allowed.

## Report
- Class(es) created / extended / reused, with module paths.
- `Used by` edits made in other classes.
- `make check` summary lines (real).
- Anything deferred, and why.

Registry note: the `registry` skill update must include the section B detail block with one row per public method (purpose, input -> output, raises, used by, TC IDs), not just the index row.

Index note: a new module or folder also updates the parent `INDEX.md` (`index` skill); a new class is added to its file's `Contains` cell.
