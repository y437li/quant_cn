"""DeepSeek reads company guidance: annual plan, IR record, incentive draft (plan 18)."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.lenient_item import LenientItem
from quant_cn.industry_graph.pdf_text_extractor import ReportPages
from quant_cn.industry_graph.quote_checker import QuoteChecker
from quant_cn.industry_graph.section_detector import SectionDetector

PROMPT_DIR = Path(__file__).with_name("prompts")
DOC_TYPES = ("annual_plan", "ir_record", "incentive_plan")
KINDS = ("target", "expectation", "commitment")
BASES = ("level", "growth", "growth_abs", "ratio")
METRIC_CLASSES = ("revenue", "net_profit", "deducted_profit", "margin", "volume", "capacity",
                  "orders", "capex", "dividend", "other")  # fmt: skip
INCENTIVE_PAGE = re.compile(r"业绩考核|考核目标|考核指标|业绩条件")
PERIOD = re.compile(r"(\d{4})(?:年)?(H[12]|Q[1-4])?(?:\s*[-~至到]\s*(\d{4}))?")
YEARS_BEFORE_ANN = 1  # an item about a year before the announcement year minus this is history


class GuidanceItem(LenientItem):
    """
    Purpose:
        One guidance statement the LLM found, before the checks.

    Contract:
        Input:
            metric: str; metric_class: str; segment: str | None; period: str | None; basis: str;
            value_low / value_high: float | None; unit: str | None; base_period: str | None;
            kind: str; condition: str | None; quote: str; page: int
        Output:
            pydantic model (unknown keys ignored, numeric text parsed)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.GuidanceReply  -- items

    Test cases:
        TC-GE-003  (via GuidanceExtractor) malformed reply raises DataSourceError
    """

    metric: str
    metric_class: str = "other"
    segment: str | None = None
    period: str | None = None
    basis: str = "level"
    value_low: float | None = None
    value_high: float | None = None
    unit: str | None = None
    base_period: str | None = None
    kind: str
    condition: str | None = None
    quote: str
    page: int


class GuidanceReply(BaseModel):
    """
    Purpose:
        The LLM reply for one document.

    Contract:
        Input:
            items: list[GuidanceItem]
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.GuidanceExtractor  -- validates every reply

    Test cases:
        TC-GE-003  (via GuidanceExtractor) malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    items: list[GuidanceItem] = []


@dataclass(frozen=True)
class GuidanceResult:
    """
    Purpose:
        The checked guidance items of one document.

    Contract:
        Input:
            items: list[dict] -- GuidanceItem fields with period normalized (YYYY, YYYYH1,
            YYYYQ3 or YYYY-YYYY) and evidence (Evidence) in place of quote / page;
            dropped: int >= 0; tokens: int >= 0; cached: bool
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.GuidanceExtractor  -- returned by fetch_guidance

    Test cases:
        TC-GE-002  (via GuidanceExtractor) kept and dropped items
    """

    items: list[dict[str, Any]] = field(default_factory=list)
    dropped: int = 0
    tokens: int = 0
    cached: bool = False


class GuidanceExtractor:
    """
    Purpose:
        Turn a company document into quote-checked, quantitative guidance rows (plan 18 ph3).
        Three document types, one prompt each (`prompts/guidance_<doc_type>.txt`):
        annual_plan (the annual report's outlook section, from its heading to the end of the
        MD&A chapter, so the 经营计划 that follows 发展战略 is included), ir_record (every page
        of an 投资者关系活动记录表) and incentive_plan (the 业绩考核 pages of a draft and the
        page after each, where target tables continue). An item is kept only when its quote is
        on a sent page, its kind is in KINDS, it carries at least one value, and its period
        names a year no earlier than the announcement year minus YEARS_BEFORE_ANN (past
        results are not guidance). Unknown metric_class / basis become "other" / "level".

    Contract:
        Input:
            llm:       BaseLlmClient
            detector:  SectionDetector
            max_chars: int > 0                      -- text sent per document
            prompts:   Mapping[str, str] | None     -- doc_type -> system prompt; default the
                                                       prompt files
        Output:
            instance; `list_source_pages`, `fetch_guidance`
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/guidance_pilot.py (plan 18 phase 3 pilot)

    Test cases:
        TC-GE-001  list_source_pages: annual outlook to chapter end; IR all pages; incentive
                   业绩考核 pages plus the next; no outlook -> []; unknown doc type raises
        TC-GE-002  valid reply: items kept with evidence and normalized period; absent quote,
                   unknown kind, no value, no period and a past period dropped; "30%" parsed
        TC-GE-003  malformed reply raises DataSourceError
    """

    def __init__(
        self,
        llm: BaseLlmClient,
        detector: SectionDetector,
        max_chars: int = 12000,
        prompts: Mapping[str, str] | None = None,
    ) -> None:
        self._llm = llm
        self._detector = detector
        self._max_chars = max_chars
        self._prompts = dict(prompts) if prompts is not None else {
            t: (PROMPT_DIR / f"guidance_{t}.txt").read_text(encoding="utf-8") for t in DOC_TYPES
        }  # fmt: skip

    def list_source_pages(self, doc_type: str, report: ReportPages) -> list[tuple[int, str]]:
        """
        Purpose:
            The pages of one document to send, 1-based, in order.

        Contract:
            Input:
                doc_type: str -- one of DOC_TYPES; report: ReportPages
            Output:
                list[tuple[int, str]]  -- [] when an annual report has no outlook section
            Raises:
                DataSourceError  -- unknown doc_type
        """
        pages = report.pages
        if doc_type == "ir_record":
            return [(i + 1, t) for i, t in enumerate(pages)]
        if doc_type == "incentive_plan":
            hits = {i for i, t in enumerate(pages) if INCENTIVE_PAGE.search(t)}
            keep = sorted(hits | {i + 1 for i in hits if i + 1 < len(pages)})
            return [(i + 1, pages[i]) for i in keep]
        if doc_type == "annual_plan":
            sections = {s.key: s for s in self._detector.list_sections(report)}
            if "outlook" not in sections:
                return []
            first, last = sections["outlook"].page_start, sections["chapter"].page_end
            return [(p, pages[p - 1]) for p in range(first, last + 1)]
        raise DataSourceError(f"guidance: unknown doc type {doc_type!r}, expected {DOC_TYPES}")

    def fetch_guidance(
        self, company: str, doc_type: str, ann_date: str, pages: Sequence[tuple[int, str]]
    ) -> GuidanceResult:
        """
        Purpose:
            Ask the model for one document's guidance and check every item against the text.

        Contract:
            Input:
                company: str; doc_type: str (DOC_TYPES); ann_date: str YYYYMMDD;
                pages: Sequence[tuple[int, str]] -- from list_source_pages
            Output:
                GuidanceResult
            Raises:
                DataSourceError  -- unknown doc_type, LLM failure, or a reply that does not fit
        """
        if doc_type not in self._prompts:
            raise DataSourceError(f"guidance: no prompt for doc type {doc_type!r}")
        text, used = QuoteChecker.build_prompt_text(pages, self._max_chars)
        user = f"公司：{company}\n公告日期：{ann_date}\n\n原文（按页）：\n{text}"
        reply = self._llm.fetch_json(self._prompts[doc_type], user)
        try:
            parsed = GuidanceReply.model_validate(reply.content)
        except ValidationError as exc:
            raise DataSourceError(f"{company}: reply does not fit the shape: {exc}") from exc
        checker = QuoteChecker(used)
        items, dropped = [], 0
        for item in parsed.items:
            ev = checker.find_evidence(item.quote, item.page)
            period = self._normalize_period(item.period, int(ann_date[:4]) - YEARS_BEFORE_ANN)
            has_value = item.value_low is not None or item.value_high is not None
            if ev is None or item.kind not in KINDS or not has_value or period is None:
                dropped += 1
                continue
            row = item.model_dump(exclude={"quote", "page"})
            row["period"] = period
            row["metric_class"] = (
                item.metric_class if item.metric_class in METRIC_CLASSES else "other"
            )
            row["basis"] = item.basis if item.basis in BASES else "level"
            row["evidence"] = ev
            items.append(row)
        tokens = reply.prompt_tokens + reply.completion_tokens
        return GuidanceResult(items, dropped, tokens, reply.cached)

    @staticmethod
    def _normalize_period(text: str | None, first_year: int) -> str | None:
        """YYYY, YYYYH1 / YYYYQ3 or YYYY-YYYY from free text; None without a year or when the
        last year is before first_year."""
        found = PERIOD.search(text or "")
        if found is None:
            return None
        start, part, end = found.group(1), found.group(2) or "", found.group(3)
        if int(end or start) < first_year:
            return None
        return f"{start}-{end}" if end and end != start else f"{start}{part}"
