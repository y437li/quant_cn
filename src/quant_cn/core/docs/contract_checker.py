"""Contract rules of CODING_STANDARD §3-§5: docstrings, TC parity, Used by, registry, structure."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from quant_cn.core.docs.base_checker import BaseChecker, Finding
from quant_cn.core.docs.code_scanner import ClassInfo, CodeScanner, ModuleInfo
from quant_cn.core.docs.docstring_parser import DocContract, DocstringParser
from quant_cn.core.docs.registry_reader import RegistryInfo, RegistryReader

CLASS_SECTIONS = ("Purpose", "Contract", "Input", "Output", "Raises", "Used by", "Test cases")
METHOD_SECTIONS = ("Purpose", "Contract")
REGISTRY = Path(".claude/CLASS_REGISTRY.md")
_TEST = re.compile(r"^test_tc_([a-z]+)_(\d{3})_")


@dataclass(frozen=True)
class CodeUnit:
    """
    Purpose:
        A class with the module it lives in and its parsed contract.

    Contract:
        Input:
            rel:      str        -- repo-relative file path
            module:   ModuleInfo
            cls:      ClassInfo
            contract: DocContract
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.ContractChecker  -- one unit per class under src/ and scripts/

    Test cases:
        TC-CC-001  class and public method missing contract sections are reported
    """

    rel: str
    module: ModuleInfo
    cls: ClassInfo
    contract: DocContract


class ContractChecker(BaseChecker):
    """
    Purpose:
        Check contracts across the tree: class docstrings carry all sections and public methods
        Purpose + Contract; docstring TC IDs and `test_tc_*` functions match one-to-one; each
        src class's `Used by` equals the src classes that reference it; every src class has its
        registry rows and a method table equal to its public methods; class names are unique;
        no module-level functions in src outside core/utils.

    Contract:
        Input:
            repo_root: Path
            scanner:   CodeScanner
            parser:    DocstringParser
            registry:  RegistryReader
        Output:
            instance; `run() -> list[Finding]` with rule "contract"
        Raises:
            (none at construction)

    Used by:
        core.docs.ContractLinter  -- `--contracts`

    Test cases:
        TC-CC-001  class and public method missing contract sections are reported
        TC-CC-002  TC ID without a test and test without a TC ID are reported
        TC-CC-003  caller missing from Used by, unknown and stale callers are reported
        TC-CC-004  missing registry row, block, method row and extra registry class are reported
        TC-CC-005  duplicate class names and loose functions in src are reported
    """

    rule = "contract"

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

    def run(self) -> list[Finding]:
        """
        Purpose:
            Run every contract rule.

        Contract:
            Input:
                (none)
            Output:
                list[Finding]  -- sorted
            Raises:
                SyntaxError, OSError
        """
        src = self._read_modules("src", self._root / "src")
        scripts = self._read_modules("scripts", self._root)
        tests = self._read_modules("tests", self._root)
        src_units = self._build_units(src)
        all_units = src_units + self._build_units(scripts)
        findings = self._check_sections(all_units)
        findings += self._check_tests(src + scripts, all_units, tests)
        findings += self._check_used_by(src_units, all_units)
        findings += self._check_structure(src, src_units)
        path = self._root / REGISTRY
        if path.exists():
            findings += self._check_registry(src, src_units, self._registry.read(path))
        return sorted(findings)

    def _read_modules(self, folder: str, root: Path) -> list[tuple[str, ModuleInfo]]:
        base = self._root / folder
        paths = sorted(base.rglob("*.py")) if base.exists() else []
        return [
            (str(p.relative_to(self._root)), self._scanner.read_module(p, root))
            for p in paths
            if "__pycache__" not in p.parts
        ]

    def _build_units(self, modules: list[tuple[str, ModuleInfo]]) -> list[CodeUnit]:
        return [
            CodeUnit(rel, info, cls, self._parser.parse(cls.docstring))
            for rel, info in modules
            for cls in info.classes
        ]

    def _check_sections(self, units: list[CodeUnit]) -> list[Finding]:
        out: list[Finding] = []
        for u in units:
            missing = [s for s in CLASS_SECTIONS if not u.contract.has(s)]
            if missing and not u.cls.name.startswith("_"):
                out.append(
                    self._build_finding(
                        u.rel, u.cls.lineno, f"class {u.cls.name} missing {missing}"
                    )
                )
            for m in u.cls.list_public_methods():
                doc = self._parser.parse(m.docstring)
                lost = [s for s in METHOD_SECTIONS if not doc.has(s)]
                if lost:
                    msg = f"{u.cls.name}.{m.name} missing {lost}"
                    out.append(self._build_finding(u.rel, m.lineno, msg))
        return out

    def _check_tests(
        self,
        code: list[tuple[str, ModuleInfo]],
        units: list[CodeUnit],
        tests: list[tuple[str, ModuleInfo]],
    ) -> list[Finding]:
        documented: dict[str, tuple[str, int]] = {}
        for u in units:
            for tc in u.contract.test_cases:
                documented.setdefault(tc, (u.rel, u.cls.lineno))
        for rel, info in code:
            for tc in self._parser.parse(info.docstring).test_cases:
                documented.setdefault(tc, (rel, 1))
        tested: dict[str, tuple[str, int]] = {}
        out: list[Finding] = []
        for rel, info in tests:
            fns = list(info.functions) + [m for c in info.classes for m in c.methods]
            for fn in fns:
                match = _TEST.match(fn.name)
                if not match:
                    continue
                tc = f"TC-{match.group(1).upper()}-{match.group(2)}"
                if tc in tested:
                    out.append(self._build_finding(rel, fn.lineno, f"{tc} has more than one test"))
                tested[tc] = (rel, fn.lineno)
        for tc in sorted(set(documented) - set(tested)):
            out.append(self._build_finding(*documented[tc], f"{tc} has no test function"))
        for tc in sorted(set(tested) - set(documented)):
            out.append(self._build_finding(*tested[tc], f"{tc} test is not in any docstring"))
        return out

    def _check_used_by(self, src_units: list[CodeUnit], all_units: list[CodeUnit]) -> list[Finding]:
        by_name = {u.cls.name: u for u in all_units}
        src_names = {u.cls.name for u in src_units}
        out: list[Finding] = []
        for u in src_units:
            actual = {v.cls.name for v in src_units if u.cls.name in v.cls.references}
            listed = {e.cls for e in u.contract.used_by if e.cls}
            for caller in sorted(actual - listed):
                out.append(
                    self._build_finding(
                        u.rel, u.cls.lineno, f"{u.cls.name} Used by misses {caller}"
                    )
                )
            for entry in u.contract.used_by:
                if not entry.cls:
                    continue
                target = by_name.get(entry.cls)
                if target is None:
                    msg = f"{u.cls.name} Used by names unknown class {entry.text}"
                elif entry.method and entry.method not in {m.name for m in target.cls.methods}:
                    msg = f"{u.cls.name} Used by names unknown method {entry.text}"
                elif entry.cls in src_names and u.cls.name not in target.cls.references:
                    msg = f"{u.cls.name} Used by lists {entry.cls}, which does not reference it"
                else:
                    continue
                out.append(self._build_finding(u.rel, u.cls.lineno, msg))
        return out

    def _check_structure(
        self, src: list[tuple[str, ModuleInfo]], units: list[CodeUnit]
    ) -> list[Finding]:
        out: list[Finding] = []
        seen: dict[str, str] = {}
        for u in units:
            if u.cls.name in seen:
                msg = f"class {u.cls.name} also defined in {seen[u.cls.name]}"
                out.append(self._build_finding(u.rel, u.cls.lineno, msg))
            seen.setdefault(u.cls.name, u.rel)
        for rel, info in src:
            if info.module.startswith("quant_cn.core.utils"):
                continue
            for fn in info.functions:
                out.append(
                    self._build_finding(
                        rel, fn.lineno, f"loose function {fn.name} outside core/utils"
                    )
                )
        return out

    def _check_registry(
        self, src: list[tuple[str, ModuleInfo]], units: list[CodeUnit], reg: RegistryInfo
    ) -> list[Finding]:
        where = str(REGISTRY)
        exceptions = self._list_exceptions(units)
        out: list[Finding] = []
        for u in units:
            name = u.cls.name
            if name in exceptions:
                if name not in reg.exceptions:
                    out.append(
                        self._build_finding(where, 0, f"exception {name} missing from section D")
                    )
                continue
            out += self._check_registry_class(u, reg)
        code_names = {u.cls.name for u in units}
        for extra in sorted((set(reg.index) | reg.exceptions | set(reg.methods)) - code_names):
            out.append(self._build_finding(where, 0, f"registry lists {extra}, not found in src"))
        constants = {
            c for rel, info in src if rel.endswith("core/frames.py") for c in info.constants
        }
        for schema in sorted(constants - reg.schemas):
            out.append(self._build_finding(where, 0, f"schema {schema} missing from section E"))
        return out

    def _check_registry_class(self, u: CodeUnit, reg: RegistryInfo) -> list[Finding]:
        where, name = str(REGISTRY), u.cls.name
        out: list[Finding] = []
        if name not in reg.index:
            out.append(self._build_finding(where, 0, f"{name} missing from section A"))
        public = [m.name for m in u.cls.list_public_methods()]
        count = reg.index.get(name, {}).get("Public methods (count)", "")
        if name in reg.index and count != str(len(public)):
            out.append(
                self._build_finding(where, 0, f"{name} method count {count} != {len(public)}")
            )
        if name not in reg.methods:
            out.append(self._build_finding(where, 0, f"{name} has no section B block"))
        else:
            rows = {m for m in reg.methods[name] if not m.startswith("_")}
            for method in sorted(set(public) ^ rows):
                out.append(
                    self._build_finding(where, 0, f"{name}.{method} method table differs from code")
                )
        if any(m.is_abstract for m in u.cls.methods) and name not in reg.abstract:
            out.append(self._build_finding(where, 0, f"abstract {name} missing from section C"))
        return out

    @staticmethod
    def _list_exceptions(units: list[CodeUnit]) -> set[str]:
        found = {"Exception"}
        changed = True
        while changed:
            new = {u.cls.name for u in units if set(u.cls.bases) & found} - found
            found |= new
            changed = bool(new)
        return found - {"Exception"}

    def _build_finding(self, path: str, line: int, message: str) -> Finding:
        return Finding(path, line, self.rule, message)
