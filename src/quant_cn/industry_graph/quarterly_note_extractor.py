"""DeepSeek reads the narrative notes of a Q1 / Q3 report: orders, customers, capacity, drivers."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.quote_checker import QuoteChecker

PROMPT = Path(__file__).with_name("prompts") / "quarterly_note_extraction.txt"
# where the narrative of a quarterly report starts and where the statements begin
NOTE_START = re.compile(
    r"变动的情况及原因|变动原因|其他提醒事项|其他重要事项|经营情况的其他重要信息"
)
NOTE_END = re.compile(
    r"(?:[四五]、\s*)?季度财务报表|财务报表\s*[（(]一[）)]|^\s*四、\s*财务报表", re.M
)
EMPTY_NOTE = re.compile(
    r"□适用\s*√不适用|√适用\s*□不适用|需提醒投资者关注的关于公司报告期经营情况的其他重要信息"
)
OTHER_NOTE = re.compile(r"其他提醒事项|其他重要事项")  # SSE / SZSE wording
# change-reason rows worth reading: income statement and operating quantities, not balance sheet
OPERATING_LINE = re.compile(r"营业收入|营业总收入|营业成本|毛利|销量|销售价格|单价|订单|产能|出货")
CONTEXT_LINES = 5  # SZSE tables wrap amounts and the reason over several lines
KINDS = ("order", "customer", "capacity", "driver", "product", "other")


class QuarterlyNoteItem(BaseModel):
    """
    Purpose:
        One fact the LLM found in the notes, before the quote check.

    Contract:
        Input:
            kind: str -- one of KINDS; summary: str; value: str | None; unit: str | None;
            counterparty: str | None; quote: str; page: int
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.QuarterlyNoteReply  -- items

    Test cases:
        TC-QNE-003  (via QuarterlyNoteExtractor) malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    kind: str
    summary: str = ""
    value: str | None = None
    unit: str | None = None
    counterparty: str | None = None
    quote: str
    page: int


class QuarterlyNoteReply(BaseModel):
    """
    Purpose:
        The LLM reply for one quarterly report.

    Contract:
        Input:
            items: list[QuarterlyNoteItem]
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.QuarterlyNoteExtractor  -- validates every reply

    Test cases:
        TC-QNE-003  (via QuarterlyNoteExtractor) malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    items: list[QuarterlyNoteItem] = []


@dataclass(frozen=True)
class QuarterlyNoteResult:
    """
    Purpose:
        The quote-checked facts of one quarterly report.

    Contract:
        Input:
            items: list[dict] -- kind, summary, value, unit, counterparty, evidence (Evidence);
            dropped: int >= 0; tokens: int >= 0; cached: bool
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.QuarterlyNoteExtractor  -- returned by fetch_notes

    Test cases:
        TC-QNE-002  (via QuarterlyNoteExtractor) kept and dropped counts
    """

    items: list[dict[str, Any]] = field(default_factory=list)
    dropped: int = 0
    tokens: int = 0
    cached: bool = False


class QuarterlyNoteExtractor:
    """
    Purpose:
        Q1 and Q3 reports carry no business chapter; their only narrative is the "主要会计数据、
        财务指标发生变动的情况及原因" table and the "其他提醒事项" note. `list_note_pages` cuts
        those pages (from the first NOTE_START page up to the statements), `compute_note_chars`
        measures the text so the caller can skip near-empty notes, and `fetch_notes` asks the LLM
        for orders and contracts, customers won, capacity changes, profit drivers and new
        products, keeping only items whose verbatim quote is on a sent page and whose kind is in
        KINDS (plan 12 phase 4, user request 2026-11-07).

    Contract:
        Input:
            llm:       BaseLlmClient
            max_chars: int > 0      -- note text sent
            system:    str | None   -- prompt; default prompts/quarterly_note_extraction.txt
        Output:
            instance; `list_note_pages`, `compute_note_chars`, `fetch_notes`
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/quarterly_notes.py (plan 12 phase 4 run)

    Test cases:
        TC-QNE-001  list_note_pages: from the change-reasons page to the page before the
                    statements, balance-sheet reason lines dropped, the note kept whole; no
                    marker -> []; compute_note_chars counts only the 其他提醒事项 text
        TC-QNE-002  valid reply: items kept with evidence; absent quote and unknown kind dropped
        TC-QNE-003  malformed reply raises DataSourceError
        TC-QNE-004  SZSE wording 三、其他重要事项 counts as the note
    """

    def __init__(
        self, llm: BaseLlmClient, max_chars: int = 8000, system: str | None = None
    ) -> None:
        self._llm = llm
        self._max_chars = max_chars
        self._system = system if system is not None else PROMPT.read_text(encoding="utf-8")

    def list_note_pages(self, pages: Sequence[str]) -> list[tuple[int, str]]:
        """
        Purpose:
            The narrative pages (1-based) of a quarterly report: before 其他提醒事项 only the
            operating change-reason lines (OPERATING_LINE plus CONTEXT_LINES), then the note.

        Contract:
            Input:
                pages: Sequence[str]  -- page texts
            Output:
                list[tuple[int, str]]  -- (page, text) in order; [] without a NOTE_START marker
            Raises:
                (none)
        """
        start = next((i for i, t in enumerate(pages) if NOTE_START.search(t)), None)
        if start is None:
            return []
        out, in_other = [], False
        for i in range(start, len(pages)):
            end = NOTE_END.search(pages[i])
            text = pages[i][: end.start()] if end else pages[i]
            kept = self._list_kept_lines(text, in_other)
            in_other = in_other or bool(OTHER_NOTE.search(text))
            if kept.strip():
                out.append((i + 1, kept))
            if end:
                break
        return out

    @staticmethod
    def _list_kept_lines(text: str, in_other: bool) -> str:
        """Before 其他提醒事项: only operating lines (and the CONTEXT_LINES after each, where a
        wrapped table cell carries the reason); from it on: everything."""
        lines = text.splitlines()
        cut = next((k for k, ln in enumerate(lines) if OTHER_NOTE.search(ln)), None)
        if in_other:
            return text
        head, tail = (lines, []) if cut is None else (lines[:cut], lines[cut:])
        keep: set[int] = set()
        for k, ln in enumerate(head):
            if OPERATING_LINE.search(ln):
                keep.update(range(k, min(len(head), k + 1 + CONTEXT_LINES)))
        return "\n".join([head[k] for k in sorted(keep)] + tail)

    def compute_note_chars(self, note_pages: Sequence[tuple[int, str]]) -> int:
        """
        Purpose:
            Characters of real text in the 其他提醒事项 note (after its heading): the 适用 /
            不适用 boxes, the standard lead sentence and whitespace removed. The caller skips
            reports below a threshold.

        Contract:
            Input:
                note_pages: Sequence[tuple[int, str]]
            Output:
                int >= 0
            Raises:
                (none)
        """
        text = "\n".join(t for _, t in note_pages)
        found = OTHER_NOTE.search(text)
        other = text[found.end() :] if found else ""
        return len(re.sub(r"\s+", "", EMPTY_NOTE.sub("", other)))

    def fetch_notes(
        self, company: str, period: str, note_pages: Sequence[tuple[int, str]]
    ) -> QuarterlyNoteResult:
        """
        Purpose:
            Ask the model about one report's notes and validate the answer against the text.

        Contract:
            Input:
                company: str; period: str (e.g. "2026Q3"); note_pages: Sequence[tuple[int, str]]
            Output:
                QuarterlyNoteResult
            Raises:
                DataSourceError  -- LLM failure or a reply that does not fit the JSON shape
        """
        text, used = QuoteChecker.build_prompt_text(note_pages, self._max_chars)
        reply = self._llm.fetch_json(
            self._system, f"公司：{company}\n报告期：{period}\n\n原文（按页）：\n{text}"
        )
        try:
            parsed = QuarterlyNoteReply.model_validate(reply.content)
        except ValidationError as exc:
            raise DataSourceError(f"{company}: reply does not fit the shape: {exc}") from exc
        checker = QuoteChecker(used)
        items, dropped = [], 0
        for item in parsed.items:
            ev = checker.find_evidence(item.quote, item.page)
            if ev is None or item.kind not in KINDS:
                dropped += 1
                continue
            items.append(
                {"kind": item.kind, "summary": item.summary, "value": item.value, "unit": item.unit,
                 "counterparty": item.counterparty, "evidence": ev}
            )  # fmt: skip
        tokens = reply.prompt_tokens + reply.completion_tokens
        return QuarterlyNoteResult(items, dropped, tokens, reply.cached)
