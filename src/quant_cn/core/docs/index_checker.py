"""INDEX.md tree parity with disk and code (CODING_STANDARD §5.1, D-014)."""

from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.base_checker import BaseChecker, Finding
from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.index_reader import IndexInfo, IndexReader
from quant_cn.core.docs.repo_files import RepoFiles


class IndexChecker(BaseChecker):
    """
    Purpose:
        Every visible folder has an INDEX.md whose folder and file rows equal what is on disk,
        and whose Contains cell for a .py file lists exactly its top-level classes (fixtures for
        conftest.py; public constants for modules without classes).

    Contract:
        Input:
            repo_root: Path
            files:     RepoFiles
            reader:    IndexReader
            scanner:   CodeScanner
        Output:
            instance; `run() -> list[Finding]` with rule "index"
        Raises:
            (none at construction)

    Used by:
        core.docs.ContractLinter  -- `--index`

    Test cases:
        TC-IC-001  folder without INDEX.md is reported
        TC-IC-002  rows missing from disk and disk entries missing from the index are reported
        TC-IC-003  Contains cell differing from the module's classes is reported
        TC-IC-004  a consistent tree yields no findings
    """

    rule = "index"

    def __init__(
        self, repo_root: Path, files: RepoFiles, reader: IndexReader, scanner: CodeScanner
    ) -> None:
        self._root = repo_root
        self._files = files
        self._reader = reader
        self._scanner = scanner

    def run(self) -> list[Finding]:
        """
        Purpose:
            Check every folder's index.

        Contract:
            Input:
                (none)
            Output:
                list[Finding]  -- sorted
            Raises:
                RuntimeError  -- file listing failed
                SyntaxError   -- a listed module does not parse
        """
        files = self._files.list_files()
        folders = self._files.list_folders()
        findings: list[Finding] = []
        for folder in folders:
            index = folder / "INDEX.md"
            if index not in files:
                findings.append(Finding(str(index), 0, self.rule, "missing INDEX.md"))
                continue
            info = self._reader.read(self._root / index)
            findings += self._check_folder(folder, info, files, folders)
        return sorted(findings)

    def _check_folder(
        self, folder: Path, info: IndexInfo, files: list[Path], folders: list[Path]
    ) -> list[Finding]:
        where = str(folder / "INDEX.md")
        disk_dirs = {f.name for f in folders if f.parent == folder and f != folder}
        disk_files = {f.name for f in files if f.parent == folder and f.name != "INDEX.md"}
        out = [
            Finding(where, 0, self.rule, f"folder not listed: {n}/")
            for n in sorted(disk_dirs - set(info.folders))
        ]
        out += [
            Finding(where, 0, self.rule, f"listed folder missing: {n}/")
            for n in sorted(set(info.folders) - disk_dirs)
        ]
        out += [
            Finding(where, 0, self.rule, f"file not listed: {n}")
            for n in sorted(disk_files - set(info.files))
        ]
        out += [
            Finding(where, 0, self.rule, f"listed file missing: {n}")
            for n in sorted(set(info.files) - disk_files)
        ]
        for name in sorted(disk_files & set(info.files)):
            if name.endswith(".py"):
                out += self._check_contains(folder / name, set(info.files[name].contains), where)
        return out

    def _check_contains(self, rel: Path, listed: set[str], where: str) -> list[Finding]:
        module = self._scanner.read_module(self._root / rel, self._root)
        if rel.name == "conftest.py":
            expected = {
                f.name for f in module.functions if any("fixture" in d for d in f.decorators)
            }
        elif module.classes:
            expected = {c.name for c in module.classes}
        else:
            expected = set(listed) & set(module.constants)
        if listed == expected:
            return []
        msg = f"{rel.name} Contains {sorted(listed)} != code {sorted(expected)}"
        return [Finding(where, 0, self.rule, msg)]
