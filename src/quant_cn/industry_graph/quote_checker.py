"""The pages an LLM is given, and the check that its quotes really come from them (D-097, D-102)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

_SPACE = re.compile(r"\s+")
MIN_QUOTE_CHARS = 4  # shorter quotes match by chance


@dataclass(frozen=True)
class Evidence:
    """
    Purpose:
        A verbatim quote and the page it was found on (after the quote check).

    Contract:
        Input:
            quote: str; page: int >= 1
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.QuoteChecker          -- returned by find_evidence

    Test cases:
        TC-QC-001  (via QuoteChecker) evidence carries the page the quote was found on
    """

    quote: str
    page: int


class QuoteChecker:
    """
    Purpose:
        Hold the pages sent to an LLM and accept a returned quote only if it occurs verbatim
        (whitespace ignored) on one of them. The claimed page is preferred; a quote found on
        another sent page is kept with that page. Also assembles the page-tagged text
        ("[第N页]") sent to the model, truncated in page order to a character budget, so the
        checked pages are exactly the sent pages.

    Contract:
        Input:
            pages: Sequence[tuple[int, str]]  -- (page number, text) actually sent
        Output:
            instance; `find_evidence`, `build_prompt_text` (classmethod)
        Raises:
            (none)

    Used by:
        industry_graph.ApplicationExtractor  -- checks applications and counterparties
        industry_graph.ValuationExtractor    -- checks methods, target price, assumptions
        industry_graph.QuarterlyNoteExtractor  -- checks quarterly-note items
        industry_graph.BusinessModeExtractor  -- checks mode claims and price actions
        industry_graph.MoatExtractor  -- checks moat claims

    Test cases:
        TC-QC-001  quote on the claimed page kept; on another page kept with that page; absent
                   or shorter than MIN_QUOTE_CHARS rejected; whitespace differences ignored
        TC-QC-002  build_prompt_text tags pages, stops at the budget, always keeps the first page
    """

    def __init__(self, pages: Sequence[tuple[int, str]]) -> None:
        self._norm = {page: self._normalize(text) for page, text in pages}

    @classmethod
    def build_prompt_text(
        cls, pages: Sequence[tuple[int, str]], max_chars: int
    ) -> tuple[str, list[tuple[int, str]]]:
        """
        Purpose:
            Page-tagged text for the prompt and the pages it contains.

        Contract:
            Input:
                pages:     Sequence[tuple[int, str]]  -- candidates in the order to send
                max_chars: int > 0  -- body-text budget; the first page always fits
            Output:
                tuple[str, list[tuple[int, str]]]  -- text, pages included
            Raises:
                (none)
        """
        out: list[str] = []
        used: list[tuple[int, str]] = []
        size = 0
        for page, body in pages:
            if size + len(body) > max_chars and used:
                break
            out.append(f"[第{page}页]\n{body}")
            used.append((page, body))
            size += len(body)
        return "\n".join(out), used

    def find_evidence(self, quote: str, page: int) -> Evidence | None:
        """
        Purpose:
            Accept a quote if it occurs on a sent page.

        Contract:
            Input:
                quote: str; page: int  -- as claimed by the model
            Output:
                Evidence | None  -- None when the quote is not on any sent page
            Raises:
                (none)
        """
        q = self._normalize(quote)
        if len(q) < MIN_QUOTE_CHARS:
            return None
        if q in self._norm.get(page, ""):
            return Evidence(quote, page)
        other = next((p for p, t in self._norm.items() if q in t), None)
        return Evidence(quote, other) if other is not None else None

    @staticmethod
    def _normalize(text: str) -> str:
        return _SPACE.sub("", text)
