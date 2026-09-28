---
name: standard-review
description: Check changed or specified code against plans/standards/CODING_STANDARD.md and its §8 definition-of-done checklist — OOP only, contract docstrings with Used by, layering, injection, no hardcoded config/secrets, PIT data rules, size limits, tests, ruff, registry. Use before reporting any code task as done, before marking a plan phase done, or when the user asks to "review", "check the standard", "is this done", or "audit the code".
---

# standard-review

Read-only review. Report findings with `file:line`; fix nothing unless the user asks.
Scope: files changed in the task (or `git diff --name-only` if the repo is under git), or the path the user names. `all` means `src/ tests/ research_space/`.

## Checks

Run each; a check with no findings is reported as `ok`. `\|` inside the table is markdown escaping: type `|` in the shell.

| # | Rule (standard §) | How to check |
|---|---|---|
| 1 | No loose functions outside `core/utils` (§1.1) | `grep -nE '^def ' <files> \| grep -v 'core/utils'` |
| 2 | Every class and public method has `Purpose:` `Contract:` (`Input:` `Output:` `Raises:`) `Used by:` `Test cases:` (§3) | ast walk below |
| 3 | `Used by` agrees with docstring, registry and grep (§3, D-010) | `registry` skill, consistency check |
| 4 | Layering: imports only same or lower layer; `pipeline`↔`statistic` never import each other; `research_space` never imported by the package (§2.1, FOLDER_STRUCTURE) | `uv run lint-imports` (contract in `pyproject.toml [tool.importlinter]`, `cli` is the top layer); for a finding, `grep -nE '^(from\|import) quant_cn\.' <files>` |
| 5 | Dependencies injected, not constructed inside methods or used as module globals (§2.3) | read `__init__` and method bodies for `Client(`, `Config(`, `duckdb.connect(` outside `__init__` of the owning class |
| 6 | No hardcoded paths, tickers, dates, thresholds, tokens (§2.4, §4) | `grep -nE "/Volumes\|/Users\|[0-9]{6}\.(SH\|SZ\|BJ)\|['\"](19\|20)[0-9]{6}['\"]\|token\s*=" <src files>` |
| 7 | Errors from `QuantCnError` tree; no bare `except:`; no `print` outside entry points (§2.5) | `grep -nE 'raise (Exception\|ValueError\|RuntimeError)\|except:\|print\(' <src files>` (ValueError is fine only if the contract lists it) |
| 8 | Size limits, hard: file ≤ 600, class ≤ 300, method ≤ 50 lines; target file ≤ 400 (§2.6, D-030) | `wc -l` per file (fail > 600, warn > 400), ast walk below |
| 9 | Data rules (§2.7): datasets declare `primary_key` + `known_on`; no fundamentals/event join outside `PitAligner`; fundamentals joined on `(ts_code, end_date)` with `report_type` filter; no direct parquet reads outside `ParquetWriter`/`LakeCatalog`; adjusted prices only from the one adjuster | `grep -nE 'read_parquet\|pq\.read\|ASOF\|merge\(\|\.join\(\|adj_factor' <src files>` and read each hit |
| 10 | Dates `YYYYMMDD` strings at storage/API boundary; conversions only via `DateCodec`/`TickerNormalizer` (§4, D-005) | `grep -nE 'to_datetime\|strptime\|strftime' <src files>` outside those classes |
| 11 | Naming per NAMING_CONVENTION §2.1–2.2 (verb-first methods from the prefix table, no `handle_/process_/do_`, no `df`/`data` names beyond local scope), `from __future__ import annotations`, type hints on every signature (§4) | `naming` skill, check block (verb table, capitals in paths, banned verbs) + ast walk |
| 12 | Tests: `tests/<layer>/test_<module>.py` exists; one test per TC ID; no network, no files outside `tmp_path`; no float `==` (§6) | `test-cases` skill, audit mode; `grep -nE 'requests\.\|http\|/Volumes' tests/` |
| 13 | Tools green (§7.6) | `make check` (ruff format --check, ruff check, mypy --strict, lint-imports, pytest --cov) — paste the summary lines |
| 14 | Registry row current; plan phase updated (§8) | `registry` consistency check; open the plan's Log |

### ast walk (checks 2, 8, 11)
```bash
python - <<'PY' <files...>
import ast, sys
REQ = ("Purpose:", "Contract:", "Used by:", "Test cases:")
for path in sys.argv[1:]:
    tree = ast.parse(open(path).read())
    if "from __future__ import annotations" not in open(path).read():
        print(f"{path}:1 missing __future__ annotations")
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            n = node.end_lineno - node.lineno + 1
            limit = 300 if isinstance(node, ast.ClassDef) else 50
            if n > limit:
                print(f"{path}:{node.lineno} {node.name} {n} lines > {limit}")
            public = not node.name.startswith("_")
            if isinstance(node, ast.ClassDef) or (public and node.name != "__init__"):
                doc = ast.get_docstring(node) or ""
                missing = [h for h in REQ if h not in doc]
                if isinstance(node, ast.ClassDef) and missing:
                    print(f"{path}:{node.lineno} class {node.name} missing {missing}")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a for a in node.args.args if a.arg not in ("self", "cls")]
                if node.returns is None or any(a.annotation is None for a in args):
                    print(f"{path}:{node.lineno} {node.name} missing type hints")
PY
```
Public methods: flag a missing contract only when its inputs/outputs are not covered by the class-level contract.

## Verdict
- **Done**: every check `ok`, tool output pasted.
- **Not done**: list blocking findings first (checks 2–4, 6, 9, 12, 13), then the rest.

## Report format
```
standard-review: <scope>  ->  Done | Not done
| # | Check | Result | Findings (file:line — issue) |
ruff/pytest output (verbatim, trimmed to summary lines)
```
Nothing else. Do not restate the standard.
