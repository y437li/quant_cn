"""Split a plan phase's free-text status into state, date, commits and note (plan 02 ph5, D-144)."""

from __future__ import annotations

import re
from dataclasses import dataclass

STATES = ("todo", "doing", "blocked", "done")
_STATE = re.compile("^(todo|doing|blocked|done)(?=$|[\\s:(\u2014\u2013-])", re.IGNORECASE)
_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_COMMIT = re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b")
_LEAD = " \t:;,\u2014\u2013-"


@dataclass(frozen=True)
class PhaseStatus:
    """
    Purpose:
        A phase status split into fields: the state word, the first date, the commit hashes and
        the remaining text.

    Contract:
        Input:
            state:      str  -- one of STATES, or "" when the text does not start with one
            state_date: str  -- first YYYY-MM-DD in the text, or ""
            commit:     str  -- commit hashes in order of appearance, joined by ", ", or ""
            note:       str  -- the text after the state word, stripped of leading separators
        Output:
            frozen dataclass; `is_valid`
        Raises:
            (none)

    Used by:
        core.docs.PhaseStatusParser.parse  -- return type

    Test cases:
        TC-PSP-001  plain and annotated statuses split into state, date, commits and note
        TC-PSP-002  a status not starting with a state word is invalid with empty state
    """

    state: str
    state_date: str
    commit: str
    note: str

    @property
    def is_valid(self) -> bool:
        """
        Purpose:
            Whether the status starts with one of the four allowed states.

        Contract:
            Input:
                (none)
            Output:
                bool
            Raises:
                (none)
        """
        return self.state in STATES


class PhaseStatusParser:
    """
    Purpose:
        Parse the Status cell of a plan's Phases table. The format is
        `<state> <YYYY-MM-DD> (<commit>) — <note>`; every part after the state is optional and
        older free-text spellings ("done (cd174ec, 4d4dfae); …", "todo (approved 2026-11-13)")
        parse too. Markdown bold and backticks are ignored.

    Contract:
        Input:
            (none)
        Output:
            instance; `parse(text) -> PhaseStatus`
        Raises:
            (none at construction)

    Used by:
        core.docs.PlanReader       -- injected; one parse per phase row
        core.docs.ContractLinter   -- builds the plans checker
        cli.ServiceBuilder         -- injected type or call

    Test cases:
        TC-PSP-001  plain and annotated statuses split into state, date, commits and note
        TC-PSP-002  a status not starting with a state word is invalid with empty state
        TC-PSP-003  a pure-digit or pure-letter token is never taken as a commit
    """

    def parse(self, text: str) -> PhaseStatus:
        """
        Purpose:
            Split one status cell.

        Contract:
            Input:
                text: str  -- the raw cell
            Output:
                PhaseStatus  -- state "" when the text does not start with a state word
            Raises:
                (none)
        """
        clean = text.replace("**", "").replace("`", "").strip()
        match = _STATE.match(clean)
        state = match.group(1).lower() if match else ""
        rest = clean[match.end() :] if match else clean
        date = _DATE.search(clean)
        commits = _COMMIT.findall(clean)
        return PhaseStatus(
            state=state,
            state_date=date.group(1) if date else "",
            commit=", ".join(commits),
            note=rest.lstrip(_LEAD).strip(),
        )
