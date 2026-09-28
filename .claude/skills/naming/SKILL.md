---
name: naming
description: Choose, check or change the name of a class, module/file, folder, method, variable, dataset, plan or doc in quant_cn per plans/standards/NAMING_CONVENTION.md. Use before creating any new file, folder or class, when the user asks "what should I call", "rename", "update the names", "fix naming", or when standard-review check 11 fails. Renames are decisions and must be applied to code, tests, registry, indexes and docs in one change.
---

# naming

Source of truth: `plans/standards/NAMING_CONVENTION.md`. This skill is the procedure; the convention is the rule.
Never invent a pattern the convention does not list; a missing row is a decision (`decisions` skill), not an exception.

## Choose a name (before creating)

| You are creating | Pattern | Check against |
|---|---|---|
| folder | lowercase `snake_case` noun; packages match the layer table | `plans/architecture/FOLDER_STRUCTURE.md` §1 |
| module (one class) | `snake_case` of the class: `parquet_writer.py` → `ParquetWriter` | registry: no second module for the concept |
| family module | plural noun, sibling subclasses of one base, ≤ 300 lines: `fetchers.py`, `runner.py` | the base lives in `base_<noun>.py` |
| abstract base | `Base<Noun>` in `core/base_<noun>.py` (or the owning layer) | registry section C |
| class | `PascalCase` noun, abbreviations as words (`TushareClient`, `PitAligner`); role suffix from the family (`*Fetcher`, `*Runner`, `*Step`, `*Chart`) | registry section A: no duplicate name in any package |
| exception | `<Noun>Error` in `core/exceptions.py` | registry section D |
| test double | `Fake<Noun>` in `tests/support.py`; builders on `Sample` | existing `FakeClock`, `FakeTushareClient`, `Sample` |
| test module / function | `tests/<layer>/test_<module>.py`; `test_<tc_id_lower>_<short_desc>` | `test-cases` skill |
| script | `scripts/<verb>_<noun>.py` | |
| dataset / YAML key | Tushare endpoint name, `snake_case` | `config/datasets.yaml` |
| plan / doc | `plans/plans/NN_<slug>.md`; governance `UPPER_SNAKE.md`; skill folder `kebab-case` | NAMING_CONVENTION §3 |

Methods: verb-first from the §2.1 table (`get_ find_ list_ read_ load_ fetch_ write_ save_ build_ compute_
validate_ check_ is_ has_ can_ ensure_ to_ from_ mark_ record_ run refresh_ rebuild_ normalize_ parse_ open_ close`).
The verb promises the effect: `is_` never raises, `validate` returns its input, `list_` returns a list, `write_`/`save_`
return the `Path` written, `get_` raises when absent and `find_` returns `None`. Properties (cheap, no I/O) may be nouns.
Names already used in code for these roles: `list_keys`, `build_params`, `list_due_keys`, `fetch_one`, `run`
(fetchers); `open_run`, `record_event`, `close_run` (run logs); `read_done_keys`, `mark_done`, `list_pending`, `save`
(fetch logs); `list_units` (steps); `build_schema`, `get_raw_filename` (DatasetSpec); `normalize`, `validate`,
`build_empty` (Schema). Reuse these verbs for the same roles in new classes.

Variables: Tushare field names verbatim; ranges `start`/`end`; counts `n_<noun>`; frames named for their content
(`df` only inside ≤ 10-line scopes); paths `<noun>_path` / `<noun>_dir`, roots `<noun>_root` (`lake_root`);
config objects `config` or `<section>_config` (`tushare_config`).

## Check names (read-only)

```bash
# methods outside the verb table (properties and dunders skipped)
uv run python - <<'PY'
import ast; from pathlib import Path
V = set("get find list read load fetch query sql write save build compute validate check is has can ensure to as from mark record log run execute refresh rebuild register add remove normalize parse format open close connect plot render".split())
for p in sorted(Path("src").rglob("*.py")):
    for c in [n for n in ast.parse(p.read_text()).body if isinstance(n, ast.ClassDef)]:
        for f in c.body:
            if isinstance(f, ast.FunctionDef) and not f.name.startswith("__") and "property" not in [ast.unparse(d) for d in f.decorator_list]:
                n = f.name.lstrip("_")
                if n.split("_")[0] not in V and n not in V: print(f"{p}: {c.name}.{f.name}")
PY
# capitals in paths (exFAT is case-insensitive: do NOT use `find -name '*[A-Z]*'`)
python3 -c "import os,re;[print(os.path.join(d,n)) for t in ('src','tests','config','scripts','research_space') for d,ds,fs in os.walk(t) for n in ds+fs if re.search('[A-Z]',n) and n!='INDEX.md' and '__pycache__' not in d]"
# banned verbs
grep -rnE 'def _?(handle|process|do|manage)_' src tests
```
Module ↔ class: each non-family module's primary class must equal the `PascalCase` of the file name (read the
`Contains` column of the folder `INDEX.md`). Known accepted deviations are listed in NAMING_CONVENTION §9.

## Rename (change)

1. **Decide.** Log it with the `decisions` skill (old → new, reason) — renames are decisions (convention §1).
2. **Map.** Write the full old → new table first: classes, modules, methods (`def x(`, `.x(`, and `Class.x` in
   docstrings / `Used by:` lines), parameters and attributes. Grep each old name for collisions with library APIs
   before replacing (`datetime.now`, `time.monotonic`, `dict.keys`, `DataFrame.empty`, pydantic `BaseModel.schema`
   / `json` / `dict` / `copy`, and the config key `lake.root`).
3. **Apply in one change** to `src/`, `tests/`, docstrings (`Contract`, `Used by`, `Test cases` text), then:
   - `.claude/CLASS_REGISTRY.md` sections A–D (names, method tables) — `registry` skill
   - every affected `INDEX.md` `Contains` cell — `index` skill
   - skills and plans that quote the old name (tell the session that owns `plans/`)
   - file renames: `git mv`; on exFAT a case-only rename needs two steps (`a.py` → `a_tmp.py` → `A.py`)
4. **Verify.** `make check` (ruff, mypy strict, import layers, pytest) and the check block above; paste real output.
   A name left in a string or docstring is a miss: `grep -rn "<old>" src tests .claude plans` must be empty.

## Report
Old → new table, files touched, `make check` summary lines, and any name that needs a new convention row.
