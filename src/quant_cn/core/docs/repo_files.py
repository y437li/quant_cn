"""List the repository's files as git sees them (tracked + untracked, minus ignored)."""

from __future__ import annotations

import subprocess
from pathlib import Path


class RepoFiles:
    """
    Purpose:
        The set of repository files a linter should see: `git ls-files --cached --others
        --exclude-standard`, so .gitignore (caches, .env, lake guards) decides what is ignored.

    Contract:
        Input:
            repo_root: Path  -- a git working tree
        Output:
            instance; `list_files`, `list_folders`
        Raises:
            (none at construction)

    Used by:
        core.docs.IndexChecker     -- folders and files that need index rows
        core.docs.ContractLinter   -- injected type or call
        core.docs.DocTableBuilder  -- injected type or call
        cli.QuantCnCli             -- injected type or call

    Test cases:
        TC-RF-001  tracked + untracked files; ignored and deleted skipped; disk case reported
        TC-RF-002  list_folders includes the root and every parent folder
        TC-RF-003  outside a git tree raises RuntimeError
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def list_files(self) -> list[Path]:
        """
        Purpose:
            Relative paths of visible files that exist on disk, spelled as on disk, sorted.

        Contract:
            Input:
                (none)
            Output:
                list[Path]  -- relative to repo_root
            Raises:
                RuntimeError  -- git missing or repo_root not a working tree
        """
        cmd = ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
        try:
            out = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(f"cannot list files in {self.repo_root}: {exc}") from exc
        names = {n for n in out.decode("utf-8").split("\0") if n}
        resolved = {self._normalize_case(Path(n)) for n in names}
        return sorted(p for p in resolved if p is not None)

    def _normalize_case(self, rel: Path) -> Path | None:
        """Return `rel` spelled as on disk (case-insensitive volumes); None if not a file."""
        folder, parts = self.repo_root, []
        for part in rel.parts:
            try:
                names = {p.name.lower(): p.name for p in folder.iterdir()}
            except OSError:
                return None
            actual = names.get(part.lower())
            if actual is None:
                return None
            parts.append(actual)
            folder = folder / actual
        return Path(*parts) if folder.is_file() else None

    def list_folders(self) -> list[Path]:
        """
        Purpose:
            Every folder that holds at least one visible file, including the root (Path(".")).

        Contract:
            Input:
                (none)
            Output:
                list[Path]  -- relative, sorted
            Raises:
                RuntimeError  -- as list_files
        """
        folders = {Path(".")}
        for path in self.list_files():
            folders.update(path.parents)
        return sorted(folders)
