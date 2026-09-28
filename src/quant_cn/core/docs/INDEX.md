# src/quant_cn/core/docs/

L1: parsers and checkers over code, docstrings and governance markdown (INDEX, registry, conventions); used by scripts/lint_contracts.py and plan 02.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `base_checker.py` | Extension point for repository checkers and their Finding records | `Finding`, `BaseChecker` |
| `code_scanner.py` | AST view of Python modules: classes, methods, module functions, names each class references | `MethodInfo`, `ClassInfo`, `ModuleInfo`, `CodeScanner` |
| `code_table_builder.py` | Build the code-side project tables (classes, methods, used_by, contracts, test_cases) | `CodeTableBuilder` |
| `contract_checker.py` | Contract rules of CODING_STANDARD §3-§5: docstrings, TC parity, Used by, registry, structure | `CodeUnit`, `ContractChecker` |
| `contract_linter.py` | Run the repository checkers as one linter (CODING_STANDARD §4.1) | `ContractLinter` |
| `convention_reader.py` | Read the method verb table from NAMING_CONVENTION §2.1 so the linter never drifts from it | `ConventionReader` |
| `decisions_reader.py` | Read the append-only decision log (plans/decisions/DECISIONS.md) into records | `DecisionRecord`, `DecisionsReader` |
| `doc_table_builder.py` | Build the document-side project tables (folders, files, decisions, plans, phases) as frames | `DocTableBuilder` |
| `docstring_parser.py` | Parse the mandatory contract docstring (CODING_STANDARD §3) into a typed record | `UsedByEntry`, `DocContract`, `DocstringParser` |
| `index_checker.py` | INDEX.md tree parity with disk and code (CODING_STANDARD §5.1, D-014) | `IndexChecker` |
| `index_reader.py` | Read a folder `INDEX.md` (CODING_STANDARD §5.1) into folder and file entries | `IndexEntry`, `IndexInfo`, `IndexReader` |
| `markdown_table.py` | Read pipe tables out of governance markdown (INDEX.md, CLASS_REGISTRY.md, conventions) | `MarkdownTable`, `MarkdownTableReader` |
| `name_checker.py` | Naming rules (NAMING_CONVENTION §1-§2, D-029/D-030): paths, verb-first methods, test names | `NameChecker` |
| `plan_reader.py` | Read an execution plan (plans/execution/NN_<slug>.md) into a plan record with its phases | `PhaseRecord`, `PlanRecord`, `PlanReader` |
| `registry_reader.py` | Read `.claude/CLASS_REGISTRY.md` (CODING_STANDARD §5, D-013) into typed sections | `RegistryInfo`, `RegistryReader` |
| `repo_files.py` | List the repository's files as git sees them (tracked + untracked, minus ignored) | `RepoFiles` |
| `size_checker.py` | Hard size limits (CODING_STANDARD §2.6, D-030): files, classes, callables, governance docs | `SizeChecker` |
