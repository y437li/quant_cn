"""Rules for the research log and committed research runs (plan 02 ph6, D-144)."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Collection
from pathlib import Path

from quant_cn.core.docs.base_checker import BaseChecker, Finding
from quant_cn.core.docs.research_log_reader import ResearchLogReader

LOG = Path("research_space/RESEARCH_LOG.md")
RUNS = Path("research_space/runs")
MAX_HELD = 5  # a file naming this many held codes is treated as a hard-coded book
_SLUG = re.compile(r"^(\d{8})_[a-z0-9]+(?:_[a-z0-9]+){0,3}$")


class ResearchLogChecker(BaseChecker):
    """
    Purpose:
        Check the research log and the run folders: the slug is `YYYYMMDD_<topic>` (topic
        ≤ 4 snake_case words), unique and matching the row date; the scripts path exists. No
        committed file under research_space/runs/ hard-codes the private book: it may not name
        MAX_HELD or more held codes nor contain a position's cost or the cash figure.

    Contract:
        Input:
            repo_root: Path
            reader:    ResearchLogReader
            files:     list[Path]            -- repo-relative visible files (RepoFiles)
            held:      Collection[str]       -- ts_codes in the private book (empty: skip)
            secrets:   Collection[str]       -- private numbers as written (costs, cash)
        Output:
            instance; `run() -> list[Finding]` with rule "research"
        Raises:
            (none at construction)

    Used by:
        core.docs.ContractLinter  -- `--research`

    Test cases:
        TC-RSC-001  bad slug, duplicate slug, date mismatch and missing scripts each give one
                    finding; a clean row gives none
        TC-RSC-002  a run file naming MAX_HELD held codes or a secret number is reported; with
                    an empty book nothing is checked
    """

    rule = "research"

    def __init__(
        self,
        repo_root: Path,
        reader: ResearchLogReader,
        files: list[Path],
        held: Collection[str],
        secrets: Collection[str],
    ) -> None:
        self._root = repo_root
        self._reader = reader
        self._files = files
        self._held = frozenset(held)
        self._secrets = frozenset(s for s in secrets if s)

    def run(self) -> list[Finding]:
        """
        Purpose:
            Check every log row, then every committed run file.

        Contract:
            Input:
                (none)
            Output:
                list[Finding]  -- sorted
            Raises:
                OSError  -- unreadable log or run file
        """
        return sorted(self._check_log() + self._check_privacy())

    def _check_log(self) -> list[Finding]:
        runs = self._reader.read(self._root / LOG)
        counts = Counter(r.slug for r in runs)
        out: list[Finding] = []
        for r in runs:
            match = _SLUG.match(r.slug)
            problems = []
            if not match:
                problems.append(f"slug {r.slug!r} is not YYYYMMDD_<topic> (≤ 4 words)")
            elif match.group(1) != r.date.replace("-", ""):
                problems.append(f"slug {r.slug!r} does not match date {r.date}")
            if counts[r.slug] > 1:
                problems.append(f"slug {r.slug!r} is used {counts[r.slug]} times")
            if not r.scripts or not (self._root / r.scripts).exists():
                problems.append(f"scripts {r.scripts!r} do not exist")
            out += [Finding(str(LOG), r.line, self.rule, p) for p in problems]
        return out

    def _check_privacy(self) -> list[Finding]:
        if not self._held:
            return []
        out: list[Finding] = []
        for rel in self._files:
            if rel.parts[: len(RUNS.parts)] != RUNS.parts:
                continue
            try:
                text = (self._root / rel).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            n_held = sum(code in text for code in self._held)
            if n_held >= MAX_HELD:
                msg = f"names {n_held} held codes: read config/local.positions.yaml at runtime"
                out.append(Finding(str(rel), 0, self.rule, msg))
            if any(s in text for s in self._secrets):
                msg = "contains a private cost or cash figure from the positions book"
                out.append(Finding(str(rel), 0, self.rule, msg))
        return out
