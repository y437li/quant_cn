---
name: registry
description: Look up, add or update entries in .claude/CLASS_REGISTRY.md, the single source of truth for every class, base class, exception, schema and allowed standalone function (plans/standards/CODING_STANDARD.md §5). Use before writing any class ("does X exist", "is there a loader for"), after creating, renaming, retiring or changing a class, and whenever a call between classes is added or removed (Used by column).
---

# registry

File: `.claude/CLASS_REGISTRY.md`. Sections: A index (one row per class), B class details (one block per class with a method table), C abstract base classes, D exceptions, E schemas, F allowed standalone functions. Column formats and block headings are fixed by the file; do not add or reorder columns.

## Lookup mode (before writing code)
1. Search the registry for the name, synonyms and purpose keywords (e.g. "loader", "fetch", "reader", "align", "calendar").
2. Confirm against code: `grep -rn "class <Name>\|<keyword>" src/`. The registry can lag; code wins, and a lag is itself a finding to fix.
3. Answer with: exact match / near-match (row + how to extend or subclass) / none. Quote the row; do not paraphrase.

## Update mode (same change set as the code)
Names in rows must be the names in code; pick new names with the `naming` skill. The detail-block columns derive
from code: `Input -> Output` from the signature annotations, `Raises` from the method docstring's `Raises:`,
Purpose from the docstring's `Purpose:`. When many classes change at once (e.g. a rename sweep), regenerate
sections A–D from the docstrings + AST rather than hand-editing, then review the diff.

1. **Add or edit the index row (section A)** for each class touched:
   - `Module`: `quant_cn.<package>.<module>`
   - `Layer`: number from CODING_STANDARD §2.1
   - `Purpose`: one line, same meaning as the docstring's Purpose
   - `Public methods (count)`: number of public methods, must equal the rows in the detail block
   - `Used by`: copy of the docstring's `Used by:` list (`package.Class.method`, notebooks by path)
   - `Tests`: `tests/<layer>/test_<module>.py` + TC count, e.g. `test_price_loader.py (5)`
   - `Added`: `YYYY-MM-DD` of first creation; never changed afterwards
1b. **Add or edit the detail block (section B)** using the template in the file:
   - class Purpose, Base, injected dependencies, Used by, Tests
   - **method table**: one row per public method with Purpose (one line, same meaning as the method
     docstring), `Input -> Output` (type or Schema names), Raises, Used by, TC IDs; private helpers
     over 20 lines get a row too
   - a method added, removed or re-purposed in code changes its row in the same change set
2. **Ripple Used by**: for every class the changed class now calls, add the caller to that row's `Used by` (and its docstring). Remove entries for calls that were deleted.
3. **Base classes**: keep `Known subclasses` current when a subclass is added or removed.
4. **Exceptions / schemas**: new ones get a row in their table; a schema's `Used by` lists classes that produce or validate it.
5. **Standalone functions**: only `core/utils`; `Why not a class method` must be a real reason (stateless, used by 3+ layers, …). No reason -> make it a method instead.
6. **Rename / retire**: rename in place (keep `Added`); a retired class is removed only after `grep` shows no callers. Record the rename or retirement with the `decisions` skill.
7. Replace the `_(none yet)_` placeholder row when a table gets its first real row.

## Consistency check
For each index row: module file exists, class exists in it, docstring `Used by:` equals the row's `Used by`, a detail block exists whose method rows match the public methods in code (names, count, purpose meaning), and `grep -rn "<ClassName>" src/ research_space/` shows no caller missing from the list. Report mismatches; the `test-cases` skill's audit mode covers TC IDs.

## Report
Rows added / changed / removed, one line each. Mismatches found, if any.
