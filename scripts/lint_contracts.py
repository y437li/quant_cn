"""Project linter entry point.

Usage: `uv run python scripts/lint_contracts.py [--contracts] [--index] [--size] [--names]`.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from quant_cn.core.docs.contract_linter import GROUPS, ContractLinter

REPO_ROOT = Path(__file__).resolve().parents[1]


class LintContractsCli:
    """
    Purpose:
        Parse flags, run ContractLinter on the repository and print findings; exit 1 on any.

    Contract:
        Input:
            repo_root: Path  -- default: the repository holding this script
        Output:
            instance; `run(argv) -> int` (0 clean, 1 findings)
        Raises:
            SystemExit  -- argparse usage errors (code 2)

    Used by:
        Makefile target lint; .pre-commit-config.yaml hook lint-contracts

    Test cases:
        TC-LCC-001  clean tree exits 0; flags select groups; findings print and exit 1
    """

    def __init__(self, repo_root: Path = REPO_ROOT) -> None:
        self.repo_root = repo_root

    def run(self, argv: Sequence[str] | None = None) -> int:
        """
        Purpose:
            Run the selected groups (no flag = all) and report.

        Contract:
            Input:
                argv: Sequence[str] | None  -- default sys.argv[1:]
            Output:
                int  -- exit code
            Raises:
                SystemExit  -- usage error
        """
        parser = argparse.ArgumentParser(prog="lint_contracts")
        for group in GROUPS:
            parser.add_argument(f"--{group}", action="store_true", help=f"run the {group} checks")
        args = parser.parse_args(argv)
        groups = [g for g in GROUPS if getattr(args, g)] or list(GROUPS)
        findings = ContractLinter(self.repo_root).run(groups)
        for finding in findings:
            print(finding.to_text())
        print(f"lint_contracts ({', '.join(groups)}): {len(findings)} finding(s)")
        return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(LintContractsCli().run())
