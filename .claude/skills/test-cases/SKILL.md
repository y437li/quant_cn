---
name: test-cases
description: Derive a test-case table and a pytest scaffold from a class's docstring contract (Purpose / Contract / Test cases) as required by plans/standards/CODING_STANDARD.md. Use whenever a new class is being designed, a class contract changes, or the user asks to "write tests", "add test cases", or "cover this class". Also use to audit that every TC ID in a docstring has a matching test.
---

# test-cases

Turn a class contract into concrete, numbered test cases and a pytest file that follows
`plans/standards/CODING_STANDARD.md` Sections 3 and 6.

## Inputs
- A target class (module path + class name), or a docstring contract pasted by the user.
- The class must already have, or the user must supply, the `Purpose` and `Contract` sections.
  If they are missing, stop and write the contract first; do not invent tests for an undefined contract.

## Procedure

1. **Read the contract.** Open the class docstring. Extract every input (type, range, emptiness rule),
   every output guarantee (type, index, columns, dtypes, invariants), and every `Raises` entry.

2. **Check the registry and existing tests.** Read `.claude/CLASS_REGISTRY.md` and any existing
   `tests/**/test_<module>.py`. Never create a second test file for the same class; extend the existing one.

3. **Derive the test-case table.** Produce one row per case. Minimum coverage per class:
   - 1 happy path per public method
   - 1 boundary case per constrained input (empty list, start == end, single row, max size)
   - 1 failure case per `Raises` entry, asserting the exact exception class
   - 1 output-contract check: shape, index type/order/uniqueness, column set, dtypes, NaN rules
   - 1 idempotence/determinism check where applicable (same input -> identical output)

   Table format (also pasted back into the class docstring `Test cases:` section):

   | ID | Type | Given | When | Then |
   |---|---|---|---|---|
   | TC-PL-001 | happy | store with 2 tickers, 5 days | load(tickers, start, end) | 10 rows, sorted MultiIndex, no NaN close |
   | TC-PL-002 | failure | end < start | load(...) | raises ValueError |

   ID rule: `TC-<ClassAbbrev>-<3 digits>`, abbreviation = capital letters of the class name.
   Reuse existing IDs; append new ones; never renumber. Prefixes already taken (check before choosing,
   collisions get an extra letter, e.g. `Compactor` → `CO` because `Config` is `C`, `TradingCalendar` → `TCA`
   because `TushareClient` is `TC`): `grep -rhoE 'TC-[A-Z]+-' src | sort -u`.
   One ID may appear in several docstrings (a base and its subclasses, a model and its sub-models); it still
   maps to exactly one test function.

4. **Scaffold the pytest file.** Path mirrors the package: `tests/<layer>/test_<module>.py`.
   Reuse the shared test kit before writing any fixture:
   - `tests/conftest.py` fixtures: `clock` (FakeClock), `repo` (tmp repo with copies of `config/*.yaml`),
     `config` (Config over that repo, lake in `tmp_path`, token `test-token`), `lake` (MiniLake: `lake_root`,
     `catalog`, `writer`, `fetch_log`, `run_log`, `query`, `clock` — a real parquet + DuckDB lake in tmp_path).
   - `tests/support.py`: `FakeClock` (fixed now, records sleeps), `FakeTushareClient` (`add(api, key, frame)`,
     `fail(api, key, exc)`, `calls`), `Sample.build_spec(**overrides)`, `Sample.build_bars(trade_date)`, `Sample.build_trade_cal(open, closed)`.
     New shared doubles go here (`Fake<Noun>`, builders on `Sample`), never duplicated per test file.
   - pytest runs with `--import-mode=importlib` and `pythonpath = ["."]`: import the kit as `from tests.support import ...`.
   Template:

   ```python
   from __future__ import annotations

   import pandas as pd
   import pytest

   from quant_cn.<layer>.<module> import <ClassName>
   from quant_cn.core.exceptions import <ExceptionsUsed>
   from tests.support import Build, FakeTushareClient, MiniLake


   @pytest.fixture
   def loader(lake: MiniLake) -> <ClassName>:
       return <ClassName>(lake.catalog, lake.clock)   # inject real mini-lake parts or fakes via __init__


   # TC-PL-001
   def test_tc_pl_001_happy_path_two_tickers(loader):
       ...


   # TC-PL-002
   def test_tc_pl_002_end_before_start_raises(loader):
       with pytest.raises(ValueError):
           ...
   ```

   Rules: one test function per TC ID, named `test_<tc_id_lower>_<short_desc>`; a `# TC-XXX-NNN`
   comment above each; `parametrize` for input variations; fakes subclass the same base class as the
   real dependency; no `==` on floats (`pytest.approx`); DataFrames compared with `assert_frame_equal`;
   text dtype checked with `pd.api.types.is_string_dtype` (pandas 3 `string`/`str`, not `object`).

5. **Sync the docstring.** Write the final ID list back into the class docstring `Test cases:` section
   so docstring and test file match one-to-one.

6. **Run and report.** Run `UV_PROJECT_ENVIRONMENT=$HOME/.venvs/quant_cn uv run pytest <file> -q`, then `make check`. If the class is not implemented yet, tests must fail
   with a clear reason (not import errors). Paste real output. Then update the `Tests` column of the
   class's row in `.claude/CLASS_REGISTRY.md`.

## Audit mode
When asked to audit: for every class in the registry, compare docstring TC IDs against test function
names. Report missing tests, orphan tests, and classes without a `Test cases:` section. Also check
`Used by`: `grep -rn "<ClassName>" src/ research_space/` must match the docstring's Used by list and
the registry column; report callers missing from either, and listed callers that no longer exist. Do not fix
anything in audit mode unless asked.

## Do not
- Invent behaviour that is not in the contract. If a case is ambiguous, list it under "Open questions".
- Test private methods directly. Test through the public contract.
- Load large real datasets. Fixtures are small and constructed in code.
