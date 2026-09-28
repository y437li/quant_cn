"""Build the code-side project tables (classes, methods, used_by, contracts, test_cases)."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from quant_cn.core.docs.code_scanner import ClassInfo, CodeScanner, ModuleInfo
from quant_cn.core.docs.docstring_parser import DocstringParser
from quant_cn.core.docs.registry_reader import RegistryInfo, RegistryReader

REGISTRY = Path(".claude/CLASS_REGISTRY.md")
LAYERS = {
    "core": 1,
    "lake": 2,
    "data_loading": 3,
    "pipeline": 4,
    "statistic": 4,
    "back_testing": 5,
    "portfolio": 5,
    "visualization": 5,
    "cli": 6,
}
_TEST = re.compile(r"^test_tc_([a-z]+)_(\d{3})_")
COLUMNS = {
    "classes": [
        "name",
        "module",
        "layer",
        "base",
        "purpose",
        "tests",
        "added",
        "in_registry",
        "path",
        "line",
    ],
    "methods": ["class", "name", "purpose", "input_output", "raises", "in_registry", "line"],
    "used_by": ["callee_class", "caller", "caller_class", "caller_method", "note"],
    "contracts": ["class", "method", "purpose", "input", "output", "raises", "test_cases"],
    "test_cases": ["tc_id", "class", "description", "test_function", "test_file"],
}


class CodeTableBuilder:
    """
    Purpose:
        Turn src/ classes (AST + contract docstrings), the class registry and tests/ into the
        code-side tables of the `project` schema, one DataFrame per table with fixed columns.

    Contract:
        Input:
            repo_root: Path
            scanner:   CodeScanner
            parser:    DocstringParser
            registry:  RegistryReader
        Output:
            instance; `build_tables() -> dict[str, DataFrame]` keyed by table name (COLUMNS)
        Raises:
            (none at construction)

    Used by:
        lake.ProjectCatalog  -- code tables
        cli.QuantCnCli       -- injected type or call

    Test cases:
        TC-CTB-001  classes, methods, used_by, contracts and test_cases built from a sample repo
        TC-CTB-002  classes missing from the registry are flagged in_registry = false
    """

    def __init__(
        self,
        repo_root: Path,
        scanner: CodeScanner,
        parser: DocstringParser,
        registry: RegistryReader,
    ) -> None:
        self._root = repo_root
        self._scanner = scanner
        self._parser = parser
        self._registry = registry

    def build_tables(self) -> dict[str, pd.DataFrame]:
        """
        Purpose:
            Build all five code tables.

        Contract:
            Input:
                (none)
            Output:
                dict[str, DataFrame]  -- keys = COLUMNS keys; every frame has exactly its columns
            Raises:
                SyntaxError, OSError
        """
        path = self._root / REGISTRY
        reg = self._registry.read(path) if path.exists() else RegistryInfo()
        rows: dict[str, list[list[object]]] = {name: [] for name in COLUMNS}
        for rel, module in self._read_modules("src", self._root / "src"):
            for cls in module.classes:
                self._add_class(rows, rel, module, cls, reg)
        rows["test_cases"] = self._build_test_links(rows["test_cases"])
        return {name: pd.DataFrame(rows[name], columns=cols) for name, cols in COLUMNS.items()}

    def _read_modules(self, folder: str, root: Path) -> list[tuple[str, ModuleInfo]]:
        base = self._root / folder
        paths = (
            sorted(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
            if base.exists()
            else []
        )
        return [(str(p.relative_to(self._root)), self._scanner.read_module(p, root)) for p in paths]

    def _add_class(
        self,
        rows: dict[str, list[list[object]]],
        rel: str,
        module: ModuleInfo,
        cls: ClassInfo,
        reg: RegistryInfo,
    ) -> None:
        doc = self._parser.parse(cls.docstring)
        index = reg.index.get(cls.name, {})
        package = module.module.split(".")[1] if "." in module.module else module.module
        rows["classes"].append(
            [
                cls.name,
                module.module,
                LAYERS.get(package),
                ", ".join(cls.bases) or None,
                doc.purpose,
                index.get("Tests"),
                index.get("Added"),
                cls.name in reg.index or cls.name in reg.exceptions,
                rel,
                cls.lineno,
            ]
        )
        rows["contracts"].append(
            [
                cls.name,
                None,
                doc.purpose,
                doc.inputs,
                doc.outputs,
                doc.raises,
                ", ".join(doc.test_cases),
            ]
        )
        self._add_methods(rows, cls, reg)
        for entry in doc.used_by:
            rows["used_by"].append([cls.name, entry.text, entry.cls, entry.method, entry.note])
        for tc in doc.test_cases:
            rows["test_cases"].append([tc, cls.name, doc.test_descriptions.get(tc, ""), None, None])

    def _add_methods(
        self, rows: dict[str, list[list[object]]], cls: ClassInfo, reg: RegistryInfo
    ) -> None:
        registry_methods = {
            r["Method"].strip("`").split("(")[0]: r for r in reg.method_rows.get(cls.name, [])
        }
        for method in cls.list_public_methods():
            mdoc = self._parser.parse(method.docstring)
            row = registry_methods.get(method.name, {})
            rows["methods"].append(
                [
                    cls.name,
                    method.name,
                    mdoc.purpose,
                    row.get("Input -> Output"),
                    row.get("Raises"),
                    method.name in registry_methods,
                    method.lineno,
                ]
            )
            rows["contracts"].append(
                [cls.name, method.name, mdoc.purpose, mdoc.inputs, mdoc.outputs, mdoc.raises, ""]
            )

    def _build_test_links(self, cases: list[list[object]]) -> list[list[object]]:
        found: dict[str, tuple[str | None, str | None]] = {}
        for rel, module in self._read_modules("tests", self._root):
            for fn in [*module.functions, *(m for c in module.classes for m in c.methods)]:
                match = _TEST.match(fn.name)
                if match:
                    found[f"TC-{match.group(1).upper()}-{match.group(2)}"] = (fn.name, rel)
        seen: set[str] = set()
        out: list[list[object]] = []
        for tc, cls, desc, _, _ in cases:
            if str(tc) in seen:
                continue
            seen.add(str(tc))
            test_function, test_file = found.get(str(tc), (None, None))
            out.append([tc, cls, desc, test_function, test_file])
        return out
