"""Shared base of the plan 28 document extractors: prompt, reply items, quote check (D-161)."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

from pydantic import ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.lenient_item import LenientItem
from quant_cn.industry_graph.quote_checker import QuoteChecker

PROMPT_DIR = Path(__file__).with_name("prompts")


class QuotedItem(LenientItem):
    """
    Purpose:
        Base of one reply item of a plan 28 extractor: the subclass fields plus the verbatim
        quote and the page it is on.

    Contract:
        Input:
            quote: str; page: int; the subclass's fields
        Output:
            pydantic model (unknown keys ignored, numeric text parsed)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.BaseQuotedExtractor  -- item_model of every subclass derives from it
        industry_graph.InquiryCounterpartyItem  -- base
        industry_graph.InquiryCustomerExtractor  -- item_model
        industry_graph.IrCounterpartyItem  -- base
        industry_graph.IrCustomerExtractor  -- item_model
        industry_graph.DealItem  -- base
        industry_graph.DealExtractor  -- item_model
        industry_graph.OperatingDataItem  -- base
        industry_graph.OperatingDataExtractor  -- item_model
        industry_graph.BuybackTermsItem  -- base
        industry_graph.BuybackTermsExtractor  -- item_model

    Test cases:
        TC-BQE-002  (via BaseQuotedExtractor) an item of the wrong shape is dropped
    """

    quote: str
    page: int


@dataclass(frozen=True)
class QuotedResult:
    """
    Purpose:
        The checked items of one document.

    Contract:
        Input:
            items: list[dict] -- item fields as the subclass's check returns them, with
            evidence {"quote", "page"} in place of quote / page;
            dropped: int >= 0 (no quote on a sent page, wrong shape, or refused by the check);
            tokens: int >= 0; cached: bool; pages: list[int] (pages sent)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.BaseQuotedExtractor  -- returned by fetch_items

    Test cases:
        TC-BQE-001  (via BaseQuotedExtractor) kept items carry evidence
    """

    items: list[dict[str, Any]] = field(default_factory=list)
    dropped: int = 0
    tokens: int = 0
    cached: bool = False
    pages: list[int] = field(default_factory=list)


class BaseQuotedExtractor(ABC):
    """
    Purpose:
        Base of the plan 28 phase 2 extractors (one per document type, D-161 update 6).
        `fetch_items` sends the chosen pages ("[第N页]" tagged, cut to max_chars) with a header
        to the LLM using the subclass's prompt file, reads the reply's `items` list, validates
        each item with the subclass's item model, keeps it only when its quote occurs on a
        sent page (QuoteChecker; only the part `build_checked_text` keeps), the subclass's
        `is_item_anchored` holds for it (default True) and its `check_item` accepts it. Items
        of the wrong shape are dropped one by one, not the whole reply. `list_top_pages` gives
        the pages that hit a keyword pattern most, in page order, for long documents.

    Contract:
        Input:
            llm:       BaseLlmClient
            max_chars: int > 0     -- text sent per document
            system:    str | None  -- prompt; default prompts/<PROMPT_FILE>
        Output:
            instance; `fetch_items`, `list_top_pages` (static), hooks `build_checked_text`
            and `is_item_anchored`; subclasses define PROMPT_FILE, item_model, list_pages and
            check_item
        Raises:
            (none at construction)

    Used by:
        industry_graph.InquiryCustomerExtractor  -- base
        industry_graph.IrCustomerExtractor  -- base
        industry_graph.DealExtractor  -- base
        industry_graph.OperatingDataExtractor  -- base
        industry_graph.BuybackTermsExtractor  -- base

    Test cases:
        TC-BQE-001  valid reply: kept items carry evidence; items whose quote is not on a sent
                    page or that check_item refuses are dropped; pages sent are reported
        TC-BQE-002  an item of the wrong shape is dropped, the others kept; a reply without an
                    items list raises DataSourceError
        TC-BQE-004  a quote outside the part build_checked_text keeps is dropped
        TC-BQE-005  an item is_item_anchored refuses is dropped
        TC-BQE-003  list_top_pages keeps the pages with the most hits, in page order, at most
                    max_pages; pages without a hit are left out
    """

    PROMPT_FILE: ClassVar[str]

    def __init__(self, llm: BaseLlmClient, max_chars: int = 12000, system: str | None = None):
        self._llm = llm
        self._max_chars = max_chars
        prompt = PROMPT_DIR / self.PROMPT_FILE
        self._system = system if system is not None else prompt.read_text(encoding="utf-8")

    @property
    @abstractmethod
    def item_model(self) -> type[QuotedItem]:
        """
        Purpose:
            The pydantic model of one reply item.

        Contract:
            Input:
                (none)
            Output:
                type[QuotedItem]
            Raises:
                (none)
        """

    @abstractmethod
    def list_pages(self, pages: Sequence[str]) -> list[tuple[int, str]]:
        """
        Purpose:
            The pages of a document to send, as (page number from 1, text).

        Contract:
            Input:
                pages: Sequence[str]  -- the document's page texts in order
            Output:
                list[tuple[int, str]]  -- empty when the document has nothing to read
            Raises:
                (none)
        """

    @abstractmethod
    def check_item(self, item: QuotedItem) -> dict[str, Any] | None:
        """
        Purpose:
            The stored fields of one quote-checked item, or None to drop it.

        Contract:
            Input:
                item: QuotedItem  -- an instance of item_model
            Output:
                dict[str, Any] without quote / page, or None
            Raises:
                (none)
        """

    def fetch_items(
        self, header: Mapping[str, str], pages: Sequence[tuple[int, str]]
    ) -> QuotedResult:
        """
        Purpose:
            Ask the model about one document and check every item against the text.

        Contract:
            Input:
                header: Mapping[str, str]  -- lines put before the text ("公司": name, …)
                pages:  Sequence[tuple[int, str]]  -- list_pages output
            Output:
                QuotedResult
            Raises:
                DataSourceError  -- LLM failure or a reply without an items list
        """
        text, used = QuoteChecker.build_prompt_text(pages, self._max_chars)
        lines = "\n".join(f"{k}：{v}" for k, v in header.items())
        reply = self._llm.fetch_json(self._system, f"{lines}\n\n原文（按页）：\n{text}")
        raw = reply.content.get("items")
        if not isinstance(raw, list):
            raise DataSourceError(f"{dict(header)}: reply has no items list")
        checker = QuoteChecker([(p, self.build_checked_text(t)) for p, t in used])
        texts = dict(used)
        items: list[dict[str, Any]] = []
        for entry in raw:
            row = self._check_entry(entry, checker, texts)
            if row is not None:
                items.append(row)
        tokens = reply.prompt_tokens + reply.completion_tokens
        return QuotedResult(
            items, len(raw) - len(items), tokens, reply.cached, [p for p, _ in used]
        )

    def build_checked_text(self, text: str) -> str:
        """
        Purpose:
            The part of a sent page a quote may come from; the whole page unless a subclass
            narrows it (an IR answer, not the investor's question).

        Contract:
            Input:
                text: str  -- one sent page
            Output:
                str
            Raises:
                (none)
        """
        return text

    @staticmethod
    def list_top_pages(
        pages: Sequence[str], pattern: re.Pattern[str], max_pages: int
    ) -> list[tuple[int, str]]:
        """
        Purpose:
            The pages with the most pattern hits, at most max_pages, in page order.

        Contract:
            Input:
                pages: Sequence[str]; pattern: compiled regex; max_pages: int > 0
            Output:
                list[tuple[int, str]]  -- (page number from 1, text); ties keep earlier pages
            Raises:
                (none)
        """
        hits = [(len(pattern.findall(t)), n, t) for n, t in enumerate(pages, 1)]
        top = sorted((h for h in hits if h[0] > 0), key=lambda h: (-h[0], h[1]))[:max_pages]
        return [(n, t) for _, n, t in sorted(top, key=lambda h: h[1])]

    def is_item_anchored(self, item: QuotedItem, page_text: str) -> bool:
        """
        Purpose:
            Whether a quote-checked item is tied to its quote (e.g. the counterparty's name is
            in it); always True unless a subclass narrows it.

        Contract:
            Input:
                item: QuotedItem; page_text: str  -- the whole page the quote was found on
            Output:
                bool
            Raises:
                (none)
        """
        return True

    def _check_entry(
        self, entry: Any, checker: QuoteChecker, texts: Mapping[int, str]
    ) -> dict[str, Any] | None:
        try:
            item = self.item_model.model_validate(entry)
        except ValidationError:
            return None
        evidence = checker.find_evidence(item.quote, item.page)
        if evidence is None or not self.is_item_anchored(item, texts.get(evidence.page, "")):
            return None
        row = self.check_item(item)
        if row is None:
            return None
        row["evidence"] = vars(evidence)
        return row
