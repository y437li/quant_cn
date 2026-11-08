"""DeepSeek reads broker valuation pages: method, multiples, target price, assumptions (D-105)."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.quote_checker import QuoteChecker

PROMPT = Path(__file__).with_name("prompts") / "valuation_extraction.txt"
KEYWORDS = re.compile(
    r"估值|可比公司|目标价|盈利预测|投资建议|PE|PB|EV/EBITDA|DCF|WACC|分部|关键假设|假设|出货|单价|毛利率"
)
LEAD_PAGES = 2  # summary page and the forecast table that usually follows
KINDS = ("implied_at_price", "target")


class ValuationItem(BaseModel):
    """
    Purpose:
        Base of the reply shapes: unknown keys ignored, so a richer reply still validates.

    Contract:
        Input:
            fields of the subclass
        Output:
            pydantic model
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.ValuationReply  -- subclass

    Test cases:
        TC-VE-003  (via ValuationExtractor) a malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")


class ValuationReply(ValuationItem):
    """
    Purpose:
        The LLM reply for one broker report, before the quote check: rating, target price,
        methods (multiple, implied or target, base year), forecasts, comparables, assumptions.

    Contract:
        Input:
            rating: str | None; target_price: dict | None; methods, forecasts, comparables,
            assumptions: list[dict]; logic: str
        Output:
            pydantic model
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.ValuationExtractor  -- validates every reply

    Test cases:
        TC-VE-003  (via ValuationExtractor) a malformed reply raises DataSourceError
    """

    rating: str | None = None
    target_price: dict[str, Any] | None = None
    methods: list[dict[str, Any]] = []
    forecasts: list[dict[str, Any]] = []
    comparables: list[dict[str, Any]] = []
    assumptions: list[dict[str, Any]] = []
    logic: str = ""


@dataclass(frozen=True)
class ValuationResult:
    """
    Purpose:
        One report's valuation after validation: only quote-checked target price, methods and
        assumptions; methods carry `multiple_kind` (D-109) and a base year; comparables carry
        a ts_code when it could be resolved.

    Contract:
        Input:
            rating, target_price, methods, forecasts, comparables, assumptions, logic,
            dropped (int >= 0), tokens (int >= 0), cached (bool)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.ValuationExtractor  -- returned by fetch_valuation

    Test cases:
        TC-VE-001  (via ValuationExtractor) fields filled from a valid reply
    """

    rating: str | None = None
    target_price: dict[str, Any] | None = None
    methods: list[dict[str, Any]] = field(default_factory=list)
    forecasts: list[dict[str, Any]] = field(default_factory=list)
    comparables: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[dict[str, Any]] = field(default_factory=list)
    logic: str = ""
    dropped: int = 0
    tokens: int = 0
    cached: bool = False


class ValuationExtractor:
    """
    Purpose:
        Extract how a broker values a company (plan 13, D-105, D-109). Pages sent: the first
        LEAD_PAGES plus every page matching KEYWORDS, within a character budget. Kept: a target
        price and methods whose quotes are on a sent page; methods with a multiple must have a
        base year and a multiple_kind of "implied_at_price" or "target" (otherwise dropped);
        assumptions with a checked quote. Comparables are resolved to ts_codes through an
        injected name → code map when the report gives no code.

    Contract:
        Input:
            llm:       BaseLlmClient
            max_chars: int > 0      -- page text sent
            system:    str | None   -- prompt; default prompts/valuation_extraction.txt
        Output:
            instance; `list_pages`, `fetch_valuation`
        Raises:
            (none at construction)

    Used by:
        research_space prototypes (plan 13 pilot); plan 13 full run (to come)

    Test cases:
        TC-VE-001  valid reply: target price, methods with kind and base year, comparables
                   resolved to codes, assumptions kept with pages
        TC-VE-002  dropped: quote not in text, multiple without base year, unknown kind
        TC-VE-003  malformed reply raises DataSourceError; list_pages keeps lead + keyword pages
    """

    def __init__(
        self, llm: BaseLlmClient, max_chars: int = 26000, system: str | None = None
    ) -> None:
        self._llm = llm
        self._max_chars = max_chars
        self._system = system if system is not None else PROMPT.read_text(encoding="utf-8")

    def list_pages(self, pages: Sequence[str]) -> list[tuple[int, str]]:
        """
        Purpose:
            The pages of a report worth sending, as (page number, text).

        Contract:
            Input:
                pages: Sequence[str]  -- text per page, index 0 = page 1
            Output:
                list[tuple[int, str]]  -- lead pages and keyword pages, in page order
            Raises:
                (none)
        """
        return [(i + 1, t) for i, t in enumerate(pages) if i < LEAD_PAGES or KEYWORDS.search(t)]

    def fetch_valuation(
        self,
        title: str,
        pages: Sequence[tuple[int, str]],
        name_to_code: Mapping[str, str] | None = None,
    ) -> ValuationResult:
        """
        Purpose:
            Ask the model about one report and keep only what the text supports.

        Contract:
            Input:
                title:        str  -- broker, date and title, given to the model as context
                pages:        Sequence[tuple[int, str]]  -- from list_pages
                name_to_code: Mapping[str, str] | None   -- company short name → ts_code
            Output:
                ValuationResult
            Raises:
                DataSourceError  -- LLM failure or a reply that does not fit the shape
        """
        text, used = QuoteChecker.build_prompt_text(pages, self._max_chars)
        reply = self._llm.fetch_json(self._system, f"研报：{title}\n\n{text}")
        try:
            parsed = ValuationReply.model_validate(reply.content)
        except ValidationError as exc:
            raise DataSourceError(f"{title}: reply does not fit the shape: {exc}") from exc
        checker = QuoteChecker(used)
        target, dropped = self._check_target(parsed.target_price, checker)
        methods, d_methods = self._list_kept_methods(parsed.methods, checker)
        assumptions, d_assumptions = self._list_kept_quoted(parsed.assumptions, checker)
        comparables = self._list_resolved(parsed.comparables, name_to_code or {})
        return ValuationResult(
            parsed.rating, target, methods, parsed.forecasts, comparables, assumptions,
            parsed.logic, dropped + d_methods + d_assumptions,
            reply.prompt_tokens + reply.completion_tokens, reply.cached,
        )  # fmt: skip

    @staticmethod
    def _check_target(
        target: dict[str, Any] | None, checker: QuoteChecker
    ) -> tuple[dict[str, Any] | None, int]:
        if not target or target.get("value") is None:
            return None, 0
        ev = checker.find_evidence(str(target.get("quote") or ""), int(target.get("page") or 0))
        if ev is None:
            return None, 1
        return {**target, "quote": ev.quote, "page": ev.page}, 0

    def _list_kept_methods(
        self, methods: list[dict[str, Any]], checker: QuoteChecker
    ) -> tuple[list[dict[str, Any]], int]:
        kept, dropped = [], 0
        for m in methods:
            has_multiple = m.get("multiple") is not None
            if has_multiple and (not m.get("base_year") or m.get("multiple_kind") not in KINDS):
                dropped += 1
                continue
            ev = checker.find_evidence(str(m.get("quote") or ""), int(m.get("page") or 0))
            if ev is None:
                dropped += 1
                continue
            kept.append({**m, "quote": ev.quote, "page": ev.page})
        return kept, dropped

    @staticmethod
    def _list_kept_quoted(
        items: list[dict[str, Any]], checker: QuoteChecker
    ) -> tuple[list[dict[str, Any]], int]:
        kept, dropped = [], 0
        for it in items:
            ev = checker.find_evidence(str(it.get("quote") or ""), int(it.get("page") or 0))
            if ev is None:
                dropped += 1
                continue
            kept.append({**it, "quote": ev.quote, "page": ev.page})
        return kept, dropped

    @staticmethod
    def _list_resolved(
        comparables: list[dict[str, Any]], name_to_code: Mapping[str, str]
    ) -> list[dict[str, Any]]:
        out = []
        for c in comparables:
            code = c.get("code") or name_to_code.get(str(c.get("name") or "").strip())
            out.append({**c, "ts_code": code})
        return out
