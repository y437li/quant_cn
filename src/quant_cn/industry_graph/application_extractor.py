"""DeepSeek reads a report's business sections: applications and named counterparties (D-102)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.quote_checker import QuoteChecker

ROLES = ("customer", "supplier", "partner", "competitor", "subsidiary", "mention")
PROMPT = Path(__file__).with_name("prompts") / "application_extraction.txt"


class ApplicationItem(BaseModel):
    """
    Purpose:
        One downstream application of a revenue line as the LLM returned it.

    Contract:
        Input:
            fields as declared (pydantic; unknown keys ignored)
        Output:
            pydantic model
        Raises:
            pydantic.ValidationError  -- wrong types in the LLM reply

    Used by:
        industry_graph.LineItem  -- applications

    Test cases:
        TC-AE-003  (via ApplicationExtractor) a malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    node_id: str | None = None
    name: str
    weight: str = "次要"
    quote: str
    page: int


class LineItem(BaseModel):
    """
    Purpose:
        One revenue line with its applications and customer types as returned.

    Contract:
        Input:
            fields as declared (pydantic; unknown keys ignored)
        Output:
            pydantic model
        Raises:
            pydantic.ValidationError  -- wrong types in the LLM reply

    Used by:
        industry_graph.ApplicationReply  -- lines

    Test cases:
        TC-AE-003  (via ApplicationExtractor) a malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    line: str
    applications: list[ApplicationItem] = []
    customer_types: list[str] = []


class CounterpartyItem(BaseModel):
    """
    Purpose:
        One company named in the text, with its role, as returned.

    Contract:
        Input:
            fields as declared (pydantic; unknown keys ignored)
        Output:
            pydantic model
        Raises:
            pydantic.ValidationError  -- wrong types in the LLM reply

    Used by:
        industry_graph.ApplicationReply  -- counterparties

    Test cases:
        TC-AE-003  (via ApplicationExtractor) a malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    name: str
    role: str
    detail: str = ""
    quote: str
    page: int


class ApplicationReply(BaseModel):
    """
    Purpose:
        The whole LLM reply of one report, validated before the quote check.

    Contract:
        Input:
            fields as declared (pydantic; unknown keys ignored)
        Output:
            pydantic model
        Raises:
            pydantic.ValidationError  -- wrong types in the LLM reply

    Used by:
        industry_graph.ApplicationExtractor  -- validates every reply

    Test cases:
        TC-AE-003  (via ApplicationExtractor) a malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    lines: list[LineItem] = []
    counterparties: list[CounterpartyItem] = []


@dataclass(frozen=True)
class ApplicationResult:
    """
    Purpose:
        What the model found in one report, after validation: per revenue line the downstream
        applications (taxonomy node or proposed name, main/secondary, evidence) and customer
        types; named counterparties with role and evidence; and the items dropped because
        their quote was not in the text.

    Contract:
        Input:
            lines:          dict[str, list[dict]]  -- line → [{node_id, name, weight, evidence}]
            customer_types: dict[str, list[str]]
            counterparties: list[dict]              -- {name, role, detail, evidence}
            dropped:        int >= 0
            tokens:         int >= 0
            cached:         bool
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.ApplicationExtractor  -- returned by fetch_applications

    Test cases:
        TC-AE-001  (via ApplicationExtractor) lines and counterparties filled from a valid reply
    """

    lines: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    customer_types: dict[str, list[str]] = field(default_factory=dict)
    counterparties: list[dict[str, Any]] = field(default_factory=list)
    dropped: int = 0
    tokens: int = 0
    cached: bool = False


class ApplicationExtractor:
    """
    Purpose:
        Send the business / industry pages of one report, its revenue lines and the candidate
        downstream taxonomy nodes to the LLM, and keep only answers whose verbatim quote is
        found in the supplied pages (whitespace ignored). A quote found on another page than
        claimed is kept with the page corrected. Unknown node ids become proposals (node_id
        None). Roles outside ROLES (customer, supplier, partner, competitor, subsidiary, mention)
        are dropped; competitor mentions are peer evidence (D-102).

    Contract:
        Input:
            llm:       BaseLlmClient
            max_chars: int > 0      -- page text sent, truncated in page order
            system:    str | None   -- prompt; default prompts/application_extraction.txt
        Output:
            instance; `fetch_applications`
        Raises:
            (none at construction)

    Used by:
        research_space prototypes (plan 12 phase 4a pilot)

    Test cases:
        TC-AE-001  valid reply: applications mapped to candidate ids, counterparties with roles
        TC-AE-002  quote check: missing quote dropped and counted; quote on another page gets
                   that page
        TC-AE-003  unknown node id becomes a proposal; bad role dropped; malformed reply raises
                   DataSourceError
    """

    def __init__(
        self, llm: BaseLlmClient, max_chars: int = 30000, system: str | None = None
    ) -> None:
        self._llm = llm
        self._max_chars = max_chars
        self._system = system if system is not None else PROMPT.read_text(encoding="utf-8")

    def fetch_applications(
        self,
        company: str,
        pages: Sequence[tuple[int, str]],
        revenue_lines: Sequence[str],
        candidates: Sequence[tuple[str, str]],
    ) -> ApplicationResult:
        """
        Purpose:
            Ask the model about one report and validate the answer against the text.

        Contract:
            Input:
                company:       str
                pages:         Sequence[tuple[int, str]]  -- (page number, text) in order
                revenue_lines: Sequence[str]              -- main-business items
                candidates:    Sequence[tuple[str, str]]  -- (node id, name) allowed for node_id
            Output:
                ApplicationResult
            Raises:
                DataSourceError  -- LLM failure or a reply that does not fit the JSON shape
        """
        text, used = QuoteChecker.build_prompt_text(pages, self._max_chars)
        user = (
            f"公司：{company}\n营收条目：{json.dumps(list(revenue_lines), ensure_ascii=False)}\n"
            f"候选下游节点（node_id: 名称）：\n"
            + "\n".join(f"{i}: {n}" for i, n in candidates)
            + f"\n\n年报原文（按页）：\n{text}"
        )
        reply = self._llm.fetch_json(self._system, user)
        try:
            parsed = ApplicationReply.model_validate(reply.content)
        except ValidationError as exc:
            raise DataSourceError(f"{company}: reply does not fit the shape: {exc}") from exc
        known = {i for i, _ in candidates}
        checker = QuoteChecker(used)
        lines, types, dropped = self._list_kept_lines(parsed, known, checker)
        parties, dropped_parties = self._list_kept_parties(parsed, checker)
        dropped += dropped_parties
        return ApplicationResult(
            lines,
            types,
            parties,
            dropped,
            reply.prompt_tokens + reply.completion_tokens,
            reply.cached,
        )

    def _list_kept_lines(
        self, parsed: ApplicationReply, known: set[str], checker: QuoteChecker
    ) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[str]], int]:
        lines: dict[str, list[dict[str, Any]]] = {}
        types: dict[str, list[str]] = {}
        dropped = 0
        for line in parsed.lines:
            kept = []
            for app in line.applications:
                ev = checker.find_evidence(app.quote, app.page)
                if ev is None:
                    dropped += 1
                    continue
                node = app.node_id if app.node_id in known else None
                weight = "主要" if app.weight == "主要" else "次要"
                kept.append({"node_id": node, "name": app.name, "weight": weight, "evidence": ev})
            lines[line.line] = kept
            types[line.line] = list(line.customer_types)
        return lines, types, dropped

    def _list_kept_parties(
        self, parsed: ApplicationReply, checker: QuoteChecker
    ) -> tuple[list[dict[str, Any]], int]:
        parties: list[dict[str, Any]] = []
        dropped = 0
        for cp in parsed.counterparties:
            ev = checker.find_evidence(cp.quote, cp.page)
            if ev is None or cp.role not in ROLES:
                dropped += 1
                continue
            parties.append({"name": cp.name, "role": cp.role, "detail": cp.detail, "evidence": ev})
        return parties, dropped
