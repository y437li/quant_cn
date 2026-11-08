"""Naming rules (NAMING_CONVENTION §1-§2, D-029/D-030): paths, verb-first methods, test names."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from quant_cn.core.docs.base_checker import BaseChecker, Finding
from quant_cn.core.docs.code_scanner import ClassInfo, CodeScanner, ModuleInfo

CODE_DIRS = ("src", "tests", "scripts")
BANNED = ("handle", "process", "do", "manage")
TOOL_FILES = frozenset({"Makefile"})
SPECIAL_MODULES = frozenset({"cli", "exceptions", "__init__", "conftest", "support"})
_LOWER = re.compile(r"^[a-z0-9_.-]+$")
_UPPER_DOC = re.compile(r"^[A-Z0-9_]+\.md$")
_TEST_NAME = re.compile(r"^test_tc_[a-z]+_\d{3}_\w+$")


class NameChecker(BaseChecker):
    """
    Purpose:
        Enforce names: lowercase paths (governance `UPPER_SNAKE.md` and tool files excepted),
        verb-first method and function names from the convention's verb table, no banned verbs,
        test functions named `test_tc_<id>_<desc>`, and module name matching its primary class.

    Contract:
        Input:
            repo_root: Path
            scanner:   CodeScanner
            files:     list[Path]      -- repo-relative visible files
            verbs:     Sequence[str]   -- from ConventionReader.read_verbs ("get_", "run", ...)
        Output:
            instance; `run() -> list[Finding]` with rule "names"
        Raises:
            (none at construction)

    Used by:
        core.docs.ContractLinter  -- `--names`

    Test cases:
        TC-NC-001  capitalised folder or file reported; UPPER_SNAKE.md and Makefile allowed
        TC-NC-002  method without an allowed verb reported; properties, dunders, overrides of
                   fixtures and pytest fixtures skipped
        TC-NC-003  banned verb and badly named test function reported
        TC-NC-004  module whose classes do not match its name reported; family modules allowed
    """

    rule = "names"

    def __init__(
        self, repo_root: Path, scanner: CodeScanner, files: list[Path], verbs: Sequence[str]
    ) -> None:
        self._root = repo_root
        self._scanner = scanner
        self._files = files
        self._verbs = list(verbs)

    def run(self) -> list[Finding]:
        """
        Purpose:
            Check every visible path and every code file.

        Contract:
            Input:
                (none)
            Output:
                list[Finding]  -- sorted
            Raises:
                SyntaxError, OSError
        """
        findings = [f for rel in self._files for f in self._check_path(rel)]
        for rel in self._files:
            if rel.suffix == ".py" and rel.parts[0] in CODE_DIRS:
                findings += self._check_module(
                    rel, self._scanner.read_module(self._root / rel, self._root)
                )
        return sorted(set(findings))

    def is_verb_name(self, name: str) -> bool:
        """
        Purpose:
            True if `name` (leading underscores ignored) starts with an allowed, unbanned verb.

        Contract:
            Input:
                name: str
            Output:
                bool
            Raises:
                (none)
        """
        bare = name.lstrip("_")
        if bare.split("_")[0] in BANNED:
            return False
        for verb in self._verbs:
            stem = verb.rstrip("_")
            if bare == stem or bare.startswith(stem + "_"):
                return True
        return False

    def _check_path(self, rel: Path) -> list[Finding]:
        out = [
            Finding(str(rel), 0, self.rule, f"folder not lowercase: {p}")
            for p in rel.parts[:-1]
            if not _LOWER.match(p)
        ]
        name = rel.name
        if not (_LOWER.match(name) or _UPPER_DOC.match(name) or name in TOOL_FILES):
            out.append(Finding(str(rel), 0, self.rule, f"file name not allowed: {name}"))
        return out

    def _check_module(self, rel: Path, info: ModuleInfo) -> list[Finding]:
        out: list[Finding] = []
        for fn in info.functions:
            if any("fixture" in d for d in fn.decorators):
                continue
            if fn.name.startswith("test_"):
                if not _TEST_NAME.match(fn.name):
                    out.append(Finding(str(rel), fn.lineno, self.rule, f"test name {fn.name}"))
            elif not self.is_verb_name(fn.name):
                out.append(
                    Finding(str(rel), fn.lineno, self.rule, f"function {fn.name}: no verb prefix")
                )
        for cls in info.classes:
            out += self._check_class(rel, cls)
        if rel.parts[0] == "src":
            out += self._check_module_name(rel, info)
        return out

    def _check_class(self, rel: Path, cls: ClassInfo) -> list[Finding]:
        out: list[Finding] = []
        for m in cls.methods:
            if m.is_property or (m.name.startswith("__") and m.name.endswith("__")):
                continue
            if not self.is_verb_name(m.name):
                msg = f"{cls.name}.{m.name}: no verb prefix"
                out.append(Finding(str(rel), m.lineno, self.rule, msg))
        return out

    def _check_module_name(self, rel: Path, info: ModuleInfo) -> list[Finding]:
        stem = rel.stem
        if stem in SPECIAL_MODULES or not info.classes:
            return []
        whole = "".join(p.capitalize() for p in stem.split("_"))
        family = "".join(p.capitalize() for p in stem.removesuffix("s").split("_"))
        if any(c.name == whole or c.name.endswith(family) for c in info.classes):
            return []
        msg = f"module {stem}.py holds no class named {whole} or *{family}"
        return [Finding(str(rel), 0, self.rule, msg)]
