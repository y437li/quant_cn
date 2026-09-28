"""Run the repository checkers as one linter (CODING_STANDARD §4.1)."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from quant_cn.core.docs.base_checker import BaseChecker, Finding
from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.contract_checker import ContractChecker
from quant_cn.core.docs.convention_reader import ConventionReader
from quant_cn.core.docs.docstring_parser import DocstringParser
from quant_cn.core.docs.index_checker import IndexChecker
from quant_cn.core.docs.index_reader import IndexReader
from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.name_checker import NameChecker
from quant_cn.core.docs.registry_reader import RegistryReader
from quant_cn.core.docs.repo_files import RepoFiles
from quant_cn.core.docs.size_checker import SizeChecker

GROUPS = ("contracts", "index", "size", "names")
CONVENTION = Path("plans/standards/NAMING_CONVENTION.md")


class ContractLinter:
    """
    Purpose:
        Build the four checkers (contracts, index, size, names) for one repository and run the
        selected groups, returning all findings sorted.

    Contract:
        Input:
            repo_root: Path  -- a git working tree with src/, tests/, scripts/, plans/
        Output:
            instance; `run(groups) -> list[Finding]`
        Raises:
            (none at construction)

    Used by:
        scripts/lint_contracts.py  -- command line (`make lint`, pre-commit)
        tests/test_contracts.py    -- the tree must pass

    Test cases:
        TC-CTL-001  the repository passes every group
        TC-CTL-002  unknown group raises ValueError; a selected group runs only its checker
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run(self, groups: Iterable[str] = GROUPS) -> list[Finding]:
        """
        Purpose:
            Run the selected checker groups.

        Contract:
            Input:
                groups: Iterable[str]  -- subset of GROUPS; default all
            Output:
                list[Finding]  -- sorted, deduplicated
            Raises:
                ValueError    -- unknown group
                RuntimeError  -- git listing failed
                SyntaxError   -- a Python file does not parse
        """
        selected = list(groups)
        unknown = sorted(set(selected) - set(GROUPS))
        if unknown:
            raise ValueError(f"unknown groups {unknown}; choose from {GROUPS}")
        findings: set[Finding] = set()
        for group in selected:
            findings.update(self._build_checker(group).run())
        return sorted(findings)

    def _build_checker(self, group: str) -> BaseChecker:
        root = self.repo_root
        scanner, tables = CodeScanner(), MarkdownTableReader()
        files = RepoFiles(root)
        if group == "contracts":
            return ContractChecker(root, scanner, DocstringParser(), RegistryReader(tables))
        if group == "index":
            return IndexChecker(root, files, IndexReader(tables), scanner)
        if group == "size":
            return SizeChecker(root, scanner, files.list_files())
        verbs = ConventionReader(tables).read_verbs(root / CONVENTION)
        return NameChecker(root, scanner, files.list_files(), verbs)
