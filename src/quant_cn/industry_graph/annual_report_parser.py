"""One annual report PDF → chain sections and top-5 counterparty tables (plan 12 phase 3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quant_cn.industry_graph.counterparty_table_parser import (
    CounterpartyTable,
    CounterpartyTableParser,
)
from quant_cn.industry_graph.pdf_text_extractor import PdfTextExtractor, ReportPages
from quant_cn.industry_graph.section_detector import Section, SectionDetector

COUNTERPARTY_PAGES = 3  # the block plus the pages a long table can spill onto


@dataclass(frozen=True)
class ParsedReport:
    """
    Purpose:
        What the rule-based pass extracts from one annual report.

    Contract:
        Input:
            path:          Path
            n_pages:       int
            sections:      list[Section]  -- [] when the MD&A chapter was not found
            chapter_share: float          -- MD&A characters / all characters (0 if missing)
            customers:     CounterpartyTable
            suppliers:     CounterpartyTable
        Output:
            frozen dataclass; `get_section`
        Raises:
            (none)

    Used by:
        industry_graph.AnnualReportParser  -- returned by parse_report

    Test cases:
        TC-ARP-001  (via AnnualReportParser) sections and both tables filled
    """

    path: Path
    n_pages: int
    sections: list[Section]
    chapter_share: float
    customers: CounterpartyTable
    suppliers: CounterpartyTable

    def get_section(self, key: str) -> Section | None:
        """
        Purpose:
            The section with this key, if located.

        Contract:
            Input:
                key: str  -- "chapter" or a SECTION_PATTERNS key
            Output:
                Section | None
            Raises:
                (none)
        """
        return next((s for s in self.sections if s.key == key), None)


class AnnualReportParser:
    """
    Purpose:
        Run the rule-based pass of plan 12 phase 3 on one annual report: read the pages
        (PdfTextExtractor), locate the MD&A chapter and chain sections (SectionDetector), and
        parse the top-5 customer and supplier tables (CounterpartyTableParser). Nothing here
        calls an LLM; the located section pages are what phase 4 sends to DeepSeek.

    Contract:
        Input:
            extractor: PdfTextExtractor
            detector:  SectionDetector
            parser:    CounterpartyTableParser
        Output:
            instance; `parse_report`, `parse_pages`
        Raises:
            (none at construction)

    Used by:
        research_space prototype notebooks; plan 12 phase 3 step (to come)

    Test cases:
        TC-ARP-001  parse_pages on a synthetic SZSE-layout report: chapter, counterparty
                    section, consistent customer and supplier tables, chapter share in (0, 1)
        TC-ARP-002  no MD&A chapter: no sections, empty tables, share 0
        TC-ARP-003  no MD&A chapter but a top-5 block elsewhere: tables still parsed
    """

    def __init__(
        self,
        extractor: PdfTextExtractor,
        detector: SectionDetector,
        parser: CounterpartyTableParser,
    ) -> None:
        self._extractor = extractor
        self._detector = detector
        self._parser = parser

    def parse_report(self, path: Path) -> ParsedReport:
        """
        Purpose:
            Read and parse one PDF.

        Contract:
            Input:
                path: Path  -- annual report PDF
            Output:
                ParsedReport
            Raises:
                DataSourceError  -- unreadable PDF (from PdfTextExtractor)
        """
        return self.parse_pages(path, self._extractor.read_pages(path))

    def parse_pages(self, path: Path, report: ReportPages) -> ParsedReport:
        """
        Purpose:
            Parse already-read pages (lets callers reuse or synthesise ReportPages).

        Contract:
            Input:
                path: Path; report: ReportPages
            Output:
                ParsedReport
            Raises:
                (none)
        """
        sections = self._detector.list_sections(report)
        chapter = next((s for s in sections if s.key == "chapter"), None)
        share = 0.0
        if chapter and report.n_chars:
            pages = report.pages[chapter.page_start - 1 : chapter.page_end]
            share = sum(len(p) for p in pages) / report.n_chars
        block = next((s for s in sections if s.key == "counterparties"), None)
        first = (
            block.page_start
            if block
            else self._detector.find_heading_page(report, "counterparties")
        )
        text = ""
        if first:
            text = "\n".join(report.pages[first - 1 : first - 1 + COUNTERPARTY_PAGES])
            heading = text.find("主要销售客户")
            text = text[heading:] if heading >= 0 else text
        customers, suppliers = self._parser.parse_tables(text)
        return ParsedReport(path, len(report.pages), sections, share, customers, suppliers)
