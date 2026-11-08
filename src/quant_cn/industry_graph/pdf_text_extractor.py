"""Page text of a report PDF without running headers, footers and page numbers (plan 12 phase 3)."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from quant_cn.core.exceptions import DataSourceError

_PAGE_NUMBER = re.compile(r"^\s*第?\s*(\d{1,4})\s*(?:页|/\s*\d{1,4})?\s*$")
_DIGITS = re.compile(r"\d+")
_TEXTUAL = re.compile(r"[^\W\d_#]")  # letters and CJK characters
MIN_HEADER_LETTERS = 4  # numbers, amounts and ranks are never running headers
MIN_PAGES_FOR_HEADERS = 4  # fewer pages: a repeated line is not evidence of a running header


@dataclass(frozen=True)
class ReportPages:
    """
    Purpose:
        The text of one report PDF, page by page, plus its outline (bookmarks) when present.

    Contract:
        Input:
            pages:   list[str]                   -- cleaned text, index 0 = page 1
            outline: list[tuple[int, str, int]]  -- (level, title, 1-based page); [] if none
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.PdfTextExtractor  -- returned by read_pages
        industry_graph.SectionDetector   -- input of list_sections
        industry_graph.AnnualReportParser -- passed between the steps

    Test cases:
        TC-PTE-001  (via PdfTextExtractor) page count and outline preserved
    """

    pages: list[str]
    outline: list[tuple[int, str, int]] = field(default_factory=list)

    @property
    def n_chars(self) -> int:
        """
        Purpose:
            Characters over all pages (for section-share statistics).

        Contract:
            Input:
                (none)
            Output:
                int >= 0
            Raises:
                (none)
        """
        return sum(len(p) for p in self.pages)


class PdfTextExtractor:
    """
    Purpose:
        Read the native text layer of a PDF page by page (no OCR; D-102) and remove the
        running header and footer: a line with at least four letters or CJK characters that,
        with digits ignored, appears on at least `header_share` of the pages
        (e.g. "牧原食品股份有限公司2025 年年度报告全文"), and
        bare page numbers ("31", "36 / 251"). Tables that cross a page break then read as
        one block, which the top-5 table parser needs (a header inside the table split rows
        in the hog-sector prototype).

    Contract:
        Input:
            header_share: float in (0, 1]  -- share of pages a line must appear on to be a header
        Output:
            instance; `read_pages`, `normalize_pages`
        Raises:
            ValueError  -- header_share outside (0, 1]

    Used by:
        industry_graph.AnnualReportParser  -- first step

    Test cases:
        TC-PTE-001  a generated 4-page PDF: header, footer and page numbers removed; body kept;
                    page count and outline preserved
        TC-PTE-002  normalize_pages keeps a line repeating on few pages; short documents untouched
        TC-PTE-003  a missing or unreadable file raises DataSourceError
    """

    def __init__(self, header_share: float = 0.5) -> None:
        if not 0 < header_share <= 1:
            raise ValueError("header_share must be in (0, 1]")
        self._header_share = header_share

    def read_pages(self, path: Path) -> ReportPages:
        """
        Purpose:
            Text and outline of one PDF, headers and footers removed.

        Contract:
            Input:
                path: Path  -- a PDF file
            Output:
                ReportPages
            Raises:
                DataSourceError  -- file missing or not a readable PDF
        """
        try:
            with pymupdf.open(path) as doc:  # type: ignore[no-untyped-call]
                if not doc.is_pdf:
                    raise ValueError("not a PDF")
                raw = [page.get_text() for page in doc]
                outline = [
                    (int(lvl), str(title), int(page)) for lvl, title, page, *_ in doc.get_toc()
                ]
        except (OSError, RuntimeError, ValueError) as exc:
            raise DataSourceError(f"cannot read PDF {path}: {exc}") from exc
        return ReportPages(self.normalize_pages(raw), outline)

    def normalize_pages(self, pages: list[str]) -> list[str]:
        """
        Purpose:
            Remove running headers/footers and page-number lines from raw page texts.

        Contract:
            Input:
                pages: list[str]  -- raw text per page
            Output:
                list[str]  -- same length; lines stripped of surrounding blanks, empty lines dropped
            Raises:
                (none)
        """
        split = [[line.strip() for line in page.splitlines() if line.strip()] for page in pages]
        headers: set[str] = set()
        if len(split) >= MIN_PAGES_FOR_HEADERS:
            counts = Counter(key for lines in split for key in {self._to_key(x) for x in lines})
            limit = self._header_share * len(split)
            headers = {
                key
                for key, n in counts.items()
                if n >= limit and len(_TEXTUAL.findall(key)) >= MIN_HEADER_LETTERS
            }
        split = [[x for x in lines if self._to_key(x) not in headers] for lines in split]
        offset = self._find_page_offset(split)
        return [
            "\n".join(
                x
                for i, x in enumerate(lines)
                if not (i in (0, len(lines) - 1) and self._is_page_number(x, page_no + 1, offset))
            )
            for page_no, lines in enumerate(split)
        ]

    @staticmethod
    def _is_page_number(line: str, page_no: int, offset: int | None) -> bool:
        match = _PAGE_NUMBER.match(line)
        if match is None or offset is None:
            return False
        return int(match[1]) - page_no == offset

    @staticmethod
    def _find_page_offset(split: list[list[str]]) -> int | None:
        """Most common (printed number - page index) over first/last lines, if on half the pages."""
        offsets: Counter[int] = Counter()
        for page_no, lines in enumerate(split, start=1):
            seen = {
                int(m[1]) - page_no for x in lines[:1] + lines[-1:] if (m := _PAGE_NUMBER.match(x))
            }
            offsets.update(seen)
        if not offsets:
            return None
        offset, n = offsets.most_common(1)[0]
        return offset if n * 2 >= len(split) else None

    @staticmethod
    def _to_key(line: str) -> str:
        return _DIGITS.sub("#", line.replace(" ", ""))
