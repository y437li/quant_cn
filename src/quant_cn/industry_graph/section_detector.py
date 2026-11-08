"""The chain sections of an A-share annual report, located by heading text (D-102)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from quant_cn.industry_graph.pdf_text_extractor import ReportPages

CHAPTER_START = re.compile(
    r"^\s*第[二三四][节章]\s*(管理层讨论与分析|经营情况讨论与分析|董事会报告)\s*$", re.M
)
CHAPTER_END = re.compile(r"^\s*第[三四五六][节章]\s*(公司治理|重要事项|重大事件)", re.M)
TOC_DOTS = re.compile(r"[.…·]{5,}")
ANY_CHAPTER = re.compile(r"第[一二三四五六七八九十]{1,2}[节章]")
TOC_MIN_CHAPTERS = 3  # a page listing this many chapter headings is the table of contents
# Heading patterns per section key, searched inside the MD&A chapter in this order of keys;
# the first page carrying the pattern is the section's start (CSRC 2021 annual-report standard).
SECTION_PATTERNS: dict[str, str] = {
    "business": r"(从事的主要业务|从事的业务情况|主要业务、经营模式|业务概要)",
    "industry": r"所处(的)?行业情况",
    "competitiveness": r"核心竞争力分析",
    "revenue_mix": r"营业收入构成|主营业务分行业、分产品、分地区",
    "capacity": r"产销量情况分析|产能状况|产能利用",
    "costs_materials": r"营业成本构成|成本分析表|主要原材料",
    "counterparties": (
        r"主要销售客户(和|及)主要供应商情况|主要客户、供应商|\(\d\)\s*主要客户情况"
        r"|前[五5](名|大)(主要)?\s*客\s*户(合计)?的?销售(金)?额"
    ),
    "competition": r"竞争格局|主要竞争对手",
    "risks": r"可能面对的风险|面临的风险|风险因素",
}


@dataclass(frozen=True)
class Section:
    """
    Purpose:
        One located section: its key, the heading-matched start page and the page before the
        next section (or the chapter end), 1-based, inclusive.

    Contract:
        Input:
            key:        str  -- a SECTION_PATTERNS key, or "chapter" for the whole MD&A
            page_start: int >= 1
            page_end:   int >= page_start
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.SectionDetector     -- returned by list_sections
        industry_graph.ParsedReport        -- sections of a parsed report

    Test cases:
        TC-SD-001  (via SectionDetector) sections ordered with consistent page ranges
    """

    key: str
    page_start: int
    page_end: int


class SectionDetector:
    """
    Purpose:
        Locate the MD&A chapter (管理层讨论与分析, 第三节 in the 2021 standard; 第二节/第四节 in
        older or exchange-specific layouts; 第二章 董事会报告 for some A+H issuers; BSE ends it
        with 第五节 重大事件 and names the business section 业务概要) and the chain sections
        inside it by heading text, not by number, so SSE, SZSE and BSE layouts all work. A
        chapter heading must stand on its own line (body text often cites
        "第三节管理层讨论与分析"). A table-of-contents page (dot leaders, or three or more 第X节
        headings) never counts as a chapter start. Only these pages go to later steps (D-102);
        in the prototype the chapter was 12-19% of a report's text.

    Contract:
        Input:
            (none)
        Output:
            instance; `find_chapter`, `list_sections`, `find_heading_page`
        Raises:
            (none)

    Used by:
        industry_graph.AnnualReportParser  -- second step

    Test cases:
        TC-SD-001  chapter found after the TOC page; sections in page order, each ending before
                   the next starts; the last ends at the chapter end
        TC-SD-002  no MD&A chapter: find_chapter None and list_sections []
        TC-SD-003  a section whose heading is absent is omitted; "chapter" always comes first
        TC-SD-004  BSE layout (title on the line after 第四节, 业务概要, (3) 主要客户情况, ends
                   at 第五节 重大事件) and A+H 第二章 董事会报告 ending at 第三章 公司治理
        TC-SD-005  find_heading_page: first non-TOC page with the heading, None when absent
    """

    def find_chapter(self, report: ReportPages) -> tuple[int, int] | None:
        """
        Purpose:
            First and last page (1-based, inclusive) of the MD&A chapter.

        Contract:
            Input:
                report: ReportPages
            Output:
                tuple[int, int] | None  -- None when no chapter heading outside the TOC
            Raises:
                (none)
        """
        pages = report.pages
        start = next(
            (i for i, t in enumerate(pages) if CHAPTER_START.search(t) and not self._is_toc(t)),
            None,
        )
        if start is None:
            return None
        end = next(
            (i for i in range(start + 1, len(pages)) if CHAPTER_END.search(pages[i])),
            len(pages),
        )
        return start + 1, max(start + 1, end)

    @staticmethod
    def _is_toc(text: str) -> bool:
        return bool(TOC_DOTS.search(text)) or len(ANY_CHAPTER.findall(text)) >= TOC_MIN_CHAPTERS

    def list_sections(self, report: ReportPages) -> list[Section]:
        """
        Purpose:
            The MD&A chapter and every chain section found in it.

        Contract:
            Input:
                report: ReportPages
            Output:
                list[Section]  -- "chapter" first, then sections by start page; [] when the
                                  chapter is missing
            Raises:
                (none)
        """
        chapter = self.find_chapter(report)
        if chapter is None:
            return []
        first, last = chapter
        starts: list[tuple[int, str]] = []
        for key, pattern in SECTION_PATTERNS.items():
            regex = re.compile(pattern)
            page = next(
                (p for p in range(first, last + 1) if regex.search(report.pages[p - 1])), None
            )
            if page is not None:
                starts.append((page, key))
        order = list(SECTION_PATTERNS)
        starts.sort(key=lambda item: (item[0], order.index(item[1])))
        sections = [Section("chapter", first, last)]
        for i, (page, key) in enumerate(starts):
            following = [p for p, _ in starts[i + 1 :] if p > page]
            end = following[0] - 1 if following else last
            sections.append(Section(key, page, max(page, end)))
        return sections

    def find_heading_page(self, report: ReportPages, key: str) -> int | None:
        """
        Purpose:
            First non-TOC page (1-based) anywhere in the report that carries a section's
            heading, for reports whose MD&A chapter is missing or named differently (A+H
            issuers that put the top-5 disclosure under 董事会报告 items).

        Contract:
            Input:
                report: ReportPages; key: str -- a SECTION_PATTERNS key
            Output:
                int | None
            Raises:
                KeyError  -- unknown key
        """
        regex = re.compile(SECTION_PATTERNS[key])
        return next(
            (i + 1 for i, t in enumerate(report.pages) if regex.search(t) and not self._is_toc(t)),
            None,
        )
