"""Hard size limits (CODING_STANDARD §2.6, D-030): files, classes, callables, governance docs."""

from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.base_checker import BaseChecker, Finding
from quant_cn.core.docs.code_scanner import CodeScanner

MAX_FILE = 600
MAX_CLASS = 300
MAX_CALLABLE = 50
MAX_DOC = 300
CODE_DIRS = ("src", "tests", "scripts")


class SizeChecker(BaseChecker):
    """
    Purpose:
        Fail any .py file over 600 lines, class over 300, function or method over 50 (physical
        lines, docstrings included), and INDEX.md / SKILL.md / execution plan over 300 lines.

    Contract:
        Input:
            repo_root: Path
            scanner:   CodeScanner
            files:     list[Path]  -- repo-relative visible files (RepoFiles.list_files)
        Output:
            instance; `run() -> list[Finding]` with rule "size"
        Raises:
            (none at construction)

    Used by:
        core.docs.ContractLinter  -- `--size`

    Test cases:
        TC-SC-001  file, class and method over the limit are each reported once
        TC-SC-002  long INDEX.md and plan files reported; other markdown ignored
    """

    rule = "size"

    def __init__(self, repo_root: Path, scanner: CodeScanner, files: list[Path]) -> None:
        self._root = repo_root
        self._scanner = scanner
        self._files = files

    def run(self) -> list[Finding]:
        """
        Purpose:
            Check every code file and governance doc.

        Contract:
            Input:
                (none)
            Output:
                list[Finding]  -- sorted
            Raises:
                SyntaxError, OSError
        """
        findings: list[Finding] = []
        for rel in self._files:
            if rel.suffix == ".py" and rel.parts[0] in CODE_DIRS:
                findings += self._check_module(rel)
            elif self._is_limited_doc(rel):
                n = len((self._root / rel).read_text(encoding="utf-8").splitlines())
                if n > MAX_DOC:
                    findings.append(Finding(str(rel), 0, self.rule, f"{n} lines > {MAX_DOC}"))
        return sorted(findings)

    def _check_module(self, rel: Path) -> list[Finding]:
        info = self._scanner.read_module(self._root / rel, self._root)
        out: list[Finding] = []
        if info.n_lines > MAX_FILE:
            out.append(Finding(str(rel), 0, self.rule, f"file {info.n_lines} lines > {MAX_FILE}"))
        callables = list(info.functions)
        for cls in info.classes:
            if cls.n_lines > MAX_CLASS:
                msg = f"class {cls.name} {cls.n_lines} lines > {MAX_CLASS}"
                out.append(Finding(str(rel), cls.lineno, self.rule, msg))
            callables += cls.methods
        for fn in callables:
            if fn.n_lines > MAX_CALLABLE:
                msg = f"{fn.name} {fn.n_lines} lines > {MAX_CALLABLE}"
                out.append(Finding(str(rel), fn.lineno, self.rule, msg))
        return out

    @staticmethod
    def _is_limited_doc(rel: Path) -> bool:
        if rel.name in ("INDEX.md", "SKILL.md"):
            return True
        return rel.parent == Path("plans/execution") and rel.name[:2].isdigit()
